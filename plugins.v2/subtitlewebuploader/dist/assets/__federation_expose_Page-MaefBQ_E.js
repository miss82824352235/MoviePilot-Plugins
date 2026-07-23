import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

/**
 * 字幕网页上传器 API 客户端。
 * 优先使用 MP 注入的 api，失败时回退到相对路径 fetch。
 */

const PLUGIN = 'SubtitleWebUploader';
const BASE = `plugin/${PLUGIN}/subtitleweb_bridge`;

function unwrap(res) {
  if (res == null) return res
  // MP 标准 Response 或插件 ok/fail
  if (typeof res === 'object') {
    if (Object.prototype.hasOwnProperty.call(res, 'success') && res.success === false) {
      const err = new Error(res.message || '请求失败');
      err.response = res;
      err.needConfirm = !!(res.data && res.data.need_confirm);
      throw err
    }
    if (Object.prototype.hasOwnProperty.call(res, 'code') && res.code !== 0) {
      const err = new Error(res.message || '请求失败');
      err.response = res;
      err.code = res.code;
      err.needConfirm = !!(res.data && res.data.need_confirm);
      throw err
    }
    if (Object.prototype.hasOwnProperty.call(res, 'data')) return res.data
  }
  return res
}

function createPluginApi(api) {
  async function get(path, params = {}) {
    const qs = new URLSearchParams();
    Object.entries(params || {}).forEach(([k, v]) => {
      if (v === undefined || v === null || v === '') return
      qs.set(k, String(v));
    });
    const suffix = qs.toString() ? `?${qs}` : '';
    if (api && typeof api.get === 'function') {
      return unwrap(await api.get(`${BASE}/${path}${suffix}`))
    }
    const r = await fetch(`/api/v1/${BASE}/${path}${suffix}`, { credentials: 'include' });
    return unwrap(await r.json())
  }

  async function post(path, body = {}) {
    if (api && typeof api.post === 'function') {
      return unwrap(await api.post(`${BASE}/${path}`, body))
    }
    const r = await fetch(`/api/v1/${BASE}/${path}`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {}),
    });
    return unwrap(await r.json())
  }

  async function postForm(path, formData) {
    if (api && typeof api.post === 'function') {
      // 部分 MP api 客户端支持 FormData
      try {
        return unwrap(await api.post(`${BASE}/${path}`, formData))
      } catch (e) {
        // fall through
      }
    }
    const r = await fetch(`/api/v1/${BASE}/${path}`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    });
    return unwrap(await r.json())
  }

  return {
    status: () => get('status'),
    search: (keyword, mediaType = '') => get('search', { keyword, type: mediaType }),
    targets: (params) => get('targets', params),
    history: (params) => get('history', params),
    getSelection: (userId = 'web') => get('selection', { user_id: userId }),
    saveSelection: (payload) => post('selection/save', payload),
    uploadPrepare: (formData) => postForm('upload/prepare', formData),
    uploadApply: (payload) => post('upload/apply', { ...payload, confirm: true }),
    deletePreview: (payload) => post('delete/preview', payload),
    deleteApply: (payload) => post('delete/apply', { ...payload, confirm: true }),
    clearPreview: (payload) => post('clear/preview', payload),
    clearApply: (payload) => post('clear/apply', { ...payload, confirm: true }),
    aiPreview: (payload) => post('ai/preview', payload),
    aiSubmit: (payload) => post('ai/submit', { ...payload, confirm: true }),
    aiCancel: (payload) => post('ai/cancel', { ...payload, confirm: true }),
    aiRestart: (payload) => post('ai/restart', { ...payload, confirm: true }),
    onlineAiSubmit: (payload) => post('online_ai/submit', { ...payload, confirm: true }),
    restore: (payload) => post('restore', { ...payload, confirm: true }),
    tasks: (payload) => post('tasks', payload || {}),
    timelineFix: (payload) => post('timeline/fix', { ...payload, confirm: true }),
    onlineSearch: (payload) => post('online/search', payload),
    onlineDownloadPreview: (payload) => post('online/download_preview', payload),
  }
}

const {createElementVNode:_createElementVNode,openBlock:_openBlock,createElementBlock:_createElementBlock,createCommentVNode:_createCommentVNode,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,withKeys:_withKeys,renderList:_renderList,Fragment:_Fragment,normalizeClass:_normalizeClass,withModifiers:_withModifiers,vModelCheckbox:_vModelCheckbox,withDirectives:_withDirectives,mergeProps:_mergeProps} = await importShared('vue');


const _hoisted_1 = {
  class: "swu-page",
  "data-revision": "v0.6.0-bridge-workbench"
};
const _hoisted_2 = { class: "swu-hero" };
const _hoisted_3 = { class: "swu-hero-main" };
const _hoisted_4 = { class: "swu-sub" };
const _hoisted_5 = { key: 0 };
const _hoisted_6 = { key: 1 };
const _hoisted_7 = {
  key: 2,
  class: "text-error"
};
const _hoisted_8 = { class: "swu-hero-meta" };
const _hoisted_9 = { class: "swu-row" };
const _hoisted_10 = {
  key: 0,
  class: "swu-media-list"
};
const _hoisted_11 = ["onClick"];
const _hoisted_12 = { class: "name" };
const _hoisted_13 = { class: "meta" };
const _hoisted_14 = {
  key: 1,
  class: "swu-empty"
};
const _hoisted_15 = { class: "swu-muted" };
const _hoisted_16 = { class: "swu-select-bar" };
const _hoisted_17 = {
  key: 0,
  class: "swu-empty"
};
const _hoisted_18 = {
  key: 1,
  class: "swu-empty"
};
const _hoisted_19 = {
  key: 2,
  class: "swu-target-grid"
};
const _hoisted_20 = ["onClick"];
const _hoisted_21 = { class: "ep" };
const _hoisted_22 = { class: "name" };
const _hoisted_23 = { class: "meta" };
const _hoisted_24 = { class: "swu-context-bar" };
const _hoisted_25 = { class: "swu-actions-grid" };
const _hoisted_26 = {
  key: 0,
  class: "swu-file-list"
};
const _hoisted_27 = { class: "swu-btn-row" };
const _hoisted_28 = {
  key: 1,
  class: "swu-preview"
};
const _hoisted_29 = { class: "swu-btn-row" };
const _hoisted_30 = {
  key: 0,
  class: "swu-empty"
};
const _hoisted_31 = {
  key: 1,
  class: "swu-online-list"
};
const _hoisted_32 = ["value"];
const _hoisted_33 = { class: "name" };
const _hoisted_34 = { class: "meta" };
const _hoisted_35 = { class: "swu-btn-row" };
const _hoisted_36 = {
  key: 0,
  class: "swu-empty"
};
const _hoisted_37 = {
  key: 1,
  class: "swu-online-list"
};
const _hoisted_38 = ["value"];
const _hoisted_39 = { class: "name" };
const _hoisted_40 = { class: "meta" };
const _hoisted_41 = { class: "swu-ai-fields" };
const _hoisted_42 = { class: "swu-btn-row" };
const _hoisted_43 = {
  key: 0,
  class: "swu-preview"
};
const _hoisted_44 = {
  key: 1,
  class: "swu-task-list"
};
const _hoisted_45 = { class: "swu-task-head" };
const _hoisted_46 = { class: "swu-muted" };
const _hoisted_47 = { class: "swu-muted swu-task-msg" };
const _hoisted_48 = {
  key: 0,
  class: "swu-empty"
};
const _hoisted_49 = { class: "swu-bottom-bar" };
const _hoisted_50 = { class: "swu-bottom-info" };
const _hoisted_51 = { class: "swu-bottom-actions" };

const {computed,onMounted,onUnmounted,ref,watch} = await importShared('vue');


const _sfc_main = {
  __name: 'Page',
  props: {
  api: { type: Object, default: null },
  pluginId: { type: String, default: 'SubtitleWebUploader' },
},
  setup(__props) {

const props = __props;

const client = createPluginApi(props.api);

const toast = ref({ show: false, text: '', color: 'success' });
const logs = ref([]);
const statusLoading = ref(false);
const bridgeLabel = ref('');
const keyword = ref('');
const searching = ref(false);
const searched = ref(false);
const mediaList = ref([]);
const currentMedia = ref(null);
const targets = ref([]);
const loadingTargets = ref(false);
const selectedIds = ref([]);
const rangeText = ref('');
const files = ref([]);
const fileInput = ref(null);
const dragging = ref(false);
const uploading = ref(false);
const applying = ref(false);
const uploadSession = ref(null);
const uploadPreviewText = ref('');
const onlineSearching = ref(false);
const onlinePreviewing = ref(false);
const onlineAiLoading = ref(false);
const onlineResults = ref([]);
const selectedOnline = ref([]);
const historyLoading = ref(false);
const historyItems = ref([]);
const selectedSubs = ref([]);
const timelineLoading = ref(false);
const sourcePolicy = ref('auto');
const overwritePolicy = ref('skip');
const sourceSubtitlePath = ref('');
const aiPreviewing = ref(false);
const aiSubmitting = ref(false);
const aiRestarting = ref(false);
const aiPreviewText = ref('');
const taskLoading = ref(false);
const taskList = ref([]);
let pollTimer = null;

const sourcePolicyItems = [
  { title: '自动选择源', value: 'auto' },
  { title: '仅外挂字幕', value: 'local_external' },
  { title: '仅内嵌字幕', value: 'embedded' },
  { title: '指定外挂路径', value: 'matched_external' },
  { title: 'ASR 语音识别', value: 'asr' },
];

const overwritePolicyItems = [
  { title: '已有则跳过', value: 'skip' },
  { title: '新变体并存', value: 'new_variant' },
  { title: '备份后替换', value: 'backup_replace' },
  { title: '直接覆盖', value: 'overwrite' },
];

const canUpload = computed(() => selectedIds.value.length > 0 && files.value.length > 0);

watch(sourcePolicy, (v) => {
  if (v === 'auto' && overwritePolicy.value === 'new_variant') overwritePolicy.value = 'skip';
  if (v !== 'auto' && overwritePolicy.value === 'skip') overwritePolicy.value = 'new_variant';
});

function notify(text, color = 'success') {
  toast.value = { show: true, text, color };
  logs.value.unshift(`[${new Date().toLocaleTimeString()}] ${text}`);
  if (logs.value.length > 40) logs.value.pop();
}

function mediaKey(m) {
  return [m.tmdbid || m.tmdb_id || '', m.type || m.media_type || '', m.title || m.name || ''].join('|')
}
function mediaTypeLabel(m) {
  const t = String(m.type || m.media_type || '').toLowerCase();
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
  const name = t.filename || t.name || t.path || '';
  const m = name.match(/[Ss](\d+)[Ee](\d+)/);
  if (m) return `S${m[1]}E${m[2]}`
  return t.season != null ? `S${t.season}` : '目标'
}
function shortName(t) {
  const n = t.filename || t.name || t.path || '未命名';
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
  const p = task?.progress?.percent ?? task?.progress_percent;
  const n = Number(p);
  if (Number.isFinite(n)) return Math.max(0, Math.min(100, n))
  const st = String(task?.status || '').toLowerCase();
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
  statusLoading.value = true;
  try {
    const data = await client.status();
    const name = data.bridge_plugin_name || data.plugin_name || data.bridge_target || '';
    const ver = data.bridge_plugin_version || data.plugin_version || data.version || '';
    const mode = data.bridge_mode || '';
    bridgeLabel.value = [name, ver].filter(Boolean).join(' ') + (mode ? ` (${mode})` : '');
    if (!name && data.message) bridgeLabel.value = data.message;
  } catch (e) {
    bridgeLabel.value = '';
    notify(e.message || '桥接状态失败', 'error');
  } finally {
    statusLoading.value = false;
  }
}

async function doSearch() {
  searching.value = true;
  searched.value = true;
  try {
    const data = await client.search(keyword.value || '');
    mediaList.value = data.items || data.results || data.medias || data || [];
    if (!Array.isArray(mediaList.value)) mediaList.value = [];
    notify(`找到 ${mediaList.value.length} 条结果`);
  } catch (e) {
    mediaList.value = [];
    notify(e.message || '搜索失败', 'error');
  } finally {
    searching.value = false;
  }
}

async function selectMedia(m) {
  currentMedia.value = m;
  selectedIds.value = [];
  await reloadTargets();
  try {
    await client.saveSelection({
      user_id: 'web',
      media: m,
      target_ids: selectedIds.value,
    });
  } catch (_) {
    /* ignore */
  }
}

async function reloadTargets() {
  if (!currentMedia.value) {
    targets.value = [];
    return
  }
  loadingTargets.value = true;
  try {
    const m = currentMedia.value;
    const data = await client.targets({
      tmdbid: m.tmdbid || m.tmdb_id || '',
      type: m.type || m.media_type || '',
      season: m.season || '',
      title: m.title || m.name || '',
      media_id: m.media_id || m.id || '',
    });
    targets.value = data.targets || data.items || data || [];
    if (!Array.isArray(targets.value)) targets.value = [];
  } catch (e) {
    targets.value = [];
    notify(e.message || '加载目标失败', 'error');
  } finally {
    loadingTargets.value = false;
  }
}

function toggleTarget(t) {
  const id = targetId(t);
  if (!id) return
  const i = selectedIds.value.indexOf(id);
  if (i >= 0) selectedIds.value.splice(i, 1);
  else selectedIds.value.push(id);
}
function selectAll() {
  selectedIds.value = targets.value.map(targetId).filter(Boolean);
  notify(`已全选当前目标 ${selectedIds.value.length} 个`);
}
function invertSelect() {
  const all = new Set(targets.value.map(targetId).filter(Boolean));
  const cur = new Set(selectedIds.value);
  selectedIds.value = [...all].filter((id) => !cur.has(id));
  notify('已反选当前目标');
}
function clearSelect() {
  selectedIds.value = [];
  notify('已清空选择');
}
function applyRange() {
  const text = (rangeText.value || '').trim();
  if (!text) {
    notify('请输入集数范围', 'warning');
    return
  }
  const wanted = new Set();
  text.split(/[,，\s]+/).forEach((part) => {
    const m = part.match(/^(\d+)\s*[-~～]\s*(\d+)$/);
    if (m) {
      const a = Number(m[1]);
      const b = Number(m[2]);
      for (let i = Math.min(a, b); i <= Math.max(a, b); i++) wanted.add(i);
    } else if (/^\d+$/.test(part)) wanted.add(Number(part));
  });
  const next = [];
  targets.value.forEach((t) => {
    const ep = Number(t.episode ?? t.ep);
    if (wanted.has(ep)) next.push(targetId(t));
  });
  selectedIds.value = next.filter(Boolean);
  notify(`已按范围选择 ${selectedIds.value.length} 个`);
}

function onFilePick(e) {
  const list = Array.from(e.target.files || []);
  files.value = [...files.value, ...list];
  e.target.value = '';
}
function onDrop(e) {
  dragging.value = false;
  const list = Array.from(e.dataTransfer?.files || []);
  files.value = [...files.value, ...list];
}

async function prepareUpload() {
  if (!canUpload.value) {
    notify('请先选集数并选择字幕文件', 'warning');
    return
  }
  uploading.value = true;
  uploadSession.value = null;
  uploadPreviewText.value = '';
  try {
    const fd = new FormData();
    fd.append('target_ids', JSON.stringify(selectedIds.value));
    files.value.forEach((f) => fd.append('files', f));
    fd.append('fix_timeline', 'true');
    fd.append('user_id', 'web');
    const data = await client.uploadPrepare(fd);
    uploadSession.value = data.session_id || data.session || data.upload_session || data;
    const count = data.preview_count || (data.previews || data.items || []).length || files.value.length;
    uploadPreviewText.value = data.message || `预览已生成：约 ${count} 条匹配`;
    notify(uploadPreviewText.value);
  } catch (e) {
    notify(e.message || '生成预览失败', 'error');
  } finally {
    uploading.value = false;
  }
}

async function applyUpload() {
  if (!uploadSession.value) {
    notify('请先生成匹配预览', 'warning');
    return
  }
  applying.value = true;
  try {
    const session =
      typeof uploadSession.value === 'string'
        ? { session_id: uploadSession.value }
        : uploadSession.value;
    const data = await client.uploadApply({
      ...session,
      target_ids: selectedIds.value,
      confirm: true,
      fix_timeline: true,
    });
    notify(data.message || '上传完成');
    files.value = [];
    uploadSession.value = null;
    await loadHistory();
  } catch (e) {
    notify(e.message || '上传失败', 'error');
  } finally {
    applying.value = false;
  }
}

async function searchOnline() {
  if (!selectedIds.value.length) {
    notify('请先选集数', 'warning');
    return
  }
  onlineSearching.value = true;
  onlineResults.value = [];
  selectedOnline.value = [];
  try {
    const data = await client.onlineSearch({ target_ids: selectedIds.value });
    onlineResults.value = data.results || data.items || data.candidates || [];
    if (!Array.isArray(onlineResults.value)) onlineResults.value = [];
    notify(`在线结果 ${onlineResults.value.length} 条`);
  } catch (e) {
    notify(e.message || '在线搜索失败', 'error');
  } finally {
    onlineSearching.value = false;
  }
}

async function previewOnline() {
  if (!selectedOnline.value.length) {
    notify('请先勾选在线字幕', 'warning');
    return
  }
  onlinePreviewing.value = true;
  try {
    const data = await client.onlineDownloadPreview({
      target_ids: selectedIds.value,
      results: selectedOnline.value,
    });
    notify(data.message || '在线字幕预览好了');
  } catch (e) {
    notify(e.message || '在线预览失败', 'error');
  } finally {
    onlinePreviewing.value = false;
  }
}

async function submitOnlineAi() {
  if (!selectedOnline.value.length || !selectedIds.value.length) {
    notify('请先选集数并勾选在线字幕', 'warning');
    return
  }
  if (!window.confirm(`将把 ${selectedOnline.value.length} 条在线字幕提交为 AI 翻译，确认？`)) return
  onlineAiLoading.value = true;
  try {
    const data = await client.onlineAiSubmit({
      target_ids: selectedIds.value,
      results: selectedOnline.value,
      confirm: true,
    });
    notify(data.message || '已提交在线→AI 任务');
    startTaskPoll();
  } catch (e) {
    notify(e.message || '在线→AI 失败', 'error');
  } finally {
    onlineAiLoading.value = false;
  }
}

async function loadHistory() {
  if (!selectedIds.value.length) {
    notify('请先选集数', 'warning');
    return
  }
  historyLoading.value = true;
  try {
    const data = await client.history({ target_ids: selectedIds.value.join(',') });
    historyItems.value = data.items || data.histories || data.subtitles || data || [];
    if (!Array.isArray(historyItems.value)) historyItems.value = [];
    selectedSubs.value = [];
    notify(`读取到 ${historyItems.value.length} 条外挂/历史`);
  } catch (e) {
    historyItems.value = [];
    notify(e.message || '刷新外挂失败', 'error');
  } finally {
    historyLoading.value = false;
  }
}

async function fixTimeline() {
  if (!selectedSubs.value.length) {
    notify('请先勾选字幕', 'warning');
    return
  }
  if (!window.confirm(`将对 ${selectedSubs.value.length} 条外挂执行调轴，确认？`)) return
  timelineLoading.value = true;
  try {
    const data = await client.timelineFix({
      target_ids: selectedIds.value,
      items: selectedSubs.value,
      confirm: true,
    });
    notify(data.message || '已提交时间轴处理');
  } catch (e) {
    notify(e.message || '调轴失败', 'error');
  } finally {
    timelineLoading.value = false;
  }
}

async function deleteSelected() {
  if (!selectedSubs.value.length) {
    notify('请先勾选字幕', 'warning');
    return
  }
  if (!window.confirm(`删除选中的 ${selectedSubs.value.length} 条外挂字幕？此操作不可撤销。`)) return
  try {
    const data = await client.deleteApply({
      target_ids: selectedIds.value,
      items: selectedSubs.value,
      confirm: true,
    });
    notify(data.message || '删除完成');
    await loadHistory();
  } catch (e) {
    notify(e.message || '删除失败', 'error');
  }
}

async function restoreSelected() {
  if (!selectedSubs.value.length) {
    notify('请先勾选字幕', 'warning');
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
    });
    notify(data.message || '恢复完成');
    await loadHistory();
  } catch (e) {
    notify(e.message || '恢复失败', 'error');
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
    notify('请先选集数', 'warning');
    return
  }
  aiPreviewing.value = true;
  try {
    const data = await client.aiPreview(aiPayload());
    aiPreviewText.value = data.message || `将提交 ${selectedIds.value.length} 个目标`;
    notify(aiPreviewText.value);
  } catch (e) {
    notify(e.message || 'AI 预检失败', 'error');
  } finally {
    aiPreviewing.value = false;
  }
}

async function submitAi() {
  if (!selectedIds.value.length) {
    notify('请先选集数', 'warning');
    return
  }
  if (!window.confirm(`提交 ${selectedIds.value.length} 个目标的 AI 任务？\n源=${sourcePolicy.value} 覆盖=${overwritePolicy.value}`))
    return
  aiSubmitting.value = true;
  try {
    const data = await client.aiSubmit({ ...aiPayload(), confirm: true });
    notify(data.message || '已提交 AI 任务');
    startTaskPoll();
  } catch (e) {
    notify(e.message || '提交 AI 失败', 'error');
  } finally {
    aiSubmitting.value = false;
  }
}

async function restartAi() {
  if (!selectedIds.value.length) {
    notify('请先选集数', 'warning');
    return
  }
  if (!window.confirm(`重做 ${selectedIds.value.length} 个目标的 AI 字幕（默认 reuse + 备份替换）？`)) return
  aiRestarting.value = true;
  try {
    const data = await client.aiRestart({
      target_ids: selectedIds.value,
      source_policy: 'reuse',
      overwrite_policy: 'backup_replace',
      source_subtitle_path: sourceSubtitlePath.value || undefined,
      confirm: true,
    });
    notify(data.message || '已提交 AI 重做');
    startTaskPoll();
  } catch (e) {
    notify(e.message || 'AI 重做失败', 'error');
  } finally {
    aiRestarting.value = false;
  }
}

async function cancelAi() {
  if (!selectedIds.value.length) {
    notify('请先选集数', 'warning');
    return
  }
  if (!window.confirm(`取消选中目标的 AI 任务？不会删除外挂字幕。`)) return
  try {
    const data = await client.aiCancel({ target_ids: selectedIds.value, confirm: true });
    notify(data.message || '任务已取消');
    await loadTasks();
  } catch (e) {
    notify(e.message || '取消失败', 'error');
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
  taskLoading.value = true;
  try {
    const data = await client.tasks({ target_ids: selectedIds.value, limit: 50 });
    taskList.value = extractTasks(data);
    notify(`任务状态已刷新：${taskList.value.length} 条`);
  } catch (e) {
    notify(e.message || '查询任务失败', 'error');
  } finally {
    taskLoading.value = false;
  }
}

function startTaskPoll() {
  loadTasks();
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(() => {
    if (selectedIds.value.length) loadTasks();
  }, 8000);
}

onMounted(() => {
  refreshStatus();
});
onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer);
});

return (_ctx, _cache) => {
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_snackbar = _resolveComponent("v-snackbar");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_select = _resolveComponent("v-select");
  const _component_v_progress_linear = _resolveComponent("v-progress-linear");
  const _component_v_list_item = _resolveComponent("v-list-item");
  const _component_v_list = _resolveComponent("v-list");
  const _component_v_menu = _resolveComponent("v-menu");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createElementVNode("div", _hoisted_2, [
      _createElementVNode("div", _hoisted_3, [
        _cache[13] || (_cache[13] = _createElementVNode("div", { class: "swu-title" }, "字幕控制台", -1)),
        _createElementVNode("div", _hoisted_4, [
          (statusLoading.value)
            ? (_openBlock(), _createElementBlock("span", _hoisted_5, "桥接加载中…"))
            : (bridgeLabel.value)
              ? (_openBlock(), _createElementBlock("span", _hoisted_6, "已连接：" + _toDisplayString(bridgeLabel.value), 1))
              : (_openBlock(), _createElementBlock("span", _hoisted_7, "桥接异常，请确认字幕匹配魔改版已启用"))
        ])
      ]),
      _createElementVNode("div", _hoisted_8, [
        _createVNode(_component_v_chip, {
          size: "small",
          color: selectedIds.value.length ? 'primary' : 'default',
          variant: "tonal"
        }, {
          default: _withCtx(() => [
            _createTextVNode(" 已选 " + _toDisplayString(selectedIds.value.length) + " 个目标 ", 1)
          ]),
          _: 1
        }, 8, ["color"]),
        _createVNode(_component_v_chip, {
          size: "small",
          variant: "tonal"
        }, {
          default: _withCtx(() => [
            _createTextVNode("待上传 " + _toDisplayString(files.value.length) + " 个文件", 1)
          ]),
          _: 1
        }),
        _createVNode(_component_v_btn, {
          size: "small",
          variant: "text",
          loading: statusLoading.value,
          onClick: refreshStatus
        }, {
          default: _withCtx(() => [...(_cache[14] || (_cache[14] = [
            _createTextVNode("刷新", -1)
          ]))]),
          _: 1
        }, 8, ["loading"])
      ])
    ]),
    _createVNode(_component_v_snackbar, {
      modelValue: toast.value.show,
      "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((toast.value.show) = $event)),
      color: toast.value.color,
      timeout: 3200,
      location: "top"
    }, {
      default: _withCtx(() => [
        _createTextVNode(_toDisplayString(toast.value.text), 1)
      ]),
      _: 1
    }, 8, ["modelValue", "color"]),
    _createVNode(_component_v_card, {
      class: "swu-card",
      variant: "tonal",
      rounded: "lg"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card_title, { class: "swu-card-title" }, {
          default: _withCtx(() => [...(_cache[15] || (_cache[15] = [
            _createTextVNode("找影片", -1)
          ]))]),
          _: 1
        }),
        _createVNode(_component_v_card_text, null, {
          default: _withCtx(() => [
            _createElementVNode("div", _hoisted_9, [
              _createVNode(_component_v_text_field, {
                modelValue: keyword.value,
                "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((keyword).value = $event)),
                label: "搜索本地媒体",
                density: "comfortable",
                variant: "outlined",
                "hide-details": "",
                clearable: "",
                onKeyup: _withKeys(doSearch, ["enter"])
              }, null, 8, ["modelValue"]),
              _createVNode(_component_v_btn, {
                color: "primary",
                loading: searching.value,
                onClick: doSearch
              }, {
                default: _withCtx(() => [...(_cache[16] || (_cache[16] = [
                  _createTextVNode("搜索", -1)
                ]))]),
                _: 1
              }, 8, ["loading"])
            ]),
            (mediaList.value.length)
              ? (_openBlock(), _createElementBlock("div", _hoisted_10, [
                  (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(mediaList.value, (m) => {
                    return (_openBlock(), _createElementBlock("button", {
                      key: mediaKey(m),
                      type: "button",
                      class: _normalizeClass(["swu-media-item", { active: currentMedia.value && mediaKey(currentMedia.value) === mediaKey(m) }]),
                      onClick: $event => (selectMedia(m))
                    }, [
                      _createElementVNode("div", _hoisted_12, _toDisplayString(m.title || m.name || '未命名'), 1),
                      _createElementVNode("div", _hoisted_13, _toDisplayString(m.year || '未知年份') + " · " + _toDisplayString(mediaTypeLabel(m)) + " · 目标 " + _toDisplayString(m.target_count || m.count || '?'), 1)
                    ], 10, _hoisted_11))
                  }), 128))
                ]))
              : (searched.value)
                ? (_openBlock(), _createElementBlock("div", _hoisted_14, "暂无结果，换个关键词试试"))
                : _createCommentVNode("", true)
          ]),
          _: 1
        })
      ]),
      _: 1
    }),
    _createVNode(_component_v_card, {
      class: "swu-card",
      variant: "tonal",
      rounded: "lg"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card_title, { class: "swu-card-title" }, {
          default: _withCtx(() => [
            _cache[17] || (_cache[17] = _createElementVNode("span", null, "选集数", -1)),
            _createElementVNode("span", _hoisted_15, _toDisplayString(currentMedia.value ? (currentMedia.value.title || currentMedia.value.name) : '先选择影片'), 1)
          ]),
          _: 1
        }),
        _createVNode(_component_v_card_text, null, {
          default: _withCtx(() => [
            _createElementVNode("div", _hoisted_16, [
              _createVNode(_component_v_btn, {
                size: "small",
                variant: "tonal",
                disabled: !targets.value.length,
                onClick: selectAll
              }, {
                default: _withCtx(() => [...(_cache[18] || (_cache[18] = [
                  _createTextVNode("全选", -1)
                ]))]),
                _: 1
              }, 8, ["disabled"]),
              _createVNode(_component_v_btn, {
                size: "small",
                variant: "tonal",
                disabled: !targets.value.length,
                onClick: invertSelect
              }, {
                default: _withCtx(() => [...(_cache[19] || (_cache[19] = [
                  _createTextVNode("反选", -1)
                ]))]),
                _: 1
              }, 8, ["disabled"]),
              _createVNode(_component_v_btn, {
                size: "small",
                variant: "text",
                disabled: !selectedIds.value.length,
                onClick: clearSelect
              }, {
                default: _withCtx(() => [...(_cache[20] || (_cache[20] = [
                  _createTextVNode("清空", -1)
                ]))]),
                _: 1
              }, 8, ["disabled"]),
              _createVNode(_component_v_text_field, {
                modelValue: rangeText.value,
                "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((rangeText).value = $event)),
                class: "swu-range",
                density: "compact",
                variant: "outlined",
                "hide-details": "",
                label: "快速选择 1-12 / 1,3,5",
                onKeyup: _withKeys(applyRange, ["enter"])
              }, null, 8, ["modelValue"]),
              _createVNode(_component_v_btn, {
                size: "small",
                variant: "tonal",
                disabled: !targets.value.length,
                onClick: applyRange
              }, {
                default: _withCtx(() => [...(_cache[21] || (_cache[21] = [
                  _createTextVNode("按范围", -1)
                ]))]),
                _: 1
              }, 8, ["disabled"]),
              _createVNode(_component_v_btn, {
                size: "small",
                variant: "text",
                loading: loadingTargets.value,
                onClick: reloadTargets
              }, {
                default: _withCtx(() => [...(_cache[22] || (_cache[22] = [
                  _createTextVNode("刷新列表", -1)
                ]))]),
                _: 1
              }, 8, ["loading"])
            ]),
            (loadingTargets.value)
              ? (_openBlock(), _createElementBlock("div", _hoisted_17, "加载目标中…"))
              : (!targets.value.length)
                ? (_openBlock(), _createElementBlock("div", _hoisted_18, "选中后这里会展示可上传字幕的目标集数"))
                : (_openBlock(), _createElementBlock("div", _hoisted_19, [
                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(targets.value, (t) => {
                      return (_openBlock(), _createElementBlock("button", {
                        key: t.target_id || t.id,
                        type: "button",
                        class: _normalizeClass(["swu-target", { selected: selectedIds.value.includes(targetId(t)) }]),
                        onClick: $event => (toggleTarget(t))
                      }, [
                        _createElementVNode("div", _hoisted_21, _toDisplayString(episodeLabel(t)), 1),
                        _createElementVNode("div", _hoisted_22, _toDisplayString(shortName(t)), 1),
                        _createElementVNode("div", _hoisted_23, [
                          _createTextVNode(" 外挂 " + _toDisplayString(subtitleCount(t)) + " ", 1),
                          (t.ai_status || t.task_status)
                            ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, [
                                _createTextVNode(" · " + _toDisplayString(t.ai_status || t.task_status), 1)
                              ], 64))
                            : _createCommentVNode("", true)
                        ])
                      ], 10, _hoisted_20))
                    }), 128))
                  ]))
          ]),
          _: 1
        })
      ]),
      _: 1
    }),
    _createElementVNode("div", _hoisted_24, [
      _createElementVNode("div", null, [
        _cache[23] || (_cache[23] = _createTextVNode("将对 ", -1)),
        _createElementVNode("b", null, _toDisplayString(selectedIds.value.length), 1),
        _cache[24] || (_cache[24] = _createTextVNode(" 个目标执行 · 上传 / 在线 / 外挂管理 / AI 分区操作", -1))
      ])
    ]),
    _createElementVNode("div", _hoisted_25, [
      _createVNode(_component_v_card, {
        class: "swu-card",
        variant: "tonal",
        rounded: "lg"
      }, {
        default: _withCtx(() => [
          _createVNode(_component_v_card_title, { class: "swu-card-title" }, {
            default: _withCtx(() => [...(_cache[25] || (_cache[25] = [
              _createTextVNode("上传外挂", -1)
            ]))]),
            _: 1
          }),
          _createVNode(_component_v_card_text, null, {
            default: _withCtx(() => [
              _createElementVNode("div", {
                class: _normalizeClass(["swu-drop", { drag: dragging.value }]),
                onDragover: _cache[3] || (_cache[3] = _withModifiers($event => (dragging.value = true), ["prevent"])),
                onDragleave: _cache[4] || (_cache[4] = _withModifiers($event => (dragging.value = false), ["prevent"])),
                onDrop: _withModifiers(onDrop, ["prevent"]),
                onClick: _cache[5] || (_cache[5] = $event => (fileInput.value?.click()))
              }, [
                _cache[26] || (_cache[26] = _createElementVNode("div", null, "拖拽字幕到这里", -1)),
                _cache[27] || (_cache[27] = _createElementVNode("div", { class: "swu-muted" }, "支持 ass/srt/ssa/vtt/zip/rar/7z · 也可点击选择", -1)),
                _createElementVNode("input", {
                  ref_key: "fileInput",
                  ref: fileInput,
                  type: "file",
                  multiple: "",
                  hidden: "",
                  onChange: onFilePick
                }, null, 544)
              ], 34),
              (files.value.length)
                ? (_openBlock(), _createElementBlock("div", _hoisted_26, [
                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(files.value, (f, i) => {
                      return (_openBlock(), _createElementBlock("div", {
                        key: i,
                        class: "swu-file-row"
                      }, [
                        _createElementVNode("span", null, _toDisplayString(f.name), 1),
                        _createVNode(_component_v_btn, {
                          size: "x-small",
                          variant: "text",
                          onClick: $event => (files.value.splice(i, 1))
                        }, {
                          default: _withCtx(() => [...(_cache[28] || (_cache[28] = [
                            _createTextVNode("移除", -1)
                          ]))]),
                          _: 1
                        }, 8, ["onClick"])
                      ]))
                    }), 128)),
                    _createVNode(_component_v_btn, {
                      size: "small",
                      variant: "text",
                      onClick: _cache[6] || (_cache[6] = $event => (files.value = []))
                    }, {
                      default: _withCtx(() => [...(_cache[29] || (_cache[29] = [
                        _createTextVNode("清空文件", -1)
                      ]))]),
                      _: 1
                    })
                  ]))
                : _createCommentVNode("", true),
              _createElementVNode("div", _hoisted_27, [
                _createVNode(_component_v_btn, {
                  color: "primary",
                  disabled: !canUpload.value,
                  loading: uploading.value,
                  onClick: prepareUpload
                }, {
                  default: _withCtx(() => [...(_cache[30] || (_cache[30] = [
                    _createTextVNode(" 生成匹配预览 ", -1)
                  ]))]),
                  _: 1
                }, 8, ["disabled", "loading"]),
                _createVNode(_component_v_btn, {
                  color: "success",
                  disabled: !uploadSession.value,
                  loading: applying.value,
                  onClick: applyUpload
                }, {
                  default: _withCtx(() => [...(_cache[31] || (_cache[31] = [
                    _createTextVNode(" 上传字幕 ", -1)
                  ]))]),
                  _: 1
                }, 8, ["disabled", "loading"])
              ]),
              (uploadPreviewText.value)
                ? (_openBlock(), _createElementBlock("div", _hoisted_28, _toDisplayString(uploadPreviewText.value), 1))
                : _createCommentVNode("", true)
            ]),
            _: 1
          })
        ]),
        _: 1
      }),
      _createVNode(_component_v_card, {
        class: "swu-card",
        variant: "tonal",
        rounded: "lg"
      }, {
        default: _withCtx(() => [
          _createVNode(_component_v_card_title, { class: "swu-card-title" }, {
            default: _withCtx(() => [...(_cache[32] || (_cache[32] = [
              _createTextVNode("在线字幕", -1)
            ]))]),
            _: 1
          }),
          _createVNode(_component_v_card_text, null, {
            default: _withCtx(() => [
              _createElementVNode("div", _hoisted_29, [
                _createVNode(_component_v_btn, {
                  color: "primary",
                  disabled: !selectedIds.value.length,
                  loading: onlineSearching.value,
                  onClick: searchOnline
                }, {
                  default: _withCtx(() => [...(_cache[33] || (_cache[33] = [
                    _createTextVNode(" 搜索在线字幕 ", -1)
                  ]))]),
                  _: 1
                }, 8, ["disabled", "loading"]),
                _createVNode(_component_v_btn, {
                  variant: "tonal",
                  disabled: !selectedOnline.value.length,
                  loading: onlinePreviewing.value,
                  onClick: previewOnline
                }, {
                  default: _withCtx(() => [...(_cache[34] || (_cache[34] = [
                    _createTextVNode(" 预览选中 ", -1)
                  ]))]),
                  _: 1
                }, 8, ["disabled", "loading"]),
                _createVNode(_component_v_btn, {
                  color: "secondary",
                  disabled: !selectedOnline.value.length || !selectedIds.value.length,
                  loading: onlineAiLoading.value,
                  onClick: submitOnlineAi
                }, {
                  default: _withCtx(() => [...(_cache[35] || (_cache[35] = [
                    _createTextVNode(" 在线→AI ", -1)
                  ]))]),
                  _: 1
                }, 8, ["disabled", "loading"])
              ]),
              (!onlineResults.value.length)
                ? (_openBlock(), _createElementBlock("div", _hoisted_30, "从在线字幕源搜索，选中候选后生成上传预览"))
                : (_openBlock(), _createElementBlock("div", _hoisted_31, [
                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(onlineResults.value, (r, idx) => {
                      return (_openBlock(), _createElementBlock("label", {
                        key: idx,
                        class: "swu-online-item"
                      }, [
                        _withDirectives(_createElementVNode("input", {
                          "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((selectedOnline).value = $event)),
                          type: "checkbox",
                          value: r
                        }, null, 8, _hoisted_32), [
                          [_vModelCheckbox, selectedOnline.value]
                        ]),
                        _createElementVNode("div", null, [
                          _createElementVNode("div", _hoisted_33, _toDisplayString(r.title || r.name || r.filename || '在线结果'), 1),
                          _createElementVNode("div", _hoisted_34, _toDisplayString(r.lang || r.language || '') + " " + _toDisplayString(r.source || r.provider || ''), 1)
                        ])
                      ]))
                    }), 128))
                  ]))
            ]),
            _: 1
          })
        ]),
        _: 1
      }),
      _createVNode(_component_v_card, {
        class: "swu-card",
        variant: "tonal",
        rounded: "lg"
      }, {
        default: _withCtx(() => [
          _createVNode(_component_v_card_title, { class: "swu-card-title" }, {
            default: _withCtx(() => [...(_cache[36] || (_cache[36] = [
              _createTextVNode("外挂管理", -1)
            ]))]),
            _: 1
          }),
          _createVNode(_component_v_card_text, null, {
            default: _withCtx(() => [
              _createElementVNode("div", _hoisted_35, [
                _createVNode(_component_v_btn, {
                  size: "small",
                  variant: "tonal",
                  disabled: !selectedIds.value.length,
                  loading: historyLoading.value,
                  onClick: loadHistory
                }, {
                  default: _withCtx(() => [...(_cache[37] || (_cache[37] = [
                    _createTextVNode(" 刷新外挂列表 ", -1)
                  ]))]),
                  _: 1
                }, 8, ["disabled", "loading"]),
                _createVNode(_component_v_btn, {
                  size: "small",
                  variant: "tonal",
                  disabled: !selectedSubs.value.length,
                  loading: timelineLoading.value,
                  onClick: fixTimeline
                }, {
                  default: _withCtx(() => [...(_cache[38] || (_cache[38] = [
                    _createTextVNode(" 调轴选中外挂 ", -1)
                  ]))]),
                  _: 1
                }, 8, ["disabled", "loading"]),
                _createVNode(_component_v_btn, {
                  size: "small",
                  color: "warning",
                  variant: "tonal",
                  disabled: !selectedSubs.value.length,
                  onClick: restoreSelected
                }, {
                  default: _withCtx(() => [...(_cache[39] || (_cache[39] = [
                    _createTextVNode(" 恢复备份 ", -1)
                  ]))]),
                  _: 1
                }, 8, ["disabled"]),
                _createVNode(_component_v_btn, {
                  size: "small",
                  color: "error",
                  variant: "tonal",
                  disabled: !selectedSubs.value.length,
                  onClick: deleteSelected
                }, {
                  default: _withCtx(() => [...(_cache[40] || (_cache[40] = [
                    _createTextVNode(" 删除外挂 ", -1)
                  ]))]),
                  _: 1
                }, 8, ["disabled"])
              ]),
              (!historyItems.value.length)
                ? (_openBlock(), _createElementBlock("div", _hoisted_36, "这里只管理外挂字幕，不会取消 AI 任务"))
                : (_openBlock(), _createElementBlock("div", _hoisted_37, [
                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(historyItems.value, (h, idx) => {
                      return (_openBlock(), _createElementBlock("label", {
                        key: idx,
                        class: "swu-online-item"
                      }, [
                        _withDirectives(_createElementVNode("input", {
                          "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((selectedSubs).value = $event)),
                          type: "checkbox",
                          value: h
                        }, null, 8, _hoisted_38), [
                          [_vModelCheckbox, selectedSubs.value]
                        ]),
                        _createElementVNode("div", null, [
                          _createElementVNode("div", _hoisted_39, _toDisplayString(h.subtitle_name || h.name || h.path || '字幕'), 1),
                          _createElementVNode("div", _hoisted_40, [
                            _createTextVNode(_toDisplayString(h.target_id || '') + " ", 1),
                            (h.has_backup || h.backup_path)
                              ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, [
                                  _createTextVNode(" · 有备份")
                                ], 64))
                              : _createCommentVNode("", true)
                          ])
                        ])
                      ]))
                    }), 128))
                  ]))
            ]),
            _: 1
          })
        ]),
        _: 1
      }),
      _createVNode(_component_v_card, {
        class: "swu-card",
        variant: "tonal",
        rounded: "lg"
      }, {
        default: _withCtx(() => [
          _createVNode(_component_v_card_title, { class: "swu-card-title" }, {
            default: _withCtx(() => [...(_cache[41] || (_cache[41] = [
              _createTextVNode("AI 翻译", -1)
            ]))]),
            _: 1
          }),
          _createVNode(_component_v_card_text, null, {
            default: _withCtx(() => [
              _createElementVNode("div", _hoisted_41, [
                _createVNode(_component_v_select, {
                  modelValue: sourcePolicy.value,
                  "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => ((sourcePolicy).value = $event)),
                  items: sourcePolicyItems,
                  label: "字幕源策略",
                  density: "compact",
                  variant: "outlined",
                  "hide-details": ""
                }, null, 8, ["modelValue"]),
                _createVNode(_component_v_select, {
                  modelValue: overwritePolicy.value,
                  "onUpdate:modelValue": _cache[10] || (_cache[10] = $event => ((overwritePolicy).value = $event)),
                  items: overwritePolicyItems,
                  label: "覆盖策略",
                  density: "compact",
                  variant: "outlined",
                  "hide-details": ""
                }, null, 8, ["modelValue"]),
                _createVNode(_component_v_text_field, {
                  modelValue: sourceSubtitlePath.value,
                  "onUpdate:modelValue": _cache[11] || (_cache[11] = $event => ((sourceSubtitlePath).value = $event)),
                  label: "外挂源字幕路径（可选）",
                  density: "compact",
                  variant: "outlined",
                  "hide-details": "",
                  clearable: ""
                }, null, 8, ["modelValue"])
              ]),
              _createElementVNode("div", _hoisted_42, [
                _createVNode(_component_v_btn, {
                  color: "primary",
                  disabled: !selectedIds.value.length,
                  loading: aiPreviewing.value,
                  onClick: previewAi
                }, {
                  default: _withCtx(() => [...(_cache[42] || (_cache[42] = [
                    _createTextVNode(" 预检 ", -1)
                  ]))]),
                  _: 1
                }, 8, ["disabled", "loading"]),
                _createVNode(_component_v_btn, {
                  color: "success",
                  disabled: !selectedIds.value.length,
                  loading: aiSubmitting.value,
                  onClick: submitAi
                }, {
                  default: _withCtx(() => [...(_cache[43] || (_cache[43] = [
                    _createTextVNode(" 提交任务 ", -1)
                  ]))]),
                  _: 1
                }, 8, ["disabled", "loading"]),
                _createVNode(_component_v_btn, {
                  variant: "tonal",
                  disabled: !selectedIds.value.length,
                  loading: aiRestarting.value,
                  onClick: restartAi
                }, {
                  default: _withCtx(() => [...(_cache[44] || (_cache[44] = [
                    _createTextVNode(" 重做 ", -1)
                  ]))]),
                  _: 1
                }, 8, ["disabled", "loading"]),
                _createVNode(_component_v_btn, {
                  variant: "tonal",
                  disabled: !selectedIds.value.length,
                  loading: taskLoading.value,
                  onClick: loadTasks
                }, {
                  default: _withCtx(() => [...(_cache[45] || (_cache[45] = [
                    _createTextVNode(" 查看状态 ", -1)
                  ]))]),
                  _: 1
                }, 8, ["disabled", "loading"]),
                _createVNode(_component_v_btn, {
                  color: "error",
                  variant: "tonal",
                  disabled: !selectedIds.value.length,
                  onClick: cancelAi
                }, {
                  default: _withCtx(() => [...(_cache[46] || (_cache[46] = [
                    _createTextVNode(" 取消任务 ", -1)
                  ]))]),
                  _: 1
                }, 8, ["disabled"])
              ]),
              (aiPreviewText.value)
                ? (_openBlock(), _createElementBlock("div", _hoisted_43, _toDisplayString(aiPreviewText.value), 1))
                : _createCommentVNode("", true),
              (taskList.value.length)
                ? (_openBlock(), _createElementBlock("div", _hoisted_44, [
                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(taskList.value, (task, i) => {
                      return (_openBlock(), _createElementBlock("div", {
                        key: i,
                        class: "swu-task"
                      }, [
                        _createElementVNode("div", _hoisted_45, [
                          _createElementVNode("span", null, _toDisplayString(taskTitle(task)), 1),
                          _createElementVNode("span", _hoisted_46, _toDisplayString(taskStatusText(task)), 1)
                        ]),
                        _createVNode(_component_v_progress_linear, {
                          "model-value": taskPercent(task),
                          height: "8",
                          rounded: "",
                          color: "primary",
                          class: "mt-1"
                        }, null, 8, ["model-value"]),
                        _createElementVNode("div", _hoisted_47, _toDisplayString(taskMessage(task)), 1)
                      ]))
                    }), 128))
                  ]))
                : _createCommentVNode("", true)
            ]),
            _: 1
          })
        ]),
        _: 1
      })
    ]),
    _createVNode(_component_v_card, {
      class: "swu-card swu-log",
      variant: "outlined",
      rounded: "lg"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card_title, { class: "swu-card-title" }, {
          default: _withCtx(() => [
            _cache[48] || (_cache[48] = _createTextVNode(" 最近结果 ", -1)),
            _createVNode(_component_v_btn, {
              size: "x-small",
              variant: "text",
              onClick: _cache[12] || (_cache[12] = $event => (logs.value = []))
            }, {
              default: _withCtx(() => [...(_cache[47] || (_cache[47] = [
                _createTextVNode("清空", -1)
              ]))]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_v_card_text, null, {
          default: _withCtx(() => [
            (!logs.value.length)
              ? (_openBlock(), _createElementBlock("div", _hoisted_48, "操作后会在这里留下提示"))
              : _createCommentVNode("", true),
            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(logs.value, (line, i) => {
              return (_openBlock(), _createElementBlock("div", {
                key: i,
                class: "swu-log-line"
              }, _toDisplayString(line), 1))
            }), 128))
          ]),
          _: 1
        })
      ]),
      _: 1
    }),
    _createElementVNode("div", _hoisted_49, [
      _createElementVNode("div", _hoisted_50, "已选 " + _toDisplayString(selectedIds.value.length) + " · 文件 " + _toDisplayString(files.value.length), 1),
      _createElementVNode("div", _hoisted_51, [
        _createVNode(_component_v_btn, {
          size: "small",
          color: "primary",
          disabled: !canUpload.value,
          onClick: prepareUpload
        }, {
          default: _withCtx(() => [...(_cache[49] || (_cache[49] = [
            _createTextVNode("上传外挂", -1)
          ]))]),
          _: 1
        }, 8, ["disabled"]),
        _createVNode(_component_v_btn, {
          size: "small",
          variant: "tonal",
          disabled: !selectedIds.value.length,
          onClick: searchOnline
        }, {
          default: _withCtx(() => [...(_cache[50] || (_cache[50] = [
            _createTextVNode("在线字幕", -1)
          ]))]),
          _: 1
        }, 8, ["disabled"]),
        _createVNode(_component_v_btn, {
          size: "small",
          variant: "tonal",
          disabled: !selectedIds.value.length,
          onClick: previewAi
        }, {
          default: _withCtx(() => [...(_cache[51] || (_cache[51] = [
            _createTextVNode("AI", -1)
          ]))]),
          _: 1
        }, 8, ["disabled"]),
        _createVNode(_component_v_menu, null, {
          activator: _withCtx(({ props: menuProps }) => [
            _createVNode(_component_v_btn, _mergeProps({
              size: "small",
              variant: "text"
            }, menuProps), {
              default: _withCtx(() => [...(_cache[52] || (_cache[52] = [
                _createTextVNode("更多", -1)
              ]))]),
              _: 1
            }, 16)
          ]),
          default: _withCtx(() => [
            _createVNode(_component_v_list, { density: "compact" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_list_item, {
                  title: "刷新外挂",
                  disabled: !selectedIds.value.length,
                  onClick: loadHistory
                }, null, 8, ["disabled"]),
                _createVNode(_component_v_list_item, {
                  title: "调轴选中外挂",
                  disabled: !selectedSubs.value.length,
                  onClick: fixTimeline
                }, null, 8, ["disabled"]),
                _createVNode(_component_v_list_item, {
                  title: "恢复备份",
                  disabled: !selectedSubs.value.length,
                  onClick: restoreSelected
                }, null, 8, ["disabled"]),
                _createVNode(_component_v_list_item, {
                  title: "删除外挂",
                  disabled: !selectedSubs.value.length,
                  onClick: deleteSelected
                }, null, 8, ["disabled"]),
                _createVNode(_component_v_list_item, {
                  title: "取消 AI 任务",
                  disabled: !selectedIds.value.length,
                  onClick: cancelAi
                }, null, 8, ["disabled"]),
                _createVNode(_component_v_list_item, {
                  title: "AI 重做",
                  disabled: !selectedIds.value.length,
                  onClick: restartAi
                }, null, 8, ["disabled"])
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ])
    ])
  ]))
}
}

};
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-cae31e72"]]);

export { Page as default };
