function unwrapResponse(payload) {
  if (payload == null) return payload
  if (typeof payload !== 'object') return payload
  if (Object.prototype.hasOwnProperty.call(payload, 'success') && payload.success === false) {
    const err = new Error(payload.message || '请求失败')
    err.response = payload
    err.success = false
    err.data = payload.data
    throw err
  }
  if (Object.prototype.hasOwnProperty.call(payload, 'data') && Object.prototype.hasOwnProperty.call(payload, 'success')) {
    return payload.data
  }
  return payload
}

export function getPluginApi(api, path, params = {}) {
  const pluginId = 'DiscRemuxPlugin'
  return api.get(`plugin/${pluginId}/${path}`, { params }).then((res) => unwrapResponse(res?.data ?? res))
}

export function postPluginApi(api, path, body = {}) {
  const pluginId = 'DiscRemuxPlugin'
  return api.post(`plugin/${pluginId}/${path}`, body).then((res) => unwrapResponse(res?.data ?? res))
}

export function normalizeError(err) {
  if (!err) return '未知错误'
  if (err.response?.message) return err.response.message
  if (err.message) return err.message
  return String(err)
}
