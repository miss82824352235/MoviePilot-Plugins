<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  initialConfig: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['save', 'close'])

const form = reactive({
  history_enabled: false,
  run_once: false,
  library_scan_enabled: false,
  library_scan_run_once: false,
  library_scan_cron: '30 3 * * *',
  source_root: '/PT/mp/源文件',
  source_roots: '/PT/mp/源文件\n/PT/ms/源文件',
  library_root: '/PT/mp/硬链接',
  library_roots: '/PT/mp/硬链接\n/PT/ms/硬链接',
  library_scan_max_items: 50,
  max_workers: 2,
  recent_days: 7,
  min_mkv_size_gb: 5,
  min_free_space_gb: 120,
  movies_only: true,
  source_disc_action: 'delete',
  library_disc_action: 'delete',
  refresh_media_server: true,
  cron_schedule: '0 3 * * *',
  intercept_enabled: false,
  intercept_transfer_mkv: true,
  normalize_tracks: true,
  reset_video_language: true,
  ...props.initialConfig,
})

watch(
  () => props.initialConfig,
  (v) => Object.assign(form, v || {}),
  { deep: true },
)

function save() {
  emit('save', { ...form })
}
</script>

<template>
  <v-card class="pa-2" variant="flat">
    <v-card-title>蓝光原盘重封装设置</v-card-title>
    <v-card-text>
      <v-alert type="info" variant="tonal" class="mb-4" density="compact">
        只从源文件目录查找 ISO/BDMV，重封装后通过 MoviePilot 硬链接入库。任务进度与控制请在插件详情页任务台查看。
      </v-alert>

      <v-row>
        <v-col cols="12"><div class="text-subtitle-2 font-weight-bold">监听与扫描</div></v-col>
        <v-col cols="12" md="4"><v-switch v-model="form.intercept_enabled" label="监听下载器原盘并接管整理" hide-details /></v-col>
        <v-col cols="12" md="4"><v-switch v-model="form.intercept_transfer_mkv" label="重封装后自动硬链接整理" hide-details /></v-col>
        <v-col cols="12" md="4"><v-switch v-model="form.library_scan_enabled" label="启用源文件原盘扫描" hide-details /></v-col>
        <v-col cols="12" md="4"><v-switch v-model="form.library_scan_run_once" label="立即扫描一次" hide-details /></v-col>
        <v-col cols="12" md="4"><v-text-field v-model.number="form.library_scan_interval_minutes" type="number" label="源文件补扫间隔(分钟)" hint="默认10；0=使用Cron" persistent-hint density="comfortable" /></v-col>
        <v-col cols="12" md="4"><v-text-field v-model="form.library_scan_cron" label="扫描 Cron(间隔0时)" hide-details density="comfortable" /></v-col>
        <v-col cols="12" md="4"><v-text-field v-model.number="form.library_scan_max_items" type="number" label="单次最多入队" hide-details density="comfortable" /></v-col>
        <v-col cols="12" md="4"><v-text-field v-model.number="form.max_workers" type="number" label="并行 Worker 数" hint="建议1-2；空间紧张时用1" persistent-hint density="comfortable" /></v-col>

        <v-col cols="12"><v-divider class="my-2" /></v-col>
        <v-col cols="12"><div class="text-subtitle-2 font-weight-bold">目录边界</div></v-col>
        <v-col cols="12" md="6">
          <v-textarea
            v-model="form.source_roots"
            label="源文件根目录（每行一个）"
            rows="3"
            hide-details
            density="comfortable"
          />
        </v-col>
        <v-col cols="12" md="6">
          <v-textarea
            v-model="form.library_roots"
            label="硬链接库根目录（仅发现/映射）"
            rows="3"
            hide-details
            density="comfortable"
          />
        </v-col>
        <v-col cols="12" md="6"><v-text-field v-model="form.source_root" label="默认源文件根" hide-details density="comfortable" /></v-col>
        <v-col cols="12" md="6"><v-text-field v-model="form.library_root" label="默认硬链接库根" hide-details density="comfortable" /></v-col>

        <v-col cols="12"><v-divider class="my-2" /></v-col>
        <v-col cols="12"><div class="text-subtitle-2 font-weight-bold">处理策略</div></v-col>
        <v-col cols="12" md="4"><v-switch v-model="form.movies_only" label="只处理电影" hide-details /></v-col>
        <v-col cols="12" md="4"><v-switch v-model="form.normalize_tracks" label="规范音轨/字幕命名" hide-details /></v-col>
        <v-col cols="12" md="4"><v-switch v-model="form.reset_video_language" label="视频轨语言设为 und" hide-details /></v-col>
        <v-col cols="12" md="4"><v-switch v-model="form.refresh_media_server" label="整理后刷新媒体库" hide-details /></v-col>
        <v-col cols="12" md="4">
          <v-text-field v-model.number="form.min_mkv_size_gb" type="number" label="跳过阈值(GB)" hide-details density="comfortable" />
        </v-col>
        <v-col cols="12" md="4">
          <v-text-field v-model.number="form.min_free_space_gb" type="number" label="最低剩余空间(GB)" hint="低于阈值跳过重封装，避免写满磁盘" persistent-hint density="comfortable" />
        </v-col>
        <v-col cols="12" md="4">
          <v-select
            v-model="form.source_disc_action"
            :items="[
              { title: '保留源原盘', value: 'keep' },
              { title: '删除源原盘并清理下载器任务', value: 'delete' },
            ]"
            label="源文件原盘处理"
            hide-details
            density="comfortable"
          />
        </v-col>
        <v-col cols="12" md="4">
          <v-select
            v-model="form.library_disc_action"
            :items="[
              { title: '保留旧入库原盘', value: 'keep' },
              { title: '写 .ignore', value: 'ignore' },
              { title: '删除旧入库原盘', value: 'delete' },
            ]"
            label="硬链接库旧原盘处理"
            hide-details
            density="comfortable"
          />
        </v-col>

        <v-col cols="12"><v-divider class="my-2" /></v-col>
        <v-col cols="12">
          <v-alert type="warning" variant="tonal" density="compact">
            历史整理模式已停用提示位：`history_enabled` 仅兼容旧配置，实际不从硬链接库直接重封装。
          </v-alert>
        </v-col>
        <v-col cols="12" md="4"><v-switch v-model="form.history_enabled" label="兼容：历史模式开关" hide-details /></v-col>
      </v-row>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn variant="text" @click="emit('close')">取消</v-btn>
      <v-btn color="primary" @click="save">保存</v-btn>
    </v-card-actions>
  </v-card>
</template>
