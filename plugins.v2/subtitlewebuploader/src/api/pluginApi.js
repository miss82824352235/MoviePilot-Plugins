/**
 * 字幕网页上传器 API 客户端。
 * 优先使用 MP 注入的 api，失败时回退到相对路径 fetch。
 */

const PLUGIN = 'SubtitleWebUploader'
const BASE = `plugin/${PLUGIN}/subtitleweb_bridge`

function unwrap(res) {
  if (res == null) return res
  // MP 标准 Response 或插件 ok/fail
  if (typeof res === 'object') {
    if (Object.prototype.hasOwnProperty.call(res, 'success') && res.success === false) {
      const err = new Error(res.message || '请求失败')
      err.response = res
      err.needConfirm = !!(res.data && res.data.need_confirm)
      throw err
    }
    if (Object.prototype.hasOwnProperty.call(res, 'code') && res.code !== 0) {
      const err = new Error(res.message || '请求失败')
      err.response = res
      err.code = res.code
      err.needConfirm = !!(res.data && res.data.need_confirm)
      throw err
    }
    if (Object.prototype.hasOwnProperty.call(res, 'data')) return res.data
  }
  return res
}

export function createPluginApi(api) {
  async function get(path, params = {}) {
    const qs = new URLSearchParams()
    Object.entries(params || {}).forEach(([k, v]) => {
      if (v === undefined || v === null || v === '') return
      qs.set(k, String(v))
    })
    const suffix = qs.toString() ? `?${qs}` : ''
    if (api && typeof api.get === 'function') {
      return unwrap(await api.get(`${BASE}/${path}${suffix}`))
    }
    const r = await fetch(`/api/v1/${BASE}/${path}${suffix}`, { credentials: 'include' })
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
    })
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
    })
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
