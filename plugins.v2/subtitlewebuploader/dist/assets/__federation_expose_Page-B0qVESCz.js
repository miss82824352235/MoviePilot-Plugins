import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,createElementVNode:_createElementVNode,renderList:_renderList,Fragment:_Fragment,openBlock:_openBlock,createElementBlock:_createElementBlock,normalizeClass:_normalizeClass,withKeys:_withKeys,createCommentVNode:_createCommentVNode,unref:_unref,withModifiers:_withModifiers,createBlock:_createBlock,mergeProps:_mergeProps} = await importShared('vue');


const _hoisted_1 = { class: "subweb-shell" };
const _hoisted_2 = { class: "hero-panel mb-4" };
const _hoisted_3 = { class: "hero-content" };
const _hoisted_4 = { class: "hero-main" };
const _hoisted_5 = { class: "orb" };
const _hoisted_6 = { class: "hero-actions" };
const _hoisted_7 = { class: "metrics-grid" };
const _hoisted_8 = { class: "metric-card" };
const _hoisted_9 = { class: "metric-card" };
const _hoisted_10 = { class: "metric-card" };
const _hoisted_11 = { class: "metric-card" };
const _hoisted_12 = { class: "quick-rail mb-4" };
const _hoisted_13 = ["onClick"];
const _hoisted_14 = { class: "section-title" };
const _hoisted_15 = { class: "d-flex ga-2 mb-3" };
const _hoisted_16 = { class: "media-stack" };
const _hoisted_17 = ["onClick"];
const _hoisted_18 = { class: "poster" };
const _hoisted_19 = { class: "media-info" };
const _hoisted_20 = {
  key: 0,
  class: "empty-box"
};
const _hoisted_21 = { class: "section-title" };
const _hoisted_22 = { class: "target-toolbar" };
const _hoisted_23 = { class: "range-picker mb-3" };
const _hoisted_24 = { class: "episode-grid" };
const _hoisted_25 = ["onClick"];
const _hoisted_26 = {
  key: 0,
  class: "empty-box full"
};
const _hoisted_27 = { class: "section-title" };
const _hoisted_28 = { class: "action-tabs" };
const _hoisted_29 = ["onClick"];
const _hoisted_30 = {
  key: 0,
  class: "panel-area"
};
const _hoisted_31 = {
  key: 0,
  class: "upload-progress mb-3"
};
const _hoisted_32 = { class: "upload-progress-head" };
const _hoisted_33 = { class: "d-flex ga-2 flex-wrap mb-3" };
const _hoisted_34 = {
  key: 1,
  class: "result-list"
};
const _hoisted_35 = {
  key: 1,
  class: "panel-area"
};
const _hoisted_36 = { class: "d-flex ga-2 flex-wrap mb-3" };
const _hoisted_37 = { class: "candidate-stack" };
const _hoisted_38 = ["checked", "onChange"];
const _hoisted_39 = {
  key: 0,
  class: "empty-box compact"
};
const _hoisted_40 = {
  key: 2,
  class: "panel-area"
};
const _hoisted_41 = { class: "d-flex ga-2 flex-wrap mb-3" };
const _hoisted_42 = { class: "candidate-stack" };
const _hoisted_43 = ["checked", "onChange"];
const _hoisted_44 = {
  key: 0,
  class: "empty-box compact"
};
const _hoisted_45 = {
  key: 3,
  class: "panel-area"
};
const _hoisted_46 = { class: "ai-card" };
const _hoisted_47 = { class: "d-flex ga-2 flex-wrap mt-3" };
const _hoisted_48 = { class: "section-title mb-2" };
const _hoisted_49 = { class: "result-summary" };
const _hoisted_50 = {
  key: 0,
  class: "log mt-3"
};
const _hoisted_51 = { class: "batch-context" };
const _hoisted_52 = { class: "batch-actions" };

const {computed,onMounted,reactive,ref} = await importShared('vue');



const _sfc_main = {
  __name: 'Page',
  props: { api: { type: Object, default: null }, pluginId: { type: String, default: 'SubtitleWebUploader' } },
  setup(__props) {

const props = __props;
const keyword = ref('');
const rangeText = ref('');
const dragOver = ref(false);
const uploadState = reactive({ active: false, percent: 0, label: '等待上传', startedAt: 0, loaded: 0, total: 0 });
const mediaType = ref('all');
const medias = ref([]);
const targets = ref([]);
const selectedTargets = ref([]);
const currentMedia = ref(null);
const pickedFiles = ref([]);
const lastPreview = ref(null);
const onlineResults = ref([]);
const selectedOnline = ref([]);
const subtitles = ref([]);
const selectedSubtitles = ref([]);
const status = ref(null);
const activePanel = ref('upload');
const showLog = ref(false);
const logText = ref('准备好了');
const lastResult = ref('待操作');
const loading = reactive({ status: false, search: false, prepare: false, apply: false, online: false, subtitles: false });
const snackbar = reactive({ show: false, text: '', color: 'info' });
const mediaTypes = [{ title: '全部', value: 'all' }, { title: '电影', value: 'movie' }, { title: '电视剧', value: 'tv' }];
const navItems = [
  { title: '上传外挂', value: 'upload', icon: 'mdi-cloud-upload-outline' },
  { title: '在线字幕', value: 'online', icon: 'mdi-web' },
  { title: '外挂管理', value: 'manage', icon: 'mdi-folder-cog-outline' },
  { title: 'AI翻译', value: 'ai', icon: 'mdi-creation' },
];
const actionTabs = navItems;
const previewItems = computed(() => (lastPreview.value?.data?.items || []));
const currentMediaTitle = computed(() => currentMedia.value ? (currentMedia.value.title || currentMedia.value.name || '已选择') : '未选择');
const actionReady = computed(() => selectedTargets.value.length > 0);
const logHeadline = computed(() => String(logText.value || '').split('\n')[0].slice(0, 160) || '暂无结果');
const uploadEtaText = computed(() => {
  if (!uploadState.active) return uploadState.percent >= 100 ? '已完成' : '等待开始'
  const elapsed = Math.max((Date.now() - uploadState.startedAt) / 1000, 0.1);
  const speed = uploadState.loaded / elapsed;
  if (!speed || !uploadState.total || uploadState.percent <= 0) return '预计时间计算中'
  const remain = Math.max((uploadState.total - uploadState.loaded) / speed, 0);
  return remain < 1 ? '即将完成' : `预计剩余 ${Math.ceil(remain)} 秒`
});

function notify(text, color = 'info') { snackbar.text = text; snackbar.color = color; snackbar.show = true; lastResult.value = text; }
function out(data) { logText.value = typeof data === 'string' ? data : JSON.stringify(data, null, 2); }
function mediaKey(m) { return `${m?.tmdb_id || m?.tmdbid || m?.douban_id || m?.title || ''}-${m?.year || ''}` }
function mediaTypeText(m) { return m.media_type || m.type || '未知类型' }
function episodeLabel(t) { return t.episode_text || t.episode || t.name || t.title || '目标' }
function shortTargetName(t) { return (t.filename || t.name || t.path || t.file_path || t.id || '').split('/').pop().slice(0, 24) }
function switchPanel(panel) { activePanel.value = panel; const name = actionTabs.find(x => x.value === panel)?.title || panel; notify(`已切换到${name}`, 'info'); }
function onDragEnter() { dragOver.value = true; }
function onDragLeave() { dragOver.value = false; }
function onDropFiles(event) { dragOver.value = false; const files = Array.from(event.dataTransfer?.files || []); if (!files.length) return; pickedFiles.value = files; notify(`已拖入 ${files.length} 个文件`, 'success'); autoPrepareUpload(); }
function route(path) { return `plugin/${props.pluginId}${path}` }
async function apiGet(path, params = {}) {
  const clean = Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ''));
  if (props.api?.get) return await props.api.get(route(path), { params: clean })
  const qs = new URLSearchParams(clean).toString();
  const r = await fetch(`/api/v1/plugin/${props.pluginId}${path}${qs ? '?' + qs : ''}`);
  const data = await r.json(); if (!r.ok) throw new Error(data.detail || data.msg || r.statusText); return data
}
async function apiPost(path, body = {}) {
  if (props.api?.post) return await props.api.post(route(path), body)
  const r = await fetch(`/api/v1/plugin/${props.pluginId}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const data = await r.json(); if (!r.ok) throw new Error(data.detail || data.msg || r.statusText); return data
}
async function loadStatus() { loading.status = true; try { const r = await apiGet('/subtitleweb_bridge/status'); status.value = r.data || r; out(r); notify('状态已刷新', 'success'); } catch (e) { notify(e.message, 'error'); out(e.message); } finally { loading.status = false; } }
async function loadSelection() { try { const r = await apiGet('/subtitleweb_bridge/selection', { user_id: 'web' }); selectedTargets.value = r.data?.selected_target_ids || []; } catch {} }
async function searchMedia() { notify('开始搜索影片', 'info'); loading.search = true; try { const r = await apiGet('/subtitleweb_bridge/search', { keyword: keyword.value, media_type: mediaType.value, page_size: 20 }); medias.value = r.data?.medias || []; out(r); notify(`找到 ${medias.value.length} 条`, 'success'); } catch (e) { notify(e.message, 'error'); out(e.message); } finally { loading.search = false; } }
async function loadTargets(m) { currentMedia.value = m; notify(`已选择影片：${m.title || m.name || '未命名'}`, 'info'); try { const params = {}; ['media_type','type','tmdb_id','tmdbid','douban_id','doubanid','title','name','year','season'].forEach(k => { if (m[k]) params[k.replace('tmdbid','tmdb_id').replace('doubanid','douban_id').replace('name','title')] = m[k]; }); const r = await apiGet('/subtitleweb_bridge/targets', params); targets.value = r.data?.targets || r.data?.items || r.data?.files || []; out(r); notify(`读取到 ${targets.value.length} 个目标`, 'success'); } catch (e) { notify(e.message, 'error'); out(e.message); } }
function toggleTarget(id, checked) { if (checked && !selectedTargets.value.includes(id)) selectedTargets.value.push(id); if (!checked) selectedTargets.value = selectedTargets.value.filter(x => x !== id); }
function selectAllTargets() { notify('已全选当前目标', 'success'); selectedTargets.value = [...new Set([...selectedTargets.value, ...targets.value.map(t => t.id).filter(Boolean)])]; }
function invertTargets() { notify('已反选当前目标', 'success'); const all = targets.value.map(t => t.id).filter(Boolean); selectedTargets.value = all.filter(id => !selectedTargets.value.includes(id)); }
function clearTargets() { selectedTargets.value = []; notify('已清空选择', 'info'); }
function episodeNumberOf(t) {
  const raw = String(t.episode || t.episode_number || t.episode_text || t.name || t.title || '');
  const m = raw.match(/(?:E|第)?(\d{1,4})(?:集)?/i);
  return m ? Number(m[1]) : null
}
function parseRangeText(text) {
  const picked = new Set();
  String(text || '').split(',').map(x => x.trim()).filter(Boolean).forEach(part => {
    const m = part.match(/^(\d+)\s*-\s*(\d+)$/);
    if (m) {
      const a = Number(m[1]); const b = Number(m[2]); const start = Math.min(a, b); const end = Math.max(a, b);
      for (let i = start; i <= end; i++) picked.add(i);
    } else if (/^\d+$/.test(part)) picked.add(Number(part));
  });
  return picked
}
function selectRange() {
  const nums = parseRangeText(rangeText.value);
  if (!nums.size) return notify('请输入集数范围，例如 1-12 或 1,3,5', 'warning')
  const ids = targets.value.filter(t => nums.has(episodeNumberOf(t))).map(t => t.id).filter(Boolean);
  selectedTargets.value = [...new Set([...selectedTargets.value, ...ids])];
  notify(`已按范围选择 ${ids.length} 个目标`, ids.length ? 'success' : 'warning');
}
function jumpAction(panel) { activePanel.value = panel; if (panel === 'manage') refreshSubtitles(); }
async function saveSelection() { notify('正在保存当前选择', 'info'); try { const r = await apiPost('/subtitleweb_bridge/selection/save', { user_id: 'web', target_ids: selectedTargets.value, media: currentMedia.value || {} }); out(r); notify('已保存选择', 'success'); } catch (e) { notify(e.message, 'error'); } }
function uploadForm(path) {
  const fd = new FormData(); fd.append('target_ids', JSON.stringify(selectedTargets.value)); for (const f of pickedFiles.value || []) fd.append('files', f);
  uploadState.active = true; uploadState.percent = 0; uploadState.label = '正在上传并生成预览'; uploadState.startedAt = Date.now(); uploadState.loaded = 0; uploadState.total = [...(pickedFiles.value || [])].reduce((n, f) => n + (f.size || 0), 0);
  notify(`开始上传 ${pickedFiles.value?.length || 0} 个文件`, 'info');
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `/api/v1/plugin/${props.pluginId}${path}`);
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) { uploadState.loaded = event.loaded; uploadState.total = event.total; uploadState.percent = Math.min(98, Math.round((event.loaded / event.total) * 100)); }
    };
    xhr.onload = () => {
      uploadState.active = false; uploadState.percent = 100; uploadState.label = '上传完成，预览已生成';
      try { const data = JSON.parse(xhr.responseText || '{}'); if (xhr.status >= 200 && xhr.status < 300) resolve(data); else reject(new Error(data.detail || data.msg || xhr.statusText)); } catch (e) { reject(e); }
    };
    xhr.onerror = () => { uploadState.active = false; reject(new Error('上传失败，请检查网络或文件大小')); };
    xhr.send(fd);
  })
}
async function autoPrepareUpload() { if (selectedTargets.value.length && pickedFiles.value?.length) { notify('已选择文件，自动生成匹配预览', 'info'); await prepareUpload(); } }
async function prepareUpload() { notify('准备生成字幕匹配预览', 'info'); if (!selectedTargets.value.length) return notify('请先选集数', 'warning'); if (!pickedFiles.value?.length) return notify('请先选择字幕文件', 'warning'); loading.prepare = true; try { const r = await uploadForm('/subtitleweb_bridge/upload/prepare'); lastPreview.value = r; out(r); notify(`预览好了：${previewItems.value.length} 条`, 'success'); } catch (e) { lastPreview.value = null; notify(e.message, 'error'); out(e.message); } finally { loading.prepare = false; } }
async function applyUpload() { notify('准备上传字幕', 'info'); if (!lastPreview.value) await prepareUpload(); if (!lastPreview.value) return; loading.apply = true; try { const r = await apiPost('/subtitleweb_bridge/upload/apply', { confirm: true, fix_timeline: true, allow_risky_offset: false, session_id: lastPreview.value.data?.session_id, items: lastPreview.value.data?.items || [] }); out(r); notify('上传完成', 'success'); await refreshSubtitles(); } catch (e) { notify(`上传失败：${e.message}`, 'error'); out(e.message); } finally { loading.apply = false; } }
function clearFiles() { pickedFiles.value = []; lastPreview.value = null; notify('已清空文件', 'success'); }
async function onlineSearch() { notify('开始搜索在线字幕', 'info'); if (!selectedTargets.value.length) return notify('请先选集数', 'warning'); loading.online = true; try { const r = await apiPost('/subtitleweb_bridge/online/search', { target_ids: selectedTargets.value, scope: 'auto' }); onlineResults.value = r.data?.results || []; selectedOnline.value = []; out(r); notify(`在线结果：${onlineResults.value.length} 条`, 'success'); } catch (e) { notify(e.message, 'error'); out(e.message); } finally { loading.online = false; } }
function toggleOnline(i, checked) { toggleIndex(selectedOnline.value, i, checked); }
function toggleIndex(arr, i, checked) { const p = arr.indexOf(i); if (checked && p < 0) arr.push(i); if (!checked && p >= 0) arr.splice(p, 1); }
async function onlinePreview() { notify('准备生成在线字幕预览', 'info'); try { const results = selectedOnline.value.map(i => onlineResults.value[i]).filter(Boolean); if (!results.length) throw new Error('请先勾选在线字幕'); const r = await apiPost('/subtitleweb_bridge/online/download_preview', { target_ids: selectedTargets.value, results }); lastPreview.value = r; activePanel.value = 'upload'; out(r); notify('在线字幕预览好了', 'success'); } catch (e) { notify(e.message, 'error'); out(e.message); } }
async function refreshSubtitles() { notify('正在刷新外挂字幕列表', 'info'); if (!selectedTargets.value.length) return notify('请先选集数', 'warning'); if (!currentMedia.value) return notify('请先选影片', 'warning'); loading.subtitles = true; try { await loadTargets(currentMedia.value); const set = new Set(selectedTargets.value); const lines = []; targets.value.filter(t => set.has(t.id)).forEach(t => (t.subtitles || []).forEach(sub => lines.push({ target_id: t.id, target: t.episode_text || t.name || t.title || t.filename || t.id, name: sub.name || sub.filename || '', path: sub.path || sub.file_path || '' }))); subtitles.value = lines; selectedSubtitles.value = []; notify(`字幕列表：${lines.length} 条`, 'success'); } catch (e) { notify(e.message, 'error'); out(e.message); } finally { loading.subtitles = false; } }
async function deleteSelectedSubtitles() { notify('准备删除外挂字幕', 'warning'); try { const items = selectedSubtitles.value.map(i => subtitles.value[i]).filter(Boolean).map(s => ({ target_id: s.target_id, subtitle_path: s.path, subtitle_name: s.name })); if (!items.length) throw new Error('请先勾选字幕'); out(await apiPost('/subtitleweb_bridge/delete/preview', { items })); if (!confirm(`删除选中的 ${items.length} 个字幕？`)) return; const r = await apiPost('/subtitleweb_bridge/delete/apply', { confirm: true, items }); out(r); notify('删除完成', 'success'); await refreshSubtitles(); } catch (e) { notify(e.message, 'error'); out(e.message); } }
async function fixSelectedSubtitles() { notify('准备提交调轴任务', 'info'); try { const items = selectedSubtitles.value.map(i => subtitles.value[i]).filter(Boolean).map(s => ({ target_id: s.target_id, subtitle_path: s.path, subtitle_name: s.name })); if (!items.length) throw new Error('请先勾选字幕'); const r = await apiPost('/subtitleweb_bridge/timeline/fix', { confirm: true, items, allow_risky_offset: false }); out(r); notify('已提交时间轴处理', 'success'); } catch (e) { notify(e.message, 'error'); out(e.message); } }
async function aiPreview() { notify('开始预检 AI 任务', 'info'); try { const r = await apiPost('/subtitleweb_bridge/ai/preview', { target_ids: selectedTargets.value }); out(r); notify('检查完成', 'success'); } catch (e) { notify(e.message, 'error'); out(e.message); } }
async function aiSubmit() { notify('准备提交 AI 翻译任务', 'info'); try { const r = await apiPost('/subtitleweb_bridge/ai/submit', { confirm: true, target_ids: selectedTargets.value, source_policy: 'auto', overwrite_policy: 'skip' }); out(r); notify('AI 已提交', 'success'); } catch (e) { notify(e.message, 'error'); out(e.message); } }
async function aiCancel() { notify('准备取消 AI 任务', 'warning'); try { if (!selectedTargets.value.length) throw new Error('请先选集数'); if (!confirm('取消选中目标的 AI 任务？')) return; const r = await apiPost('/subtitleweb_bridge/ai/cancel', { confirm: true, target_ids: selectedTargets.value }); out(r); notify('AI 任务已取消', 'success'); } catch (e) { notify(e.message, 'error'); out(e.message); } }
async function tasks() { notify('正在查询任务状态', 'info'); try { const r = await apiPost('/subtitleweb_bridge/tasks', { target_ids: selectedTargets.value, limit: 100 }); out(r); notify('状态已刷新', 'success'); } catch (e) { notify(e.message, 'error'); out(e.message); } }

onMounted(() => { loadStatus(); loadSelection(); });

return (_ctx, _cache) => {
  const _component_v_snackbar = _resolveComponent("v-snackbar");
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_select = _resolveComponent("v-select");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_file_input = _resolveComponent("v-file-input");
  const _component_v_progress_linear = _resolveComponent("v-progress-linear");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_list_item = _resolveComponent("v-list-item");
  const _component_v_list = _resolveComponent("v-list");
  const _component_v_menu = _resolveComponent("v-menu");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_v_snackbar, {
      modelValue: snackbar.show,
      "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((snackbar.show) = $event)),
      color: snackbar.color,
      location: "bottom right",
      timeout: "2800"
    }, {
      default: _withCtx(() => [
        _createTextVNode(_toDisplayString(snackbar.text), 1)
      ]),
      _: 1
    }, 8, ["modelValue", "color"]),
    _createElementVNode("section", _hoisted_2, [
      _cache[18] || (_cache[18] = _createElementVNode("div", { class: "hero-glow hero-glow-a" }, null, -1)),
      _cache[19] || (_cache[19] = _createElementVNode("div", { class: "hero-glow hero-glow-b" }, null, -1)),
      _createElementVNode("div", _hoisted_3, [
        _createElementVNode("div", _hoisted_4, [
          _createElementVNode("div", _hoisted_5, [
            _createVNode(_component_v_icon, {
              icon: "mdi-subtitles-outline",
              size: "34"
            })
          ]),
          _cache[12] || (_cache[12] = _createElementVNode("div", { class: "min-w-0" }, [
            _createElementVNode("div", { class: "eyebrow" }, "Subtitle Command Center"),
            _createElementVNode("h1", null, "字幕控制台"),
            _createElementVNode("p", null, "选片、选集、上传、在线字幕、AI 翻译和外挂管理，一页完成。")
          ], -1))
        ]),
        _createElementVNode("div", _hoisted_6, [
          _createVNode(_component_v_chip, {
            color: status.value?.enabled ? 'success' : 'warning',
            variant: "flat",
            class: "status-chip"
          }, {
            default: _withCtx(() => [
              _createTextVNode(_toDisplayString(status.value?.enabled ? '插件已启用' : '插件未启用'), 1)
            ]),
            _: 1
          }, 8, ["color"]),
          _createVNode(_component_v_chip, {
            color: status.value?.bridge ? 'cyan' : 'error',
            variant: "flat",
            class: "status-chip"
          }, {
            default: _withCtx(() => [
              _createTextVNode(_toDisplayString(status.value?.bridge ? `桥接：${status.value.bridge_mode || '未知'}` : '桥接异常'), 1)
            ]),
            _: 1
          }, 8, ["color"]),
          _createVNode(_component_v_btn, {
            color: "white",
            variant: "tonal",
            class: "hero-btn",
            loading: loading.status,
            onClick: loadStatus
          }, {
            default: _withCtx(() => [
              _createVNode(_component_v_icon, {
                icon: "mdi-refresh",
                class: "mr-1"
              }),
              _cache[13] || (_cache[13] = _createTextVNode("刷新 ", -1))
            ]),
            _: 1
          }, 8, ["loading"])
        ])
      ]),
      _createElementVNode("div", _hoisted_7, [
        _createElementVNode("div", _hoisted_8, [
          _cache[14] || (_cache[14] = _createElementVNode("span", null, "当前影片", -1)),
          _createElementVNode("strong", null, _toDisplayString(currentMediaTitle.value), 1)
        ]),
        _createElementVNode("div", _hoisted_9, [
          _cache[15] || (_cache[15] = _createElementVNode("span", null, "已选目标", -1)),
          _createElementVNode("strong", null, _toDisplayString(selectedTargets.value.length) + " 集", 1)
        ]),
        _createElementVNode("div", _hoisted_10, [
          _cache[16] || (_cache[16] = _createElementVNode("span", null, "待上传文件", -1)),
          _createElementVNode("strong", null, _toDisplayString(pickedFiles.value?.length || 0) + " 个", 1)
        ]),
        _createElementVNode("div", _hoisted_11, [
          _cache[17] || (_cache[17] = _createElementVNode("span", null, "最近结果", -1)),
          _createElementVNode("strong", null, _toDisplayString(lastResult.value), 1)
        ])
      ])
    ]),
    _createElementVNode("div", _hoisted_12, [
      (_openBlock(), _createElementBlock(_Fragment, null, _renderList(navItems, (item) => {
        return _createElementVNode("button", {
          key: item.value,
          class: _normalizeClass(['rail-btn', { active: activePanel.value === item.value }]),
          onClick: $event => (switchPanel(item.value))
        }, [
          _createVNode(_component_v_icon, {
            icon: item.icon,
            size: "18"
          }, null, 8, ["icon"]),
          _createElementVNode("span", null, _toDisplayString(item.title), 1)
        ], 10, _hoisted_13)
      }), 64))
    ]),
    _createVNode(_component_v_row, {
      class: "workbench",
      align: "stretch"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_col, {
          cols: "12",
          lg: "4"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              class: "glass-card h-100",
              rounded: "xl",
              variant: "flat"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_text, null, {
                  default: _withCtx(() => [
                    _createElementVNode("div", _hoisted_14, [
                      _cache[20] || (_cache[20] = _createElementVNode("div", null, [
                        _createElementVNode("span", { class: "section-kicker" }, "STEP 01"),
                        _createElementVNode("h2", null, "找影片")
                      ], -1)),
                      _createVNode(_component_v_chip, {
                        size: "small",
                        variant: "tonal"
                      }, {
                        default: _withCtx(() => [
                          _createTextVNode(_toDisplayString(medias.value.length) + " 条", 1)
                        ]),
                        _: 1
                      })
                    ]),
                    _createVNode(_component_v_text_field, {
                      modelValue: keyword.value,
                      "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((keyword).value = $event)),
                      label: "搜索电影 / 剧集",
                      "prepend-inner-icon": "mdi-magnify",
                      variant: "outlined",
                      density: "comfortable",
                      clearable: "",
                      onKeyup: _withKeys(searchMedia, ["enter"])
                    }, null, 8, ["modelValue"]),
                    _createElementVNode("div", _hoisted_15, [
                      _createVNode(_component_v_select, {
                        modelValue: mediaType.value,
                        "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((mediaType).value = $event)),
                        items: mediaTypes,
                        label: "类型",
                        variant: "outlined",
                        density: "comfortable",
                        "hide-details": ""
                      }, null, 8, ["modelValue"]),
                      _createVNode(_component_v_btn, {
                        color: "primary",
                        class: "search-btn",
                        loading: loading.search,
                        onClick: searchMedia
                      }, {
                        default: _withCtx(() => [...(_cache[21] || (_cache[21] = [
                          _createTextVNode("搜索", -1)
                        ]))]),
                        _: 1
                      }, 8, ["loading"])
                    ]),
                    _createElementVNode("div", _hoisted_16, [
                      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(medias.value, (m) => {
                        return (_openBlock(), _createElementBlock("button", {
                          key: mediaKey(m),
                          class: _normalizeClass(['media-card', { selected: mediaKey(m) === mediaKey(currentMedia.value || {}) }]),
                          onClick: $event => (loadTargets(m))
                        }, [
                          _createElementVNode("div", _hoisted_18, [
                            _createVNode(_component_v_icon, { icon: "mdi-movie-open-outline" })
                          ]),
                          _createElementVNode("div", _hoisted_19, [
                            _createElementVNode("strong", null, _toDisplayString(m.title || m.name || '未命名'), 1),
                            _createElementVNode("span", null, _toDisplayString(m.year || '未知年份') + " · " + _toDisplayString(mediaTypeText(m)) + " · TMDB " + _toDisplayString(m.tmdb_id || m.tmdbid || '-'), 1)
                          ]),
                          _createVNode(_component_v_icon, { icon: "mdi-chevron-right" })
                        ], 10, _hoisted_17))
                      }), 128)),
                      (!medias.value.length)
                        ? (_openBlock(), _createElementBlock("div", _hoisted_20, [
                            _createVNode(_component_v_icon, {
                              icon: "mdi-magnify-scan",
                              size: "32"
                            }),
                            _cache[22] || (_cache[22] = _createElementVNode("div", null, "搜索后选择影片", -1)),
                            _cache[23] || (_cache[23] = _createElementVNode("small", null, "会从字幕匹配插件读取本地目标文件", -1))
                          ]))
                        : _createCommentVNode("", true)
                    ])
                  ]),
                  _: 1
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_v_col, {
          cols: "12",
          lg: "4"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              class: "glass-card h-100",
              rounded: "xl",
              variant: "flat"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_text, null, {
                  default: _withCtx(() => [
                    _createElementVNode("div", _hoisted_21, [
                      _cache[24] || (_cache[24] = _createElementVNode("div", null, [
                        _createElementVNode("span", { class: "section-kicker" }, "STEP 02"),
                        _createElementVNode("h2", null, "选集数")
                      ], -1)),
                      _createVNode(_component_v_chip, {
                        size: "small",
                        color: "primary",
                        variant: "tonal"
                      }, {
                        default: _withCtx(() => [
                          _createTextVNode("已选 " + _toDisplayString(selectedTargets.value.length), 1)
                        ]),
                        _: 1
                      })
                    ]),
                    _createElementVNode("div", _hoisted_22, [
                      _createVNode(_component_v_btn, {
                        size: "small",
                        variant: "tonal",
                        onClick: selectAllTargets
                      }, {
                        default: _withCtx(() => [...(_cache[25] || (_cache[25] = [
                          _createTextVNode("全选", -1)
                        ]))]),
                        _: 1
                      }),
                      _createVNode(_component_v_btn, {
                        size: "small",
                        variant: "tonal",
                        onClick: invertTargets
                      }, {
                        default: _withCtx(() => [...(_cache[26] || (_cache[26] = [
                          _createTextVNode("反选", -1)
                        ]))]),
                        _: 1
                      }),
                      _createVNode(_component_v_btn, {
                        size: "small",
                        variant: "tonal",
                        onClick: clearTargets
                      }, {
                        default: _withCtx(() => [...(_cache[27] || (_cache[27] = [
                          _createTextVNode("清空", -1)
                        ]))]),
                        _: 1
                      }),
                      _createVNode(_component_v_btn, {
                        size: "small",
                        color: "primary",
                        variant: "flat",
                        onClick: saveSelection
                      }, {
                        default: _withCtx(() => [...(_cache[28] || (_cache[28] = [
                          _createTextVNode("保存选择", -1)
                        ]))]),
                        _: 1
                      })
                    ]),
                    _createElementVNode("div", _hoisted_23, [
                      _createVNode(_component_v_text_field, {
                        modelValue: rangeText.value,
                        "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((rangeText).value = $event)),
                        label: "快速选择集数",
                        placeholder: "例如 1-12 或 1,3,5",
                        density: "compact",
                        variant: "outlined",
                        "hide-details": ""
                      }, null, 8, ["modelValue"]),
                      _createVNode(_component_v_btn, {
                        color: "primary",
                        variant: "tonal",
                        onClick: selectRange
                      }, {
                        default: _withCtx(() => [...(_cache[29] || (_cache[29] = [
                          _createTextVNode("按范围选择", -1)
                        ]))]),
                        _: 1
                      })
                    ]),
                    _createElementVNode("div", _hoisted_24, [
                      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(targets.value, (t) => {
                        return (_openBlock(), _createElementBlock("button", {
                          key: t.id,
                          class: _normalizeClass(['episode-chip', { selected: selectedTargets.value.includes(t.id) }]),
                          onClick: $event => (toggleTarget(t.id, !selectedTargets.value.includes(t.id)))
                        }, [
                          _createElementVNode("span", null, _toDisplayString(episodeLabel(t)), 1),
                          _createElementVNode("small", null, _toDisplayString(shortTargetName(t)), 1)
                        ], 10, _hoisted_25))
                      }), 128)),
                      (!targets.value.length)
                        ? (_openBlock(), _createElementBlock("div", _hoisted_26, [
                            _createVNode(_component_v_icon, {
                              icon: "mdi-format-list-checks",
                              size: "32"
                            }),
                            _cache[30] || (_cache[30] = _createElementVNode("div", null, "等待选择影片", -1)),
                            _cache[31] || (_cache[31] = _createElementVNode("small", null, "选中后这里会展示可上传字幕的目标集数", -1))
                          ]))
                        : _createCommentVNode("", true)
                    ])
                  ]),
                  _: 1
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_v_col, {
          cols: "12",
          lg: "4"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              class: "glass-card h-100",
              rounded: "xl",
              variant: "flat"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_text, null, {
                  default: _withCtx(() => [
                    _createElementVNode("div", _hoisted_27, [
                      _cache[32] || (_cache[32] = _createElementVNode("div", null, [
                        _createElementVNode("span", { class: "section-kicker" }, "ACTION"),
                        _createElementVNode("h2", null, "操作面板")
                      ], -1)),
                      _createVNode(_component_v_chip, {
                        size: "small",
                        color: actionReady.value ? 'success' : 'warning',
                        variant: "tonal"
                      }, {
                        default: _withCtx(() => [
                          _createTextVNode(_toDisplayString(actionReady.value ? `已选 ${selectedTargets.value.length} 集` : '先选集'), 1)
                        ]),
                        _: 1
                      }, 8, ["color"])
                    ]),
                    _createElementVNode("div", _hoisted_28, [
                      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(_unref(actionTabs), (item) => {
                        return (_openBlock(), _createElementBlock("button", {
                          key: item.value,
                          class: _normalizeClass({ active: activePanel.value === item.value }),
                          onClick: $event => (switchPanel(item.value))
                        }, [
                          _createVNode(_component_v_icon, {
                            icon: item.icon,
                            size: "17"
                          }, null, 8, ["icon"]),
                          _createTextVNode(_toDisplayString(item.title), 1)
                        ], 10, _hoisted_29))
                      }), 128))
                    ]),
                    _createVNode(_component_v_alert, {
                      class: "mb-3",
                      type: "info",
                      variant: "tonal",
                      density: "comfortable"
                    }, {
                      default: _withCtx(() => [
                        _createTextVNode(" 当前桥接对象：" + _toDisplayString(status.value?.bridge_target || '等待加载中') + "。优先做“上传外挂字幕 / 在线字幕 / 外挂管理 / AI翻译”四件事，避免混淆。 ", 1)
                      ]),
                      _: 1
                    }),
                    (activePanel.value === 'upload')
                      ? (_openBlock(), _createElementBlock("div", _hoisted_30, [
                          _createElementVNode("div", {
                            class: _normalizeClass(["drop-zone", { dragging: dragOver.value }]),
                            onDragenter: _withModifiers(onDragEnter, ["prevent"]),
                            onDragover: _withModifiers(onDragEnter, ["prevent"]),
                            onDragleave: _withModifiers(onDragLeave, ["prevent"]),
                            onDrop: _withModifiers(onDropFiles, ["prevent"])
                          }, [
                            _createVNode(_component_v_icon, {
                              icon: "mdi-cloud-upload-outline",
                              size: "42"
                            }),
                            _cache[33] || (_cache[33] = _createElementVNode("strong", null, "拖拽字幕到这里", -1)),
                            _cache[34] || (_cache[34] = _createElementVNode("span", null, "也可以点击下方选择文件，支持 ASS / SRT / ZIP / RAR / 7Z", -1))
                          ], 34),
                          _createVNode(_component_v_file_input, {
                            modelValue: pickedFiles.value,
                            "onUpdate:modelValue": [
                              _cache[4] || (_cache[4] = $event => ((pickedFiles).value = $event)),
                              autoPrepareUpload
                            ],
                            multiple: "",
                            "show-size": "",
                            counter: "",
                            chips: "",
                            accept: ".ass,.srt,.ssa,.vtt,.zip,.rar,.7z",
                            label: "选择字幕文件",
                            "prepend-icon": "mdi-cloud-upload",
                            variant: "outlined",
                            density: "comfortable"
                          }, null, 8, ["modelValue"]),
                          (uploadState.active || uploadState.percent)
                            ? (_openBlock(), _createElementBlock("div", _hoisted_31, [
                                _createElementVNode("div", _hoisted_32, [
                                  _createElementVNode("strong", null, _toDisplayString(uploadState.label), 1),
                                  _createElementVNode("span", null, _toDisplayString(uploadState.percent) + "% · " + _toDisplayString(uploadEtaText.value), 1)
                                ]),
                                _createVNode(_component_v_progress_linear, {
                                  "model-value": uploadState.percent,
                                  height: "10",
                                  rounded: "",
                                  color: "primary"
                                }, null, 8, ["model-value"])
                              ]))
                            : _createCommentVNode("", true),
                          _createElementVNode("div", _hoisted_33, [
                            _createVNode(_component_v_btn, {
                              color: "primary",
                              loading: loading.prepare,
                              onClick: prepareUpload
                            }, {
                              default: _withCtx(() => [...(_cache[35] || (_cache[35] = [
                                _createTextVNode("生成匹配预览", -1)
                              ]))]),
                              _: 1
                            }, 8, ["loading"]),
                            _createVNode(_component_v_btn, {
                              color: "success",
                              loading: loading.apply,
                              onClick: applyUpload
                            }, {
                              default: _withCtx(() => [...(_cache[36] || (_cache[36] = [
                                _createTextVNode("上传字幕", -1)
                              ]))]),
                              _: 1
                            }, 8, ["loading"]),
                            _createVNode(_component_v_btn, {
                              variant: "tonal",
                              onClick: clearFiles
                            }, {
                              default: _withCtx(() => [...(_cache[37] || (_cache[37] = [
                                _createTextVNode("清空", -1)
                              ]))]),
                              _: 1
                            })
                          ]),
                          (previewItems.value.length)
                            ? (_openBlock(), _createElementBlock("div", _hoisted_34, [
                                (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(previewItems.value, (item, i) => {
                                  return (_openBlock(), _createElementBlock("div", {
                                    key: i,
                                    class: "result-item"
                                  }, [
                                    _createVNode(_component_v_icon, {
                                      icon: "mdi-file-check-outline",
                                      color: "success"
                                    }),
                                    _createElementVNode("div", null, [
                                      _createElementVNode("strong", null, _toDisplayString(item.source_name || item.name), 1),
                                      _createElementVNode("span", null, "→ " + _toDisplayString(item.output_name || '未匹配') + " " + _toDisplayString(item.detected_label || ''), 1)
                                    ])
                                  ]))
                                }), 128))
                              ]))
                            : (_openBlock(), _createBlock(_component_v_alert, {
                                key: 2,
                                type: "info",
                                variant: "tonal"
                              }, {
                                default: _withCtx(() => [...(_cache[38] || (_cache[38] = [
                                  _createTextVNode("拖入字幕后会自动预览；上传时默认处理时间轴。", -1)
                                ]))]),
                                _: 1
                              }))
                        ]))
                      : _createCommentVNode("", true),
                    (activePanel.value === 'online')
                      ? (_openBlock(), _createElementBlock("div", _hoisted_35, [
                          _cache[41] || (_cache[41] = _createElementVNode("p", { class: "muted" }, "从在线字幕源搜索，选中候选后生成上传预览。", -1)),
                          _createElementVNode("div", _hoisted_36, [
                            _createVNode(_component_v_btn, {
                              color: "primary",
                              loading: loading.online,
                              onClick: onlineSearch
                            }, {
                              default: _withCtx(() => [...(_cache[39] || (_cache[39] = [
                                _createTextVNode("搜索在线字幕", -1)
                              ]))]),
                              _: 1
                            }, 8, ["loading"]),
                            _createVNode(_component_v_btn, {
                              color: "success",
                              variant: "tonal",
                              onClick: onlinePreview
                            }, {
                              default: _withCtx(() => [...(_cache[40] || (_cache[40] = [
                                _createTextVNode("预览选中", -1)
                              ]))]),
                              _: 1
                            })
                          ]),
                          _createElementVNode("div", _hoisted_37, [
                            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(onlineResults.value, (item, i) => {
                              return (_openBlock(), _createElementBlock("label", {
                                key: i,
                                class: "candidate-card"
                              }, [
                                _createElementVNode("input", {
                                  type: "checkbox",
                                  checked: selectedOnline.value.includes(i),
                                  onChange: $event => (toggleOnline(i, $event.target.checked))
                                }, null, 40, _hoisted_38),
                                _createElementVNode("div", null, [
                                  _createElementVNode("strong", null, _toDisplayString(item.name || item.title || item.filename || '在线字幕'), 1),
                                  _createElementVNode("span", null, _toDisplayString(item.provider || '') + " · " + _toDisplayString(item.language || item.lang || ''), 1)
                                ])
                              ]))
                            }), 128)),
                            (!onlineResults.value.length)
                              ? (_openBlock(), _createElementBlock("div", _hoisted_39, "暂无在线字幕候选"))
                              : _createCommentVNode("", true)
                          ])
                        ]))
                      : _createCommentVNode("", true),
                    (activePanel.value === 'manage')
                      ? (_openBlock(), _createElementBlock("div", _hoisted_40, [
                          _cache[45] || (_cache[45] = _createElementVNode("p", { class: "muted" }, "这里只管理外挂字幕，不会取消 AI 任务。", -1)),
                          _createElementVNode("div", _hoisted_41, [
                            _createVNode(_component_v_btn, {
                              color: "primary",
                              loading: loading.subtitles,
                              onClick: refreshSubtitles
                            }, {
                              default: _withCtx(() => [...(_cache[42] || (_cache[42] = [
                                _createTextVNode("刷新", -1)
                              ]))]),
                              _: 1
                            }, 8, ["loading"]),
                            _createVNode(_component_v_btn, {
                              color: "error",
                              variant: "tonal",
                              onClick: deleteSelectedSubtitles
                            }, {
                              default: _withCtx(() => [...(_cache[43] || (_cache[43] = [
                                _createTextVNode("删除外挂", -1)
                              ]))]),
                              _: 1
                            }),
                            _createVNode(_component_v_btn, {
                              color: "success",
                              variant: "tonal",
                              onClick: fixSelectedSubtitles
                            }, {
                              default: _withCtx(() => [...(_cache[44] || (_cache[44] = [
                                _createTextVNode("调轴", -1)
                              ]))]),
                              _: 1
                            })
                          ]),
                          _createElementVNode("div", _hoisted_42, [
                            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(subtitles.value, (s, i) => {
                              return (_openBlock(), _createElementBlock("label", {
                                key: i,
                                class: "candidate-card"
                              }, [
                                _createElementVNode("input", {
                                  type: "checkbox",
                                  checked: selectedSubtitles.value.includes(i),
                                  onChange: $event => (toggleIndex(selectedSubtitles.value, i, $event.target.checked))
                                }, null, 40, _hoisted_43),
                                _createElementVNode("div", null, [
                                  _createElementVNode("strong", null, _toDisplayString(s.name || '外挂字幕'), 1),
                                  _createElementVNode("span", null, _toDisplayString(s.target) + " · " + _toDisplayString(s.path), 1)
                                ])
                              ]))
                            }), 128)),
                            (!subtitles.value.length)
                              ? (_openBlock(), _createElementBlock("div", _hoisted_44, "暂无外挂字幕，或先刷新列表"))
                              : _createCommentVNode("", true)
                          ])
                        ]))
                      : _createCommentVNode("", true),
                    (activePanel.value === 'ai')
                      ? (_openBlock(), _createElementBlock("div", _hoisted_45, [
                          _createElementVNode("div", _hoisted_46, [
                            _createVNode(_component_v_icon, {
                              icon: "mdi-creation",
                              size: "34"
                            }),
                            _cache[46] || (_cache[46] = _createElementVNode("div", null, [
                              _createElementVNode("strong", null, "AI 翻译任务"),
                              _createElementVNode("span", null, "提交、查看或取消 AI 任务；不会删除外挂字幕。")
                            ], -1))
                          ]),
                          _createElementVNode("div", _hoisted_47, [
                            _createVNode(_component_v_btn, {
                              color: "primary",
                              onClick: aiPreview
                            }, {
                              default: _withCtx(() => [...(_cache[47] || (_cache[47] = [
                                _createTextVNode("预检", -1)
                              ]))]),
                              _: 1
                            }),
                            _createVNode(_component_v_btn, {
                              color: "success",
                              onClick: aiSubmit
                            }, {
                              default: _withCtx(() => [...(_cache[48] || (_cache[48] = [
                                _createTextVNode("提交任务", -1)
                              ]))]),
                              _: 1
                            }),
                            _createVNode(_component_v_btn, {
                              variant: "tonal",
                              onClick: tasks
                            }, {
                              default: _withCtx(() => [...(_cache[49] || (_cache[49] = [
                                _createTextVNode("查看状态", -1)
                              ]))]),
                              _: 1
                            }),
                            _createVNode(_component_v_btn, {
                              color: "error",
                              variant: "tonal",
                              onClick: aiCancel
                            }, {
                              default: _withCtx(() => [...(_cache[50] || (_cache[50] = [
                                _createTextVNode("取消任务", -1)
                              ]))]),
                              _: 1
                            })
                          ])
                        ]))
                      : _createCommentVNode("", true)
                  ]),
                  _: 1
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }),
    _createVNode(_component_v_card, {
      class: "glass-card mt-4",
      rounded: "xl",
      variant: "flat"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card_text, null, {
          default: _withCtx(() => [
            _createElementVNode("div", _hoisted_48, [
              _cache[51] || (_cache[51] = _createElementVNode("div", null, [
                _createElementVNode("span", { class: "section-kicker" }, "RESULT"),
                _createElementVNode("h2", null, "最近结果")
              ], -1)),
              _createVNode(_component_v_btn, {
                size: "small",
                variant: "tonal",
                onClick: _cache[5] || (_cache[5] = $event => (showLog.value = !showLog.value))
              }, {
                default: _withCtx(() => [
                  _createTextVNode(_toDisplayString(showLog.value ? '收起' : '展开日志'), 1)
                ]),
                _: 1
              })
            ]),
            _createElementVNode("div", _hoisted_49, _toDisplayString(logHeadline.value), 1),
            (showLog.value)
              ? (_openBlock(), _createElementBlock("pre", _hoisted_50, _toDisplayString(logText.value), 1))
              : _createCommentVNode("", true)
          ]),
          _: 1
        })
      ]),
      _: 1
    }),
    _createElementVNode("div", {
      class: _normalizeClass(["batch-bar", { disabled: !selectedTargets.value.length }])
    }, [
      _createElementVNode("div", _hoisted_51, [
        _createElementVNode("strong", null, _toDisplayString(selectedTargets.value.length ? `已选择 ${selectedTargets.value.length} 个目标` : '先选择集数，再执行批量操作'), 1),
        _createElementVNode("span", null, _toDisplayString(currentMediaTitle.value) + " · " + _toDisplayString(status.value?.bridge_target || '桥接加载中'), 1)
      ]),
      _createElementVNode("div", _hoisted_52, [
        _createVNode(_component_v_btn, {
          color: "primary",
          variant: "flat",
          disabled: !selectedTargets.value.length,
          onClick: _cache[6] || (_cache[6] = $event => (jumpAction('upload')))
        }, {
          default: _withCtx(() => [...(_cache[52] || (_cache[52] = [
            _createTextVNode("上传外挂", -1)
          ]))]),
          _: 1
        }, 8, ["disabled"]),
        _createVNode(_component_v_btn, {
          color: "info",
          variant: "tonal",
          disabled: !selectedTargets.value.length,
          onClick: _cache[7] || (_cache[7] = $event => (jumpAction('online')))
        }, {
          default: _withCtx(() => [...(_cache[53] || (_cache[53] = [
            _createTextVNode("在线字幕", -1)
          ]))]),
          _: 1
        }, 8, ["disabled"]),
        _createVNode(_component_v_btn, {
          color: "secondary",
          variant: "tonal",
          disabled: !selectedTargets.value.length,
          onClick: _cache[8] || (_cache[8] = $event => (jumpAction('ai')))
        }, {
          default: _withCtx(() => [...(_cache[54] || (_cache[54] = [
            _createTextVNode("AI翻译", -1)
          ]))]),
          _: 1
        }, 8, ["disabled"]),
        _createVNode(_component_v_menu, null, {
          activator: _withCtx(({ props: menuProps }) => [
            _createVNode(_component_v_btn, _mergeProps(menuProps, {
              variant: "tonal",
              disabled: !selectedTargets.value.length
            }), {
              default: _withCtx(() => [...(_cache[55] || (_cache[55] = [
                _createTextVNode("更多", -1)
              ]))]),
              _: 1
            }, 16, ["disabled"])
          ]),
          default: _withCtx(() => [
            _createVNode(_component_v_list, { density: "compact" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_list_item, {
                  title: "刷新外挂列表",
                  "prepend-icon": "mdi-refresh",
                  onClick: _cache[9] || (_cache[9] = $event => {jumpAction('manage'); refreshSubtitles();})
                }),
                _createVNode(_component_v_list_item, {
                  title: "调轴选中外挂",
                  "prepend-icon": "mdi-timeline-clock-outline",
                  onClick: _cache[10] || (_cache[10] = $event => (jumpAction('manage')))
                }),
                _createVNode(_component_v_list_item, {
                  title: "删除外挂字幕",
                  "prepend-icon": "mdi-delete-outline",
                  class: "text-error",
                  onClick: _cache[11] || (_cache[11] = $event => (jumpAction('manage')))
                }),
                _createVNode(_component_v_list_item, {
                  title: "取消 AI 任务",
                  "prepend-icon": "mdi-cancel",
                  class: "text-error",
                  onClick: aiCancel
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ])
    ], 2)
  ]))
}
}

};
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-0e1d5b32"]]);

export { Page as default };
