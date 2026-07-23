<template>
  <div class="swu-page" data-revision="v0.6.0-bridge-workbench">
    <!-- Hero / 状态 -->
    <div class="swu-hero">
      <div class="swu-hero-main">
        <div class="swu-title">字幕控制台</div>
        <div class="swu-sub">
          <span v-if="statusLoading">桥接加载中…</span>
          <span v-else-if="bridgeLabel">已连接：{{ bridgeLabel }}</span>
          <span v-else class="text-error">桥接异常，请确认字幕匹配魔改版已启用</span>
        </div>
      </div>
      <div class="swu-hero-meta">
        <v-chip size="small" :color="selectedIds.length ? 'primary' : 'default'" variant="tonal">
          已选 {{ selectedIds.length }} 个目标
        </v-chip>
        <v-chip size="small" variant="tonal">待上传 {{ files.length }} 个文件</v-chip>
        <v-btn size="small" variant="text" :loading="statusLoading" @click="refreshStatus">刷新</v-btn>
      </div>
    </div>

    <v-snackbar v-model="toast.show" :color="toast.color" :timeout="3200" location="top">
      {{ toast.text }}
    </v-snackbar>

    <!-- 选片 -->
    <v-card class="swu-card" variant="tonal" rounded="lg">
      <v-card-title class="swu-card-title">找影片</v-card-title>
      <v-card-text>
        <div class="swu-row">
          <v-text-field
            v-model="keyword"
            label="搜索本地媒体"
            density="comfortable"
            variant="outlined"
            hide-details
            clearable
            @keyup.enter="doSearch"
          />
          <v-btn color="primary" :loading="searching" @click="doSearch">搜索</v-btn>
        </div>
        <div v-if="mediaList.length" class="swu-media-list">
          <button
            v-for="m in mediaList"
            :key="mediaKey(m)"
            type="button"
            class="swu-media-item"
            :class="{ active: currentMedia && mediaKey(currentMedia) === mediaKey(m) }"
            @click="selectMedia(m)"
          >
            <div class="name">{{ m.title || m.name || '未命名' }}</div>
            <div class="meta">
              {{ m.year || '未知年份' }} · {{ mediaTypeLabel(m) }} · 目标 {{ m.target_count || m.count || '?' }}
            </div>
          </button>
        </div>
        <div v-else-if="searched" class="swu-empty">暂无结果，换个关键词试试</div>
      </v-card-text>
    </v-card>

    <!-- 目标选择 -->
    <v-card class="swu-card" variant="tonal" rounded="lg">
      <v-card-title class="swu-card-title">
        <span>选集数</span>
        <span class="swu-muted">{{ currentMedia ? (currentMedia.title || currentMedia.name) : '先选择影片' }}</span>
      </v-card-title>
      <v-card-text>
        <div class="swu-select-bar">
          <v-btn size="small" variant="tonal" :disabled="!targets.length" @click="selectAll">全选</v-btn>
          <v-btn size="small" variant="tonal" :disabled="!targets.length" @click="invertSelect">反选</v-btn>
          <v-btn size="small" variant="text" :disabled="!selectedIds.length" @click="clearSelect">清空</v-btn>
          <v-text-field
            v-model="rangeText"
            class="swu-range"
            density="compact"
            variant="outlined"
            hide-details
            label="快速选择 1-12 / 1,3,5"
            @keyup.enter="applyRange"
          />
          <v-btn size="small" variant="tonal" :disabled="!targets.length" @click="applyRange">按范围</v-btn>
          <v-btn size="small" variant="text" :loading="loadingTargets" @click="reloadTargets">刷新列表</v-btn>
        </div>

        <div v-if="loadingTargets" class="swu-empty">加载目标中…</div>
        <div v-else-if="!targets.length" class="swu-empty">选中后这里会展示可上传字幕的目标集数</div>
        <div v-else class="swu-target-grid">
          <button
            v-for="t in targets"
            :key="t.target_id || t.id"
            type="button"
            class="swu-target"
            :class="{ selected: selectedIds.includes(targetId(t)) }"
            @click="toggleTarget(t)"
          >
            <div class="ep">{{ episodeLabel(t) }}</div>
            <div class="name">{{ shortName(t) }}</div>
            <div class="meta">
              外挂 {{ subtitleCount(t) }}
              <template v-if="t.ai_status || t.task_status"> · {{ t.ai_status || t.task_status }}</template>
            </div>
          </button>
        </div>
      </v-card-text>
    </v-card>

    <!-- 上下文动作提示 -->
    <div class="swu-context-bar">
      <div>将对 <b>{{ selectedIds.length }}</b> 个目标执行 · 上传 / 在线 / 外挂管理 / AI 分区操作</div>
    </div>

    <!-- 四区动作 -->
    <div class="swu-actions-grid">
      <!-- 上传 -->
      <v-card class="swu-card" variant="tonal" rounded="lg">
        <v-card-title class="swu-card-title">上传外挂</v-card-title>
        <v-card-text>
          <div
            class="swu-drop"
            :class="{ drag: dragging }"
            @dragover.prevent="dragging = true"
            @dragleave.prevent="dragging = false"
            @drop.prevent="onDrop"
            @click="fileInput?.click()"
          >
            <div>拖拽字幕到这里</div>
            <div class="swu-muted">支持 ass/srt/ssa/vtt/zip/rar/7z · 也可点击选择</div>
            <input ref="fileInput" type="file" multiple hidden @change="onFilePick" />
          </div>
          <div v-if="files.length" class="swu-file-list">
            <div v-for="(f, i) in files" :key="i" class="swu-file-row">
              <span>{{ f.name }}</span>
              <v-btn size="x-small" variant="text" @click="files.splice(i, 1)">移除</v-btn>
            </div>
            <v-btn size="small" variant="text" @click="files = []">清空文件</v-btn>
          </div>
          <div class="swu-btn-row">
            <v-btn color="primary" :disabled="!canUpload" :loading="uploading" @click="prepareUpload">
              生成匹配预览
            </v-btn>
            <v-btn color="success" :disabled="!uploadSession" :loading="applying" @click="applyUpload">
              上传字幕
            </v-btn>
          </div>
          <div v-if="uploadPreviewText" class="swu-preview">{{ uploadPreviewText }}</div>
        </v-card-text>
      </v-card>

      <!-- 在线 -->
      <v-card class="swu-card" variant="tonal" rounded="lg">
        <v-card-title class="swu-card-title">在线字幕</v-card-title>
        <v-card-text>
          <div class="swu-btn-row">
            <v-btn color="primary" :disabled="!selectedIds.length" :loading="onlineSearching" @click="searchOnline">
              搜索在线字幕
            </v-btn>
            <v-btn
              variant="tonal"
              :disabled="!selectedOnline.length"
              :loading="onlinePreviewing"
              @click="previewOnline"
            >
              预览选中
            </v-btn>
            <v-btn
              color="secondary"
              :disabled="!selectedOnline.length || !selectedIds.length"
              :loading="onlineAiLoading"
              @click="submitOnlineAi"
            >
              在线→AI
            </v-btn>
          </div>
          <div v-if="!onlineResults.length" class="swu-empty">从在线字幕源搜索，选中候选后生成上传预览</div>
          <div v-else class="swu-online-list">
            <label v-for="(r, idx) in onlineResults" :key="idx" class="swu-online-item">
              <input v-model="selectedOnline" type="checkbox" :value="r" />
              <div>
                <div class="name">{{ r.title || r.name || r.filename || '在线结果' }}</div>
                <div class="meta">{{ r.lang || r.language || '' }} {{ r.source || r.provider || '' }}</div>
              </div>
            </label>
          </div>
        </v-card-text>
      </v-card>

      <!-- 外挂管理 -->
      <v-card class="swu-card" variant="tonal" rounded="lg">
        <v-card-title class="swu-card-title">外挂管理</v-card-title>
        <v-card-text>
          <div class="swu-btn-row">
            <v-btn size="small" variant="tonal" :disabled="!selectedIds.length" :loading="historyLoading" @click="loadHistory">
              刷新外挂列表
            </v-btn>
            <v-btn size="small" variant="tonal" :disabled="!selectedSubs.length" :loading="timelineLoading" @click="fixTimeline">
              调轴选中外挂
            </v-btn>
            <v-btn size="small" color="warning" variant="tonal" :disabled="!selectedSubs.length" @click="restoreSelected">
              恢复备份
            </v-btn>
            <v-btn size="small" color="error" variant="tonal" :disabled="!selectedSubs.length" @click="deleteSelected">
              删除外挂
            </v-btn>
          </div>
          <div v-if="!historyItems.length" class="swu-empty">这里只管理外挂字幕，不会取消 AI 任务</div>
          <div v-else class="swu-online-list">
            <label v-for="(h, idx) in historyItems" :key="idx" class="swu-online-item">
              <input v-model="selectedSubs" type="checkbox" :value="h" />
              <div>
                <div class="name">{{ h.subtitle_name || h.name || h.path || '字幕' }}</div>
                <div class="meta">
                  {{ h.target_id || '' }}
                  <template v-if="h.has_backup || h.backup_path"> · 有备份</template>
                </div>
              </div>
            </label>
          </div>
        </v-card-text>
      </v-card>

      <!-- AI -->
      <v-card class="swu-card" variant="tonal" rounded="lg">
        <v-card-title class="swu-card-title">AI 翻译</v-card-title>
        <v-card-text>
          <div class="swu-ai-fields">
            <v-select
              v-model="sourcePolicy"
              :items="sourcePolicyItems"
              label="字幕源策略"
              density="compact"
              variant="outlined"
              hide-details
            />
            <v-select
              v-model="overwritePolicy"
              :items="overwritePolicyItems"
              label="覆盖策略"
              density="compact"
              variant="outlined"
              hide-details
            />
            <v-text-field
              v-model="sourceSubtitlePath"
              label="外挂源字幕路径（可选）"
              density="compact"
              variant="outlined"
              hide-details
              clearable
            />
          </div>
          <div class="swu-btn-row">
            <v-btn color="primary" :disabled="!selectedIds.length" :loading="aiPreviewing" @click="previewAi">
              预检
            </v-btn>
            <v-btn color="success" :disabled="!selectedIds.length" :loading="aiSubmitting" @click="submitAi">
              提交任务
            </v-btn>
            <v-btn variant="tonal" :disabled="!selectedIds.length" :loading="aiRestarting" @click="restartAi">
              重做
            </v-btn>
            <v-btn variant="tonal" :disabled="!selectedIds.length" :loading="taskLoading" @click="loadTasks">
              查看状态
            </v-btn>
            <v-btn color="error" variant="tonal" :disabled="!selectedIds.length" @click="cancelAi">
              取消任务
            </v-btn>
          </div>
          <div v-if="aiPreviewText" class="swu-preview">{{ aiPreviewText }}</div>
          <div v-if="taskList.length" class="swu-task-list">
            <div v-for="(task, i) in taskList" :key="i" class="swu-task">
              <div class="swu-task-head">
                <span>{{ taskTitle(task) }}</span>
                <span class="swu-muted">{{ taskStatusText(task) }}</span>
              </div>
              <v-progress-linear
                :model-value="taskPercent(task)"
                height="8"
                rounded
                color="primary"
                class="mt-1"
              />
              <div class="swu-muted swu-task-msg">{{ taskMessage(task) }}</div>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </div>

    <!-- 日志 -->
    <v-card class="swu-card swu-log" variant="outlined" rounded="lg">
      <v-card-title class="swu-card-title">
        最近结果
        <v-btn size="x-small" variant="text" @click="logs = []">清空</v-btn>
      </v-card-title>
      <v-card-text>
        <div v-if="!logs.length" class="swu-empty">操作后会在这里留下提示</div>
        <div v-for="(line, i) in logs" :key="i" class="swu-log-line">{{ line }}</div>
      </v-card-text>
    </v-card>

    <!-- 底部批量动作栏（移动端吸附） -->
    <div class="swu-bottom-bar">
      <div class="swu-bottom-info">已选 {{ selectedIds.length }} · 文件 {{ files.length }}</div>
      <div class="swu-bottom-actions">
        <v-btn size="small" color="primary" :disabled="!canUpload" @click="prepareUpload">上传外挂</v-btn>
        <v-btn size="small" variant="tonal" :disabled="!selectedIds.length" @click="searchOnline">在线字幕</v-btn>
        <v-btn size="small" variant="tonal" :disabled="!selectedIds.length" @click="previewAi">AI</v-btn>
        <v-menu>
          <template #activator="{ props: menuProps }">
            <v-btn size="small" variant="text" v-bind="menuProps">更多</v-btn>
          </template>
          <v-list density="compact">
            <v-list-item title="刷新外挂" :disabled="!selectedIds.length" @click="loadHistory" />
            <v-list-item title="调轴选中外挂" :disabled="!selectedSubs.length" @click="fixTimeline" />
            <v-list-item title="恢复备份" :disabled="!selectedSubs.length" @click="restoreSelected" />
            <v-list-item title="删除外挂" :disabled="!selectedSubs.length" @click="deleteSelected" />
            <v-list-item title="取消 AI 任务" :disabled="!selectedIds.length" @click="cancelAi" />
            <v-list-item title="AI 重做" :disabled="!selectedIds.length" @click="restartAi" />
          </v-list>
        </v-menu>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { createPluginApi } from '../api/pluginApi.js'

const props = defineProps({
  api: { type: Object, default: null },
  pluginId: { type: String, default: 'SubtitleWebUploader' },
})

const client = createPluginApi(props.api)

const toast = ref({ show: false, text: '', color: 'success' })
const logs = ref([])
const statusLoading = ref(false)
const bridgeLabel = ref('')
const keyword = ref('')
const searching = ref(false)
const searched = ref(false)
const mediaList = ref([])
const currentMedia = ref(null)
const targets = ref([])
const loadingTargets = ref(false)
const selectedIds = ref([])
const rangeText = ref('')
const files = ref([])
const fileInput = ref(null)
const dragging = ref(false)
const uploading = ref(false)
const applying = ref(false)
const uploadSession = ref(null)
const uploadPreviewText = ref('')
const onlineSearching = ref(false)
const onlinePreviewing = ref(false)
const onlineAiLoading = ref(false)
const onlineResults = ref([])
const selectedOnline = ref([])
const historyLoading = ref(false)
const historyItems = ref([])
const selectedSubs = ref([])
const timelineLoading = ref(false)
const sourcePolicy = ref('auto')
const overwritePolicy = ref('skip')
const sourceSubtitlePath = ref('')
const aiPreviewing = ref(false)
const aiSubmitting = ref(false)
const aiRestarting = ref(false)
const aiPreviewText = ref('')
const taskLoading = ref(false)
const taskList = ref([])
let pollTimer = null

const sourcePolicyItems = [
  { title: '自动选择源', value: 'auto' },
  { title: '仅外挂字幕', value: 'local_external' },
  { title: '仅内嵌字幕', value: 'embedded' },
  { title: '指定外挂路径', value: 'matched_external' },
  { title: 'ASR 语音识别', value: 'asr' },
]

const overwritePolicyItems = [
  { title: '已有则跳过', value: 'skip' },
  { title: '新变体并存', value: 'new_variant' },
  { title: '备份后替换', value: 'backup_replace' },
  { title: '直接覆盖', value: 'overwrite' },
]

const canUpload = computed(() => selectedIds.value.length > 0 && files.value.length > 0)

watch(sourcePolicy, (v) => {
  if (v === 'auto' && overwritePolicy.value === 'new_variant') overwritePolicy.value = 'skip'
  if (v !== 'auto' && overwritePolicy.value === 'skip') overwritePolicy.value = 'new_variant'
})

function notify(text, color = 'success') {
  toast.value = { show: true, text, color }
  logs.value.unshift(`[${new Date().toLocaleTimeString()}] ${text}`)
  if (logs.value.length > 40) logs.value.pop()
}

function mediaKey(m) {
  return [m.tmdbid || m.tmdb_id || '', m.type || m.media_type || '', m.title || m.name || ''].join('|')
}
function mediaTypeLabel(m) {
  const t = String(m.type || m.media_type || '').toLowerCase()
  if (t.includes('movie') || t === '电影') return '电影'
  if (t.includes('tv') || t === '电视剧' || t === '剧集') return '电视剧'
  return m.type || m.media_type || '未知类型'
}
function targetId(t) {
  return String(t.target_id || t.id || '')
}
function episodeLabel(t) {
  if (t.episode != null) return `E${String(t.episode).padStart(2, '0')}`
  if (t.ep != null) return `E${String(t.ep).padStart(2, '0')}`
  const name = t.filename || t.name || t.path || ''
  const m = name.match(/[Ss](\d+)[Ee](\d+)/)
  if (m) return `S${m[1]}E${m[2]}`
  return t.season != null ? `S${t.season}` : '目标'
}
function shortName(t) {
  const n = t.filename || t.name || t.path || '未命名'
  return n.length > 42 ? `${n.slice(0, 40)}…` : n
}
function subtitleCount(t) {
  if (Array.isArray(t.subtitles)) return t.subtitles.length
  if (t.subtitle_count != null) return t.subtitle_count
  return t.external_count || 0
}
function taskTitle(task) {
  return task.title || task.target_id || task.id || task.task_id || '任务'
}
function taskPercent(task) {
  const p = task?.progress?.percent ?? task?.progress_percent
  const n = Number(p)
  if (Number.isFinite(n)) return Math.max(0, Math.min(100, n))
  const st = String(task?.status || '').toLowerCase()
  if (st.includes('complete') || st === 'success' || st === 'done') return 100
  if (st.includes('progress') || st === 'running') return 45
  return 8
}
function taskStatusText(task) {
  return task?.status_text || task?.status || task?.progress_stage || ''
}
function taskMessage(task) {
  return task?.progress?.message || task?.progress_message || task?.message || ''
}

async function refreshStatus() {
  statusLoading.value = true
  try {
    const data = await client.status()
    const name = data.bridge_plugin_name || data.plugin_name || data.bridge_target || ''
    const ver = data.bridge_plugin_version || data.plugin_version || data.version || ''
    const mode = data.bridge_mode || ''
    bridgeLabel.value = [name, ver].filter(Boolean).join(' ') + (mode ? ` (${mode})` : '')
    if (!name && data.message) bridgeLabel.value = data.message
  } catch (e) {
    bridgeLabel.value = ''
    notify(e.message || '桥接状态失败', 'error')
  } finally {
    statusLoading.value = false
  }
}

async function doSearch() {
  searching.value = true
  searched.value = true
  try {
    const data = await client.search(keyword.value || '')
    mediaList.value = data.items || data.results || data.medias || data || []
    if (!Array.isArray(mediaList.value)) mediaList.value = []
    notify(`找到 ${mediaList.value.length} 条结果`)
  } catch (e) {
    mediaList.value = []
    notify(e.message || '搜索失败', 'error')
  } finally {
    searching.value = false
  }
}

async function selectMedia(m) {
  currentMedia.value = m
  selectedIds.value = []
  await reloadTargets()
  try {
    await client.saveSelection({
      user_id: 'web',
      media: m,
      target_ids: selectedIds.value,
    })
  } catch (_) {
    /* ignore */
  }
}

async function reloadTargets() {
  if (!currentMedia.value) {
    targets.value = []
    return
  }
  loadingTargets.value = true
  try {
    const m = currentMedia.value
    const data = await client.targets({
      tmdbid: m.tmdbid || m.tmdb_id || '',
      type: m.type || m.media_type || '',
      season: m.season || '',
      title: m.title || m.name || '',
      media_id: m.media_id || m.id || '',
    })
    targets.value = data.targets || data.items || data || []
    if (!Array.isArray(targets.value)) targets.value = []
  } catch (e) {
    targets.value = []
    notify(e.message || '加载目标失败', 'error')
  } finally {
    loadingTargets.value = false
  }
}

function toggleTarget(t) {
  const id = targetId(t)
  if (!id) return
  const i = selectedIds.value.indexOf(id)
  if (i >= 0) selectedIds.value.splice(i, 1)
  else selectedIds.value.push(id)
}
function selectAll() {
  selectedIds.value = targets.value.map(targetId).filter(Boolean)
  notify(`已全选当前目标 ${selectedIds.value.length} 个`)
}
function invertSelect() {
  const all = new Set(targets.value.map(targetId).filter(Boolean))
  const cur = new Set(selectedIds.value)
  selectedIds.value = [...all].filter((id) => !cur.has(id))
  notify('已反选当前目标')
}
function clearSelect() {
  selectedIds.value = []
  notify('已清空选择')
}
function applyRange() {
  const text = (rangeText.value || '').trim()
  if (!text) {
    notify('请输入集数范围', 'warning')
    return
  }
  const wanted = new Set()
  text.split(/[,，\s]+/).forEach((part) => {
    const m = part.match(/^(\d+)\s*[-~～]\s*(\d+)$/)
    if (m) {
      const a = Number(m[1])
      const b = Number(m[2])
      for (let i = Math.min(a, b); i <= Math.max(a, b); i++) wanted.add(i)
    } else if (/^\d+$/.test(part)) wanted.add(Number(part))
  })
  const next = []
  targets.value.forEach((t) => {
    const ep = Number(t.episode ?? t.ep)
    if (wanted.has(ep)) next.push(targetId(t))
  })
  selectedIds.value = next.filter(Boolean)
  notify(`已按范围选择 ${selectedIds.value.length} 个`)
}

function onFilePick(e) {
  const list = Array.from(e.target.files || [])
  files.value = [...files.value, ...list]
  e.target.value = ''
}
function onDrop(e) {
  dragging.value = false
  const list = Array.from(e.dataTransfer?.files || [])
  files.value = [...files.value, ...list]
}

async function prepareUpload() {
  if (!canUpload.value) {
    notify('请先选集数并选择字幕文件', 'warning')
    return
  }
  uploading.value = true
  uploadSession.value = null
  uploadPreviewText.value = ''
  try {
    const fd = new FormData()
    fd.append('target_ids', JSON.stringify(selectedIds.value))
    files.value.forEach((f) => fd.append('files', f))
    fd.append('fix_timeline', 'true')
    fd.append('user_id', 'web')
    const data = await client.uploadPrepare(fd)
    uploadSession.value = data.session_id || data.session || data.upload_session || data
    const count = data.preview_count || (data.previews || data.items || []).length || files.value.length
    uploadPreviewText.value = data.message || `预览已生成：约 ${count} 条匹配`
    notify(uploadPreviewText.value)
  } catch (e) {
    notify(e.message || '生成预览失败', 'error')
  } finally {
    uploading.value = false
  }
}

async function applyUpload() {
  if (!uploadSession.value) {
    notify('请先生成匹配预览', 'warning')
    return
  }
  applying.value = true
  try {
    const session =
      typeof uploadSession.value === 'string'
        ? { session_id: uploadSession.value }
        : uploadSession.value
    const data = await client.uploadApply({
      ...session,
      target_ids: selectedIds.value,
      confirm: true,
      fix_timeline: true,
    })
    notify(data.message || '上传完成')
    files.value = []
    uploadSession.value = null
    await loadHistory()
  } catch (e) {
    notify(e.message || '上传失败', 'error')
  } finally {
    applying.value = false
  }
}

async function searchOnline() {
  if (!selectedIds.value.length) {
    notify('请先选集数', 'warning')
    return
  }
  onlineSearching.value = true
  onlineResults.value = []
  selectedOnline.value = []
  try {
    const data = await client.onlineSearch({ target_ids: selectedIds.value })
    onlineResults.value = data.results || data.items || data.candidates || []
    if (!Array.isArray(onlineResults.value)) onlineResults.value = []
    notify(`在线结果 ${onlineResults.value.length} 条`)
  } catch (e) {
    notify(e.message || '在线搜索失败', 'error')
  } finally {
    onlineSearching.value = false
  }
}

async function previewOnline() {
  if (!selectedOnline.value.length) {
    notify('请先勾选在线字幕', 'warning')
    return
  }
  onlinePreviewing.value = true
  try {
    const data = await client.onlineDownloadPreview({
      target_ids: selectedIds.value,
      results: selectedOnline.value,
    })
    notify(data.message || '在线字幕预览好了')
  } catch (e) {
    notify(e.message || '在线预览失败', 'error')
  } finally {
    onlinePreviewing.value = false
  }
}

async function submitOnlineAi() {
  if (!selectedOnline.value.length || !selectedIds.value.length) {
    notify('请先选集数并勾选在线字幕', 'warning')
    return
  }
  if (!window.confirm(`将把 ${selectedOnline.value.length} 条在线字幕提交为 AI 翻译，确认？`)) return
  onlineAiLoading.value = true
  try {
    const data = await client.onlineAiSubmit({
      target_ids: selectedIds.value,
      results: selectedOnline.value,
      confirm: true,
    })
    notify(data.message || '已提交在线→AI 任务')
    startTaskPoll()
  } catch (e) {
    notify(e.message || '在线→AI 失败', 'error')
  } finally {
    onlineAiLoading.value = false
  }
}

async function loadHistory() {
  if (!selectedIds.value.length) {
    notify('请先选集数', 'warning')
    return
  }
  historyLoading.value = true
  try {
    const data = await client.history({ target_ids: selectedIds.value.join(',') })
    historyItems.value = data.items || data.histories || data.subtitles || data || []
    if (!Array.isArray(historyItems.value)) historyItems.value = []
    selectedSubs.value = []
    notify(`读取到 ${historyItems.value.length} 条外挂/历史`)
  } catch (e) {
    historyItems.value = []
    notify(e.message || '刷新外挂失败', 'error')
  } finally {
    historyLoading.value = false
  }
}

async function fixTimeline() {
  if (!selectedSubs.value.length) {
    notify('请先勾选字幕', 'warning')
    return
  }
  if (!window.confirm(`将对 ${selectedSubs.value.length} 条外挂执行调轴，确认？`)) return
  timelineLoading.value = true
  try {
    const data = await client.timelineFix({
      target_ids: selectedIds.value,
      items: selectedSubs.value,
      confirm: true,
    })
    notify(data.message || '已提交时间轴处理')
  } catch (e) {
    notify(e.message || '调轴失败', 'error')
  } finally {
    timelineLoading.value = false
  }
}

async function deleteSelected() {
  if (!selectedSubs.value.length) {
    notify('请先勾选字幕', 'warning')
    return
  }
  if (!window.confirm(`删除选中的 ${selectedSubs.value.length} 条外挂字幕？此操作不可撤销。`)) return
  try {
    const data = await client.deleteApply({
      target_ids: selectedIds.value,
      items: selectedSubs.value,
      confirm: true,
    })
    notify(data.message || '删除完成')
    await loadHistory()
  } catch (e) {
    notify(e.message || '删除失败', 'error')
  }
}

async function restoreSelected() {
  if (!selectedSubs.value.length) {
    notify('请先勾选字幕', 'warning')
    return
  }
  if (!window.confirm(`恢复选中的 ${selectedSubs.value.length} 条字幕备份？`)) return
  try {
    const data = await client.restore({
      items: selectedSubs.value.map((h) => ({
        target_id: h.target_id,
        subtitle_path: h.subtitle_path || h.path,
        subtitle_name: h.subtitle_name || h.name,
      })),
      confirm: true,
    })
    notify(data.message || '恢复完成')
    await loadHistory()
  } catch (e) {
    notify(e.message || '恢复失败', 'error')
  }
}

function aiPayload() {
  return {
    target_ids: selectedIds.value,
    source_policy: sourcePolicy.value,
    overwrite_policy: overwritePolicy.value,
    source_subtitle_path: sourceSubtitlePath.value || undefined,
  }
}

async function previewAi() {
  if (!selectedIds.value.length) {
    notify('请先选集数', 'warning')
    return
  }
  aiPreviewing.value = true
  try {
    const data = await client.aiPreview(aiPayload())
    aiPreviewText.value = data.message || `将提交 ${selectedIds.value.length} 个目标`
    notify(aiPreviewText.value)
  } catch (e) {
    notify(e.message || 'AI 预检失败', 'error')
  } finally {
    aiPreviewing.value = false
  }
}

async function submitAi() {
  if (!selectedIds.value.length) {
    notify('请先选集数', 'warning')
    return
  }
  if (!window.confirm(`提交 ${selectedIds.value.length} 个目标的 AI 任务？\n源=${sourcePolicy.value} 覆盖=${overwritePolicy.value}`))
    return
  aiSubmitting.value = true
  try {
    const data = await client.aiSubmit({ ...aiPayload(), confirm: true })
    notify(data.message || '已提交 AI 任务')
    startTaskPoll()
  } catch (e) {
    notify(e.message || '提交 AI 失败', 'error')
  } finally {
    aiSubmitting.value = false
  }
}

async function restartAi() {
  if (!selectedIds.value.length) {
    notify('请先选集数', 'warning')
    return
  }
  if (!window.confirm(`重做 ${selectedIds.value.length} 个目标的 AI 字幕（默认 reuse + 备份替换）？`)) return
  aiRestarting.value = true
  try {
    const data = await client.aiRestart({
      target_ids: selectedIds.value,
      source_policy: 'reuse',
      overwrite_policy: 'backup_replace',
      source_subtitle_path: sourceSubtitlePath.value || undefined,
      confirm: true,
    })
    notify(data.message || '已提交 AI 重做')
    startTaskPoll()
  } catch (e) {
    notify(e.message || 'AI 重做失败', 'error')
  } finally {
    aiRestarting.value = false
  }
}

async function cancelAi() {
  if (!selectedIds.value.length) {
    notify('请先选集数', 'warning')
    return
  }
  if (!window.confirm(`取消选中目标的 AI 任务？不会删除外挂字幕。`)) return
  try {
    const data = await client.aiCancel({ target_ids: selectedIds.value, confirm: true })
    notify(data.message || '任务已取消')
    await loadTasks()
  } catch (e) {
    notify(e.message || '取消失败', 'error')
  }
}

function extractTasks(data) {
  if (!data) return []
  if (Array.isArray(data.tasks)) return data.tasks
  if (Array.isArray(data)) return data
  if (data.ai_tasks?.tasks) return data.ai_tasks.tasks
  if (data.task_status?.tasks) return data.task_status.tasks
  if (data.task_status?.ai_tasks?.tasks) return data.task_status.ai_tasks.tasks
  return []
}

async function loadTasks() {
  taskLoading.value = true
  try {
    const data = await client.tasks({ target_ids: selectedIds.value, limit: 50 })
    taskList.value = extractTasks(data)
    notify(`任务状态已刷新：${taskList.value.length} 条`)
  } catch (e) {
    notify(e.message || '查询任务失败', 'error')
  } finally {
    taskLoading.value = false
  }
}

function startTaskPoll() {
  loadTasks()
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(() => {
    if (selectedIds.value.length) loadTasks()
  }, 8000)
}

onMounted(() => {
  refreshStatus()
})
onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.swu-page {
  --swu-gap: 12px;
  padding: 12px 12px 88px;
  max-width: 1200px;
  margin: 0 auto;
  box-sizing: border-box;
}
.swu-hero {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
  padding: 14px 16px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.16), rgba(var(--v-theme-surface-variant), 0.4));
}
.swu-title {
  font-size: 1.35rem;
  font-weight: 700;
}
.swu-sub {
  opacity: 0.85;
  margin-top: 4px;
  font-size: 0.92rem;
}
.swu-hero-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.swu-card {
  margin-bottom: var(--swu-gap);
}
.swu-card-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  font-weight: 700 !important;
  font-size: 1.05rem !important;
}
.swu-muted {
  opacity: 0.7;
  font-weight: 400;
  font-size: 0.85rem;
}
.swu-row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.swu-row .v-text-field {
  flex: 1;
}
.swu-media-list,
.swu-target-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 8px;
  margin-top: 12px;
}
.swu-media-item,
.swu-target {
  text-align: left;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 12px;
  padding: 10px;
  background: rgba(var(--v-theme-surface), 0.6);
  cursor: pointer;
}
.swu-media-item.active,
.swu-target.selected {
  border-color: rgb(var(--v-theme-primary));
  box-shadow: 0 0 0 1px rgb(var(--v-theme-primary));
}
.swu-media-item .name,
.swu-target .name,
.swu-online-item .name {
  font-weight: 600;
  font-size: 0.95rem;
}
.swu-media-item .meta,
.swu-target .meta,
.swu-online-item .meta,
.swu-task-msg {
  opacity: 0.72;
  font-size: 0.8rem;
  margin-top: 2px;
}
.swu-target .ep {
  font-weight: 700;
  color: rgb(var(--v-theme-primary));
}
.swu-select-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.swu-range {
  min-width: 180px;
  max-width: 260px;
  flex: 1;
}
.swu-context-bar {
  margin: 4px 0 12px;
  padding: 8px 12px;
  border-radius: 10px;
  background: rgba(var(--v-theme-primary), 0.08);
  font-size: 0.9rem;
}
.swu-actions-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--swu-gap);
}
.swu-drop {
  border: 1.5px dashed rgba(var(--v-border-color), 0.6);
  border-radius: 12px;
  padding: 18px 12px;
  text-align: center;
  cursor: pointer;
  margin-bottom: 10px;
}
.swu-drop.drag {
  border-color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.08);
}
.swu-file-list,
.swu-online-list,
.swu-task-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 220px;
  overflow: auto;
}
.swu-file-row,
.swu-online-item {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  font-size: 0.9rem;
}
.swu-btn-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}
.swu-ai-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 8px;
}
.swu-ai-fields .v-text-field {
  grid-column: 1 / -1;
}
.swu-preview {
  margin-top: 8px;
  font-size: 0.88rem;
  opacity: 0.9;
}
.swu-empty {
  opacity: 0.65;
  padding: 10px 0;
  font-size: 0.9rem;
}
.swu-log-line {
  font-size: 0.82rem;
  opacity: 0.85;
  padding: 2px 0;
  border-bottom: 1px solid rgba(var(--v-border-color), 0.2);
}
.swu-bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 20;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 10px 12px calc(10px + env(safe-area-inset-bottom));
  background: rgba(var(--v-theme-surface), 0.92);
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}
.swu-bottom-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: flex-end;
}
.swu-bottom-info {
  font-size: 0.85rem;
  opacity: 0.85;
  white-space: nowrap;
}
@media (max-width: 959.98px) {
  .swu-actions-grid {
    grid-template-columns: 1fr;
  }
  .swu-ai-fields {
    grid-template-columns: 1fr;
  }
  .swu-media-list,
  .swu-target-grid {
    grid-template-columns: 1fr 1fr;
  }
}
@media (max-width: 599.98px) {
  .swu-page {
    padding: 10px 10px 96px;
  }
  .swu-title {
    font-size: 1.2rem;
  }
  .swu-row {
    flex-direction: column;
    align-items: stretch;
  }
  .swu-media-list,
  .swu-target-grid {
    grid-template-columns: 1fr;
  }
  .swu-bottom-bar {
    flex-direction: column;
    align-items: stretch;
  }
  .swu-bottom-actions {
    justify-content: stretch;
  }
  .swu-bottom-actions .v-btn {
    flex: 1;
  }
}
</style>
