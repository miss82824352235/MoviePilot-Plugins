export function unwrapResponse(response) {
  return response?.data ?? response
}

export async function getPluginApi(api, path) {
  if (!api?.get) throw new Error('缺少 MoviePilot 注入的 api.get')
  return unwrapResponse(await api.get(`plugin/BTSubscribeCenter/${path}`))
}

export async function postPluginApi(api, path, payload = {}) {
  if (!api?.post) throw new Error('缺少 MoviePilot 注入的 api.post')
  return unwrapResponse(await api.post(`plugin/BTSubscribeCenter/${path}`, payload))
}
