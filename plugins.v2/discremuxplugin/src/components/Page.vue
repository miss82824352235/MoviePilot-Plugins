<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { getPluginApi, normalizeError, postPluginApi } from '../api/pluginApi'

const props = defineProps({
  api: { type: Object, required: true },
})

const loading = ref(false)
const acting = ref(false)
const error = ref('')
const toast = ref('')
const status = reactive({
  current_task_id: null,
  queue_size: 0,
  worker_running: false,
  worker_count: 0,
  max_workers: 0,
  counts: {},
  tasks: [],
  updated_at: '',
  plugin: {},
})
const selected = ref(new Set())
const confirmDialog = reactive({
  open: false,
  action: '',
  title: '',
  message: '',
})
let timer = null

const tasks = computed(() => status.tasks || [])
const selectedIds = computed(() => Array.from(selected.value))
const allSelected = computed(() => tasks.value.length > 0 && selectedIds.value.length === tasks.value.length)
const someSelected = computed(() => selectedIds.value.length > 0 && !allSelected.value)
const counts = computed(() => status.counts || {})
const activeCount = computed(() => {
  const c = counts.value
  return (c.waiting || 0) + (c.scanning || 0) + (c.remuxing || 0) + (c.normalizing || 0) + (c.transferring || 0) + (c.verifying || 0) + (c.paused || 0)
})

const statusColor = {
  waiting: 'info',
  scanning: 'info',
  remuxing: 'primary',
  normalizing: 'primary',
  transferring: 'secondary',
  verifying: 'secondary',
  paused: 'warning',
  success: 'success',
  failed: 'error',
  skipped: 'grey',
  terminated: 'error',
  interrupted: 'warning',
}

const statusText = {
  waiting: '等待中',
  scanning: '扫描中',
  remuxing: '重封装',
  normalizing: '规范轨道',
  transferring: '整理入库',
  verifying: '验证中',
  paused: '已暂停',
  success: '成功',
  failed: '失败',
  skipped: '已跳过',
  terminated: '已终止',
  interrupted: '已中断',
}

function showToast(msg) {
  toast.value = msg
  setTimeout(() => {
    if (toast.value === msg) toast.value = ''
  }, 3200)
}

function formatBytes(n) {
  const num = Number(n || 0)
  if (!num) return '-'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let v = num
  let i = 0
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024
    i += 1
  }
  return `${v.toFixed(i === 0 ? 0 : 1)} ${units[i]}`
}

function formatDuration(sec) {
  const s = Math.max(0, Math.floor(Number(sec || 0)))
  if (!s) return '-'
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const r = s % 60
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m ${r}s`
  return `${r}s`
}

function formatEta(sec) {
  if (sec == null || sec === '' || Number.isNaN(Number(sec))) return '计算中'
  return formatDuration(sec)
}

function isSelected(id) {
  return selected.value.has(id)
}

function toggleSelect(id) {
  const next = new Set(selected.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  selected.value = next
}

function toggleSelectAll() {
  if (allSelected.value) {
    selected.value = new Set()
    return
  }
  selected.value = new Set(tasks.value.map((t) => t.id))
}

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    const data = await getPluginApi(props.api, 'status')
    Object.assign(status, data || {})
    // 清理已不存在的选中项
    const ids = new Set((status.tasks || []).map((t) => t.id))
    selected.value = new Set(Array.from(selected.value).filter((id) => ids.has(id)))
  } catch (e) {
    error.value = normalizeError(e)
  } finally {
    loading.value = false
  }
}

function openConfirm(action) {
  if (!selectedIds.value.length && action !== 'clear_finished') {
    showToast('请先选择任务')
    return
  }
  const map = {
    skip: {
      title: '确认跳过',
      message: '跳过会安全停止所选任务并继续队列下一项，不会删除源原盘。',
    },
    terminate: {
      title: '确认终止',
      message: '终止会停止所选任务并标记为已终止，不会删除源原盘和未验证输出。',
    },
    clear_finished: {
      title: '清理结束任务',
      message: '仅清理成功/失败/跳过/终止等结束记录，不影响运行中任务。',
    },
  }
  confirmDialog.action = action
  confirmDialog.title = map[action]?.title || '确认操作'
  confirmDialog.message = map[action]?.message || '确认执行该操作？'
  confirmDialog.open = true
}

async function doControl(action, confirm = false) {
  if (!selectedIds.value.length && !['clear_finished'].includes(action)) {
    showToast('请先选择任务')
    return
  }
  acting.value = true
  error.value = ''
  try {
    const body = {
      action,
      task_ids: selectedIds.value,
      select_all: false,
      confirm,
    }
    if (action === 'clear_finished') {
      body.task_ids = []
    }
    const data = await postPluginApi(props.api, 'task_control', body)
    showToast(data?.message || data?.data?.message || `动作 ${action} 完成`)
    confirmDialog.open = false
    await refresh()
  } catch (e) {
    const msg = normalizeError(e)
    if (e?.response?.data?.need_confirm || /confirm=true/.test(msg)) {
      openConfirm(action)
    } else {
      error.value = msg
      showToast(msg)
    }
  } finally {
    acting.value = false
  }
}

async function confirmDanger() {
  const action = confirmDialog.action
  confirmDialog.open = false
  await doControl(action, true)
}

async function enqueueScan() {
  acting.value = true
  error.value = ''
  try {
    await postPluginApi(props.api, 'enqueue_scan', { confirm: true })
    showToast('已提交扫描入队')
    await refresh()
  } catch (e) {
    error.value = normalizeError(e)
    showToast(error.value)
  } finally {
    acting.value = false
  }
}

onMounted(async () => {
  await refresh()
  timer = setInterval(refresh, 3000)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <div class="disc-console">
    <v-alert
      v-if="toast"
      type="success"
      variant="tonal"
      density="compact"
      class="mb-3"
    >
      {{ toast }}
    </v-alert>
    <v-alert
      v-if="error"
      type="error"
      variant="tonal"
      density="compact"
      class="mb-3"
      closable
      @click:close="error = ''"
    >
      {{ error }}
    </v-alert>

    <v-card class="mb-4 hero-card" variant="tonal" color="primary">
      <v-card-text class="pa-4 pa-md-5">
        <div class="d-flex flex-wrap align-center justify-space-between ga-3">
          <div>
            <div class="text-h6 font-weight-bold">蓝光原盘重封装任务台</div>
            <div class="text-body-2 opacity-90 mt-1">
              源文件 ISO/BDMV → MakeMKV → 轨道规范 → MP 硬链接入库
            </div>
            <div class="text-caption mt-2 opacity-80">
              版本 {{ status.plugin?.version || '-' }} ·
              队列 {{ status.queue_size || 0 }} ·
              Worker {{ status.worker_count ?? 0 }}/{{ status.max_workers || status.plugin?.max_workers || 2 }} ·
              磁盘保护 {{ status.plugin?.min_free_space_gb || 120 }}GB ·
              更新 {{ status.updated_at || '-' }}
            </div>
          </div>
          <div class="d-flex flex-wrap ga-2">
            <v-btn
              color="surface"
              variant="flat"
              :loading="loading"
              @click="refresh"
            >
              刷新
            </v-btn>
            <v-btn
              color="surface"
              variant="flat"
              :loading="acting"
              @click="enqueueScan"
            >
              扫描入队
            </v-btn>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <v-row class="mb-2" dense>
      <v-col cols="6" sm="4" md="2">
        <v-card variant="tonal" class="stat-card">
          <v-card-text class="py-3">
            <div class="text-caption text-medium-emphasis">活动中</div>
            <div class="text-h6">{{ activeCount }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" sm="4" md="2">
        <v-card variant="tonal" color="primary" class="stat-card">
          <v-card-text class="py-3">
            <div class="text-caption">重封装</div>
            <div class="text-h6">{{ counts.remuxing || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" sm="4" md="2">
        <v-card variant="tonal" color="warning" class="stat-card">
          <v-card-text class="py-3">
            <div class="text-caption">暂停</div>
            <div class="text-h6">{{ counts.paused || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" sm="4" md="2">
        <v-card variant="tonal" color="success" class="stat-card">
          <v-card-text class="py-3">
            <div class="text-caption">成功</div>
            <div class="text-h6">{{ counts.success || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" sm="4" md="2">
        <v-card variant="tonal" color="error" class="stat-card">
          <v-card-text class="py-3">
            <div class="text-caption">失败</div>
            <div class="text-h6">{{ counts.failed || 0 }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" sm="4" md="2">
        <v-card variant="tonal" class="stat-card">
          <v-card-text class="py-3">
            <div class="text-caption text-medium-emphasis">跳过/终止</div>
            <div class="text-h6">{{ (counts.skipped || 0) + (counts.terminated || 0) }}</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-card class="mb-4" variant="flat">
      <v-card-text class="pa-3">
        <div class="d-flex flex-wrap align-center ga-2 control-bar">
          <v-checkbox
            :model-value="allSelected"
            :indeterminate="someSelected"
            label="全选"
            hide-details
            density="compact"
            @update:model-value="toggleSelectAll"
          />
          <v-chip size="small" variant="tonal">已选 {{ selectedIds.length }}</v-chip>
          <v-spacer />
          <v-btn size="small" variant="tonal" :disabled="!selectedIds.length || acting" @click="doControl('pause')">暂停</v-btn>
          <v-btn size="small" variant="tonal" color="primary" :disabled="!selectedIds.length || acting" @click="doControl('resume')">继续</v-btn>
          <v-btn size="small" variant="tonal" color="warning" :disabled="!selectedIds.length || acting" @click="openConfirm('skip')">跳过</v-btn>
          <v-btn size="small" variant="tonal" color="error" :disabled="!selectedIds.length || acting" @click="openConfirm('terminate')">终止</v-btn>
          <v-btn size="small" variant="text" :disabled="acting" @click="openConfirm('clear_finished')">清理结束</v-btn>
        </div>
      </v-card-text>
    </v-card>

    <div v-if="!tasks.length" class="text-center text-medium-emphasis py-10">
      当前没有任务。可点“扫描入队”，或等待监听下载器命中 ISO/BDMV。
    </div>

    <v-row dense>
      <v-col
        v-for="task in tasks"
        :key="task.id"
        cols="12"
      >
        <v-card
          class="task-card"
          :class="{ selected: isSelected(task.id) }"
          variant="outlined"
          @click="toggleSelect(task.id)"
        >
          <v-card-text class="pa-4">
            <div class="d-flex align-start ga-3">
              <v-checkbox
                :model-value="isSelected(task.id)"
                hide-details
                density="compact"
                class="mt-0"
                @click.stop
                @update:model-value="toggleSelect(task.id)"
              />
              <div class="flex-grow-1 min-w-0">
                <div class="d-flex flex-wrap align-center ga-2 mb-1">
                  <div class="text-subtitle-1 font-weight-bold text-truncate">{{ task.title }}</div>
                  <v-chip size="x-small" :color="statusColor[task.status] || 'default'" variant="tonal">
                    {{ statusText[task.status] || task.status }}
                  </v-chip>
                  <v-chip size="x-small" variant="outlined">{{ (task.disc_type || 'unknown').toUpperCase() }}</v-chip>
                  <v-chip size="x-small" variant="text">{{ task.mode || '-' }}</v-chip>
                </div>
                <div class="text-caption text-medium-emphasis text-truncate mb-2">
                  {{ task.source_path }}
                </div>
                <div class="d-flex flex-wrap ga-3 text-caption mb-2">
                  <span>进度 {{ Number(task.progress || 0).toFixed(1) }}%</span>
                  <span>已用 {{ formatDuration(task.elapsed_seconds) }}</span>
                  <span>ETA {{ formatEta(task.eta_seconds) }}</span>
                  <span>源大小 {{ formatBytes(task.source_size) }}</span>
                </div>
                <v-progress-linear
                  :model-value="Number(task.progress || 0)"
                  height="10"
                  rounded
                  :color="statusColor[task.status] || 'primary'"
                  class="mb-2"
                />
                <div class="text-body-2">
                  {{ task.message || task.stage || '-' }}
                </div>
                <div v-if="task.error" class="text-caption text-error mt-1">
                  {{ task.error }}
                </div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="confirmDialog.open" max-width="480">
      <v-card>
        <v-card-title>{{ confirmDialog.title }}</v-card-title>
        <v-card-text>{{ confirmDialog.message }}</v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="confirmDialog.open = false">取消</v-btn>
          <v-btn color="error" variant="flat" :loading="acting" @click="confirmDanger">确认</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped>
.disc-console {
  max-width: 1100px;
  margin: 0 auto;
  padding: 8px 4px 24px;
}
.hero-card {
  border-radius: 16px;
}
.stat-card {
  border-radius: 14px;
  height: 100%;
}
.task-card {
  border-radius: 14px;
  transition: border-color .15s ease, box-shadow .15s ease;
  cursor: pointer;
}
.task-card.selected {
  border-color: rgb(var(--v-theme-primary));
  box-shadow: 0 0 0 1px rgba(var(--v-theme-primary), .35);
}
.control-bar {
  min-height: 40px;
}
.min-w-0 {
  min-width: 0;
}
@media (max-width: 599.98px) {
  .disc-console {
    padding-bottom: 72px;
  }
  .control-bar :deep(.v-btn) {
    flex: 1 1 calc(50% - 8px);
  }
}
</style>
