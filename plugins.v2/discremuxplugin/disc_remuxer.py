import csv
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, Optional, Set

from app.log import logger


class DiscRemuxer:
    """蓝光/光盘源自动化重封装处理器。"""

    _TINFO_DURATION_INDEX: int = 9
    _MIN_DURATION_RATIO: float = 0.95
    _SAFE_FINISH_IDLE_SECONDS: int = 180
    _SAFE_FINISH_CHECK_SECONDS: int = 10
    _SAFE_FINISH_STABLE_ROUNDS: int = 3

    def __init__(self) -> None:
        """初始化 MakeMKV 进程句柄。"""
        self._process: Optional[subprocess.Popen] = None

    def terminate(self, timeout: int = 10) -> None:
        """终止当前正在运行的 MakeMKV 进程。"""
        process = self._process
        if not process or process.poll() is not None:
            return
        logger.info(f"正在终止 MakeMKV 进程: pid={process.pid}")
        process.terminate()
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            logger.warning(f"MakeMKV 进程未在 {timeout} 秒内退出，强制终止: pid={process.pid}")
            process.kill()
            process.wait(timeout=5)

    def validate_environment(self) -> None:
        """检查 MakeMKV 是否可用，如果不存在则自动尝试编译安装。"""
        try:
            subprocess.run(["makemkvcon"], capture_output=True, check=False)
            logger.info("环境检查通过，makemkvcon 已安装。")
        except FileNotFoundError:
            logger.warning("未检测到 makemkvcon，正在尝试自动编译安装，这可能需要几分钟，请耐心等待...")
            self._install_makemkv()
        except Exception as e:
            raise RuntimeError(f"环境检查失败，详细信息: {e}")

    def _install_makemkv(self) -> None:
        """调用插件内置脚本安装 MakeMKV。"""
        script_path = Path(__file__).parent / "install_makemkv.sh"
        if not script_path.exists():
            raise RuntimeError(f"安装脚本丢失: {script_path}")

        try:
            process = subprocess.run(
                ["bash", str(script_path)],
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info("MakeMKV 自动编译安装完成。")
            logger.debug(f"安装日志输出: {process.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"MakeMKV 自动安装失败:\n{e.stderr}")
            raise RuntimeError("MakeMKV 自动安装失败，请查看日志或尝试手动进入容器安装。")

    def _run_process(self, cmd: list[str]) -> str:
        """运行外部命令并返回标准输出。"""
        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=0,
        )
        try:
            output, _ = self._process.communicate()
            return_code = self._process.returncode
            if return_code != 0:
                stderr = "\n".join((output or "").splitlines()[-80:])
                raise subprocess.CalledProcessError(return_code, cmd, stderr=stderr)
            return output or ""
        finally:
            self._process = None

    def _run_makemkv_with_safe_finish(
            self,
            cmd: list[str],
            output_dir: Path,
            before: Set[Path],
            started_at: float,
            expected_duration: int,
    ) -> Path:
        """运行 MakeMKV，并在输出已稳定但进程不退出时安全收尾。"""
        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        output_lines: list[str] = []
        stable_rounds = 0
        last_signature: Optional[tuple[int, int]] = None
        output_valid_since: Optional[float] = None
        try:
            assert self._process.stdout is not None
            while True:
                line = self._process.stdout.readline()
                if line:
                    output_lines.append(line.rstrip("\n"))

                return_code = self._process.poll()
                now = time.time()
                generated_file = self._try_find_generated_mkv(output_dir, before, started_at)
                if generated_file:
                    try:
                        stat = generated_file.stat()
                        signature = (stat.st_size, int(stat.st_mtime))
                    except OSError:
                        signature = None
                    if signature and signature == last_signature:
                        stable_rounds += 1
                    elif signature:
                        stable_rounds = 1
                        last_signature = signature
                    if stable_rounds >= self._SAFE_FINISH_STABLE_ROUNDS:
                        actual_duration = self._probe_duration_seconds(generated_file)
                        if self._duration_is_valid(actual_duration, expected_duration):
                            output_valid_since = output_valid_since or now
                            if return_code is None and now - output_valid_since >= self._SAFE_FINISH_IDLE_SECONDS:
                                logger.warning(
                                    "MakeMKV 输出已稳定且时长达标，但进程仍未退出，执行安全收尾: "
                                    f"pid={self._process.pid}, file={generated_file}, "
                                    f"actual={actual_duration:.0f}s, expected={expected_duration}s"
                                )
                                self.terminate(timeout=10)
                                return generated_file
                            if return_code is not None:
                                self._raise_if_makemkv_failed(return_code, cmd, output_lines)
                                return generated_file

                if return_code is not None:
                    self._raise_if_makemkv_failed(return_code, cmd, output_lines)
                    return self._find_generated_mkv(output_dir, before, started_at)

                if not line:
                    time.sleep(self._SAFE_FINISH_CHECK_SECONDS)
        finally:
            self._process = None

    @staticmethod
    def _raise_if_makemkv_failed(return_code: int, cmd: list[str], output_lines: list[str]) -> None:
        """在 MakeMKV 返回失败状态时抛出包含尾部日志的异常。"""
        if return_code == 0:
            return
        stderr = "\n".join(output_lines[-80:])
        raise subprocess.CalledProcessError(return_code, cmd, stderr=stderr)

    def _extract_info(self, source_root: Path) -> Dict[int, Dict[int, str]]:
        """读取原盘 Title 信息。"""
        cmd = ["makemkvcon", "--robot", "--messages=-stdout", "info", f"file:{source_root}"]
        logger.info(f"正在扫描原盘媒体信息: {source_root}")
        output = self._run_process(cmd)

        titles: Dict[int, Dict[int, str]] = {}
        for line in output.splitlines():
            if line.startswith("TINFO:"):
                row = next(csv.reader([line[6:]]))
                titles.setdefault(int(row[0]), {})[int(row[1])] = row[3]
        return titles

    @staticmethod
    def parse_duration(duration_str: str) -> int:
        """将 H:M:S 时长转换为秒。"""
        try:
            h, m, s = map(int, duration_str.split(":"))
            return h * 3600 + m * 60 + s
        except (ValueError, AttributeError):
            return 0

    def _get_longest_title(self, titles: Dict[int, Dict[int, str]]) -> str:
        """根据 MakeMKV TINFO 时长选择最长 Title。"""
        if not titles:
            raise RuntimeError("未能在该原盘中找到任何可提取的 Title。")
        target_title, _ = max(
            titles.items(),
            key=lambda item: self.parse_duration(item[1].get(self._TINFO_DURATION_INDEX, "00:00:00")),
        )
        return str(target_title)

    def _title_duration_seconds(self, titles: Dict[int, Dict[int, str]], title_id: str) -> int:
        """读取指定 Title 的期望时长秒数。"""
        try:
            title_info = titles.get(int(title_id), {})
        except (TypeError, ValueError):
            return 0
        return self.parse_duration(title_info.get(self._TINFO_DURATION_INDEX, "00:00:00"))

    @staticmethod
    def _probe_duration_seconds(mkv_file: Path) -> float:
        """使用 ffprobe 读取 MKV 实际时长秒数。"""
        try:
            process = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(mkv_file),
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
            if process.returncode != 0:
                logger.warning(f"ffprobe 读取 MKV 时长失败: {mkv_file}, {process.stderr}")
                return 0
            return float((process.stdout or "0").strip() or 0)
        except Exception as err:
            logger.warning(f"ffprobe 读取 MKV 时长异常: {mkv_file}, {err}")
            return 0

    @staticmethod
    def _find_generated_mkv(output_dir: Path, before: set[Path], started_at: float) -> Path:
        """查找 MakeMKV 本轮新生成的 MKV 文件。"""
        candidates = []
        for mkv_file in output_dir.glob("*.mkv"):
            if mkv_file in before or not mkv_file.is_file():
                continue
            try:
                stat = mkv_file.stat()
            except OSError:
                continue
            if stat.st_mtime >= started_at - 2:
                candidates.append((stat.st_mtime, stat.st_size, mkv_file))
        if not candidates:
            raise RuntimeError(f"处理完成，但未能找到 MakeMKV 新生成的 MKV 文件: {output_dir}")
        candidates.sort(reverse=True)
        return candidates[0][2]

    @classmethod
    def _duration_is_valid(cls, actual_duration: float, expected_duration: int) -> bool:
        """判断实际输出时长是否达到期望主片时长下限。"""
        if expected_duration <= 0:
            return actual_duration > 0
        return actual_duration >= expected_duration * cls._MIN_DURATION_RATIO

    @classmethod
    def _try_find_generated_mkv(cls, output_dir: Path, before: set[Path], started_at: float) -> Optional[Path]:
        """尝试查找本轮 MakeMKV 新生成的 MKV 文件。"""
        try:
            return cls._find_generated_mkv(output_dir, before, started_at)
        except RuntimeError:
            return None

    def _validate_generated_mkv(self, generated_file: Path, expected_duration: int) -> None:
        """校验输出 MKV 的实际时长是否接近选中正片时长。"""
        if expected_duration <= 0:
            logger.warning(f"未读取到选中 Title 的有效时长，跳过输出时长校验: {generated_file}")
            return
        actual_duration = self._probe_duration_seconds(generated_file)
        min_duration = expected_duration * self._MIN_DURATION_RATIO
        if actual_duration < min_duration:
            raise RuntimeError(
                "重封装输出时长异常，已阻止入库: "
                f"file={generated_file}, actual={actual_duration:.0f}s, expected={expected_duration}s"
            )
        logger.info(
            "重封装输出时长校验通过: "
            f"file={generated_file.name}, actual={actual_duration:.0f}s, expected={expected_duration}s"
        )

    def remux_to_mkv(
        self,
        source_root_path: str,
        output_file_path: str,
    ) -> Path:
        """提取最长正片，先生成 partial 文件，成功后改名为最终 MKV。"""
        source_root = Path(source_root_path)
        output_file = Path(output_file_path)
        output_dir = output_file.parent
        partial_file = output_file.with_suffix(".partial.mkv")

        output_dir.mkdir(parents=True, exist_ok=True)
        if partial_file.exists():
            partial_file.unlink()

        titles = self._extract_info(source_root)
        target_title = self._get_longest_title(titles)
        expected_duration = self._title_duration_seconds(titles, target_title)
        logger.info(f"自动识别主正片 Title ID: {target_title}, expected_duration={expected_duration}s")

        with tempfile.TemporaryDirectory(prefix=".discremux-", dir=output_dir) as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            before = set(temp_dir.glob("*.mkv"))
            started_at = time.time()
            cmd = [
                "makemkvcon",
                "--robot",
                "--messages=-stdout",
                "mkv",
                f"file:{source_root}",
                target_title,
                temp_dir.as_posix(),
            ]
            logger.info(f"开始执行 MakeMKV 重封装: source={source_root}, output_dir={temp_dir}")

            generated_file = self._run_makemkv_with_safe_finish(
                cmd=cmd,
                output_dir=temp_dir,
                before=before,
                started_at=started_at,
                expected_duration=expected_duration,
            )
            self._validate_generated_mkv(generated_file, expected_duration)
            try:
                generated_file.replace(partial_file)
            except OSError:
                shutil.move(generated_file.as_posix(), partial_file.as_posix())

        partial_file.replace(output_file)
        logger.info(f"重封装完成: {output_file}")
        return output_file
