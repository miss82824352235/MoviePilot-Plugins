<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { getPluginApi, postPluginApi } from '../api/pluginApi'
import Config from './Config.vue'

const props = defineProps({ api: { type: [Object, Function], default: null } })
const emit = defineEmits(['close', 'switch'])

const loading = ref(false)
const error = ref('')
const stats = ref({ subscriptions: 0, candidates: 0, pending: 0, downloaded: 0 })
const downloadFactSummary = ref({})
const cleanupSummary = ref({})
const replacementSummary = ref({})
const submittedNoHashItems = ref([])
const showNoHashDialog = ref(false)
const subscriptions = ref({})
const candidates = ref([])
const selected = ref(null)
const detailCandidates = ref([])
const filter = ref('all')
const keyword = ref('')
const page = ref(1)
const pageSize = ref(24)
const actionMessage = ref('')
const actionOk = ref(true)
const showGroupDialog = ref(false)
const groupInput = ref('')
const searchMode = ref('subscriptions')
const rssResults = ref([])
const showConfigDialog = ref(false)
const currentConfig = ref({})
const showEditDialog = ref(false)
const editForm = ref({})
const showFactsDialog = ref(false)
const factsTab = ref('downloaded')
const recognitionIssues = ref([])
const showIssuesDialog = ref(false)
const issuePreview = ref(null)
const issueAgentHint = ref(null)
const showIssuePreviewDialog = ref(false)
const showIssueAgentDialog = ref(false)
const showConfirmDialog = ref(false)
const confirmState = ref({ title: '', message: '', color: 'primary', confirmText: '确认', cancelText: '取消', resolve: null })
const candidatePage = ref(1)
const candidatePageSize = ref(20)
const candidateStatus = ref('all')
const detailCandidatePage = ref(1)
const detailCandidatePageSize = ref(12)
const rssPage = ref(1)
const rssPageSize = ref(20)

const subList = computed(() => Object.values(subscriptions.value || {}))
const filteredSubs = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return subList.value.filter(sub => {
    if (sub.display_valid === false) return false
    if (filter.value === 'active' && sub.state !== 'active') return false
    if (filter.value === 'paused' && sub.state !== 'paused') return false
    if (filter.value === 'pending' && !Object.keys(sub.pending || {}).length) return false
    if (filter.value === 'airing' && sub.mode !== 'airing') return false
    if (filter.value === 'backfill' && sub.mode !== 'backfill') return false
    if (kw && !`${sub.title || ''} ${sub.preferred_group || ''}`.toLowerCase().includes(kw)) return false
    return true
  })
})
const pagedSubs = computed(() => filteredSubs.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value))
const openIssues = computed(() => (recognitionIssues.value || []).filter(item => item.status !== 'ignored'))
const candidateStatusOptions = computed(() => {
  const counts = {}
  for (const item of candidates.value || []) counts[item.status || 'unknown'] = (counts[item.status || 'unknown'] || 0) + 1
  const labels = { ready: '可下载', pending: '等待中', orphan: '未绑定', skipped: '已跳过', recognition_issue: '识别异常', recognition_conflict: '识别冲突', downloaded: '已下载', submitted: '已提交', download_failed: '下载失败', transferred: '已转移', transfer_recorded: '有转移记录', ignored: '已忽略', unrecognized: '未识别' }
  return Object.entries(counts).sort((a, b) => b[1] - a[1]).map(([value, count]) => ({ value, count, label: labels[value] || value }))
})
const filteredCandidates = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  const source = candidates.value || []
  return source.filter(item => {
    if (candidateStatus.value !== 'all' && (item.status || 'unknown') !== candidateStatus.value) return false
    if (kw && !`${item.title || ''} ${item.media_title || ''} ${item.group || ''} ${item.reason || ''}`.toLowerCase().includes(kw)) return false
    return true
  })
})
const pagedCandidates = computed(() => filteredCandidates.value.slice((candidatePage.value - 1) * candidatePageSize.value, candidatePage.value * candidatePageSize.value))
const pagedDetailCandidates = computed(() => (detailCandidates.value || []).slice((detailCandidatePage.value - 1) * detailCandidatePageSize.value, detailCandidatePage.value * detailCandidatePageSize.value))
const pagedRssResults = computed(() => (rssResults.value || []).slice((rssPage.value - 1) * rssPageSize.value, rssPage.value * rssPageSize.value))
watch([keyword, searchMode], () => {
  candidatePage.value = 1
  rssPage.value = 1
  page.value = 1
})
watch(candidateStatus, () => { candidatePage.value = 1 })
watch(detailCandidates, () => { detailCandidatePage.value = 1 })

function imageUrl(src) {
  if (!src) return ''
  if (String(src).startsWith('http')) return src
  if (String(src).startsWith('/')) return `https://image.tmdb.org/t/p/w500${src}`
  return src
}
function tmdbImage(sub, type) {
  if (type === 'poster') return imageUrl(sub.poster || '')
  return imageUrl(sub.backdrop || sub.poster || '')
}
function seasonText(sub) { return `S${String(sub.season || 1).padStart(2, '0')}` }
function downloadedCount(sub) { return Number(sub.library_completed_episode ?? sub.episode_fact_counts?.library_exists ?? 0) }
function pendingCount(sub) { return Number(sub.pending_count ?? Object.keys(sub.pending || {}).length) }
function totalEpisode(sub) { return Number(sub.total_episode || 0) }
function progressValue(sub) { const total = totalEpisode(sub); const done = downloadedCount(sub); return Number(total ? Math.min(100, Math.round(done * 100 / total)) : (done ? 100 : 0)) }
function groupText(sub) { return sub.preferred_group || sub.username || 'BT订阅中心' }
function lackCount(sub) { return Number(sub.lack_episode ?? Math.max(totalEpisode(sub) - downloadedCount(sub), 0)) }
function episodeItems(sub) {
  const total = totalEpisode(sub)
  const maxEp = Math.max(total, ...Object.keys(sub?.downloaded || {}).map(v => Number(v) || 0), ...(sub?.library_episodes || []).map(v => Number(v) || 0), ...(sub?.candidate_episodes || []).map(v => Number(v) || 0), 0)
  const limit = maxEp || 12
  return Array.from({ length: limit }, (_, i) => i + 1)
}
function episodeState(sub, ep) {
  const epNum = Number(ep)
  const downloaded = sub?.downloaded || {}
  const facts = sub?.episode_facts || {}
  const fact = facts[String(epNum)] || null
  const record = downloaded[String(epNum)] || null
  const library = new Set((sub?.library_episodes || []).map(v => Number(v)))
  const candidates = new Set((sub?.candidate_episodes || []).map(v => Number(v)))
  const missing = new Set((sub?.missing_episodes || []).map(v => Number(v)))
  if (library.has(epNum) || fact?.final_state === 'library_exists') return 'library'
  if (fact?.final_state === 'submitted_no_hash') return 'nohash'
  if (fact?.final_state === 'download_failed' || record?.state === 'download_failed') return 'failed'
  if (fact?.final_state === 'downloading') return 'downloading'
  if (['download_history','transfer_recorded','submitted'].includes(fact?.final_state) || record?.state === 'download_history' || record?.state === 'transfer_recorded' || record?.state === 'submitted') return 'submitted'
  if (record) return 'downloaded'
  if (candidates.has(epNum)) return 'candidate'
  if (missing.has(epNum)) return 'missing'
  return 'unknown'
}
function episodeColor(sub, ep) {
  return { library: 'success', downloaded: 'primary', submitted: 'info', downloading: 'cyan', nohash: 'orange', failed: 'error', candidate: 'warning', missing: 'error', unknown: 'grey' }[episodeState(sub, ep)] || 'grey'
}
function episodeLabel(sub, ep) {
  return { library: '已入库', downloaded: '已记录', submitted: '已提交', downloading: '下载中', nohash: '缺Hash', failed: '失败', candidate: '有候选', missing: '缺集', unknown: '未知' }[episodeState(sub, ep)] || '未知'
}

function statusColor(status) {
  return { ready: 'success', pending: 'warning', recognition_issue: 'error', recognition_conflict: 'orange', unrecognized: 'error', orphan: 'info', skipped: 'grey', ignored: 'grey', downloaded: 'success', submitted: 'info', download_failed: 'error', transferred: 'success', transfer_recorded: 'info', replacement_ready: 'purple', replacement_submitted: 'info', replacement_failed: 'error' }[status] || 'primary'
}
function showAction(message, ok = true) {
  actionMessage.value = message
  actionOk.value = ok
  setTimeout(() => { actionMessage.value = '' }, 3500)
}
function askConfirm(options = {}) {
  return new Promise(resolve => {
    confirmState.value = {
      title: options.title || '确认操作',
      message: options.message || '是否继续？',
      color: options.color || 'primary',
      confirmText: options.confirmText || '确认',
      cancelText: options.cancelText || '取消',
      resolve,
    }
    showConfirmDialog.value = true
  })
}
function closeConfirm(result) {
  const resolver = confirmState.value.resolve
  showConfirmDialog.value = false
  confirmState.value = { title: '', message: '', color: 'primary', confirmText: '确认', cancelText: '取消', resolve: null }
  if (resolver) resolver(Boolean(result))
}
function normalize(value) {
  if (value?.success === false) throw new Error(value.message || '操作失败')
  return value?.data ?? value
}
async function loadAll() {
  loading.value = true
  error.value = ''
  try {
    const overview = normalize(await getPluginApi(props.api, 'overview'))
    stats.value = overview?.stats || stats.value
    currentConfig.value = overview?.config || currentConfig.value
    downloadFactSummary.value = overview?.download_fact_summary || {}
    cleanupSummary.value = overview?.cleanup_summary || {}
    replacementSummary.value = overview?.replacement_summary || {}
    subscriptions.value = overview?.subscriptions || {}
    candidates.value = overview?.candidates || []
    recognitionIssues.value = overview?.recognition_issues || []
  } catch (err) {
    error.value = err.message || String(err)
  } finally {
    loading.value = false
  }
}
async function openSub(sub) {
  selected.value = sub
  detailCandidates.value = candidates.value.filter(item => item.subscription_id === sub.id)
  detailCandidatePage.value = 1
  try {
    const detail = normalize(await getPluginApi(props.api, `subscription?sub_id=${encodeURIComponent(sub.id)}`))
    selected.value = detail.subscription || sub
    detailCandidates.value = detail.candidates || detailCandidates.value
  } catch (err) {
    showAction(err.message || '加载订阅详情失败', false)
  }
}
async function refreshRss() {
  loading.value = true
  try {
    await postPluginApi(props.api, 'refresh', {})
    showAction('RSS 刷新完成')
    await loadAll()
  } catch (err) {
    showAction(err.message || '刷新失败', false)
  } finally {
    loading.value = false
  }
}
async function setState(sub, state) {
  try {
    const path = state === 'active' ? 'resume_subscription' : 'pause_subscription'
    await postPluginApi(props.api, path, { sub_id: sub.id })
    showAction(state === 'active' ? '已恢复订阅' : '已暂停订阅')
    await loadAll()
    if (selected.value?.id === sub.id) selected.value = subscriptions.value[sub.id]
  } catch (err) {
    showAction(err.message || '状态更新失败', false)
  }
}
function openGroup(sub) {
  selected.value = sub
  groupInput.value = sub.preferred_group || ''
  showGroupDialog.value = true
}
async function saveGroup() {
  try {
    await postPluginApi(props.api, 'set_group', { sub_id: selected.value.id, group: groupInput.value })
    showGroupDialog.value = false
    showAction('发布组标记已更新')
    await loadAll()
    selected.value = subscriptions.value[selected.value.id]
  } catch (err) {
    showAction(err.message || '发布组标记更新失败', false)
  }
}
async function ignoreCandidate(item) {
  try {
    await postPluginApi(props.api, 'ignore_candidate', { key: item.key })
    showAction('已忽略候选')
    await loadAll()
    if (selected.value) await openSub(selected.value)
  } catch (err) {
    showAction(err.message || '忽略失败', false)
  }
}
async function downloadCandidate(item) {
  if (!(await askConfirm({ title: '下载候选资源', message: item.title, color: 'primary', confirmText: '下载' }))) return
  try {
    const res = normalize(await postPluginApi(props.api, 'download_candidate', { key: item.key, confirm: true }))
    showAction(res?.download_hash ? `已提交下载：${String(res.download_hash).slice(0, 8)}` : '已提交下载')
    await loadAll()
    if (selected.value) await openSub(selected.value)
  } catch (err) {
    showAction(err.message || '下载失败', false)
  }
}


async function searchRssNow() {
  const kw = keyword.value.trim()
  if (!kw) { showAction('请输入搜索关键字', false); return }
  loading.value = true
  try {
    const res = normalize(await postPluginApi(props.api, 'rss_search', { keyword: kw, limit: 120 }))
    rssResults.value = res || []
    rssPage.value = 1
    searchMode.value = 'rss'
    showAction(`已搜索 RSS/BT 源，命中 ${rssResults.value.length} 条`)
  } catch (err) {
    showAction(err.message || 'RSS 搜索失败', false)
  } finally {
    loading.value = false
  }
}
async function saveConfigDialog(config) {
  try {
    await postPluginApi(props.api, 'save_config', config)
    showConfigDialog.value = false
    showAction('设置已保存')
    await loadAll()
  } catch (err) {
    showAction(err.message || '设置保存失败', false)
  }
}
function closePage() {
  if (window.history.length > 1) window.history.back()
  else showAction('当前是侧栏页面，已留在 BT订阅中心')
}
async function refreshSubStatus(sub) {
  try {
    const res = normalize(await postPluginApi(props.api, 'refresh_subscription_status', { sub_id: sub.id }))
    subscriptions.value[sub.id] = res
    if (selected.value?.id === sub.id) selected.value = res
    showAction('入库状态已刷新')
  } catch (err) {
    showAction(err.message || '刷新入库状态失败', false)
  }
}
async function deleteSubscription(sub) {
  if (!(await askConfirm({ title: '删除私有订阅', message: sub.title, color: 'error', confirmText: '删除' }))) return
  try {
    await postPluginApi(props.api, 'delete_subscription', { sub_id: sub.id, confirm: true })
    showAction('私有订阅已删除')
    if (selected.value?.id === sub.id) selected.value = null
    await loadAll()
  } catch (err) { showAction(err.message || '删除失败', false) }
}
async function createBackfillFromSub(sub) {
  try {
    await postPluginApi(props.api, 'add_subscription', { title: sub.title, tmdbid: sub.tmdbid, season: sub.season || 1, mode: 'backfill', group: sub.preferred_group || '' })
    showAction('已按老番补全模式保存')
    await loadAll()
  } catch (err) { showAction(err.message || '操作失败', false) }
}


function openEdit(sub) {
  selected.value = sub
  editForm.value = { ...sub }
  showEditDialog.value = true
}
async function saveSubscriptionEdit() {
  try {
    const payload = { ...editForm.value, sub_id: selected.value.id }
    const res = normalize(await postPluginApi(props.api, 'update_subscription', payload))
    subscriptions.value[selected.value.id] = res
    selected.value = res
    showEditDialog.value = false
    showAction('订阅已更新')
  } catch (err) { showAction(err.message || '编辑订阅失败', false) }
}
async function refreshSubMeta(sub) {
  try {
    const res = normalize(await postPluginApi(props.api, 'refresh_subscription_meta', { sub_id: sub.id }))
    subscriptions.value[sub.id] = res
    if (selected.value?.id === sub.id) selected.value = res
    showAction('媒体信息已刷新')
  } catch (err) { showAction(err.message || '刷新媒体信息失败', false) }
}
async function searchSubCandidates(sub) {
  try {
    const res = normalize(await postPluginApi(props.api, 'search_subscription_candidates', { sub_id: sub.id, include_rss: true }))
    detailCandidates.value = [...(res.candidates || []), ...(res.rss_results || [])]
    selected.value = res.subscription || sub
    searchMode.value = 'candidates'
    keyword.value = sub.title || ''
    rssResults.value = res.rss_results || []
    showAction(`已搜索候选：本地 ${res.candidates?.length || 0}，BT源 ${res.rss_results?.length || 0}`)
  } catch (err) { showAction(err.message || '搜索候选失败', false) }
}
async function clearPending(sub) {
  if (!(await askConfirm({ title: '清空等待队列', message: sub.title, color: 'warning', confirmText: '清空' }))) return
  try {
    const res = normalize(await postPluginApi(props.api, 'clear_pending', { sub_id: sub.id, confirm: true }))
    subscriptions.value[sub.id] = res
    if (selected.value?.id === sub.id) selected.value = res
    showAction('等待队列已清空')
  } catch (err) { showAction(err.message || '清空等待失败', false) }
}
async function resetDownloaded(sub) {
  if (!(await askConfirm({ title: '重置下载记录', message: `${sub.title}\n这不会删除文件，只会清空插件私有下载事实。`, color: 'warning', confirmText: '重置' }))) return
  try {
    const res = normalize(await postPluginApi(props.api, 'reset_downloaded', { sub_id: sub.id, confirm: true }))
    subscriptions.value[sub.id] = res
    if (selected.value?.id === sub.id) selected.value = res
    showAction('下载记录已重置')
  } catch (err) { showAction(err.message || '重置下载记录失败', false) }
}
function openFacts(sub) {
  selected.value = sub
  showFactsDialog.value = true
}

async function rescanIssue(item) {
  try {
    const res = normalize(await postPluginApi(props.api, 'rescan_issue', { key: item.key }))
    showAction(res.status === 'resolved' ? '异常已重新识别为动画' : '已重扫并更新建议', res.status === 'resolved')
    await loadAll()
  } catch (err) { showAction(err.message || '重扫异常失败', false) }
}
async function ignoreIssue(item) {
  try {
    await postPluginApi(props.api, 'ignore_issue', { key: item.key })
    showAction('已忽略识别异常')
    await loadAll()
  } catch (err) { showAction(err.message || '忽略异常失败', false) }
}

async function previewIssueIdentifier(item) {
  try {
    const res = normalize(await postPluginApi(props.api, 'issue_identifier_preview', { key: item.key }))
    issuePreview.value = res
    showIssuePreviewDialog.value = true
  } catch (err) { showAction(err.message || '生成识别词预览失败', false) }
}
async function applyIssueIdentifier() {
  if (!issuePreview.value?.key || !issuePreview.value?.identifier) return
  if (!(await askConfirm({ title: '写入自定义识别词', message: `${issuePreview.value.identifier}

会先保存当前识别词快照，然后写入该窄作用域规则并回流候选。`, color: 'warning', confirmText: '写入' }))) return
  try {
    const res = normalize(await postPluginApi(props.api, 'apply_issue_identifier', { key: issuePreview.value.key, identifier: issuePreview.value.identifier, confirm: true }))
    showIssuePreviewDialog.value = false
    showAction(`识别词已写入：${res.write?.added ? '新增成功' : (res.write?.message || '已存在')}`)
    await loadAll()
  } catch (err) { showAction(err.message || '写入识别词失败', false) }
}
async function openIssueAgentHint(item) {
  try {
    const res = normalize(await postPluginApi(props.api, 'issue_agent_hint', { key: item.key }))
    issueAgentHint.value = res
    showIssueAgentDialog.value = true
  } catch (err) { showAction(err.message || '生成智能体提示失败', false) }
}
async function autoWriteIssue(item) {
  try {
    const hint = normalize(await postPluginApi(props.api, 'issue_agent_hint', { key: item.key }))
    const payload = { key: item.key, identifier: hint.suggested_identifier || '', confirm: true }
    const res = normalize(await postPluginApi(props.api, 'issue_agent_apply', payload))
    issueAgentHint.value = { ...hint, applied: res }
    showIssueAgentDialog.value = true
    showAction('智能体已自动写入识别词并回流候选')
    await loadAll()
  } catch (err) { showAction(err.message || '智能体自动写入失败', false) }
}

async function reflowIssue(item) {
  if (!(await askConfirm({ title: '回流候选', message: `${item.title}

仅把该异常重新放回候选池，不写识别词、不立即下载。`, color: 'primary', confirmText: '回流' }))) return
  try {
    await postPluginApi(props.api, 'reflow_issue', { key: item.key, confirm: true })
    showAction('异常已回流候选')
    await loadAll()
  } catch (err) { showAction(err.message || '回流候选失败', false) }
}
async function openNoHashDiagnostics() {
  try {
    const res = normalize(await getPluginApi(props.api, 'submitted_no_hash?limit=300'))
    submittedNoHashItems.value = res || []
    showNoHashDialog.value = true
  } catch (err) { showAction(err.message || '加载缺Hash诊断失败', false) }
}

onMounted(loadAll)
</script>

<template>
  <div class="bt-root">
    <v-alert v-if="actionMessage" :type="actionOk ? 'success' : 'error'" variant="tonal" class="mb-3">{{ actionMessage }}</v-alert>
    <v-alert v-if="error" type="error" variant="tonal" class="mb-3">{{ error }}</v-alert>

    <div class="bt-hero mb-4">
      <div>
        <div class="text-h5 font-weight-bold">BT订阅中心</div>
        <div class="text-body-2 text-medium-emphasis">像使用 MoviePilot 订阅一样管理 BT/RSS 动漫源：订阅、候选、缺集、下载事实、整季包替换都在一个页面闭环。</div>
      </div>
      <div class="d-flex ga-2 align-center">
        <v-btn color="primary" variant="tonal" prepend-icon="mdi-refresh" :loading="loading" @click="refreshRss">刷新 RSS</v-btn>
        <v-btn color="error" variant="tonal" prepend-icon="mdi-alert-decagram" @click="showIssuesDialog = true">识别异常 {{ openIssues.length }}</v-btn>
        <v-btn variant="text" icon="mdi-cog" aria-label="打开设置" title="打开设置" @click="showConfigDialog = true" />
        <v-btn variant="text" icon="mdi-close" aria-label="关闭页面" title="关闭页面" @click="closePage" />
      </div>
    </div>

    <v-row class="mb-2">
      <v-col cols="6" md="3"><v-card variant="tonal" color="primary"><v-card-text>私有订阅</v-card-text><v-card-title>{{ stats.subscriptions }}</v-card-title></v-card></v-col>
      <v-col cols="6" md="3"><v-card variant="tonal" color="info"><v-card-text>候选资源</v-card-text><v-card-title>{{ stats.candidates }}</v-card-title></v-card></v-col>
      <v-col cols="6" md="3"><v-card variant="tonal" color="warning"><v-card-text>待处理候选</v-card-text><v-card-title>{{ stats.pending }}</v-card-title></v-card></v-col>
      <v-col cols="6" md="3"><v-card variant="tonal" color="success"><v-card-text>已提交/记录</v-card-text><v-card-title>{{ stats.downloaded }}</v-card-title></v-card></v-col>
      <v-col cols="6" md="3"><v-card variant="tonal" color="error"><v-card-text>识别异常</v-card-text><v-card-title>{{ openIssues.length }}</v-card-title></v-card></v-col>
    </v-row>

    <v-alert v-if="downloadFactSummary.total_records" type="info" variant="tonal" class="mb-4">
      <div class="d-flex flex-wrap align-center justify-space-between ga-2">
        <span>下载事实：总记录 {{ downloadFactSummary.total_records || 0 }}，可追踪Hash {{ downloadFactSummary.hash_tracked || 0 }}，历史缺Hash {{ downloadFactSummary.submitted_no_hash || 0 }}，下载中 {{ downloadFactSummary.downloading || 0 }}，已入库 {{ downloadFactSummary.library_exists || 0 }}；入库后清理 qB：成功 {{ cleanupSummary.removed || 0 }}，失败 {{ cleanupSummary.failed || 0 }}；整季包替换：监控 {{ replacementSummary.watching || 0 }}，已提交 {{ replacementSummary.submitted || 0 }}，已验证 {{ replacementSummary.verified || 0 }}，失败 {{ replacementSummary.failed || 0 }}。</span>
        <v-btn v-if="downloadFactSummary.submitted_no_hash" size="small" color="orange" variant="tonal" prepend-icon="mdi-alert-circle-outline" @click="openNoHashDiagnostics">查看缺Hash</v-btn>
      </div>
    </v-alert>

    <v-card class="search-panel mb-4" variant="tonal" rounded="lg">
      <v-card-text>
        <div class="d-flex flex-wrap ga-2 align-center mb-3">
          <v-text-field v-model="keyword" density="compact" variant="outlined" hide-details prepend-inner-icon="mdi-magnify" label="搜索订阅 / RSS候选 / 已配置BT源" style="max-width: 420px" @keyup.enter="searchMode === 'rss' ? searchRssNow() : null" />
          <v-btn color="primary" variant="tonal" prepend-icon="mdi-rss" :loading="loading" @click="searchRssNow">搜已配置BT源</v-btn>
        </div>
        <v-tabs v-model="searchMode" density="compact">
          <v-tab value="subscriptions">订阅 {{ filteredSubs.length }}</v-tab>
          <v-tab value="candidates">RSS候选 {{ filteredCandidates.length }}</v-tab>
          <v-tab value="rss">实时BT源 {{ rssResults.length }}</v-tab>
        </v-tabs>
        <div v-if="searchMode === 'subscriptions'" class="d-flex flex-wrap ga-2 mt-3 align-center">
          <v-chip-group v-model="filter" mandatory selected-class="text-primary">
            <v-chip value="all">全部</v-chip><v-chip value="active">运行中</v-chip><v-chip value="paused">已暂停</v-chip><v-chip value="pending">有等待</v-chip><v-chip value="airing">新番</v-chip><v-chip value="backfill">老番</v-chip>
          </v-chip-group>
        </div>
      </v-card-text>
    </v-card>


    <v-card v-if="searchMode === 'candidates'" class="mb-4" variant="tonal" rounded="lg">
      <v-card-title class="d-flex flex-wrap align-center justify-space-between ga-2"><span>BT/RSS 候选池</span><v-chip size="small" variant="tonal">{{ filteredCandidates.length }} / {{ candidates.length }}</v-chip></v-card-title>
      <v-card-subtitle>候选按识别、订阅绑定、下载事实和入库状态分层展示；发布组只用于统计与后续整季包替换，不再阻塞追更。</v-card-subtitle>
      <v-card-text>
        <div class="d-flex flex-wrap ga-2 mb-3">
          <v-chip :color="candidateStatus === 'all' ? 'primary' : undefined" :variant="candidateStatus === 'all' ? 'tonal' : 'outlined'" size="small" @click="candidateStatus='all'">全部 {{ candidates.length }}</v-chip>
          <v-chip v-for="opt in candidateStatusOptions" :key="opt.value" :color="candidateStatus === opt.value ? statusColor(opt.value) : undefined" :variant="candidateStatus === opt.value ? 'tonal' : 'outlined'" size="small" @click="candidateStatus=opt.value">{{ opt.label }} {{ opt.count }}</v-chip>
        </div>
        <v-list density="compact" lines="two">
          <v-list-item v-for="item in pagedCandidates" :key="item.key" class="bt-candidate-row">
            <template #prepend><v-chip size="x-small" :color="statusColor(item.status)" variant="tonal">{{ item.status || '-' }}</v-chip></template>
            <v-list-item-title>{{ item.title }}</v-list-item-title>
            <v-list-item-subtitle>组：{{ item.group || '-' }}｜E：{{ (item.episodes || []).join(',') || '-' }}｜{{ item.reason }}</v-list-item-subtitle>
            <template #append><v-btn icon="mdi-download" size="small" variant="text" aria-label="下载候选" title="下载候选" @click="downloadCandidate(item)" /><v-btn icon="mdi-eye-off" size="small" variant="text" aria-label="忽略候选" title="忽略候选" @click="ignoreCandidate(item)" /></template>
          </v-list-item>
          <v-list-item v-if="!filteredCandidates.length" title="暂无候选" subtitle="刷新 RSS 或切换实时BT源搜索。" />
        </v-list>
        <div v-if="filteredCandidates.length > candidatePageSize" class="d-flex flex-wrap justify-center align-center ga-2 mt-3">
          <div class="text-caption text-medium-emphasis">第 {{ candidatePage }} 页 / 共 {{ Math.ceil(filteredCandidates.length / candidatePageSize) }} 页</div>
          <v-pagination v-model="candidatePage" :length="Math.ceil(filteredCandidates.length / candidatePageSize)" density="comfortable" total-visible="7" />
        </div>
      </v-card-text>
    </v-card>

    <v-card v-if="searchMode === 'rss'" class="mb-4" variant="tonal" rounded="lg">
      <v-card-title>实时BT源搜索结果</v-card-title>
      <v-card-text>
        <v-alert type="info" variant="tonal" class="mb-3">这里只搜索你在插件里配置的 RSS/BT 来源；下载仍需确认，且必须通过动漫/特摄准入与去重。</v-alert>
        <v-list density="compact" lines="two">
          <v-list-item v-for="item in pagedRssResults" :key="item.key">
            <template #prepend><v-chip size="x-small" color="info" variant="tonal">BT源</v-chip></template>
            <v-list-item-title>{{ item.title }}</v-list-item-title>
            <v-list-item-subtitle>组：{{ item.group || '-' }}｜{{ item.source_url }}</v-list-item-subtitle>
            <template #append><v-btn icon="mdi-download" size="small" variant="text" aria-label="下载候选" title="下载候选" @click="downloadCandidate(item)" /></template>
          </v-list-item>
          <v-list-item v-if="!rssResults.length" title="暂无结果" subtitle="输入关键字后点击“搜已配置BT源”。" />
        </v-list>
        <div v-if="rssResults.length > rssPageSize" class="d-flex flex-wrap justify-center align-center ga-2 mt-3">
          <div class="text-caption text-medium-emphasis">第 {{ rssPage }} 页 / 共 {{ Math.ceil(rssResults.length / rssPageSize) }} 页</div>
          <v-pagination v-model="rssPage" :length="Math.ceil(rssResults.length / rssPageSize)" density="comfortable" total-visible="7" />
        </div>
      </v-card-text>
    </v-card>

    <v-row v-if="searchMode === 'subscriptions'">
      <v-col v-for="sub in pagedSubs" :key="sub.id" cols="12" sm="6" md="4" lg="3">
        <v-card class="sub-card" rounded="lg" elevation="3" :style="{ backgroundImage: `linear-gradient(90deg, rgba(4,8,18,.96), rgba(4,8,18,.72)), url('${tmdbImage(sub, 'backdrop')}')` }" @click="openSub(sub)">
          <v-card-text class="pa-3 fill-height d-flex flex-column">
            <div class="d-flex align-start">
              <div class="poster-wrap me-3"><v-img v-if="tmdbImage(sub, 'poster')" :src="tmdbImage(sub, 'poster')" width="58" height="82" cover class="rounded poster" /><div v-else class="poster-fallback rounded">{{ seasonText(sub) }}</div></div>
              <div class="flex-grow-1 min-w-0">
                <div class="text-caption sub-muted">{{ sub.year || '----' }}</div>
                <div class="text-subtitle-1 font-weight-bold title-line sub-title">{{ sub.title }} {{ seasonText(sub) }}</div>
                <div class="text-caption mt-2 sub-line"><v-icon size="14" icon="mdi-progress-download" class="me-1" />{{ downloadedCount(sub) }} / {{ totalEpisode(sub) || '?' }} <span class="mx-1">·</span> 缺 {{ lackCount(sub) }}</div><div class="text-caption sub-muted mt-1"><v-icon size="14" icon="mdi-account" class="me-1" />{{ groupText(sub) }}</div>
              </div>
              <v-menu @click.stop>
                <template #activator="{ props: menuProps }"><v-btn v-bind="menuProps" icon="mdi-dots-vertical" variant="text" size="small" aria-label="订阅更多操作" title="订阅更多操作" @click.stop /></template>
                <v-list density="compact">
                  <v-list-item prepend-icon="mdi-eye" title="查看详情" @click="openSub(sub)" />
                  <v-list-item prepend-icon="mdi-pencil" title="编辑订阅" @click="openEdit(sub)" />
                  <v-list-item prepend-icon="mdi-clipboard-text-clock" title="查看下载/等待记录" @click="openFacts(sub)" />
                  <v-divider />
                  <v-list-item prepend-icon="mdi-magnify" title="搜索缺集候选" @click="searchSubCandidates(sub)" />
                  <v-list-item prepend-icon="mdi-rss" title="从BT源实时搜索" @click="keyword=sub.title;searchRssNow()" />
                  <v-list-item prepend-icon="mdi-image-refresh" title="刷新媒体信息" @click="refreshSubMeta(sub)" />
                  <v-list-item prepend-icon="mdi-refresh" title="刷新入库状态" @click="refreshSubStatus(sub)" />
                  <v-divider />
                  <v-list-item prepend-icon="mdi-account-group" title="设置发布组标记" @click="openGroup(sub)" />
                  <v-list-item prepend-icon="mdi-folder-download" title="设为老番补全" @click="createBackfillFromSub(sub)" />
                  <v-list-item v-if="sub.state === 'active'" prepend-icon="mdi-pause-circle" title="暂停订阅" @click="setState(sub, 'paused')" />
                  <v-list-item v-else prepend-icon="mdi-play-circle" title="恢复订阅" @click="setState(sub, 'active')" />
                  <v-divider />
                  <v-list-item prepend-icon="mdi-clock-remove" title="清空等待队列" @click="clearPending(sub)" />
                  <v-list-item prepend-icon="mdi-history" title="重置下载记录" @click="resetDownloaded(sub)" />
                  <v-list-item prepend-icon="mdi-delete-outline" title="删除私有订阅" @click="deleteSubscription(sub)" />
                </v-list>
              </v-menu>
            </div>
            <v-spacer />
            <v-progress-linear :model-value="progressValue(sub)" color="success" height="5" rounded class="mt-3" />
            <div class="d-flex justify-space-between text-caption mt-2 sub-muted"><span>{{ sub.username || 'BT订阅中心' }}</span><span>{{ sub.state === 'paused' ? '已暂停' : `待定 ${pendingCount(sub)}` }}</span></div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <div v-if="searchMode === 'subscriptions' && filteredSubs.length > pageSize" class="d-flex flex-wrap justify-center align-center ga-2 my-4">
      <div class="text-caption text-medium-emphasis">第 {{ page }} 页 / 共 {{ Math.ceil(filteredSubs.length / pageSize) }} 页</div>
      <v-pagination v-model="page" :length="Math.ceil(filteredSubs.length / pageSize)" density="comfortable" total-visible="7" />
    </div>


    <v-dialog :model-value="!!selected" max-width="1120" scrollable class="subscription-detail-shell" @update:model-value="v => { if (!v) selected = null }">
      <v-card v-if="selected" class="detail-dialog-full" rounded="0">
        <v-toolbar color="surface" density="comfortable" class="detail-toolbar">
          <v-btn icon="mdi-close" variant="text" aria-label="关闭详情" title="关闭详情" @click="selected = null" />
          <v-toolbar-title class="text-subtitle-1 text-md-h6 font-weight-bold text-truncate">{{ selected.title }} {{ seasonText(selected) }}</v-toolbar-title>
          <v-spacer />
          <v-btn size="small" color="primary" variant="tonal" prepend-icon="mdi-pencil" @click="openEdit(selected)">编辑</v-btn><v-btn size="small" color="info" variant="tonal" class="ms-2" prepend-icon="mdi-magnify" @click="searchSubCandidates(selected)">搜候选</v-btn>
          <v-btn v-if="selected.state === 'active'" size="small" color="warning" variant="tonal" class="ms-2" prepend-icon="mdi-pause-circle" @click="setState(selected, 'paused')">暂停</v-btn>
          <v-btn v-else size="small" color="success" variant="tonal" class="ms-2" prepend-icon="mdi-play-circle" @click="setState(selected, 'active')">恢复</v-btn>
        </v-toolbar>

        <div class="detail-scroll">
          <div class="detail-hero" :style="{ backgroundImage: `linear-gradient(90deg, rgba(4,8,18,.94), rgba(4,8,18,.70), rgba(4,8,18,.35)), url('${tmdbImage(selected, 'backdrop')}')` }">
            <div class="detail-hero-content">
              <v-img v-if="tmdbImage(selected, 'poster')" :src="tmdbImage(selected, 'poster')" width="128" height="186" cover class="detail-poster" />
              <div v-else class="detail-poster detail-poster-fallback">{{ seasonText(selected) }}</div>
              <div class="detail-title-block">
                <div class="d-flex flex-wrap ga-2 mb-2">
                  <v-chip size="small" color="primary" variant="tonal">{{ selected.mode === 'airing' ? '新番追更' : '老番补全' }}</v-chip>
                  <v-chip size="small" :color="selected.state === 'paused' ? 'warning' : 'success'" variant="tonal">{{ selected.state === 'paused' ? '已暂停' : '运行中' }}</v-chip>
                  <v-chip size="small" color="info" variant="tonal">BT/RSS</v-chip>
                </div>
                <div class="text-h5 text-md-h4 font-weight-bold mb-2">{{ selected.title }} {{ seasonText(selected) }}</div>
                <div class="text-body-2 detail-meta mb-3">{{ selected.year || '未知年份' }} · {{ selected.source || 'BT/RSS' }} · 发布组：{{ groupText(selected) }}</div>
                <div class="detail-overview text-body-2">{{ selected.description || '暂无简介。' }}</div>
              </div>
            </div>
          </div>

          <div class="detail-content">
            <v-row class="mb-3">
              <v-col cols="6" md="3"><v-card variant="tonal" color="success" rounded="lg"><v-card-text class="py-3"><div class="text-caption">已入库/完成</div><div class="text-h5 font-weight-bold">{{ downloadedCount(selected) }}</div></v-card-text></v-card></v-col>
              <v-col cols="6" md="3"><v-card variant="tonal" color="primary" rounded="lg"><v-card-text class="py-3"><div class="text-caption">总集数</div><div class="text-h5 font-weight-bold">{{ totalEpisode(selected) || '?' }}</div></v-card-text></v-card></v-col>
              <v-col cols="6" md="3"><v-card variant="tonal" color="error" rounded="lg"><v-card-text class="py-3"><div class="text-caption">缺集</div><div class="text-h5 font-weight-bold">{{ lackCount(selected) }}</div></v-card-text></v-card></v-col>
              <v-col cols="6" md="3"><v-card variant="tonal" color="warning" rounded="lg"><v-card-text class="py-3"><div class="text-caption">等待候选</div><div class="text-h5 font-weight-bold">{{ pendingCount(selected) }}</div></v-card-text></v-card></v-col>
            </v-row>

            <v-card variant="tonal" rounded="lg" class="mb-4">
              <v-card-text>
                <div class="d-flex justify-space-between text-caption mb-2"><span>订阅进度</span><span>{{ progressValue(selected) }}%</span></div>
                <v-progress-linear :model-value="progressValue(selected)" color="success" height="8" rounded />
              </v-card-text>
            </v-card>

            <v-card variant="tonal" rounded="lg" class="mb-4">
              <v-card-title class="text-subtitle-1">集数状态</v-card-title>
              <v-card-text>
                <div class="episode-grid">
                  <v-tooltip v-for="ep in episodeItems(selected)" :key="ep" :text="`E${String(ep).padStart(2, '0')} · ${episodeLabel(selected, ep)}`" location="top">
                    <template #activator="{ props: tipProps }">
                      <v-chip v-bind="tipProps" size="small" :color="episodeColor(selected, ep)" variant="tonal" class="episode-chip">E{{ String(ep).padStart(2, '0') }}</v-chip>
                    </template>
                  </v-tooltip>
                </div>
                <div class="d-flex flex-wrap ga-2 mt-3 text-caption text-medium-emphasis">
                  <span><v-icon size="12" color="success" icon="mdi-circle" /> 已入库</span>
                  <span><v-icon size="12" color="info" icon="mdi-circle" /> 已提交</span><span><v-icon size="12" color="orange" icon="mdi-circle" /> 缺Hash</span>
                  <span><v-icon size="12" color="warning" icon="mdi-circle" /> 有候选</span>
                  <span><v-icon size="12" color="error" icon="mdi-circle" /> 缺集</span>
                </div>
              </v-card-text>
            </v-card>

            <v-card variant="tonal" rounded="lg">
              <v-card-title class="d-flex align-center justify-space-between">
                <span>相关候选</span>
                <v-chip size="small" variant="tonal">{{ detailCandidates.length }} 条</v-chip>
              </v-card-title>
              <v-card-text>
                <v-list density="compact" lines="three" class="candidate-list">
                  <v-list-item v-for="item in pagedDetailCandidates" :key="item.key" class="candidate-row">
                    <template #prepend><v-chip size="x-small" :color="statusColor(item.status)" variant="tonal">{{ item.status || '-' }}</v-chip></template>
                    <v-list-item-title>{{ item.title }}</v-list-item-title>
                    <v-list-item-subtitle>组：{{ item.group || '-' }}｜E：{{ (item.episodes || []).join(',') || '-' }}｜{{ item.reason }}</v-list-item-subtitle>
                    <template #append>
                      <v-btn icon="mdi-download" size="small" variant="text" aria-label="下载候选" title="下载候选" @click="downloadCandidate(item)" />
                      <v-btn icon="mdi-eye-off" size="small" variant="text" aria-label="忽略候选" title="忽略候选" @click="ignoreCandidate(item)" />
                    </template>
                  </v-list-item>
                  <v-list-item v-if="!detailCandidates.length" title="暂无候选" subtitle="刷新 RSS 后会在这里看到匹配到本订阅的候选资源。" />
                </v-list>
                <div v-if="detailCandidates.length > detailCandidatePageSize" class="d-flex flex-wrap justify-center align-center ga-2 mt-3">
                  <div class="text-caption text-medium-emphasis">第 {{ detailCandidatePage }} 页 / 共 {{ Math.ceil(detailCandidates.length / detailCandidatePageSize) }} 页</div>
                  <v-pagination v-model="detailCandidatePage" :length="Math.ceil(detailCandidates.length / detailCandidatePageSize)" density="comfortable" total-visible="7" />
                </div>
              </v-card-text>
            </v-card>
          </div>
        </div>
      </v-card>
    </v-dialog>



    <v-dialog v-model="showEditDialog" max-width="680" scrollable>
      <v-card>
        <v-card-title>编辑私有订阅</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12" md="8"><v-text-field v-model="editForm.title" label="标题" /></v-col>
            <v-col cols="12" md="4"><v-text-field v-model="editForm.year" label="年份" /></v-col>
            <v-col cols="12" md="4"><v-text-field v-model="editForm.season" label="季号" type="number" /></v-col>
            <v-col cols="12" md="4"><v-text-field v-model="editForm.total_episode" label="总集数" type="number" /></v-col>
            <v-col cols="12" md="4"><v-select v-model="editForm.mode" :items="[{title:'新番追更',value:'airing'},{title:'老番补全',value:'backfill'}]" label="模式" /></v-col>
            <v-col cols="12" md="6"><v-select v-model="editForm.state" :items="[{title:'运行中',value:'active'},{title:'已暂停',value:'paused'}]" label="状态" /></v-col>
            <v-col cols="12" md="6"><v-text-field v-model="editForm.preferred_group" label="发布组标记" /></v-col>
            <v-col cols="12"><v-textarea v-model="editForm.description" label="简介/备注" rows="3" /></v-col>
          </v-row>
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn variant="text" @click="showEditDialog=false">取消</v-btn><v-btn color="primary" @click="saveSubscriptionEdit">保存</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showFactsDialog" max-width="860" scrollable>
      <v-card>
        <v-card-title>下载/等待记录</v-card-title>
        <v-card-text v-if="selected">
          <v-tabs v-model="factsTab" density="compact"><v-tab value="downloaded">下载事实 {{ Object.keys(selected.episode_facts || selected.downloaded || {}).length }}</v-tab><v-tab value="pending">等待 {{ Object.keys(selected.pending || {}).length }}</v-tab><v-tab value="groups">发布组 {{ Object.keys(selected.seen_groups || {}).length }}</v-tab></v-tabs>
          <v-window v-model="factsTab" class="mt-3">
            <v-window-item value="downloaded"><v-list density="compact"><v-list-item v-if="selected.replacement_state" :title="`整季包替换 · ${selected.replacement_message || selected.replacement_state}`" :subtitle="`Hash: ${selected.replacement_hash ? String(selected.replacement_hash).slice(0,12) : '-'} · 发布组: ${selected.replacement_group || '-'} · 状态: ${selected.replacement_state}`" prepend-icon="mdi-package-variant-closed" /><v-list-item v-for="(item, ep) in (selected.episode_facts || selected.downloaded || {})" :key="ep" :title="`E${String(ep).padStart(2,'0')} · ${item.final_status_text || item.status_text || item.plugin_status_text || item.group || '-'}`" :subtitle="`Hash: ${item.download_hash ? String(item.download_hash).slice(0,12) : '-'} · 下载器: ${item.downloader_name || '-'} · ${item.downloader_progress ?? '-'}%`" /><v-list-item v-if="!Object.keys(selected.episode_facts || selected.downloaded || {}).length && !selected.replacement_state" title="暂无下载事实" /></v-list></v-window-item>
            <v-window-item value="pending"><v-list density="compact"><v-list-item v-for="(item, ep) in (selected.pending || {})" :key="ep" :title="`E${String(ep).padStart(2,'0')} · 等待候选`" :subtitle="`first_seen: ${item.first_seen || '-'} · candidates: ${(item.candidates || []).length}`" /><v-list-item v-if="!Object.keys(selected.pending || {}).length" title="暂无等待记录" /></v-list></v-window-item>
            <v-window-item value="groups"><v-list density="compact"><v-list-item v-for="(info, name) in (selected.seen_groups || {})" :key="name" :title="`${name} · ${info.count || 0}`" :subtitle="info.last_seen || '-'" /><v-list-item v-if="!Object.keys(selected.seen_groups || {}).length" title="暂无发布组统计" /></v-list></v-window-item>
          </v-window>
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn variant="text" @click="showFactsDialog=false">关闭</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showNoHashDialog" max-width="980" scrollable>
      <v-card>
        <v-card-title class="d-flex align-center justify-space-between">
          <span>历史缺 Hash 诊断</span>
          <v-chip color="orange" variant="tonal">{{ submittedNoHashItems.length }} 条</v-chip>
        </v-card-title>
        <v-card-subtitle>这些记录来自旧版本“已提交下载”事实，但没有 download_hash，因此无法自动追踪下载器/转移状态。本页只读，不会重新下载或修改记录。</v-card-subtitle>
        <v-card-text>
          <v-list density="compact" lines="three">
            <v-list-item v-for="item in submittedNoHashItems" :key="`${item.sub_id}-${item.episode}`">
              <template #prepend><v-chip color="orange" size="x-small" variant="tonal">缺Hash</v-chip></template>
              <v-list-item-title>{{ item.title }} S{{ String(item.season || 1).padStart(2,'0') }}E{{ String(item.episode).padStart(2,'0') }}</v-list-item-title>
              <v-list-item-subtitle>{{ item.record_title || '-' }}</v-list-item-subtitle>
              <v-list-item-subtitle>组：{{ item.group || '-' }}｜候选：{{ item.candidate_count || 0 }}｜{{ item.suggestion }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item v-if="!submittedNoHashItems.length" title="暂无历史缺Hash记录" />
          </v-list>
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn variant="text" @click="showNoHashDialog=false">关闭</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showIssuesDialog" max-width="980" scrollable>
      <v-card>
        <v-card-title class="d-flex align-center justify-space-between">
          <span>识别异常待处理</span>
          <v-chip color="error" variant="tonal">{{ openIssues.length }} 条</v-chip>
        </v-card-title>
        <v-card-text>
          <v-alert type="warning" variant="tonal" class="mb-3">这些资源来自已筛选的动漫/特摄来源，但 MP 识别失败或识别成真人/剧集分类。插件不会直接当真人下载；后续可手动处理或调用智能体生成窄作用域识别词后回流候选。</v-alert>
          <v-list density="compact" lines="three">
            <v-list-item v-for="item in openIssues" :key="item.key">
              <template #prepend><v-chip size="x-small" color="error" variant="tonal">{{ item.status || 'open' }}</v-chip></template>
              <v-list-item-title>{{ item.title }}</v-list-item-title>
              <v-list-item-subtitle>识别：{{ item.media_title || '-' }} / {{ item.media_type || '-' }} / {{ item.media_category || '-' }}｜{{ item.issue_reason || item.reason }}</v-list-item-subtitle>
              <div class="text-caption text-medium-emphasis mt-1">{{ item.suggestion }}</div>
              <template #append>
                <div class="d-flex flex-wrap ga-1 justify-end">
                  <v-btn size="small" variant="text" prepend-icon="mdi-refresh" @click="rescanIssue(item)">重扫</v-btn>
                  <v-btn size="small" variant="text" prepend-icon="mdi-robot" @click="autoWriteIssue(item)">智能体自动写入</v-btn>
                  <v-btn size="small" color="primary" variant="text" prepend-icon="mdi-identifier" @click="previewIssueIdentifier(item)">识别词</v-btn>
                  <v-btn size="small" color="info" variant="text" prepend-icon="mdi-recycle" @click="reflowIssue(item)">回流</v-btn>
                  <v-btn size="small" variant="text" prepend-icon="mdi-eye-off" @click="ignoreIssue(item)">忽略</v-btn>
                </div>
              </template>
            </v-list-item>
            <v-list-item v-if="!openIssues.length" title="暂无待处理异常" subtitle="刷新 RSS 后，如有识别失败或非动画识别，会显示在这里。" />
          </v-list>
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn variant="text" @click="showIssuesDialog=false">关闭</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showIssuePreviewDialog" max-width="760" scrollable>
      <v-card>
        <v-card-title>识别词预览</v-card-title>
        <v-card-text v-if="issuePreview">
          <v-alert type="warning" variant="tonal" class="mb-3">写入前会保存当前自定义识别词快照；规则已按当前异常标题锚定，避免影响无关资源。</v-alert>
          <v-textarea :model-value="issuePreview.identifier" label="将写入的识别词" readonly rows="3" />
          <div class="text-caption text-medium-emphasis mt-2">目标：{{ issuePreview.target?.title || '-' }} / TMDB {{ issuePreview.target?.tmdbid || '-' }} / S{{ issuePreview.target?.season || 1 }}</div>
          <v-chip v-if="issuePreview.exists" color="info" variant="tonal" class="mt-2">该识别词已存在</v-chip>
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn variant="text" @click="showIssuePreviewDialog=false">取消</v-btn><v-btn color="primary" variant="tonal" @click="applyIssueIdentifier">写入并回流候选</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showIssueAgentDialog" max-width="820" scrollable>
      <v-card>
        <v-card-title>调用智能体处理提示</v-card-title>
        <v-card-text v-if="issueAgentHint">
          <v-alert type="info" variant="tonal" class="mb-3">智能体高置信时可直接自动写入窄作用域识别词并回流候选；下面保留提示与写入结果供核对。</v-alert>
          <v-textarea :model-value="issueAgentHint.prompt" label="智能体提示" readonly rows="12" />
          <v-textarea v-if="issueAgentHint.suggested_identifier" :model-value="issueAgentHint.suggested_identifier" label="当前建议识别词" readonly rows="2" class="mt-3" />
          <v-alert v-if="issueAgentHint.applied" type="success" variant="tonal" class="mt-3">{{ issueAgentHint.applied.message || '已自动写入' }}</v-alert>
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn variant="text" @click="showIssueAgentDialog=false">关闭</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showConfigDialog" max-width="960" scrollable>
      <Config :initial-config="currentConfig" @save="saveConfigDialog" @close="showConfigDialog=false" />
    </v-dialog>

    <v-dialog v-model="showConfirmDialog" max-width="460" persistent>
      <v-card rounded="lg">
        <v-card-title class="d-flex align-center ga-2">
          <v-icon :color="confirmState.color" icon="mdi-alert-circle-outline" />
          <span>{{ confirmState.title }}</span>
        </v-card-title>
        <v-card-text style="white-space: pre-line">{{ confirmState.message }}</v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeConfirm(false)">{{ confirmState.cancelText }}</v-btn>
          <v-btn :color="confirmState.color" variant="tonal" @click="closeConfirm(true)">{{ confirmState.confirmText }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showGroupDialog" max-width="420">
      <v-card>
        <v-card-title>设置发布组标记</v-card-title>
        <v-card-text><v-text-field v-model="groupInput" label="发布组，如 ANi / 喵萌奶茶屋" /></v-card-text>
        <v-card-actions><v-spacer /><v-btn variant="text" @click="showGroupDialog=false">取消</v-btn><v-btn color="primary" @click="saveGroup">保存</v-btn></v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped>
.bt-root { min-height: 60vh; }
.bt-hero { display:flex; justify-content:space-between; gap:16px; align-items:center; padding:16px; border-radius:16px; background:rgba(var(--v-theme-surface), .55); border:1px solid rgba(var(--v-border-color), .22); }
.sub-card { min-height: 184px; color: rgba(255,255,255,.96); background-size: cover; background-position: center; overflow: hidden; cursor: pointer; transition: transform .16s ease, box-shadow .16s ease; }
.sub-card:hover { transform: translateY(-3px); box-shadow: 0 14px 34px rgba(0,0,0,.32) !important; }
.poster { background: rgba(255,255,255,.08); }
.poster-wrap { width:58px;height:82px;flex:0 0 auto; }
.poster-fallback { width:58px;height:82px;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.12);font-size:12px;color:rgba(255,255,255,.8); }
.title-line { line-height: 1.25; min-height: 40px; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.min-w-0 { min-width:0; }
.sub-title { color: rgba(255,255,255,.98); text-shadow: 0 2px 10px rgba(0,0,0,.55); }
.sub-line { color: rgba(255,255,255,.92); text-shadow: 0 1px 8px rgba(0,0,0,.48); }
.sub-muted { color: rgba(255,255,255,.78) !important; text-shadow: 0 1px 8px rgba(0,0,0,.45); }
.search-panel { border: 1px solid rgba(var(--v-border-color), .16); }

.detail-toolbar { position: sticky; top: 0; z-index: 5; border-bottom: 1px solid rgba(var(--v-border-color), .18); }
.detail-dialog-full { height: 86vh; max-height: 86vh; border-radius: 18px !important; display: flex; flex-direction: column; background: rgb(var(--v-theme-background)); }
.detail-scroll { flex: 1; overflow-y: auto; }
.detail-hero { min-height: 230px; background-size: cover; background-position: center; display: flex; align-items: flex-end; }
.detail-hero-content { width: min(1180px, 100%); margin: 0 auto; padding: 28px; display: flex; gap: 22px; align-items: flex-end; }
.detail-poster { border-radius: 14px; box-shadow: 0 18px 45px rgba(0,0,0,.38); flex: 0 0 auto; background: rgba(255,255,255,.08); }
.detail-poster-fallback { width:128px;height:186px;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.12);color:rgba(255,255,255,.88); }
.detail-title-block { min-width: 0; color: white; text-shadow: 0 2px 12px rgba(0,0,0,.45); }
.detail-meta { color: rgba(255,255,255,.76); }
.detail-overview { max-width: 760px; color: rgba(255,255,255,.82); display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; }
.detail-content { width: min(1180px, 100%); margin: 0 auto; padding: 18px 28px 32px; }
.episode-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.episode-chip { min-width: 54px; justify-content: center; }
.candidate-list { background: transparent; }
.candidate-row { border-radius: 10px; }
@media (max-width: 720px) {
  .bt-hero { flex-direction: column; align-items: stretch; }
  .bt-hero > .d-flex { justify-content: flex-start; flex-wrap: wrap; }
  .detail-hero-content { padding: 18px; gap: 14px; align-items: center; }
  .detail-poster, .detail-poster-fallback { width: 86px !important; height: 126px !important; }
  .detail-content { padding: 14px 14px 24px; }
}

</style>
