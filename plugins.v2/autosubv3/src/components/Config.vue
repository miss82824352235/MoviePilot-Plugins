<script setup>
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  api: {
    type: Object,
    default: () => ({}),
  },
  pluginId: {
    type: String,
    default: 'AutoSubv3',
  },
  initialConfig: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['save', 'close', 'switch'])

const defaultConfig = {
  enabled: false,
  clear_history: false,
  send_notify: false,
  listen_transfer_event: true,
  generation_mode: 'monitor',
  process_new_only: true,
  path_whitelist: '',
  run_now: false,
  path_list: '',
  file_size: '10',
  translate_preference: 'english_first',
  translate_zh: true,
  enable_asr: true,
  auto_detect_language: false,
  asr_model_strategy: 'auto_english_fast',
  skip_chinese: false,
    max_segment_duration: 5.5,
    max_segment_chars: 28,
  subtitle_max_lines: 2,
  subtitle_max_chars_per_line: 14,
  subtitle_min_duration: 0.9,
  subtitle_max_duration: 5.5,
  subtitle_max_reading_speed: 14,
  default_glossary: '',
  faster_whisper_model: 'base',
  proxy: true,
  openai_proxy: false,
  compatible: false,
  openai_url: 'https://api.siliconflow.cn',
  openai_key: '',
  openai_model: 'inclusionAI/Ling-flash-2.0',
  llm_provider: 'openai',
  llm_base_url: 'https://api.siliconflow.cn/v1',
  llm_base_url_preset: '',
  llm_api_key: '',
  llm_model: 'inclusionAI/Ling-flash-2.0',
  llm_context_tokens: '',
  llm_use_proxy: false,
  llm_user_agent: '',
  context_window: 5,
  max_retries: 3,
  enable_merge: false,
  subtitle_output_mode: 'bilingual',
  enable_batch: true,
  batch_size: 20,
  parallel_workers: 10,
}

function normalizeModelValue(value) {
  if (typeof value === 'string') return value
  if (value && typeof value === 'object') {
    return String(value.value || value.id || value.model || value.title || value.name || '').trim()
  }
  return value == null ? '' : String(value).trim()
}

function normalizeInitialConfig(value = {}) {
  const merged = { ...defaultConfig, ...(value || {}) }
  merged.generation_mode = merged.generation_mode === 'fallback' ? 'fallback' : 'monitor'
  merged.llm_model = normalizeModelValue(merged.llm_model || merged.openai_model)
  merged.openai_model = normalizeModelValue(merged.openai_model || merged.llm_model)
  return merged
}

const config = reactive(normalizeInitialConfig(props.initialConfig))
const saving = ref(false)
const loadingModels = ref(false)
const testingModel = ref(false)
const error = ref('')
const apiError = ref('')
const apiMessage = ref('')
const remoteModels = ref([])
const uiRevision = 'v3.5.66-independent-llm-provider'
const loadingProviders = ref(false)
const loadingMetadata = ref(false)
const providers = ref([])
const metadata = ref(null)
const pluginBase = computed(() => `plugin/${props.pluginId || 'AutoSubv3'}`)
const apiReady = computed(() => typeof props.api?.post === 'function')

const whisperModels = [
  { title: 'tiny', value: 'tiny' },
  { title: 'base', value: 'base' },
  { title: 'small', value: 'small' },
  { title: 'medium', value: 'medium' },
  { title: 'distil-large-v3', value: 'distil-large-v3' },
  { title: 'large-v3', value: 'large-v3' },
  { title: 'large-v3-turbo', value: 'deepdml/faster-whisper-large-v3-turbo-ct2' },
]
const outputModes = [
  { title: '双语字幕（翻译+原文）', value: 'bilingual' },
  { title: '纯中文字幕', value: 'chinese_only' },
]
const asrModelStrategies = [
  { title: '自动：英语快速、非英语多语（推荐）', value: 'auto_english_fast' },
  { title: '手动指定模型', value: 'manual' },
]
const preferences = [
  { title: '仅英文', value: 'english_only' },
  { title: '英文优先', value: 'english_first' },
  { title: '原音优先', value: 'origin_first' },
]
const modelItems = computed(() => {
  const items = [...remoteModels.value]
  const model = normalizeModelValue(config.llm_model)
  if (model && !items.some(item => item.value === model)) {
    items.unshift({ title: model, value: model })
  }
  return items
})
watch(
  () => props.initialConfig,
  (value) => {
    Object.assign(config, normalizeInitialConfig(value))
  },
)
watch(
  () => [config.llm_provider, config.llm_base_url, config.llm_base_url_preset, config.llm_api_key, config.llm_model, config.llm_use_proxy, config.llm_user_agent],
  () => {
    apiError.value = ''
    apiMessage.value = ''
  },
)

function unwrapResponse(response) {
  return response?.data?.data || response?.data || response || {}
}

function normalizeModelList(payload) {
  const candidates = payload?.models || payload?.items || payload?.data?.models || payload?.data?.items || []
  if (!Array.isArray(candidates)) return []
  return candidates
    .map((item) => {
      if (typeof item === 'string') return { title: item, value: item }
      const value = item?.value || item?.id || item?.model || ''
      const title = item?.title || item?.name || value
      return value ? { title, value } : null
    })
    .filter(Boolean)
}

function responseMessage(response) {
  return response?.data?.message || response?.message || ''
}

function errorMessage(err, fallback) {
  return err?.response?.data?.detail || err?.message || fallback
}

const providerItems = computed(() => providers.value.map((item) => ({
  title: item.name || item.id,
  value: item.id,
  raw: item,
})))
const selectedProvider = computed(() => providers.value.find((item) => item.id === config.llm_provider) || null)
const baseUrlPresetItems = computed(() => {
  const raw = selectedProvider.value?.base_url_presets || []
  return raw.map((item) => ({ title: item.label || item.id || item.value, value: item.id || item.value, raw: item }))
})
const apiKeyLabel = computed(() => selectedProvider.value?.api_key_label || 'API Key')
const apiKeyHint = computed(() => selectedProvider.value?.api_key_hint || '填写当前 Provider 的 API Key。')
const baseUrlEditable = computed(() => selectedProvider.value?.base_url_editable !== false)
const supportsApiKey = computed(() => selectedProvider.value?.supports_api_key !== false)
const contextLimitText = computed(() => {
  const limit = metadata.value?.context_length || metadata.value?.input_token_limit
  const output = metadata.value?.max_output_tokens || metadata.value?.output_token_limit
  if (!limit && !output) return ''
  return `上下文上限 ${limit || '未知'}${output ? `，输出上限 ${output}` : ''}`
})

function normalizedConfigForSave() {
  const llmModel = normalizeModelValue(config.llm_model)
  return {
    ...config,
    llm_model: llmModel,
    openai_url: config.llm_base_url || config.openai_url,
    openai_key: config.llm_api_key || config.openai_key,
    openai_model: llmModel || normalizeModelValue(config.openai_model),
    openai_proxy: config.llm_use_proxy,
  }
}

function apiPayload(extra = {}) {
  const llmModel = normalizeModelValue(config.llm_model)
  return {
    provider: config.llm_provider || 'openai',
    llm_provider: config.llm_provider || 'openai',
    base_url: config.llm_base_url,
    llm_base_url: config.llm_base_url,
    base_url_preset: config.llm_base_url_preset,
    llm_base_url_preset: config.llm_base_url_preset,
    api_key: config.llm_api_key,
    llm_api_key: config.llm_api_key,
    model: llmModel,
    llm_model: llmModel,
    user_agent: config.llm_user_agent,
    llm_user_agent: config.llm_user_agent,
    use_proxy: config.llm_use_proxy,
    llm_use_proxy: config.llm_use_proxy,
    ...extra,
  }
}

function apiClient() {
  if (!apiReady.value) throw new Error('当前页面未注入插件 API 客户端，请刷新后重试')
  return props.api
}

async function fetchProviders() {
  loadingProviders.value = true
  apiError.value = ''
  apiMessage.value = ''
  try {
    const data = unwrapResponse(await apiClient().get(`${pluginBase.value}/llm_providers`))
    providers.value = data.providers || data.items || []
    if (selectedProvider.value && !config.llm_base_url && selectedProvider.value.default_base_url) {
      config.llm_base_url = selectedProvider.value.default_base_url
    }
    apiMessage.value = `已获取 ${providers.value.length} 个 Provider`
  } catch (err) {
    apiError.value = errorMessage(err, '获取 Provider 目录失败')
  } finally {
    loadingProviders.value = false
  }
}

function applyProviderDefaults() {
  const provider = selectedProvider.value
  if (!provider) return
  if (!config.llm_base_url && provider.default_base_url) config.llm_base_url = provider.default_base_url
  if (!config.llm_base_url_preset && provider.base_url_presets?.length) {
    config.llm_base_url_preset = provider.base_url_presets[0].id || ''
  }
}

async function fetchModels() {
  loadingModels.value = true
  apiError.value = ''
  apiMessage.value = ''
  try {
    const data = unwrapResponse(await apiClient().post(`${pluginBase.value}/llm_models`, apiPayload()))
    remoteModels.value = normalizeModelList(data)
    if (!remoteModels.value.length) {
      throw new Error('模型列表为空，请检查插件独立 Provider、Base URL 和 API Key')
    }
    apiMessage.value = `已获取 ${remoteModels.value.length} 个模型（${data.source || 'plugin_independent_llm_helper'}）`
  } catch (err) {
    apiError.value = errorMessage(err, '获取模型列表失败')
  } finally {
    loadingModels.value = false
  }
}

async function testModel() {
  testingModel.value = true
  apiError.value = ''
  apiMessage.value = ''
  try {
    const response = await apiClient().post(`${pluginBase.value}/llm_test`, apiPayload())
    const data = unwrapResponse(response)
    apiMessage.value = responseMessage(response) || `模型 ${data.model || config.llm_model} 可用`
  } catch (err) {
    apiError.value = errorMessage(err, '测试模型失败')
  } finally {
    testingModel.value = false
  }
}

async function fetchMetadata() {
  loadingMetadata.value = true
  apiError.value = ''
  apiMessage.value = ''
  try {
    const data = unwrapResponse(await apiClient().post(`${pluginBase.value}/llm_model_metadata`, apiPayload()))
    metadata.value = data
    const limit = Number(data.context_length || data.input_token_limit || 0)
    if (limit && Number(config.llm_context_tokens || 0) > limit) {
      config.llm_context_tokens = String(limit)
    }
    apiMessage.value = `已读取模型能力：${data.name || data.model_id || config.llm_model}`
  } catch (err) {
    apiError.value = errorMessage(err, '获取模型 metadata 失败')
  } finally {
    loadingMetadata.value = false
  }
}

watch(() => config.llm_provider, () => applyProviderDefaults())

function save() {
  saving.value = true
  error.value = ''
  try {
    const payload = normalizedConfigForSave()
    config.llm_model = payload.llm_model
    config.openai_model = payload.openai_model
    emit('save', payload)
  } catch (err) {
    error.value = err?.message || '保存配置失败'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="autosub-config">
    <VToolbar density="comfortable" color="transparent">
      <div class="text-h6 ms-3">AI字幕生成配置</div>
      <VSpacer />
      <VBtn variant="text" prepend-icon="mdi-format-list-bulleted" @click="emit('switch')">查看任务</VBtn>
      <VBtn color="primary" variant="tonal" prepend-icon="mdi-content-save" :loading="saving" @click="save">保存</VBtn>
      <VBtn icon="mdi-close" variant="text" @click="emit('close')" />
    </VToolbar>
    <VDivider />

    <div class="config-shell">
      <VAlert v-if="error" class="mb-4" type="error" variant="tonal" density="compact" :text="error" />

      <section class="config-section">
        <div class="section-title">基础设置</div>
        <VRow>
          <VCol cols="12" md="6">
            <VSwitch
              v-model="config.generation_mode"
              label="启用独立入库监控"
              true-value="monitor"
              false-value="fallback"
              hint="关闭后仍可接收字幕匹配联动任务和手动任务"
              persistent-hint
            />
          </VCol>
          <VCol cols="12" md="3">
            <VSwitch v-model="config.enabled" label="启用插件" color="primary" hide-details />
          </VCol>
          <VCol cols="12" md="3">
            <VSwitch v-model="config.send_notify" label="发送通知" hide-details />
          </VCol>
        </VRow>

        <VRow>
          <VCol cols="12" md="3">
            <VSwitch v-model="config.clear_history" label="清理历史记录" hide-details />
          </VCol>
          <VCol cols="12" md="3">
            <VSwitch v-model="config.process_new_only" label="仅处理新增视频" hide-details />
          </VCol>
          <VCol cols="12" md="3">
            <VSwitch v-model="config.run_now" label="手动执行一次" color="secondary" hide-details />
          </VCol>
          <VCol cols="12" md="3">
            <VSwitch v-model="config.translate_zh" label="外语翻译成中文" hide-details />
          </VCol>
          <VCol cols="12" md="3">
            <VSwitch v-model="config.skip_chinese" label="中文视频不翻译" hide-details />
          </VCol>
          <VCol cols="12" md="3">
            <VSwitch v-model="config.enable_asr" label="允许 ASR 生成字幕" hide-details />
          </VCol>
        </VRow>
      </section>

      <section class="config-section">
        <div class="section-title">独立 LLM 配置</div>
        <VAlert type="info" variant="tonal" class="mb-3" density="comfortable">
          AutoSubv3 使用独立 LLM 参数；这里只复刻 MoviePilot 智能助手的 Provider 目录、Base URL 预设、模型列表和 metadata 机制，不读取也不绑定 MP 智能助手当前填写值。
        </VAlert>
        <VRow>
          <VCol cols="12" md="4">
            <VSelect
              v-model="config.llm_provider"
              :items="providerItems"
              item-title="title"
              item-value="value"
              label="LLM Provider"
              placeholder="openai"
              :loading="loadingProviders"
              @update:model-value="applyProviderDefaults"
            />
          </VCol>
          <VCol cols="12" md="4">
            <VSelect
              v-model="config.llm_base_url_preset"
              :items="baseUrlPresetItems"
              item-title="title"
              item-value="value"
              label="Base URL 预设"
              clearable
              placeholder="使用 Provider 默认或自定义"
            />
          </VCol>
          <VCol cols="12" md="4">
            <VTextField v-model="config.llm_context_tokens" label="上下文 Token 上限" :hint="contextLimitText || '可按模型 metadata 建议填写'" persistent-hint />
          </VCol>
        </VRow>
        <VRow>
          <VCol cols="12" md="6">
            <VTextField v-model="config.llm_base_url" label="LLM Base URL" placeholder="https://api.example.com/v1" :disabled="!baseUrlEditable" />
          </VCol>
          <VCol cols="12" md="6">
            <VTextField v-model="config.llm_api_key" :label="apiKeyLabel" type="password" :placeholder="apiKeyHint" :disabled="!supportsApiKey" />
          </VCol>
        </VRow>

        <VRow align="center">
          <VCol cols="12" md="6">
            <VCombobox
              :model-value="normalizeModelValue(config.llm_model)"
              :items="modelItems"
              item-title="title"
              item-value="value"
              label="LLM模型名称"
              placeholder="选择或填写模型 ID"
              @update:model-value="config.llm_model = normalizeModelValue($event)"
            />
          </VCol>
          <VCol cols="12" md="6" class="api-actions">
            <VBtn
              color="secondary"
              variant="tonal"
              prepend-icon="mdi-cloud-search"
              :loading="loadingProviders"
              :disabled="loadingModels || testingModel || loadingMetadata || !apiReady"
              @click="fetchProviders"
            >
              获取Provider
            </VBtn>
            <VBtn
              color="primary"
              variant="tonal"
              prepend-icon="mdi-format-list-bulleted"
              :loading="loadingModels"
              :disabled="testingModel || loadingProviders || loadingMetadata || !apiReady"
              @click="fetchModels"
            >
              获取模型
            </VBtn>
            <VBtn
              color="secondary"
              variant="tonal"
              prepend-icon="mdi-database-search"
              :loading="loadingMetadata"
              :disabled="loadingModels || loadingProviders || testingModel || !apiReady"
              @click="fetchMetadata"
            >
              模型能力
            </VBtn>
            <VBtn
              color="success"
              variant="tonal"
              prepend-icon="mdi-check-circle-outline"
              :loading="testingModel"
              :disabled="loadingModels || loadingProviders || loadingMetadata || !apiReady"
              @click="testModel"
            >
              测试模型
            </VBtn>
          </VCol>
        </VRow>

        <VRow>
          <VCol cols="12" md="3">
            <VSwitch v-model="config.llm_use_proxy" label="使用代理服务器" hide-details />
          </VCol>
          <VCol cols="12" md="3">
            <VTextField v-model="config.llm_user_agent" label="User-Agent" placeholder="可选" />
          </VCol>
          <VCol cols="12" md="6">
            <VAlert
              v-if="apiError || apiMessage"
              class="api-feedback"
              :type="apiError ? 'error' : 'success'"
              variant="tonal"
              density="compact"
              :text="apiError || apiMessage"
            />
          </VCol>
        </VRow>
      </section>

      <section class="config-section">
        <div class="section-title">翻译参数</div>
        <VRow>
          <VCol cols="12" md="4">
            <VTextField v-model="config.context_window" label="上下文窗口大小" placeholder="5" />
          </VCol>
          <VCol cols="12" md="4">
            <VTextField v-model="config.max_retries" label="LLM 请求重试次数" placeholder="3" />
          </VCol>
          <VCol cols="12" md="4">
            <VSwitch v-model="config.enable_batch" label="启用批量翻译" hide-details />
          </VCol>
        </VRow>

        <VRow>
          <VCol cols="12" md="6">
            <VTextField v-model="config.batch_size" label="每批翻译行数" placeholder="20（建议不超过30）" />
          </VCol>
          <VCol cols="12" md="6">
            <VTextField v-model="config.parallel_workers" label="并发线程数" placeholder="10" />
          </VCol>
        </VRow>
      </section>

      <section class="config-section">
        <div class="section-title">Whisper 与输出</div>
        <VRow>
          <VCol cols="12" md="6">
            <VSelect
              v-model="config.asr_model_strategy"
              :items="asrModelStrategies"
              label="Whisper 模型策略"
              hint="自动策略按选中的主音轨元数据决定，不扫描整片，也不会因少量混杂对白切换模型"
              persistent-hint
            />
          </VCol>
          <VCol cols="12" md="6">
            <VSelect
              v-model="config.faster_whisper_model"
              :items="whisperModels"
              :label="config.asr_model_strategy === 'manual' ? '手动 Whisper 模型' : '手动模式模型'"
              :hint="config.asr_model_strategy === 'manual' ? '仅在手动策略下使用' : '切换到手动策略后生效'"
              persistent-hint
            />
          </VCol>
          <VCol cols="12" md="6">
            <VSelect v-model="config.subtitle_output_mode" :items="outputModes" label="字幕输出模式" />
          </VCol>
        </VRow>

        <VRow>
          <VCol cols="12" md="4">
              <VTextField v-model="config.max_segment_duration" label="每段字幕最大时长（秒）" placeholder="5.5" />
          </VCol>
          <VCol cols="12" md="4">
              <VTextField v-model="config.max_segment_chars" label="每段字幕最大字符数" placeholder="28" hint="会自动限制为显示规范的两行容量" persistent-hint />
          </VCol>
          <VCol cols="12" md="4">
            <VTextField v-model="config.file_size" label="文件最小大小（MB）" placeholder="10" />
          </VCol>
        </VRow>

        <VRow>
          <VCol cols="12" md="3"><VTextField v-model="config.subtitle_max_chars_per_line" label="中文每行最大字数" placeholder="14" /></VCol>
          <VCol cols="12" md="3"><VTextField v-model="config.subtitle_min_duration" label="字幕最短时长（秒）" placeholder="0.9" /></VCol>
          <VCol cols="12" md="3"><VTextField v-model="config.subtitle_max_duration" label="字幕最长时长（秒）" placeholder="5.5" /></VCol>
          <VCol cols="12" md="3"><VTextField v-model="config.subtitle_max_reading_speed" label="最大阅读速度（字/秒）" placeholder="14" /></VCol>
        </VRow>

        <VRow>
          <VCol cols="12">
            <VTextarea
              v-model="config.default_glossary"
              label="默认术语表"
              :rows="3"
              placeholder="每行一个术语，例如：Hamilton = 汉密尔顿；Eliza = 伊莱莎"
              hint="应用到所有新任务；联动提交时提供的本片术语表会优先覆盖。"
              persistent-hint
            />
          </VCol>
        </VRow>

        <VRow>
          <VCol cols="12" md="6">
            <VSelect v-model="config.translate_preference" :items="preferences" label="字幕源语言偏好" />
          </VCol>
          <VCol cols="12" md="3">
            <VSwitch v-model="config.auto_detect_language" label="自动检测语言" hide-details />
          </VCol>
          <VCol cols="12" md="3">
            <VSwitch v-model="config.proxy" label="使用代理下载模型" hide-details />
          </VCol>
        </VRow>
      </section>

      <section class="config-section">
        <div class="section-title">路径</div>
        <VRow>
          <VCol cols="12">
            <VTextarea
              v-model="config.path_whitelist"
              label="监控路径（每行一个）"
              :rows="3"
              placeholder="/mnt/media/movies&#10;/downloads"
              hint="目录变化时自动触发字幕生成"
              persistent-hint
            />
          </VCol>
          <VCol cols="12">
            <VTextarea
              v-model="config.path_list"
              label="媒体路径（手动执行时使用）"
              :rows="3"
              placeholder="绝对路径，每行一个，支持文件和文件夹"
            />
          </VCol>
        </VRow>
      </section>

      <div class="config-footer">
        <VBtn variant="text" prepend-icon="mdi-format-list-bulleted" @click="emit('switch')">查看任务</VBtn>
        <VSpacer />
        <VBtn variant="text" @click="emit('close')">关闭</VBtn>
        <VBtn color="primary" prepend-icon="mdi-content-save" :loading="saving" @click="save">保存</VBtn>
      </div>
    </div>

  </div>
</template>

<style scoped>
.autosub-config {
  background: rgb(var(--v-theme-background));
}

.config-shell {
  padding: 18px;
}

.config-section {
  margin-bottom: 20px;
}

.section-title {
  color: rgba(var(--v-theme-on-surface), 0.68);
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
}

.api-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.api-feedback {
  margin-top: 2px;
}

.config-footer {
  align-items: center;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  display: flex;
  gap: 10px;
  padding-top: 16px;
}
</style>
