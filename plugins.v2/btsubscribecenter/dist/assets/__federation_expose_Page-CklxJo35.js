import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc, g as getPluginApi, p as postPluginApi } from './_plugin-vue_export-helper-BZnQ7HOe.js';
import _sfc_main$1 from './__federation_expose_Config-fPojw3gj.js';

const {toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementVNode:_createElementVNode,createVNode:_createVNode,withKeys:_withKeys,createElementBlock:_createElementBlock,renderList:_renderList,Fragment:_Fragment,withModifiers:_withModifiers,mergeProps:_mergeProps,normalizeStyle:_normalizeStyle} = await importShared('vue');


const _hoisted_1 = { class: "bt-root" };
const _hoisted_2 = { class: "bt-hero mb-4" };
const _hoisted_3 = { class: "d-flex ga-2 align-center" };
const _hoisted_4 = { class: "d-flex flex-wrap align-center justify-space-between ga-2" };
const _hoisted_5 = { class: "d-flex flex-wrap ga-2 align-center mb-3" };
const _hoisted_6 = {
  key: 0,
  class: "d-flex flex-wrap ga-2 mt-3 align-center"
};
const _hoisted_7 = { class: "d-flex flex-wrap ga-2 mb-3" };
const _hoisted_8 = {
  key: 0,
  class: "d-flex flex-wrap justify-center align-center ga-2 mt-3"
};
const _hoisted_9 = { class: "text-caption text-medium-emphasis" };
const _hoisted_10 = {
  key: 0,
  class: "d-flex flex-wrap justify-center align-center ga-2 mt-3"
};
const _hoisted_11 = { class: "text-caption text-medium-emphasis" };
const _hoisted_12 = { class: "d-flex align-start" };
const _hoisted_13 = { class: "poster-wrap me-3" };
const _hoisted_14 = {
  key: 1,
  class: "poster-fallback rounded"
};
const _hoisted_15 = { class: "flex-grow-1 min-w-0" };
const _hoisted_16 = { class: "text-caption sub-muted" };
const _hoisted_17 = { class: "text-subtitle-1 font-weight-bold title-line sub-title" };
const _hoisted_18 = { class: "text-caption mt-2 sub-line" };
const _hoisted_19 = { class: "text-caption sub-muted mt-1" };
const _hoisted_20 = { class: "d-flex justify-space-between text-caption mt-2 sub-muted" };
const _hoisted_21 = {
  key: 6,
  class: "d-flex flex-wrap justify-center align-center ga-2 my-4"
};
const _hoisted_22 = { class: "text-caption text-medium-emphasis" };
const _hoisted_23 = { class: "detail-scroll" };
const _hoisted_24 = { class: "detail-hero-content" };
const _hoisted_25 = {
  key: 1,
  class: "detail-poster detail-poster-fallback"
};
const _hoisted_26 = { class: "detail-title-block" };
const _hoisted_27 = { class: "d-flex flex-wrap ga-2 mb-2" };
const _hoisted_28 = { class: "text-h5 text-md-h4 font-weight-bold mb-2" };
const _hoisted_29 = { class: "text-body-2 detail-meta mb-3" };
const _hoisted_30 = { class: "detail-overview text-body-2" };
const _hoisted_31 = { class: "detail-content" };
const _hoisted_32 = { class: "text-h5 font-weight-bold" };
const _hoisted_33 = { class: "text-h5 font-weight-bold" };
const _hoisted_34 = { class: "text-h5 font-weight-bold" };
const _hoisted_35 = { class: "text-h5 font-weight-bold" };
const _hoisted_36 = { class: "d-flex justify-space-between text-caption mb-2" };
const _hoisted_37 = { class: "episode-grid" };
const _hoisted_38 = { class: "d-flex flex-wrap ga-2 mt-3 text-caption text-medium-emphasis" };
const _hoisted_39 = {
  key: 0,
  class: "d-flex flex-wrap justify-center align-center ga-2 mt-3"
};
const _hoisted_40 = { class: "text-caption text-medium-emphasis" };
const _hoisted_41 = { class: "text-caption text-medium-emphasis mt-1" };
const _hoisted_42 = { class: "d-flex flex-wrap ga-1 justify-end" };
const _hoisted_43 = { class: "text-caption text-medium-emphasis mt-2" };

const {computed,onMounted,ref,watch} = await importShared('vue');


const _sfc_main = {
  __name: 'Page',
  props: { api: { type: [Object, Function], default: null } },
  emits: ['close', 'switch'],
  setup(__props, { emit: __emit }) {

const props = __props;

const loading = ref(false);
const error = ref('');
const stats = ref({ subscriptions: 0, candidates: 0, pending: 0, downloaded: 0 });
const downloadFactSummary = ref({});
const cleanupSummary = ref({});
const replacementSummary = ref({});
const submittedNoHashItems = ref([]);
const showNoHashDialog = ref(false);
const subscriptions = ref({});
const candidates = ref([]);
const selected = ref(null);
const detailCandidates = ref([]);
const filter = ref('all');
const keyword = ref('');
const page = ref(1);
const pageSize = ref(24);
const actionMessage = ref('');
const actionOk = ref(true);
const showGroupDialog = ref(false);
const groupInput = ref('');
const searchMode = ref('subscriptions');
const rssResults = ref([]);
const showConfigDialog = ref(false);
const currentConfig = ref({});
const showEditDialog = ref(false);
const editForm = ref({});
const showFactsDialog = ref(false);
const factsTab = ref('downloaded');
const recognitionIssues = ref([]);
const showIssuesDialog = ref(false);
const issuePreview = ref(null);
const issueAgentHint = ref(null);
const showIssuePreviewDialog = ref(false);
const showIssueAgentDialog = ref(false);
const showConfirmDialog = ref(false);
const confirmState = ref({ title: '', message: '', color: 'primary', confirmText: '确认', cancelText: '取消', resolve: null });
const candidatePage = ref(1);
const candidatePageSize = ref(20);
const candidateStatus = ref('all');
const detailCandidatePage = ref(1);
const detailCandidatePageSize = ref(12);
const rssPage = ref(1);
const rssPageSize = ref(20);

const subList = computed(() => Object.values(subscriptions.value || {}));
const filteredSubs = computed(() => {
  const kw = keyword.value.trim().toLowerCase();
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
});
const pagedSubs = computed(() => filteredSubs.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value));
const openIssues = computed(() => (recognitionIssues.value || []).filter(item => item.status !== 'ignored'));
const candidateStatusOptions = computed(() => {
  const counts = {};
  for (const item of candidates.value || []) counts[item.status || 'unknown'] = (counts[item.status || 'unknown'] || 0) + 1;
  const labels = { ready: '可下载', pending: '等待中', orphan: '未绑定', skipped: '已跳过', recognition_issue: '识别异常', recognition_conflict: '识别冲突', downloaded: '已下载', submitted: '已提交', download_failed: '下载失败', transferred: '已转移', transfer_recorded: '有转移记录', ignored: '已忽略', unrecognized: '未识别' };
  return Object.entries(counts).sort((a, b) => b[1] - a[1]).map(([value, count]) => ({ value, count, label: labels[value] || value }))
});
const filteredCandidates = computed(() => {
  const kw = keyword.value.trim().toLowerCase();
  const source = candidates.value || [];
  return source.filter(item => {
    if (candidateStatus.value !== 'all' && (item.status || 'unknown') !== candidateStatus.value) return false
    if (kw && !`${item.title || ''} ${item.media_title || ''} ${item.group || ''} ${item.reason || ''}`.toLowerCase().includes(kw)) return false
    return true
  })
});
const pagedCandidates = computed(() => filteredCandidates.value.slice((candidatePage.value - 1) * candidatePageSize.value, candidatePage.value * candidatePageSize.value));
const pagedDetailCandidates = computed(() => (detailCandidates.value || []).slice((detailCandidatePage.value - 1) * detailCandidatePageSize.value, detailCandidatePage.value * detailCandidatePageSize.value));
const pagedRssResults = computed(() => (rssResults.value || []).slice((rssPage.value - 1) * rssPageSize.value, rssPage.value * rssPageSize.value));
watch([keyword, searchMode], () => {
  candidatePage.value = 1;
  rssPage.value = 1;
  page.value = 1;
});
watch(candidateStatus, () => { candidatePage.value = 1; });
watch(detailCandidates, () => { detailCandidatePage.value = 1; });

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
  const total = totalEpisode(sub);
  const maxEp = Math.max(total, ...Object.keys(sub?.downloaded || {}).map(v => Number(v) || 0), ...(sub?.library_episodes || []).map(v => Number(v) || 0), ...(sub?.candidate_episodes || []).map(v => Number(v) || 0), 0);
  const limit = maxEp || 12;
  return Array.from({ length: limit }, (_, i) => i + 1)
}
function episodeState(sub, ep) {
  const epNum = Number(ep);
  const downloaded = sub?.downloaded || {};
  const facts = sub?.episode_facts || {};
  const fact = facts[String(epNum)] || null;
  const record = downloaded[String(epNum)] || null;
  const library = new Set((sub?.library_episodes || []).map(v => Number(v)));
  const candidates = new Set((sub?.candidate_episodes || []).map(v => Number(v)));
  const missing = new Set((sub?.missing_episodes || []).map(v => Number(v)));
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
  actionMessage.value = message;
  actionOk.value = ok;
  setTimeout(() => { actionMessage.value = ''; }, 3500);
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
    };
    showConfirmDialog.value = true;
  })
}
function closeConfirm(result) {
  const resolver = confirmState.value.resolve;
  showConfirmDialog.value = false;
  confirmState.value = { title: '', message: '', color: 'primary', confirmText: '确认', cancelText: '取消', resolve: null };
  if (resolver) resolver(Boolean(result));
}
function normalize(value) {
  if (value?.success === false) throw new Error(value.message || '操作失败')
  return value?.data ?? value
}
async function loadAll() {
  loading.value = true;
  error.value = '';
  try {
    const overview = normalize(await getPluginApi(props.api, 'overview'));
    stats.value = overview?.stats || stats.value;
    currentConfig.value = overview?.config || currentConfig.value;
    downloadFactSummary.value = overview?.download_fact_summary || {};
    cleanupSummary.value = overview?.cleanup_summary || {};
    replacementSummary.value = overview?.replacement_summary || {};
    subscriptions.value = overview?.subscriptions || {};
    candidates.value = overview?.candidates || [];
    recognitionIssues.value = overview?.recognition_issues || [];
  } catch (err) {
    error.value = err.message || String(err);
  } finally {
    loading.value = false;
  }
}
async function openSub(sub) {
  selected.value = sub;
  detailCandidates.value = candidates.value.filter(item => item.subscription_id === sub.id);
  detailCandidatePage.value = 1;
  try {
    const detail = normalize(await getPluginApi(props.api, `subscription?sub_id=${encodeURIComponent(sub.id)}`));
    selected.value = detail.subscription || sub;
    detailCandidates.value = detail.candidates || detailCandidates.value;
  } catch (err) {
    showAction(err.message || '加载订阅详情失败', false);
  }
}
async function refreshRss() {
  loading.value = true;
  try {
    await postPluginApi(props.api, 'refresh', {});
    showAction('RSS 刷新完成');
    await loadAll();
  } catch (err) {
    showAction(err.message || '刷新失败', false);
  } finally {
    loading.value = false;
  }
}
async function setState(sub, state) {
  try {
    const path = state === 'active' ? 'resume_subscription' : 'pause_subscription';
    await postPluginApi(props.api, path, { sub_id: sub.id });
    showAction(state === 'active' ? '已恢复订阅' : '已暂停订阅');
    await loadAll();
    if (selected.value?.id === sub.id) selected.value = subscriptions.value[sub.id];
  } catch (err) {
    showAction(err.message || '状态更新失败', false);
  }
}
function openGroup(sub) {
  selected.value = sub;
  groupInput.value = sub.preferred_group || '';
  showGroupDialog.value = true;
}
async function saveGroup() {
  try {
    await postPluginApi(props.api, 'set_group', { sub_id: selected.value.id, group: groupInput.value });
    showGroupDialog.value = false;
    showAction('发布组标记已更新');
    await loadAll();
    selected.value = subscriptions.value[selected.value.id];
  } catch (err) {
    showAction(err.message || '发布组标记更新失败', false);
  }
}
async function ignoreCandidate(item) {
  try {
    await postPluginApi(props.api, 'ignore_candidate', { key: item.key });
    showAction('已忽略候选');
    await loadAll();
    if (selected.value) await openSub(selected.value);
  } catch (err) {
    showAction(err.message || '忽略失败', false);
  }
}
async function downloadCandidate(item) {
  if (!(await askConfirm({ title: '下载候选资源', message: item.title, color: 'primary', confirmText: '下载' }))) return
  try {
    const res = normalize(await postPluginApi(props.api, 'download_candidate', { key: item.key, confirm: true }));
    showAction(res?.download_hash ? `已提交下载：${String(res.download_hash).slice(0, 8)}` : '已提交下载');
    await loadAll();
    if (selected.value) await openSub(selected.value);
  } catch (err) {
    showAction(err.message || '下载失败', false);
  }
}


async function searchRssNow() {
  const kw = keyword.value.trim();
  if (!kw) { showAction('请输入搜索关键字', false); return }
  loading.value = true;
  try {
    const res = normalize(await postPluginApi(props.api, 'rss_search', { keyword: kw, limit: 120 }));
    rssResults.value = res || [];
    rssPage.value = 1;
    searchMode.value = 'rss';
    showAction(`已搜索 RSS/BT 源，命中 ${rssResults.value.length} 条`);
  } catch (err) {
    showAction(err.message || 'RSS 搜索失败', false);
  } finally {
    loading.value = false;
  }
}
async function saveConfigDialog(config) {
  try {
    await postPluginApi(props.api, 'save_config', config);
    showConfigDialog.value = false;
    showAction('设置已保存');
    await loadAll();
  } catch (err) {
    showAction(err.message || '设置保存失败', false);
  }
}
function closePage() {
  if (window.history.length > 1) window.history.back();
  else showAction('当前是侧栏页面，已留在 BT订阅中心');
}
async function refreshSubStatus(sub) {
  try {
    const res = normalize(await postPluginApi(props.api, 'refresh_subscription_status', { sub_id: sub.id }));
    subscriptions.value[sub.id] = res;
    if (selected.value?.id === sub.id) selected.value = res;
    showAction('入库状态已刷新');
  } catch (err) {
    showAction(err.message || '刷新入库状态失败', false);
  }
}
async function deleteSubscription(sub) {
  if (!(await askConfirm({ title: '删除私有订阅', message: sub.title, color: 'error', confirmText: '删除' }))) return
  try {
    await postPluginApi(props.api, 'delete_subscription', { sub_id: sub.id, confirm: true });
    showAction('私有订阅已删除');
    if (selected.value?.id === sub.id) selected.value = null;
    await loadAll();
  } catch (err) { showAction(err.message || '删除失败', false); }
}
async function createBackfillFromSub(sub) {
  try {
    await postPluginApi(props.api, 'add_subscription', { title: sub.title, tmdbid: sub.tmdbid, season: sub.season || 1, mode: 'backfill', group: sub.preferred_group || '' });
    showAction('已按老番补全模式保存');
    await loadAll();
  } catch (err) { showAction(err.message || '操作失败', false); }
}


function openEdit(sub) {
  selected.value = sub;
  editForm.value = { ...sub };
  showEditDialog.value = true;
}
async function saveSubscriptionEdit() {
  try {
    const payload = { ...editForm.value, sub_id: selected.value.id };
    const res = normalize(await postPluginApi(props.api, 'update_subscription', payload));
    subscriptions.value[selected.value.id] = res;
    selected.value = res;
    showEditDialog.value = false;
    showAction('订阅已更新');
  } catch (err) { showAction(err.message || '编辑订阅失败', false); }
}
async function refreshSubMeta(sub) {
  try {
    const res = normalize(await postPluginApi(props.api, 'refresh_subscription_meta', { sub_id: sub.id }));
    subscriptions.value[sub.id] = res;
    if (selected.value?.id === sub.id) selected.value = res;
    showAction('媒体信息已刷新');
  } catch (err) { showAction(err.message || '刷新媒体信息失败', false); }
}
async function searchSubCandidates(sub) {
  try {
    const res = normalize(await postPluginApi(props.api, 'search_subscription_candidates', { sub_id: sub.id, include_rss: true }));
    detailCandidates.value = [...(res.candidates || []), ...(res.rss_results || [])];
    selected.value = res.subscription || sub;
    searchMode.value = 'candidates';
    keyword.value = sub.title || '';
    rssResults.value = res.rss_results || [];
    showAction(`已搜索候选：本地 ${res.candidates?.length || 0}，BT源 ${res.rss_results?.length || 0}`);
  } catch (err) { showAction(err.message || '搜索候选失败', false); }
}
async function clearPending(sub) {
  if (!(await askConfirm({ title: '清空等待队列', message: sub.title, color: 'warning', confirmText: '清空' }))) return
  try {
    const res = normalize(await postPluginApi(props.api, 'clear_pending', { sub_id: sub.id, confirm: true }));
    subscriptions.value[sub.id] = res;
    if (selected.value?.id === sub.id) selected.value = res;
    showAction('等待队列已清空');
  } catch (err) { showAction(err.message || '清空等待失败', false); }
}
async function resetDownloaded(sub) {
  if (!(await askConfirm({ title: '重置下载记录', message: `${sub.title}\n这不会删除文件，只会清空插件私有下载事实。`, color: 'warning', confirmText: '重置' }))) return
  try {
    const res = normalize(await postPluginApi(props.api, 'reset_downloaded', { sub_id: sub.id, confirm: true }));
    subscriptions.value[sub.id] = res;
    if (selected.value?.id === sub.id) selected.value = res;
    showAction('下载记录已重置');
  } catch (err) { showAction(err.message || '重置下载记录失败', false); }
}
function openFacts(sub) {
  selected.value = sub;
  showFactsDialog.value = true;
}

async function rescanIssue(item) {
  try {
    const res = normalize(await postPluginApi(props.api, 'rescan_issue', { key: item.key }));
    showAction(res.status === 'resolved' ? '异常已重新识别为动画' : '已重扫并更新建议', res.status === 'resolved');
    await loadAll();
  } catch (err) { showAction(err.message || '重扫异常失败', false); }
}
async function ignoreIssue(item) {
  try {
    await postPluginApi(props.api, 'ignore_issue', { key: item.key });
    showAction('已忽略识别异常');
    await loadAll();
  } catch (err) { showAction(err.message || '忽略异常失败', false); }
}

async function previewIssueIdentifier(item) {
  try {
    const res = normalize(await postPluginApi(props.api, 'issue_identifier_preview', { key: item.key }));
    issuePreview.value = res;
    showIssuePreviewDialog.value = true;
  } catch (err) { showAction(err.message || '生成识别词预览失败', false); }
}
async function applyIssueIdentifier() {
  if (!issuePreview.value?.key || !issuePreview.value?.identifier) return
  if (!(await askConfirm({ title: '写入自定义识别词', message: `${issuePreview.value.identifier}

会先保存当前识别词快照，然后写入该窄作用域规则并回流候选。`, color: 'warning', confirmText: '写入' }))) return
  try {
    const res = normalize(await postPluginApi(props.api, 'apply_issue_identifier', { key: issuePreview.value.key, identifier: issuePreview.value.identifier, confirm: true }));
    showIssuePreviewDialog.value = false;
    showAction(`识别词已写入：${res.write?.added ? '新增成功' : (res.write?.message || '已存在')}`);
    await loadAll();
  } catch (err) { showAction(err.message || '写入识别词失败', false); }
}
async function autoWriteIssue(item) {
  try {
    const hint = normalize(await postPluginApi(props.api, 'issue_agent_hint', { key: item.key }));
    const payload = { key: item.key, identifier: hint.suggested_identifier || '', confirm: true };
    const res = normalize(await postPluginApi(props.api, 'issue_agent_apply', payload));
    issueAgentHint.value = { ...hint, applied: res };
    showIssueAgentDialog.value = true;
    showAction('智能体已自动写入识别词并回流候选');
    await loadAll();
  } catch (err) { showAction(err.message || '智能体自动写入失败', false); }
}

async function reflowIssue(item) {
  if (!(await askConfirm({ title: '回流候选', message: `${item.title}

仅把该异常重新放回候选池，不写识别词、不立即下载。`, color: 'primary', confirmText: '回流' }))) return
  try {
    await postPluginApi(props.api, 'reflow_issue', { key: item.key, confirm: true });
    showAction('异常已回流候选');
    await loadAll();
  } catch (err) { showAction(err.message || '回流候选失败', false); }
}
async function openNoHashDiagnostics() {
  try {
    const res = normalize(await getPluginApi(props.api, 'submitted_no_hash?limit=300'));
    submittedNoHashItems.value = res || [];
    showNoHashDialog.value = true;
  } catch (err) { showAction(err.message || '加载缺Hash诊断失败', false); }
}

onMounted(loadAll);

return (_ctx, _cache) => {
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_tab = _resolveComponent("v-tab");
  const _component_v_tabs = _resolveComponent("v-tabs");
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_chip_group = _resolveComponent("v-chip-group");
  const _component_v_card_subtitle = _resolveComponent("v-card-subtitle");
  const _component_v_list_item_title = _resolveComponent("v-list-item-title");
  const _component_v_list_item_subtitle = _resolveComponent("v-list-item-subtitle");
  const _component_v_list_item = _resolveComponent("v-list-item");
  const _component_v_list = _resolveComponent("v-list");
  const _component_v_pagination = _resolveComponent("v-pagination");
  const _component_v_img = _resolveComponent("v-img");
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_divider = _resolveComponent("v-divider");
  const _component_v_menu = _resolveComponent("v-menu");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_progress_linear = _resolveComponent("v-progress-linear");
  const _component_v_toolbar_title = _resolveComponent("v-toolbar-title");
  const _component_v_toolbar = _resolveComponent("v-toolbar");
  const _component_v_tooltip = _resolveComponent("v-tooltip");
  const _component_v_dialog = _resolveComponent("v-dialog");
  const _component_v_select = _resolveComponent("v-select");
  const _component_v_textarea = _resolveComponent("v-textarea");
  const _component_v_card_actions = _resolveComponent("v-card-actions");
  const _component_v_window_item = _resolveComponent("v-window-item");
  const _component_v_window = _resolveComponent("v-window");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    (actionMessage.value)
      ? (_openBlock(), _createBlock(_component_v_alert, {
          key: 0,
          type: actionOk.value ? 'success' : 'error',
          variant: "tonal",
          class: "mb-3"
        }, {
          default: _withCtx(() => [
            _createTextVNode(_toDisplayString(actionMessage.value), 1)
          ]),
          _: 1
        }, 8, ["type"]))
      : _createCommentVNode("", true),
    (error.value)
      ? (_openBlock(), _createBlock(_component_v_alert, {
          key: 1,
          type: "error",
          variant: "tonal",
          class: "mb-3"
        }, {
          default: _withCtx(() => [
            _createTextVNode(_toDisplayString(error.value), 1)
          ]),
          _: 1
        }))
      : _createCommentVNode("", true),
    _createElementVNode("div", _hoisted_2, [
      _cache[50] || (_cache[50] = _createElementVNode("div", null, [
        _createElementVNode("div", { class: "text-h5 font-weight-bold" }, "BT订阅中心"),
        _createElementVNode("div", { class: "text-body-2 text-medium-emphasis" }, "像使用 MoviePilot 订阅一样管理 BT/RSS 动漫源：订阅、候选、缺集、下载事实、整季包替换都在一个页面闭环。")
      ], -1)),
      _createElementVNode("div", _hoisted_3, [
        _createVNode(_component_v_btn, {
          color: "primary",
          variant: "tonal",
          "prepend-icon": "mdi-refresh",
          loading: loading.value,
          onClick: refreshRss
        }, {
          default: _withCtx(() => [...(_cache[49] || (_cache[49] = [
            _createTextVNode("刷新 RSS", -1)
          ]))]),
          _: 1
        }, 8, ["loading"]),
        _createVNode(_component_v_btn, {
          color: "error",
          variant: "tonal",
          "prepend-icon": "mdi-alert-decagram",
          onClick: _cache[0] || (_cache[0] = $event => (showIssuesDialog.value = true))
        }, {
          default: _withCtx(() => [
            _createTextVNode("识别异常 " + _toDisplayString(openIssues.value.length), 1)
          ]),
          _: 1
        }),
        _createVNode(_component_v_btn, {
          variant: "text",
          icon: "mdi-cog",
          "aria-label": "打开设置",
          title: "打开设置",
          onClick: _cache[1] || (_cache[1] = $event => (showConfigDialog.value = true))
        }),
        _createVNode(_component_v_btn, {
          variant: "text",
          icon: "mdi-close",
          "aria-label": "关闭页面",
          title: "关闭页面",
          onClick: closePage
        })
      ])
    ]),
    _createVNode(_component_v_row, { class: "mb-2" }, {
      default: _withCtx(() => [
        _createVNode(_component_v_col, {
          cols: "6",
          md: "3"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              variant: "tonal",
              color: "primary"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_text, null, {
                  default: _withCtx(() => [...(_cache[51] || (_cache[51] = [
                    _createTextVNode("私有订阅", -1)
                  ]))]),
                  _: 1
                }),
                _createVNode(_component_v_card_title, null, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(stats.value.subscriptions), 1)
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
          cols: "6",
          md: "3"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              variant: "tonal",
              color: "info"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_text, null, {
                  default: _withCtx(() => [...(_cache[52] || (_cache[52] = [
                    _createTextVNode("候选资源", -1)
                  ]))]),
                  _: 1
                }),
                _createVNode(_component_v_card_title, null, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(stats.value.candidates), 1)
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
          cols: "6",
          md: "3"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              variant: "tonal",
              color: "warning"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_text, null, {
                  default: _withCtx(() => [...(_cache[53] || (_cache[53] = [
                    _createTextVNode("待处理候选", -1)
                  ]))]),
                  _: 1
                }),
                _createVNode(_component_v_card_title, null, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(stats.value.pending), 1)
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
          cols: "6",
          md: "3"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              variant: "tonal",
              color: "success"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_text, null, {
                  default: _withCtx(() => [...(_cache[54] || (_cache[54] = [
                    _createTextVNode("已提交/记录", -1)
                  ]))]),
                  _: 1
                }),
                _createVNode(_component_v_card_title, null, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(stats.value.downloaded), 1)
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
          cols: "6",
          md: "3"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              variant: "tonal",
              color: "error"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_text, null, {
                  default: _withCtx(() => [...(_cache[55] || (_cache[55] = [
                    _createTextVNode("识别异常", -1)
                  ]))]),
                  _: 1
                }),
                _createVNode(_component_v_card_title, null, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(openIssues.value.length), 1)
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
    (downloadFactSummary.value.total_records)
      ? (_openBlock(), _createBlock(_component_v_alert, {
          key: 2,
          type: "info",
          variant: "tonal",
          class: "mb-4"
        }, {
          default: _withCtx(() => [
            _createElementVNode("div", _hoisted_4, [
              _createElementVNode("span", null, "下载事实：总记录 " + _toDisplayString(downloadFactSummary.value.total_records || 0) + "，可追踪Hash " + _toDisplayString(downloadFactSummary.value.hash_tracked || 0) + "，历史缺Hash " + _toDisplayString(downloadFactSummary.value.submitted_no_hash || 0) + "，下载中 " + _toDisplayString(downloadFactSummary.value.downloading || 0) + "，已入库 " + _toDisplayString(downloadFactSummary.value.library_exists || 0) + "；入库后清理 qB：成功 " + _toDisplayString(cleanupSummary.value.removed || 0) + "，失败 " + _toDisplayString(cleanupSummary.value.failed || 0) + "；整季包替换：监控 " + _toDisplayString(replacementSummary.value.watching || 0) + "，已提交 " + _toDisplayString(replacementSummary.value.submitted || 0) + "，已验证 " + _toDisplayString(replacementSummary.value.verified || 0) + "，失败 " + _toDisplayString(replacementSummary.value.failed || 0) + "。", 1),
              (downloadFactSummary.value.submitted_no_hash)
                ? (_openBlock(), _createBlock(_component_v_btn, {
                    key: 0,
                    size: "small",
                    color: "orange",
                    variant: "tonal",
                    "prepend-icon": "mdi-alert-circle-outline",
                    onClick: openNoHashDiagnostics
                  }, {
                    default: _withCtx(() => [...(_cache[56] || (_cache[56] = [
                      _createTextVNode("查看缺Hash", -1)
                    ]))]),
                    _: 1
                  }))
                : _createCommentVNode("", true)
            ])
          ]),
          _: 1
        }))
      : _createCommentVNode("", true),
    _createVNode(_component_v_card, {
      class: "search-panel mb-4",
      variant: "tonal",
      rounded: "lg"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card_text, null, {
          default: _withCtx(() => [
            _createElementVNode("div", _hoisted_5, [
              _createVNode(_component_v_text_field, {
                modelValue: keyword.value,
                "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((keyword).value = $event)),
                density: "compact",
                variant: "outlined",
                "hide-details": "",
                "prepend-inner-icon": "mdi-magnify",
                label: "搜索订阅 / RSS候选 / 已配置BT源",
                style: {"max-width":"420px"},
                onKeyup: _cache[3] || (_cache[3] = _withKeys($event => (searchMode.value === 'rss' ? searchRssNow() : null), ["enter"]))
              }, null, 8, ["modelValue"]),
              _createVNode(_component_v_btn, {
                color: "primary",
                variant: "tonal",
                "prepend-icon": "mdi-rss",
                loading: loading.value,
                onClick: searchRssNow
              }, {
                default: _withCtx(() => [...(_cache[57] || (_cache[57] = [
                  _createTextVNode("搜已配置BT源", -1)
                ]))]),
                _: 1
              }, 8, ["loading"])
            ]),
            _createVNode(_component_v_tabs, {
              modelValue: searchMode.value,
              "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((searchMode).value = $event)),
              density: "compact"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_tab, { value: "subscriptions" }, {
                  default: _withCtx(() => [
                    _createTextVNode("订阅 " + _toDisplayString(filteredSubs.value.length), 1)
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_tab, { value: "candidates" }, {
                  default: _withCtx(() => [
                    _createTextVNode("RSS候选 " + _toDisplayString(filteredCandidates.value.length), 1)
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_tab, { value: "rss" }, {
                  default: _withCtx(() => [
                    _createTextVNode("实时BT源 " + _toDisplayString(rssResults.value.length), 1)
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }, 8, ["modelValue"]),
            (searchMode.value === 'subscriptions')
              ? (_openBlock(), _createElementBlock("div", _hoisted_6, [
                  _createVNode(_component_v_chip_group, {
                    modelValue: filter.value,
                    "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((filter).value = $event)),
                    mandatory: "",
                    "selected-class": "text-primary"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_chip, { value: "all" }, {
                        default: _withCtx(() => [...(_cache[58] || (_cache[58] = [
                          _createTextVNode("全部", -1)
                        ]))]),
                        _: 1
                      }),
                      _createVNode(_component_v_chip, { value: "active" }, {
                        default: _withCtx(() => [...(_cache[59] || (_cache[59] = [
                          _createTextVNode("运行中", -1)
                        ]))]),
                        _: 1
                      }),
                      _createVNode(_component_v_chip, { value: "paused" }, {
                        default: _withCtx(() => [...(_cache[60] || (_cache[60] = [
                          _createTextVNode("已暂停", -1)
                        ]))]),
                        _: 1
                      }),
                      _createVNode(_component_v_chip, { value: "pending" }, {
                        default: _withCtx(() => [...(_cache[61] || (_cache[61] = [
                          _createTextVNode("有等待", -1)
                        ]))]),
                        _: 1
                      }),
                      _createVNode(_component_v_chip, { value: "airing" }, {
                        default: _withCtx(() => [...(_cache[62] || (_cache[62] = [
                          _createTextVNode("新番", -1)
                        ]))]),
                        _: 1
                      }),
                      _createVNode(_component_v_chip, { value: "backfill" }, {
                        default: _withCtx(() => [...(_cache[63] || (_cache[63] = [
                          _createTextVNode("老番", -1)
                        ]))]),
                        _: 1
                      })
                    ]),
                    _: 1
                  }, 8, ["modelValue"])
                ]))
              : _createCommentVNode("", true)
          ]),
          _: 1
        })
      ]),
      _: 1
    }),
    (searchMode.value === 'candidates')
      ? (_openBlock(), _createBlock(_component_v_card, {
          key: 3,
          class: "mb-4",
          variant: "tonal",
          rounded: "lg"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "d-flex flex-wrap align-center justify-space-between ga-2" }, {
              default: _withCtx(() => [
                _cache[64] || (_cache[64] = _createElementVNode("span", null, "BT/RSS 候选池", -1)),
                _createVNode(_component_v_chip, {
                  size: "small",
                  variant: "tonal"
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(filteredCandidates.value.length) + " / " + _toDisplayString(candidates.value.length), 1)
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_subtitle, null, {
              default: _withCtx(() => [...(_cache[65] || (_cache[65] = [
                _createTextVNode("候选按识别、订阅绑定、下载事实和入库状态分层展示；发布组只用于统计与后续整季包替换，不再阻塞追更。", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                _createElementVNode("div", _hoisted_7, [
                  _createVNode(_component_v_chip, {
                    color: candidateStatus.value === 'all' ? 'primary' : undefined,
                    variant: candidateStatus.value === 'all' ? 'tonal' : 'outlined',
                    size: "small",
                    onClick: _cache[6] || (_cache[6] = $event => (candidateStatus.value='all'))
                  }, {
                    default: _withCtx(() => [
                      _createTextVNode("全部 " + _toDisplayString(candidates.value.length), 1)
                    ]),
                    _: 1
                  }, 8, ["color", "variant"]),
                  (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(candidateStatusOptions.value, (opt) => {
                    return (_openBlock(), _createBlock(_component_v_chip, {
                      key: opt.value,
                      color: candidateStatus.value === opt.value ? statusColor(opt.value) : undefined,
                      variant: candidateStatus.value === opt.value ? 'tonal' : 'outlined',
                      size: "small",
                      onClick: $event => (candidateStatus.value=opt.value)
                    }, {
                      default: _withCtx(() => [
                        _createTextVNode(_toDisplayString(opt.label) + " " + _toDisplayString(opt.count), 1)
                      ]),
                      _: 2
                    }, 1032, ["color", "variant", "onClick"]))
                  }), 128))
                ]),
                _createVNode(_component_v_list, {
                  density: "compact",
                  lines: "two"
                }, {
                  default: _withCtx(() => [
                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(pagedCandidates.value, (item) => {
                      return (_openBlock(), _createBlock(_component_v_list_item, {
                        key: item.key,
                        class: "bt-candidate-row"
                      }, {
                        prepend: _withCtx(() => [
                          _createVNode(_component_v_chip, {
                            size: "x-small",
                            color: statusColor(item.status),
                            variant: "tonal"
                          }, {
                            default: _withCtx(() => [
                              _createTextVNode(_toDisplayString(item.status || '-'), 1)
                            ]),
                            _: 2
                          }, 1032, ["color"])
                        ]),
                        append: _withCtx(() => [
                          _createVNode(_component_v_btn, {
                            icon: "mdi-download",
                            size: "small",
                            variant: "text",
                            "aria-label": "下载候选",
                            title: "下载候选",
                            onClick: $event => (downloadCandidate(item))
                          }, null, 8, ["onClick"]),
                          _createVNode(_component_v_btn, {
                            icon: "mdi-eye-off",
                            size: "small",
                            variant: "text",
                            "aria-label": "忽略候选",
                            title: "忽略候选",
                            onClick: $event => (ignoreCandidate(item))
                          }, null, 8, ["onClick"])
                        ]),
                        default: _withCtx(() => [
                          _createVNode(_component_v_list_item_title, null, {
                            default: _withCtx(() => [
                              _createTextVNode(_toDisplayString(item.title), 1)
                            ]),
                            _: 2
                          }, 1024),
                          _createVNode(_component_v_list_item_subtitle, null, {
                            default: _withCtx(() => [
                              _createTextVNode("组：" + _toDisplayString(item.group || '-') + "｜E：" + _toDisplayString((item.episodes || []).join(',') || '-') + "｜" + _toDisplayString(item.reason), 1)
                            ]),
                            _: 2
                          }, 1024)
                        ]),
                        _: 2
                      }, 1024))
                    }), 128)),
                    (!filteredCandidates.value.length)
                      ? (_openBlock(), _createBlock(_component_v_list_item, {
                          key: 0,
                          title: "暂无候选",
                          subtitle: "刷新 RSS 或切换实时BT源搜索。"
                        }))
                      : _createCommentVNode("", true)
                  ]),
                  _: 1
                }),
                (filteredCandidates.value.length > candidatePageSize.value)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_8, [
                      _createElementVNode("div", _hoisted_9, "第 " + _toDisplayString(candidatePage.value) + " 页 / 共 " + _toDisplayString(Math.ceil(filteredCandidates.value.length / candidatePageSize.value)) + " 页", 1),
                      _createVNode(_component_v_pagination, {
                        modelValue: candidatePage.value,
                        "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((candidatePage).value = $event)),
                        length: Math.ceil(filteredCandidates.value.length / candidatePageSize.value),
                        density: "comfortable",
                        "total-visible": "7"
                      }, null, 8, ["modelValue", "length"])
                    ]))
                  : _createCommentVNode("", true)
              ]),
              _: 1
            })
          ]),
          _: 1
        }))
      : _createCommentVNode("", true),
    (searchMode.value === 'rss')
      ? (_openBlock(), _createBlock(_component_v_card, {
          key: 4,
          class: "mb-4",
          variant: "tonal",
          rounded: "lg"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, null, {
              default: _withCtx(() => [...(_cache[66] || (_cache[66] = [
                _createTextVNode("实时BT源搜索结果", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_alert, {
                  type: "info",
                  variant: "tonal",
                  class: "mb-3"
                }, {
                  default: _withCtx(() => [...(_cache[67] || (_cache[67] = [
                    _createTextVNode("这里只搜索你在插件里配置的 RSS/BT 来源；下载仍需确认，且必须通过动漫/特摄准入与去重。", -1)
                  ]))]),
                  _: 1
                }),
                _createVNode(_component_v_list, {
                  density: "compact",
                  lines: "two"
                }, {
                  default: _withCtx(() => [
                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(pagedRssResults.value, (item) => {
                      return (_openBlock(), _createBlock(_component_v_list_item, {
                        key: item.key
                      }, {
                        prepend: _withCtx(() => [
                          _createVNode(_component_v_chip, {
                            size: "x-small",
                            color: "info",
                            variant: "tonal"
                          }, {
                            default: _withCtx(() => [...(_cache[68] || (_cache[68] = [
                              _createTextVNode("BT源", -1)
                            ]))]),
                            _: 1
                          })
                        ]),
                        append: _withCtx(() => [
                          _createVNode(_component_v_btn, {
                            icon: "mdi-download",
                            size: "small",
                            variant: "text",
                            "aria-label": "下载候选",
                            title: "下载候选",
                            onClick: $event => (downloadCandidate(item))
                          }, null, 8, ["onClick"])
                        ]),
                        default: _withCtx(() => [
                          _createVNode(_component_v_list_item_title, null, {
                            default: _withCtx(() => [
                              _createTextVNode(_toDisplayString(item.title), 1)
                            ]),
                            _: 2
                          }, 1024),
                          _createVNode(_component_v_list_item_subtitle, null, {
                            default: _withCtx(() => [
                              _createTextVNode("组：" + _toDisplayString(item.group || '-') + "｜" + _toDisplayString(item.source_url), 1)
                            ]),
                            _: 2
                          }, 1024)
                        ]),
                        _: 2
                      }, 1024))
                    }), 128)),
                    (!rssResults.value.length)
                      ? (_openBlock(), _createBlock(_component_v_list_item, {
                          key: 0,
                          title: "暂无结果",
                          subtitle: "输入关键字后点击“搜已配置BT源”。"
                        }))
                      : _createCommentVNode("", true)
                  ]),
                  _: 1
                }),
                (rssResults.value.length > rssPageSize.value)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_10, [
                      _createElementVNode("div", _hoisted_11, "第 " + _toDisplayString(rssPage.value) + " 页 / 共 " + _toDisplayString(Math.ceil(rssResults.value.length / rssPageSize.value)) + " 页", 1),
                      _createVNode(_component_v_pagination, {
                        modelValue: rssPage.value,
                        "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((rssPage).value = $event)),
                        length: Math.ceil(rssResults.value.length / rssPageSize.value),
                        density: "comfortable",
                        "total-visible": "7"
                      }, null, 8, ["modelValue", "length"])
                    ]))
                  : _createCommentVNode("", true)
              ]),
              _: 1
            })
          ]),
          _: 1
        }))
      : _createCommentVNode("", true),
    (searchMode.value === 'subscriptions')
      ? (_openBlock(), _createBlock(_component_v_row, { key: 5 }, {
          default: _withCtx(() => [
            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(pagedSubs.value, (sub) => {
              return (_openBlock(), _createBlock(_component_v_col, {
                key: sub.id,
                cols: "12",
                sm: "6",
                md: "4",
                lg: "3"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_card, {
                    class: "sub-card",
                    rounded: "lg",
                    elevation: "3",
                    style: _normalizeStyle({ backgroundImage: `linear-gradient(90deg, rgba(4,8,18,.96), rgba(4,8,18,.72)), url('${tmdbImage(sub, 'backdrop')}')` }),
                    onClick: $event => (openSub(sub))
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_v_card_text, { class: "pa-3 fill-height d-flex flex-column" }, {
                        default: _withCtx(() => [
                          _createElementVNode("div", _hoisted_12, [
                            _createElementVNode("div", _hoisted_13, [
                              (tmdbImage(sub, 'poster'))
                                ? (_openBlock(), _createBlock(_component_v_img, {
                                    key: 0,
                                    src: tmdbImage(sub, 'poster'),
                                    width: "58",
                                    height: "82",
                                    cover: "",
                                    class: "rounded poster"
                                  }, null, 8, ["src"]))
                                : (_openBlock(), _createElementBlock("div", _hoisted_14, _toDisplayString(seasonText(sub)), 1))
                            ]),
                            _createElementVNode("div", _hoisted_15, [
                              _createElementVNode("div", _hoisted_16, _toDisplayString(sub.year || '----'), 1),
                              _createElementVNode("div", _hoisted_17, _toDisplayString(sub.title) + " " + _toDisplayString(seasonText(sub)), 1),
                              _createElementVNode("div", _hoisted_18, [
                                _createVNode(_component_v_icon, {
                                  size: "14",
                                  icon: "mdi-progress-download",
                                  class: "me-1"
                                }),
                                _createTextVNode(_toDisplayString(downloadedCount(sub)) + " / " + _toDisplayString(totalEpisode(sub) || '?') + " ", 1),
                                _cache[69] || (_cache[69] = _createElementVNode("span", { class: "mx-1" }, "·", -1)),
                                _createTextVNode(" 缺 " + _toDisplayString(lackCount(sub)), 1)
                              ]),
                              _createElementVNode("div", _hoisted_19, [
                                _createVNode(_component_v_icon, {
                                  size: "14",
                                  icon: "mdi-account",
                                  class: "me-1"
                                }),
                                _createTextVNode(_toDisplayString(groupText(sub)), 1)
                              ])
                            ]),
                            _createVNode(_component_v_menu, {
                              onClick: _cache[10] || (_cache[10] = _withModifiers(() => {}, ["stop"]))
                            }, {
                              activator: _withCtx(({ props: menuProps }) => [
                                _createVNode(_component_v_btn, _mergeProps({ ref_for: true }, menuProps, {
                                  icon: "mdi-dots-vertical",
                                  variant: "text",
                                  size: "small",
                                  "aria-label": "订阅更多操作",
                                  title: "订阅更多操作",
                                  onClick: _cache[9] || (_cache[9] = _withModifiers(() => {}, ["stop"]))
                                }), null, 16)
                              ]),
                              default: _withCtx(() => [
                                _createVNode(_component_v_list, { density: "compact" }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_list_item, {
                                      "prepend-icon": "mdi-eye",
                                      title: "查看详情",
                                      onClick: $event => (openSub(sub))
                                    }, null, 8, ["onClick"]),
                                    _createVNode(_component_v_list_item, {
                                      "prepend-icon": "mdi-pencil",
                                      title: "编辑订阅",
                                      onClick: $event => (openEdit(sub))
                                    }, null, 8, ["onClick"]),
                                    _createVNode(_component_v_list_item, {
                                      "prepend-icon": "mdi-clipboard-text-clock",
                                      title: "查看下载/等待记录",
                                      onClick: $event => (openFacts(sub))
                                    }, null, 8, ["onClick"]),
                                    _createVNode(_component_v_divider),
                                    _createVNode(_component_v_list_item, {
                                      "prepend-icon": "mdi-magnify",
                                      title: "搜索缺集候选",
                                      onClick: $event => (searchSubCandidates(sub))
                                    }, null, 8, ["onClick"]),
                                    _createVNode(_component_v_list_item, {
                                      "prepend-icon": "mdi-rss",
                                      title: "从BT源实时搜索",
                                      onClick: $event => {keyword.value=sub.title;searchRssNow();}
                                    }, null, 8, ["onClick"]),
                                    _createVNode(_component_v_list_item, {
                                      "prepend-icon": "mdi-image-refresh",
                                      title: "刷新媒体信息",
                                      onClick: $event => (refreshSubMeta(sub))
                                    }, null, 8, ["onClick"]),
                                    _createVNode(_component_v_list_item, {
                                      "prepend-icon": "mdi-refresh",
                                      title: "刷新入库状态",
                                      onClick: $event => (refreshSubStatus(sub))
                                    }, null, 8, ["onClick"]),
                                    _createVNode(_component_v_divider),
                                    _createVNode(_component_v_list_item, {
                                      "prepend-icon": "mdi-account-group",
                                      title: "设置发布组标记",
                                      onClick: $event => (openGroup(sub))
                                    }, null, 8, ["onClick"]),
                                    _createVNode(_component_v_list_item, {
                                      "prepend-icon": "mdi-folder-download",
                                      title: "设为老番补全",
                                      onClick: $event => (createBackfillFromSub(sub))
                                    }, null, 8, ["onClick"]),
                                    (sub.state === 'active')
                                      ? (_openBlock(), _createBlock(_component_v_list_item, {
                                          key: 0,
                                          "prepend-icon": "mdi-pause-circle",
                                          title: "暂停订阅",
                                          onClick: $event => (setState(sub, 'paused'))
                                        }, null, 8, ["onClick"]))
                                      : (_openBlock(), _createBlock(_component_v_list_item, {
                                          key: 1,
                                          "prepend-icon": "mdi-play-circle",
                                          title: "恢复订阅",
                                          onClick: $event => (setState(sub, 'active'))
                                        }, null, 8, ["onClick"])),
                                    _createVNode(_component_v_divider),
                                    _createVNode(_component_v_list_item, {
                                      "prepend-icon": "mdi-clock-remove",
                                      title: "清空等待队列",
                                      onClick: $event => (clearPending(sub))
                                    }, null, 8, ["onClick"]),
                                    _createVNode(_component_v_list_item, {
                                      "prepend-icon": "mdi-history",
                                      title: "重置下载记录",
                                      onClick: $event => (resetDownloaded(sub))
                                    }, null, 8, ["onClick"]),
                                    _createVNode(_component_v_list_item, {
                                      "prepend-icon": "mdi-delete-outline",
                                      title: "删除私有订阅",
                                      onClick: $event => (deleteSubscription(sub))
                                    }, null, 8, ["onClick"])
                                  ]),
                                  _: 2
                                }, 1024)
                              ]),
                              _: 2
                            }, 1024)
                          ]),
                          _createVNode(_component_v_spacer),
                          _createVNode(_component_v_progress_linear, {
                            "model-value": progressValue(sub),
                            color: "success",
                            height: "5",
                            rounded: "",
                            class: "mt-3"
                          }, null, 8, ["model-value"]),
                          _createElementVNode("div", _hoisted_20, [
                            _createElementVNode("span", null, _toDisplayString(sub.username || 'BT订阅中心'), 1),
                            _createElementVNode("span", null, _toDisplayString(sub.state === 'paused' ? '已暂停' : `待定 ${pendingCount(sub)}`), 1)
                          ])
                        ]),
                        _: 2
                      }, 1024)
                    ]),
                    _: 2
                  }, 1032, ["style", "onClick"])
                ]),
                _: 2
              }, 1024))
            }), 128))
          ]),
          _: 1
        }))
      : _createCommentVNode("", true),
    (searchMode.value === 'subscriptions' && filteredSubs.value.length > pageSize.value)
      ? (_openBlock(), _createElementBlock("div", _hoisted_21, [
          _createElementVNode("div", _hoisted_22, "第 " + _toDisplayString(page.value) + " 页 / 共 " + _toDisplayString(Math.ceil(filteredSubs.value.length / pageSize.value)) + " 页", 1),
          _createVNode(_component_v_pagination, {
            modelValue: page.value,
            "onUpdate:modelValue": _cache[11] || (_cache[11] = $event => ((page).value = $event)),
            length: Math.ceil(filteredSubs.value.length / pageSize.value),
            density: "comfortable",
            "total-visible": "7"
          }, null, 8, ["modelValue", "length"])
        ]))
      : _createCommentVNode("", true),
    _createVNode(_component_v_dialog, {
      "model-value": !!selected.value,
      "max-width": "1120",
      scrollable: "",
      class: "subscription-detail-shell",
      "onUpdate:modelValue": _cache[18] || (_cache[18] = v => { if (!v) selected.value = null; })
    }, {
      default: _withCtx(() => [
        (selected.value)
          ? (_openBlock(), _createBlock(_component_v_card, {
              key: 0,
              class: "detail-dialog-full",
              rounded: "0"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_toolbar, {
                  color: "surface",
                  density: "comfortable",
                  class: "detail-toolbar"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_btn, {
                      icon: "mdi-close",
                      variant: "text",
                      "aria-label": "关闭详情",
                      title: "关闭详情",
                      onClick: _cache[12] || (_cache[12] = $event => (selected.value = null))
                    }),
                    _createVNode(_component_v_toolbar_title, { class: "text-subtitle-1 text-md-h6 font-weight-bold text-truncate" }, {
                      default: _withCtx(() => [
                        _createTextVNode(_toDisplayString(selected.value.title) + " " + _toDisplayString(seasonText(selected.value)), 1)
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_spacer),
                    _createVNode(_component_v_btn, {
                      size: "small",
                      color: "primary",
                      variant: "tonal",
                      "prepend-icon": "mdi-pencil",
                      onClick: _cache[13] || (_cache[13] = $event => (openEdit(selected.value)))
                    }, {
                      default: _withCtx(() => [...(_cache[70] || (_cache[70] = [
                        _createTextVNode("编辑", -1)
                      ]))]),
                      _: 1
                    }),
                    _createVNode(_component_v_btn, {
                      size: "small",
                      color: "info",
                      variant: "tonal",
                      class: "ms-2",
                      "prepend-icon": "mdi-magnify",
                      onClick: _cache[14] || (_cache[14] = $event => (searchSubCandidates(selected.value)))
                    }, {
                      default: _withCtx(() => [...(_cache[71] || (_cache[71] = [
                        _createTextVNode("搜候选", -1)
                      ]))]),
                      _: 1
                    }),
                    (selected.value.state === 'active')
                      ? (_openBlock(), _createBlock(_component_v_btn, {
                          key: 0,
                          size: "small",
                          color: "warning",
                          variant: "tonal",
                          class: "ms-2",
                          "prepend-icon": "mdi-pause-circle",
                          onClick: _cache[15] || (_cache[15] = $event => (setState(selected.value, 'paused')))
                        }, {
                          default: _withCtx(() => [...(_cache[72] || (_cache[72] = [
                            _createTextVNode("暂停", -1)
                          ]))]),
                          _: 1
                        }))
                      : (_openBlock(), _createBlock(_component_v_btn, {
                          key: 1,
                          size: "small",
                          color: "success",
                          variant: "tonal",
                          class: "ms-2",
                          "prepend-icon": "mdi-play-circle",
                          onClick: _cache[16] || (_cache[16] = $event => (setState(selected.value, 'active')))
                        }, {
                          default: _withCtx(() => [...(_cache[73] || (_cache[73] = [
                            _createTextVNode("恢复", -1)
                          ]))]),
                          _: 1
                        }))
                  ]),
                  _: 1
                }),
                _createElementVNode("div", _hoisted_23, [
                  _createElementVNode("div", {
                    class: "detail-hero",
                    style: _normalizeStyle({ backgroundImage: `linear-gradient(90deg, rgba(4,8,18,.94), rgba(4,8,18,.70), rgba(4,8,18,.35)), url('${tmdbImage(selected.value, 'backdrop')}')` })
                  }, [
                    _createElementVNode("div", _hoisted_24, [
                      (tmdbImage(selected.value, 'poster'))
                        ? (_openBlock(), _createBlock(_component_v_img, {
                            key: 0,
                            src: tmdbImage(selected.value, 'poster'),
                            width: "128",
                            height: "186",
                            cover: "",
                            class: "detail-poster"
                          }, null, 8, ["src"]))
                        : (_openBlock(), _createElementBlock("div", _hoisted_25, _toDisplayString(seasonText(selected.value)), 1)),
                      _createElementVNode("div", _hoisted_26, [
                        _createElementVNode("div", _hoisted_27, [
                          _createVNode(_component_v_chip, {
                            size: "small",
                            color: "primary",
                            variant: "tonal"
                          }, {
                            default: _withCtx(() => [
                              _createTextVNode(_toDisplayString(selected.value.mode === 'airing' ? '新番追更' : '老番补全'), 1)
                            ]),
                            _: 1
                          }),
                          _createVNode(_component_v_chip, {
                            size: "small",
                            color: selected.value.state === 'paused' ? 'warning' : 'success',
                            variant: "tonal"
                          }, {
                            default: _withCtx(() => [
                              _createTextVNode(_toDisplayString(selected.value.state === 'paused' ? '已暂停' : '运行中'), 1)
                            ]),
                            _: 1
                          }, 8, ["color"]),
                          _createVNode(_component_v_chip, {
                            size: "small",
                            color: "info",
                            variant: "tonal"
                          }, {
                            default: _withCtx(() => [...(_cache[74] || (_cache[74] = [
                              _createTextVNode("BT/RSS", -1)
                            ]))]),
                            _: 1
                          })
                        ]),
                        _createElementVNode("div", _hoisted_28, _toDisplayString(selected.value.title) + " " + _toDisplayString(seasonText(selected.value)), 1),
                        _createElementVNode("div", _hoisted_29, _toDisplayString(selected.value.year || '未知年份') + " · " + _toDisplayString(selected.value.source || 'BT/RSS') + " · 发布组：" + _toDisplayString(groupText(selected.value)), 1),
                        _createElementVNode("div", _hoisted_30, _toDisplayString(selected.value.description || '暂无简介。'), 1)
                      ])
                    ])
                  ], 4),
                  _createElementVNode("div", _hoisted_31, [
                    _createVNode(_component_v_row, { class: "mb-3" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_col, {
                          cols: "6",
                          md: "3"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_card, {
                              variant: "tonal",
                              color: "success",
                              rounded: "lg"
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_card_text, { class: "py-3" }, {
                                  default: _withCtx(() => [
                                    _cache[75] || (_cache[75] = _createElementVNode("div", { class: "text-caption" }, "已入库/完成", -1)),
                                    _createElementVNode("div", _hoisted_32, _toDisplayString(downloadedCount(selected.value)), 1)
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
                          cols: "6",
                          md: "3"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_card, {
                              variant: "tonal",
                              color: "primary",
                              rounded: "lg"
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_card_text, { class: "py-3" }, {
                                  default: _withCtx(() => [
                                    _cache[76] || (_cache[76] = _createElementVNode("div", { class: "text-caption" }, "总集数", -1)),
                                    _createElementVNode("div", _hoisted_33, _toDisplayString(totalEpisode(selected.value) || '?'), 1)
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
                          cols: "6",
                          md: "3"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_card, {
                              variant: "tonal",
                              color: "error",
                              rounded: "lg"
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_card_text, { class: "py-3" }, {
                                  default: _withCtx(() => [
                                    _cache[77] || (_cache[77] = _createElementVNode("div", { class: "text-caption" }, "缺集", -1)),
                                    _createElementVNode("div", _hoisted_34, _toDisplayString(lackCount(selected.value)), 1)
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
                          cols: "6",
                          md: "3"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_card, {
                              variant: "tonal",
                              color: "warning",
                              rounded: "lg"
                            }, {
                              default: _withCtx(() => [
                                _createVNode(_component_v_card_text, { class: "py-3" }, {
                                  default: _withCtx(() => [
                                    _cache[78] || (_cache[78] = _createElementVNode("div", { class: "text-caption" }, "等待候选", -1)),
                                    _createElementVNode("div", _hoisted_35, _toDisplayString(pendingCount(selected.value)), 1)
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
                      variant: "tonal",
                      rounded: "lg",
                      class: "mb-4"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_card_text, null, {
                          default: _withCtx(() => [
                            _createElementVNode("div", _hoisted_36, [
                              _cache[79] || (_cache[79] = _createElementVNode("span", null, "订阅进度", -1)),
                              _createElementVNode("span", null, _toDisplayString(progressValue(selected.value)) + "%", 1)
                            ]),
                            _createVNode(_component_v_progress_linear, {
                              "model-value": progressValue(selected.value),
                              color: "success",
                              height: "8",
                              rounded: ""
                            }, null, 8, ["model-value"])
                          ]),
                          _: 1
                        })
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_card, {
                      variant: "tonal",
                      rounded: "lg",
                      class: "mb-4"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_card_title, { class: "text-subtitle-1" }, {
                          default: _withCtx(() => [...(_cache[80] || (_cache[80] = [
                            _createTextVNode("集数状态", -1)
                          ]))]),
                          _: 1
                        }),
                        _createVNode(_component_v_card_text, null, {
                          default: _withCtx(() => [
                            _createElementVNode("div", _hoisted_37, [
                              (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(episodeItems(selected.value), (ep) => {
                                return (_openBlock(), _createBlock(_component_v_tooltip, {
                                  key: ep,
                                  text: `E${String(ep).padStart(2, '0')} · ${episodeLabel(selected.value, ep)}`,
                                  location: "top"
                                }, {
                                  activator: _withCtx(({ props: tipProps }) => [
                                    _createVNode(_component_v_chip, _mergeProps({ ref_for: true }, tipProps, {
                                      size: "small",
                                      color: episodeColor(selected.value, ep),
                                      variant: "tonal",
                                      class: "episode-chip"
                                    }), {
                                      default: _withCtx(() => [
                                        _createTextVNode("E" + _toDisplayString(String(ep).padStart(2, '0')), 1)
                                      ]),
                                      _: 2
                                    }, 1040, ["color"])
                                  ]),
                                  _: 2
                                }, 1032, ["text"]))
                              }), 128))
                            ]),
                            _createElementVNode("div", _hoisted_38, [
                              _createElementVNode("span", null, [
                                _createVNode(_component_v_icon, {
                                  size: "12",
                                  color: "success",
                                  icon: "mdi-circle"
                                }),
                                _cache[81] || (_cache[81] = _createTextVNode(" 已入库", -1))
                              ]),
                              _createElementVNode("span", null, [
                                _createVNode(_component_v_icon, {
                                  size: "12",
                                  color: "info",
                                  icon: "mdi-circle"
                                }),
                                _cache[82] || (_cache[82] = _createTextVNode(" 已提交", -1))
                              ]),
                              _createElementVNode("span", null, [
                                _createVNode(_component_v_icon, {
                                  size: "12",
                                  color: "orange",
                                  icon: "mdi-circle"
                                }),
                                _cache[83] || (_cache[83] = _createTextVNode(" 缺Hash", -1))
                              ]),
                              _createElementVNode("span", null, [
                                _createVNode(_component_v_icon, {
                                  size: "12",
                                  color: "warning",
                                  icon: "mdi-circle"
                                }),
                                _cache[84] || (_cache[84] = _createTextVNode(" 有候选", -1))
                              ]),
                              _createElementVNode("span", null, [
                                _createVNode(_component_v_icon, {
                                  size: "12",
                                  color: "error",
                                  icon: "mdi-circle"
                                }),
                                _cache[85] || (_cache[85] = _createTextVNode(" 缺集", -1))
                              ])
                            ])
                          ]),
                          _: 1
                        })
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_card, {
                      variant: "tonal",
                      rounded: "lg"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_card_title, { class: "d-flex align-center justify-space-between" }, {
                          default: _withCtx(() => [
                            _cache[86] || (_cache[86] = _createElementVNode("span", null, "相关候选", -1)),
                            _createVNode(_component_v_chip, {
                              size: "small",
                              variant: "tonal"
                            }, {
                              default: _withCtx(() => [
                                _createTextVNode(_toDisplayString(detailCandidates.value.length) + " 条", 1)
                              ]),
                              _: 1
                            })
                          ]),
                          _: 1
                        }),
                        _createVNode(_component_v_card_text, null, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_list, {
                              density: "compact",
                              lines: "three",
                              class: "candidate-list"
                            }, {
                              default: _withCtx(() => [
                                (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(pagedDetailCandidates.value, (item) => {
                                  return (_openBlock(), _createBlock(_component_v_list_item, {
                                    key: item.key,
                                    class: "candidate-row"
                                  }, {
                                    prepend: _withCtx(() => [
                                      _createVNode(_component_v_chip, {
                                        size: "x-small",
                                        color: statusColor(item.status),
                                        variant: "tonal"
                                      }, {
                                        default: _withCtx(() => [
                                          _createTextVNode(_toDisplayString(item.status || '-'), 1)
                                        ]),
                                        _: 2
                                      }, 1032, ["color"])
                                    ]),
                                    append: _withCtx(() => [
                                      _createVNode(_component_v_btn, {
                                        icon: "mdi-download",
                                        size: "small",
                                        variant: "text",
                                        "aria-label": "下载候选",
                                        title: "下载候选",
                                        onClick: $event => (downloadCandidate(item))
                                      }, null, 8, ["onClick"]),
                                      _createVNode(_component_v_btn, {
                                        icon: "mdi-eye-off",
                                        size: "small",
                                        variant: "text",
                                        "aria-label": "忽略候选",
                                        title: "忽略候选",
                                        onClick: $event => (ignoreCandidate(item))
                                      }, null, 8, ["onClick"])
                                    ]),
                                    default: _withCtx(() => [
                                      _createVNode(_component_v_list_item_title, null, {
                                        default: _withCtx(() => [
                                          _createTextVNode(_toDisplayString(item.title), 1)
                                        ]),
                                        _: 2
                                      }, 1024),
                                      _createVNode(_component_v_list_item_subtitle, null, {
                                        default: _withCtx(() => [
                                          _createTextVNode("组：" + _toDisplayString(item.group || '-') + "｜E：" + _toDisplayString((item.episodes || []).join(',') || '-') + "｜" + _toDisplayString(item.reason), 1)
                                        ]),
                                        _: 2
                                      }, 1024)
                                    ]),
                                    _: 2
                                  }, 1024))
                                }), 128)),
                                (!detailCandidates.value.length)
                                  ? (_openBlock(), _createBlock(_component_v_list_item, {
                                      key: 0,
                                      title: "暂无候选",
                                      subtitle: "刷新 RSS 后会在这里看到匹配到本订阅的候选资源。"
                                    }))
                                  : _createCommentVNode("", true)
                              ]),
                              _: 1
                            }),
                            (detailCandidates.value.length > detailCandidatePageSize.value)
                              ? (_openBlock(), _createElementBlock("div", _hoisted_39, [
                                  _createElementVNode("div", _hoisted_40, "第 " + _toDisplayString(detailCandidatePage.value) + " 页 / 共 " + _toDisplayString(Math.ceil(detailCandidates.value.length / detailCandidatePageSize.value)) + " 页", 1),
                                  _createVNode(_component_v_pagination, {
                                    modelValue: detailCandidatePage.value,
                                    "onUpdate:modelValue": _cache[17] || (_cache[17] = $event => ((detailCandidatePage).value = $event)),
                                    length: Math.ceil(detailCandidates.value.length / detailCandidatePageSize.value),
                                    density: "comfortable",
                                    "total-visible": "7"
                                  }, null, 8, ["modelValue", "length"])
                                ]))
                              : _createCommentVNode("", true)
                          ]),
                          _: 1
                        })
                      ]),
                      _: 1
                    })
                  ])
                ])
              ]),
              _: 1
            }))
          : _createCommentVNode("", true)
      ]),
      _: 1
    }, 8, ["model-value"]),
    _createVNode(_component_v_dialog, {
      modelValue: showEditDialog.value,
      "onUpdate:modelValue": _cache[28] || (_cache[28] = $event => ((showEditDialog).value = $event)),
      "max-width": "680",
      scrollable: ""
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, null, {
              default: _withCtx(() => [...(_cache[87] || (_cache[87] = [
                _createTextVNode("编辑私有订阅", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_row, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "8"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_text_field, {
                          modelValue: editForm.value.title,
                          "onUpdate:modelValue": _cache[19] || (_cache[19] = $event => ((editForm.value.title) = $event)),
                          label: "标题"
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "4"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_text_field, {
                          modelValue: editForm.value.year,
                          "onUpdate:modelValue": _cache[20] || (_cache[20] = $event => ((editForm.value.year) = $event)),
                          label: "年份"
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "4"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_text_field, {
                          modelValue: editForm.value.season,
                          "onUpdate:modelValue": _cache[21] || (_cache[21] = $event => ((editForm.value.season) = $event)),
                          label: "季号",
                          type: "number"
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "4"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_text_field, {
                          modelValue: editForm.value.total_episode,
                          "onUpdate:modelValue": _cache[22] || (_cache[22] = $event => ((editForm.value.total_episode) = $event)),
                          label: "总集数",
                          type: "number"
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "4"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_select, {
                          modelValue: editForm.value.mode,
                          "onUpdate:modelValue": _cache[23] || (_cache[23] = $event => ((editForm.value.mode) = $event)),
                          items: [{title:'新番追更',value:'airing'},{title:'老番补全',value:'backfill'}],
                          label: "模式"
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "6"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_select, {
                          modelValue: editForm.value.state,
                          "onUpdate:modelValue": _cache[24] || (_cache[24] = $event => ((editForm.value.state) = $event)),
                          items: [{title:'运行中',value:'active'},{title:'已暂停',value:'paused'}],
                          label: "状态"
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_col, {
                      cols: "12",
                      md: "6"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_text_field, {
                          modelValue: editForm.value.preferred_group,
                          "onUpdate:modelValue": _cache[25] || (_cache[25] = $event => ((editForm.value.preferred_group) = $event)),
                          label: "发布组标记"
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_col, { cols: "12" }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_textarea, {
                          modelValue: editForm.value.description,
                          "onUpdate:modelValue": _cache[26] || (_cache[26] = $event => ((editForm.value.description) = $event)),
                          label: "简介/备注",
                          rows: "3"
                        }, null, 8, ["modelValue"])
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  variant: "text",
                  onClick: _cache[27] || (_cache[27] = $event => (showEditDialog.value=false))
                }, {
                  default: _withCtx(() => [...(_cache[88] || (_cache[88] = [
                    _createTextVNode("取消", -1)
                  ]))]),
                  _: 1
                }),
                _createVNode(_component_v_btn, {
                  color: "primary",
                  onClick: saveSubscriptionEdit
                }, {
                  default: _withCtx(() => [...(_cache[89] || (_cache[89] = [
                    _createTextVNode("保存", -1)
                  ]))]),
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
    }, 8, ["modelValue"]),
    _createVNode(_component_v_dialog, {
      modelValue: showFactsDialog.value,
      "onUpdate:modelValue": _cache[32] || (_cache[32] = $event => ((showFactsDialog).value = $event)),
      "max-width": "860",
      scrollable: ""
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, null, {
              default: _withCtx(() => [...(_cache[90] || (_cache[90] = [
                _createTextVNode("下载/等待记录", -1)
              ]))]),
              _: 1
            }),
            (selected.value)
              ? (_openBlock(), _createBlock(_component_v_card_text, { key: 0 }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_tabs, {
                      modelValue: factsTab.value,
                      "onUpdate:modelValue": _cache[29] || (_cache[29] = $event => ((factsTab).value = $event)),
                      density: "compact"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_tab, { value: "downloaded" }, {
                          default: _withCtx(() => [
                            _createTextVNode("下载事实 " + _toDisplayString(Object.keys(selected.value.episode_facts || selected.value.downloaded || {}).length), 1)
                          ]),
                          _: 1
                        }),
                        _createVNode(_component_v_tab, { value: "pending" }, {
                          default: _withCtx(() => [
                            _createTextVNode("等待 " + _toDisplayString(Object.keys(selected.value.pending || {}).length), 1)
                          ]),
                          _: 1
                        }),
                        _createVNode(_component_v_tab, { value: "groups" }, {
                          default: _withCtx(() => [
                            _createTextVNode("发布组 " + _toDisplayString(Object.keys(selected.value.seen_groups || {}).length), 1)
                          ]),
                          _: 1
                        })
                      ]),
                      _: 1
                    }, 8, ["modelValue"]),
                    _createVNode(_component_v_window, {
                      modelValue: factsTab.value,
                      "onUpdate:modelValue": _cache[30] || (_cache[30] = $event => ((factsTab).value = $event)),
                      class: "mt-3"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_window_item, { value: "downloaded" }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_list, { density: "compact" }, {
                              default: _withCtx(() => [
                                (selected.value.replacement_state)
                                  ? (_openBlock(), _createBlock(_component_v_list_item, {
                                      key: 0,
                                      title: `整季包替换 · ${selected.value.replacement_message || selected.value.replacement_state}`,
                                      subtitle: `Hash: ${selected.value.replacement_hash ? String(selected.value.replacement_hash).slice(0,12) : '-'} · 发布组: ${selected.value.replacement_group || '-'} · 状态: ${selected.value.replacement_state}`,
                                      "prepend-icon": "mdi-package-variant-closed"
                                    }, null, 8, ["title", "subtitle"]))
                                  : _createCommentVNode("", true),
                                (_openBlock(true), _createElementBlock(_Fragment, null, _renderList((selected.value.episode_facts || selected.value.downloaded || {}), (item, ep) => {
                                  return (_openBlock(), _createBlock(_component_v_list_item, {
                                    key: ep,
                                    title: `E${String(ep).padStart(2,'0')} · ${item.final_status_text || item.status_text || item.plugin_status_text || item.group || '-'}`,
                                    subtitle: `Hash: ${item.download_hash ? String(item.download_hash).slice(0,12) : '-'} · 下载器: ${item.downloader_name || '-'} · ${item.downloader_progress ?? '-'}%`
                                  }, null, 8, ["title", "subtitle"]))
                                }), 128)),
                                (!Object.keys(selected.value.episode_facts || selected.value.downloaded || {}).length && !selected.value.replacement_state)
                                  ? (_openBlock(), _createBlock(_component_v_list_item, {
                                      key: 1,
                                      title: "暂无下载事实"
                                    }))
                                  : _createCommentVNode("", true)
                              ]),
                              _: 1
                            })
                          ]),
                          _: 1
                        }),
                        _createVNode(_component_v_window_item, { value: "pending" }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_list, { density: "compact" }, {
                              default: _withCtx(() => [
                                (_openBlock(true), _createElementBlock(_Fragment, null, _renderList((selected.value.pending || {}), (item, ep) => {
                                  return (_openBlock(), _createBlock(_component_v_list_item, {
                                    key: ep,
                                    title: `E${String(ep).padStart(2,'0')} · 等待候选`,
                                    subtitle: `first_seen: ${item.first_seen || '-'} · candidates: ${(item.candidates || []).length}`
                                  }, null, 8, ["title", "subtitle"]))
                                }), 128)),
                                (!Object.keys(selected.value.pending || {}).length)
                                  ? (_openBlock(), _createBlock(_component_v_list_item, {
                                      key: 0,
                                      title: "暂无等待记录"
                                    }))
                                  : _createCommentVNode("", true)
                              ]),
                              _: 1
                            })
                          ]),
                          _: 1
                        }),
                        _createVNode(_component_v_window_item, { value: "groups" }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_list, { density: "compact" }, {
                              default: _withCtx(() => [
                                (_openBlock(true), _createElementBlock(_Fragment, null, _renderList((selected.value.seen_groups || {}), (info, name) => {
                                  return (_openBlock(), _createBlock(_component_v_list_item, {
                                    key: name,
                                    title: `${name} · ${info.count || 0}`,
                                    subtitle: info.last_seen || '-'
                                  }, null, 8, ["title", "subtitle"]))
                                }), 128)),
                                (!Object.keys(selected.value.seen_groups || {}).length)
                                  ? (_openBlock(), _createBlock(_component_v_list_item, {
                                      key: 0,
                                      title: "暂无发布组统计"
                                    }))
                                  : _createCommentVNode("", true)
                              ]),
                              _: 1
                            })
                          ]),
                          _: 1
                        })
                      ]),
                      _: 1
                    }, 8, ["modelValue"])
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  variant: "text",
                  onClick: _cache[31] || (_cache[31] = $event => (showFactsDialog.value=false))
                }, {
                  default: _withCtx(() => [...(_cache[91] || (_cache[91] = [
                    _createTextVNode("关闭", -1)
                  ]))]),
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
    }, 8, ["modelValue"]),
    _createVNode(_component_v_dialog, {
      modelValue: showNoHashDialog.value,
      "onUpdate:modelValue": _cache[34] || (_cache[34] = $event => ((showNoHashDialog).value = $event)),
      "max-width": "980",
      scrollable: ""
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "d-flex align-center justify-space-between" }, {
              default: _withCtx(() => [
                _cache[92] || (_cache[92] = _createElementVNode("span", null, "历史缺 Hash 诊断", -1)),
                _createVNode(_component_v_chip, {
                  color: "orange",
                  variant: "tonal"
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(submittedNoHashItems.value.length) + " 条", 1)
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_subtitle, null, {
              default: _withCtx(() => [...(_cache[93] || (_cache[93] = [
                _createTextVNode("这些记录来自旧版本“已提交下载”事实，但没有 download_hash，因此无法自动追踪下载器/转移状态。本页只读，不会重新下载或修改记录。", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_list, {
                  density: "compact",
                  lines: "three"
                }, {
                  default: _withCtx(() => [
                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(submittedNoHashItems.value, (item) => {
                      return (_openBlock(), _createBlock(_component_v_list_item, {
                        key: `${item.sub_id}-${item.episode}`
                      }, {
                        prepend: _withCtx(() => [
                          _createVNode(_component_v_chip, {
                            color: "orange",
                            size: "x-small",
                            variant: "tonal"
                          }, {
                            default: _withCtx(() => [...(_cache[94] || (_cache[94] = [
                              _createTextVNode("缺Hash", -1)
                            ]))]),
                            _: 1
                          })
                        ]),
                        default: _withCtx(() => [
                          _createVNode(_component_v_list_item_title, null, {
                            default: _withCtx(() => [
                              _createTextVNode(_toDisplayString(item.title) + " S" + _toDisplayString(String(item.season || 1).padStart(2,'0')) + "E" + _toDisplayString(String(item.episode).padStart(2,'0')), 1)
                            ]),
                            _: 2
                          }, 1024),
                          _createVNode(_component_v_list_item_subtitle, null, {
                            default: _withCtx(() => [
                              _createTextVNode(_toDisplayString(item.record_title || '-'), 1)
                            ]),
                            _: 2
                          }, 1024),
                          _createVNode(_component_v_list_item_subtitle, null, {
                            default: _withCtx(() => [
                              _createTextVNode("组：" + _toDisplayString(item.group || '-') + "｜候选：" + _toDisplayString(item.candidate_count || 0) + "｜" + _toDisplayString(item.suggestion), 1)
                            ]),
                            _: 2
                          }, 1024)
                        ]),
                        _: 2
                      }, 1024))
                    }), 128)),
                    (!submittedNoHashItems.value.length)
                      ? (_openBlock(), _createBlock(_component_v_list_item, {
                          key: 0,
                          title: "暂无历史缺Hash记录"
                        }))
                      : _createCommentVNode("", true)
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  variant: "text",
                  onClick: _cache[33] || (_cache[33] = $event => (showNoHashDialog.value=false))
                }, {
                  default: _withCtx(() => [...(_cache[95] || (_cache[95] = [
                    _createTextVNode("关闭", -1)
                  ]))]),
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
    }, 8, ["modelValue"]),
    _createVNode(_component_v_dialog, {
      modelValue: showIssuesDialog.value,
      "onUpdate:modelValue": _cache[36] || (_cache[36] = $event => ((showIssuesDialog).value = $event)),
      "max-width": "980",
      scrollable: ""
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "d-flex align-center justify-space-between" }, {
              default: _withCtx(() => [
                _cache[96] || (_cache[96] = _createElementVNode("span", null, "识别异常待处理", -1)),
                _createVNode(_component_v_chip, {
                  color: "error",
                  variant: "tonal"
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(openIssues.value.length) + " 条", 1)
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_alert, {
                  type: "warning",
                  variant: "tonal",
                  class: "mb-3"
                }, {
                  default: _withCtx(() => [...(_cache[97] || (_cache[97] = [
                    _createTextVNode("这些资源来自已筛选的动漫/特摄来源，但 MP 识别失败或识别成真人/剧集分类。插件不会直接当真人下载；后续可手动处理或调用智能体生成窄作用域识别词后回流候选。", -1)
                  ]))]),
                  _: 1
                }),
                _createVNode(_component_v_list, {
                  density: "compact",
                  lines: "three"
                }, {
                  default: _withCtx(() => [
                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(openIssues.value, (item) => {
                      return (_openBlock(), _createBlock(_component_v_list_item, {
                        key: item.key
                      }, {
                        prepend: _withCtx(() => [
                          _createVNode(_component_v_chip, {
                            size: "x-small",
                            color: "error",
                            variant: "tonal"
                          }, {
                            default: _withCtx(() => [
                              _createTextVNode(_toDisplayString(item.status || 'open'), 1)
                            ]),
                            _: 2
                          }, 1024)
                        ]),
                        append: _withCtx(() => [
                          _createElementVNode("div", _hoisted_42, [
                            _createVNode(_component_v_btn, {
                              size: "small",
                              variant: "text",
                              "prepend-icon": "mdi-refresh",
                              onClick: $event => (rescanIssue(item))
                            }, {
                              default: _withCtx(() => [...(_cache[98] || (_cache[98] = [
                                _createTextVNode("重扫", -1)
                              ]))]),
                              _: 1
                            }, 8, ["onClick"]),
                            _createVNode(_component_v_btn, {
                              size: "small",
                              variant: "text",
                              "prepend-icon": "mdi-robot",
                              onClick: $event => (autoWriteIssue(item))
                            }, {
                              default: _withCtx(() => [...(_cache[99] || (_cache[99] = [
                                _createTextVNode("智能体自动写入", -1)
                              ]))]),
                              _: 1
                            }, 8, ["onClick"]),
                            _createVNode(_component_v_btn, {
                              size: "small",
                              color: "primary",
                              variant: "text",
                              "prepend-icon": "mdi-identifier",
                              onClick: $event => (previewIssueIdentifier(item))
                            }, {
                              default: _withCtx(() => [...(_cache[100] || (_cache[100] = [
                                _createTextVNode("识别词", -1)
                              ]))]),
                              _: 1
                            }, 8, ["onClick"]),
                            _createVNode(_component_v_btn, {
                              size: "small",
                              color: "info",
                              variant: "text",
                              "prepend-icon": "mdi-recycle",
                              onClick: $event => (reflowIssue(item))
                            }, {
                              default: _withCtx(() => [...(_cache[101] || (_cache[101] = [
                                _createTextVNode("回流", -1)
                              ]))]),
                              _: 1
                            }, 8, ["onClick"]),
                            _createVNode(_component_v_btn, {
                              size: "small",
                              variant: "text",
                              "prepend-icon": "mdi-eye-off",
                              onClick: $event => (ignoreIssue(item))
                            }, {
                              default: _withCtx(() => [...(_cache[102] || (_cache[102] = [
                                _createTextVNode("忽略", -1)
                              ]))]),
                              _: 1
                            }, 8, ["onClick"])
                          ])
                        ]),
                        default: _withCtx(() => [
                          _createVNode(_component_v_list_item_title, null, {
                            default: _withCtx(() => [
                              _createTextVNode(_toDisplayString(item.title), 1)
                            ]),
                            _: 2
                          }, 1024),
                          _createVNode(_component_v_list_item_subtitle, null, {
                            default: _withCtx(() => [
                              _createTextVNode("识别：" + _toDisplayString(item.media_title || '-') + " / " + _toDisplayString(item.media_type || '-') + " / " + _toDisplayString(item.media_category || '-') + "｜" + _toDisplayString(item.issue_reason || item.reason), 1)
                            ]),
                            _: 2
                          }, 1024),
                          _createElementVNode("div", _hoisted_41, _toDisplayString(item.suggestion), 1)
                        ]),
                        _: 2
                      }, 1024))
                    }), 128)),
                    (!openIssues.value.length)
                      ? (_openBlock(), _createBlock(_component_v_list_item, {
                          key: 0,
                          title: "暂无待处理异常",
                          subtitle: "刷新 RSS 后，如有识别失败或非动画识别，会显示在这里。"
                        }))
                      : _createCommentVNode("", true)
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  variant: "text",
                  onClick: _cache[35] || (_cache[35] = $event => (showIssuesDialog.value=false))
                }, {
                  default: _withCtx(() => [...(_cache[103] || (_cache[103] = [
                    _createTextVNode("关闭", -1)
                  ]))]),
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
    }, 8, ["modelValue"]),
    _createVNode(_component_v_dialog, {
      modelValue: showIssuePreviewDialog.value,
      "onUpdate:modelValue": _cache[38] || (_cache[38] = $event => ((showIssuePreviewDialog).value = $event)),
      "max-width": "760",
      scrollable: ""
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, null, {
              default: _withCtx(() => [...(_cache[104] || (_cache[104] = [
                _createTextVNode("识别词预览", -1)
              ]))]),
              _: 1
            }),
            (issuePreview.value)
              ? (_openBlock(), _createBlock(_component_v_card_text, { key: 0 }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_alert, {
                      type: "warning",
                      variant: "tonal",
                      class: "mb-3"
                    }, {
                      default: _withCtx(() => [...(_cache[105] || (_cache[105] = [
                        _createTextVNode("写入前会保存当前自定义识别词快照；规则已按当前异常标题锚定，避免影响无关资源。", -1)
                      ]))]),
                      _: 1
                    }),
                    _createVNode(_component_v_textarea, {
                      "model-value": issuePreview.value.identifier,
                      label: "将写入的识别词",
                      readonly: "",
                      rows: "3"
                    }, null, 8, ["model-value"]),
                    _createElementVNode("div", _hoisted_43, "目标：" + _toDisplayString(issuePreview.value.target?.title || '-') + " / TMDB " + _toDisplayString(issuePreview.value.target?.tmdbid || '-') + " / S" + _toDisplayString(issuePreview.value.target?.season || 1), 1),
                    (issuePreview.value.exists)
                      ? (_openBlock(), _createBlock(_component_v_chip, {
                          key: 0,
                          color: "info",
                          variant: "tonal",
                          class: "mt-2"
                        }, {
                          default: _withCtx(() => [...(_cache[106] || (_cache[106] = [
                            _createTextVNode("该识别词已存在", -1)
                          ]))]),
                          _: 1
                        }))
                      : _createCommentVNode("", true)
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  variant: "text",
                  onClick: _cache[37] || (_cache[37] = $event => (showIssuePreviewDialog.value=false))
                }, {
                  default: _withCtx(() => [...(_cache[107] || (_cache[107] = [
                    _createTextVNode("取消", -1)
                  ]))]),
                  _: 1
                }),
                _createVNode(_component_v_btn, {
                  color: "primary",
                  variant: "tonal",
                  onClick: applyIssueIdentifier
                }, {
                  default: _withCtx(() => [...(_cache[108] || (_cache[108] = [
                    _createTextVNode("写入并回流候选", -1)
                  ]))]),
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
    }, 8, ["modelValue"]),
    _createVNode(_component_v_dialog, {
      modelValue: showIssueAgentDialog.value,
      "onUpdate:modelValue": _cache[40] || (_cache[40] = $event => ((showIssueAgentDialog).value = $event)),
      "max-width": "820",
      scrollable: ""
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, null, {
              default: _withCtx(() => [...(_cache[109] || (_cache[109] = [
                _createTextVNode("调用智能体处理提示", -1)
              ]))]),
              _: 1
            }),
            (issueAgentHint.value)
              ? (_openBlock(), _createBlock(_component_v_card_text, { key: 0 }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_alert, {
                      type: "info",
                      variant: "tonal",
                      class: "mb-3"
                    }, {
                      default: _withCtx(() => [...(_cache[110] || (_cache[110] = [
                        _createTextVNode("智能体高置信时可直接自动写入窄作用域识别词并回流候选；下面保留提示与写入结果供核对。", -1)
                      ]))]),
                      _: 1
                    }),
                    _createVNode(_component_v_textarea, {
                      "model-value": issueAgentHint.value.prompt,
                      label: "智能体提示",
                      readonly: "",
                      rows: "12"
                    }, null, 8, ["model-value"]),
                    (issueAgentHint.value.suggested_identifier)
                      ? (_openBlock(), _createBlock(_component_v_textarea, {
                          key: 0,
                          "model-value": issueAgentHint.value.suggested_identifier,
                          label: "当前建议识别词",
                          readonly: "",
                          rows: "2",
                          class: "mt-3"
                        }, null, 8, ["model-value"]))
                      : _createCommentVNode("", true),
                    (issueAgentHint.value.applied)
                      ? (_openBlock(), _createBlock(_component_v_alert, {
                          key: 1,
                          type: "success",
                          variant: "tonal",
                          class: "mt-3"
                        }, {
                          default: _withCtx(() => [
                            _createTextVNode(_toDisplayString(issueAgentHint.value.applied.message || '已自动写入'), 1)
                          ]),
                          _: 1
                        }))
                      : _createCommentVNode("", true)
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  variant: "text",
                  onClick: _cache[39] || (_cache[39] = $event => (showIssueAgentDialog.value=false))
                }, {
                  default: _withCtx(() => [...(_cache[111] || (_cache[111] = [
                    _createTextVNode("关闭", -1)
                  ]))]),
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
    }, 8, ["modelValue"]),
    _createVNode(_component_v_dialog, {
      modelValue: showConfigDialog.value,
      "onUpdate:modelValue": _cache[42] || (_cache[42] = $event => ((showConfigDialog).value = $event)),
      "max-width": "960",
      scrollable: ""
    }, {
      default: _withCtx(() => [
        _createVNode(_sfc_main$1, {
          "initial-config": currentConfig.value,
          onSave: saveConfigDialog,
          onClose: _cache[41] || (_cache[41] = $event => (showConfigDialog.value=false))
        }, null, 8, ["initial-config"])
      ]),
      _: 1
    }, 8, ["modelValue"]),
    _createVNode(_component_v_dialog, {
      modelValue: showConfirmDialog.value,
      "onUpdate:modelValue": _cache[45] || (_cache[45] = $event => ((showConfirmDialog).value = $event)),
      "max-width": "460",
      persistent: ""
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, { rounded: "lg" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "d-flex align-center ga-2" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  color: confirmState.value.color,
                  icon: "mdi-alert-circle-outline"
                }, null, 8, ["color"]),
                _createElementVNode("span", null, _toDisplayString(confirmState.value.title), 1)
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_text, { style: {"white-space":"pre-line"} }, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(confirmState.value.message), 1)
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  variant: "text",
                  onClick: _cache[43] || (_cache[43] = $event => (closeConfirm(false)))
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(confirmState.value.cancelText), 1)
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_btn, {
                  color: confirmState.value.color,
                  variant: "tonal",
                  onClick: _cache[44] || (_cache[44] = $event => (closeConfirm(true)))
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(confirmState.value.confirmText), 1)
                  ]),
                  _: 1
                }, 8, ["color"])
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"]),
    _createVNode(_component_v_dialog, {
      modelValue: showGroupDialog.value,
      "onUpdate:modelValue": _cache[48] || (_cache[48] = $event => ((showGroupDialog).value = $event)),
      "max-width": "420"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, null, {
              default: _withCtx(() => [...(_cache[112] || (_cache[112] = [
                _createTextVNode("设置发布组标记", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_text_field, {
                  modelValue: groupInput.value,
                  "onUpdate:modelValue": _cache[46] || (_cache[46] = $event => ((groupInput).value = $event)),
                  label: "发布组，如 ANi / 喵萌奶茶屋"
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  variant: "text",
                  onClick: _cache[47] || (_cache[47] = $event => (showGroupDialog.value=false))
                }, {
                  default: _withCtx(() => [...(_cache[113] || (_cache[113] = [
                    _createTextVNode("取消", -1)
                  ]))]),
                  _: 1
                }),
                _createVNode(_component_v_btn, {
                  color: "primary",
                  onClick: saveGroup
                }, {
                  default: _withCtx(() => [...(_cache[114] || (_cache[114] = [
                    _createTextVNode("保存", -1)
                  ]))]),
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
    }, 8, ["modelValue"])
  ]))
}
}

};
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-eedc367f"]]);

export { Page as default };
