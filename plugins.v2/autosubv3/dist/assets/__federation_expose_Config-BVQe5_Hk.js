import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {createElementVNode:_createElementVNode,resolveComponent:_resolveComponent,createVNode:_createVNode,createTextVNode:_createTextVNode,withCtx:_withCtx,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "autosub-config" };
const _hoisted_2 = { class: "config-shell" };
const _hoisted_3 = { class: "config-section" };
const _hoisted_4 = { class: "config-section" };
const _hoisted_5 = { class: "config-section" };
const _hoisted_6 = { class: "config-section" };
const _hoisted_7 = { class: "config-section" };
const _hoisted_8 = { class: "config-footer" };

const {computed,reactive,ref,watch} = await importShared('vue');

const _sfc_main = {
  __name: 'Config',
  props: {
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
},
  emits: ['save', 'close', 'switch'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;

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
  max_segment_duration: 8,
  max_segment_chars: 50,
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
};

function normalizeModelValue(value) {
  if (typeof value === 'string') return value
  if (value && typeof value === 'object') {
    return String(value.value || value.id || value.model || value.title || value.name || '').trim()
  }
  return value == null ? '' : String(value).trim()
}

function normalizeInitialConfig(value = {}) {
  const merged = { ...defaultConfig, ...(value || {}) };
  merged.generation_mode = merged.generation_mode === 'fallback' ? 'fallback' : 'monitor';
  merged.llm_model = normalizeModelValue(merged.llm_model || merged.openai_model);
  merged.openai_model = normalizeModelValue(merged.openai_model || merged.llm_model);
  return merged
}

const config = reactive(normalizeInitialConfig(props.initialConfig));
const saving = ref(false);
const loadingModels = ref(false);
const testingModel = ref(false);
const error = ref('');
const apiError = ref('');
const apiMessage = ref('');
const remoteModels = ref([]);
const loadingProviders = ref(false);
const loadingMetadata = ref(false);
const providers = ref([]);
const metadata = ref(null);
const pluginBase = computed(() => `plugin/${props.pluginId || 'AutoSubv3'}`);
const apiReady = computed(() => typeof props.api?.post === 'function');

const whisperModels = [
  { title: 'tiny', value: 'tiny' },
  { title: 'base', value: 'base' },
  { title: 'small', value: 'small' },
  { title: 'medium', value: 'medium' },
  { title: 'distil-large-v3', value: 'distil-large-v3' },
  { title: 'large-v3', value: 'large-v3' },
  { title: 'large-v3-turbo', value: 'deepdml/faster-whisper-large-v3-turbo-ct2' },
];
const outputModes = [
  { title: '双语字幕（翻译+原文）', value: 'bilingual' },
  { title: '纯中文字幕', value: 'chinese_only' },
];
const asrModelStrategies = [
  { title: '自动：英语快速、非英语多语（推荐）', value: 'auto_english_fast' },
  { title: '手动指定模型', value: 'manual' },
];
const preferences = [
  { title: '仅英文', value: 'english_only' },
  { title: '英文优先', value: 'english_first' },
  { title: '原音优先', value: 'origin_first' },
];
const modelItems = computed(() => {
  const items = [...remoteModels.value];
  const model = normalizeModelValue(config.llm_model);
  if (model && !items.some(item => item.value === model)) {
    items.unshift({ title: model, value: model });
  }
  return items
});
watch(
  () => props.initialConfig,
  (value) => {
    Object.assign(config, normalizeInitialConfig(value));
  },
);
watch(
  () => [config.llm_provider, config.llm_base_url, config.llm_base_url_preset, config.llm_api_key, config.llm_model, config.llm_use_proxy, config.llm_user_agent],
  () => {
    apiError.value = '';
    apiMessage.value = '';
  },
);

function unwrapResponse(response) {
  return response?.data?.data || response?.data || response || {}
}

function normalizeModelList(payload) {
  const candidates = payload?.models || payload?.items || payload?.data?.models || payload?.data?.items || [];
  if (!Array.isArray(candidates)) return []
  return candidates
    .map((item) => {
      if (typeof item === 'string') return { title: item, value: item }
      const value = item?.value || item?.id || item?.model || '';
      const title = item?.title || item?.name || value;
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
})));
const selectedProvider = computed(() => providers.value.find((item) => item.id === config.llm_provider) || null);
const baseUrlPresetItems = computed(() => {
  const raw = selectedProvider.value?.base_url_presets || [];
  return raw.map((item) => ({ title: item.label || item.id || item.value, value: item.id || item.value, raw: item }))
});
const apiKeyLabel = computed(() => selectedProvider.value?.api_key_label || 'API Key');
const apiKeyHint = computed(() => selectedProvider.value?.api_key_hint || '填写当前 Provider 的 API Key。');
const baseUrlEditable = computed(() => selectedProvider.value?.base_url_editable !== false);
const supportsApiKey = computed(() => selectedProvider.value?.supports_api_key !== false);
const contextLimitText = computed(() => {
  const limit = metadata.value?.context_length || metadata.value?.input_token_limit;
  const output = metadata.value?.max_output_tokens || metadata.value?.output_token_limit;
  if (!limit && !output) return ''
  return `上下文上限 ${limit || '未知'}${output ? `，输出上限 ${output}` : ''}`
});

function normalizedConfigForSave() {
  const llmModel = normalizeModelValue(config.llm_model);
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
  const llmModel = normalizeModelValue(config.llm_model);
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
  loadingProviders.value = true;
  apiError.value = '';
  apiMessage.value = '';
  try {
    const data = unwrapResponse(await apiClient().get(`${pluginBase.value}/llm_providers`));
    providers.value = data.providers || data.items || [];
    if (selectedProvider.value && !config.llm_base_url && selectedProvider.value.default_base_url) {
      config.llm_base_url = selectedProvider.value.default_base_url;
    }
    apiMessage.value = `已获取 ${providers.value.length} 个 Provider`;
  } catch (err) {
    apiError.value = errorMessage(err, '获取 Provider 目录失败');
  } finally {
    loadingProviders.value = false;
  }
}

function applyProviderDefaults() {
  const provider = selectedProvider.value;
  if (!provider) return
  if (!config.llm_base_url && provider.default_base_url) config.llm_base_url = provider.default_base_url;
  if (!config.llm_base_url_preset && provider.base_url_presets?.length) {
    config.llm_base_url_preset = provider.base_url_presets[0].id || '';
  }
}

async function fetchModels() {
  loadingModels.value = true;
  apiError.value = '';
  apiMessage.value = '';
  try {
    const data = unwrapResponse(await apiClient().post(`${pluginBase.value}/llm_models`, apiPayload()));
    remoteModels.value = normalizeModelList(data);
    if (!remoteModels.value.length) {
      throw new Error('模型列表为空，请检查插件独立 Provider、Base URL 和 API Key')
    }
    apiMessage.value = `已获取 ${remoteModels.value.length} 个模型（${data.source || 'plugin_independent_llm_helper'}）`;
  } catch (err) {
    apiError.value = errorMessage(err, '获取模型列表失败');
  } finally {
    loadingModels.value = false;
  }
}

async function testModel() {
  testingModel.value = true;
  apiError.value = '';
  apiMessage.value = '';
  try {
    const response = await apiClient().post(`${pluginBase.value}/llm_test`, apiPayload());
    const data = unwrapResponse(response);
    apiMessage.value = responseMessage(response) || `模型 ${data.model || config.llm_model} 可用`;
  } catch (err) {
    apiError.value = errorMessage(err, '测试模型失败');
  } finally {
    testingModel.value = false;
  }
}

async function fetchMetadata() {
  loadingMetadata.value = true;
  apiError.value = '';
  apiMessage.value = '';
  try {
    const data = unwrapResponse(await apiClient().post(`${pluginBase.value}/llm_model_metadata`, apiPayload()));
    metadata.value = data;
    const limit = Number(data.context_length || data.input_token_limit || 0);
    if (limit && Number(config.llm_context_tokens || 0) > limit) {
      config.llm_context_tokens = String(limit);
    }
    apiMessage.value = `已读取模型能力：${data.name || data.model_id || config.llm_model}`;
  } catch (err) {
    apiError.value = errorMessage(err, '获取模型 metadata 失败');
  } finally {
    loadingMetadata.value = false;
  }
}

watch(() => config.llm_provider, () => applyProviderDefaults());

function save() {
  saving.value = true;
  error.value = '';
  try {
    const payload = normalizedConfigForSave();
    config.llm_model = payload.llm_model;
    config.openai_model = payload.openai_model;
    emit('save', payload);
  } catch (err) {
    error.value = err?.message || '保存配置失败';
  } finally {
    saving.value = false;
  }
}

return (_ctx, _cache) => {
  const _component_VSpacer = _resolveComponent("VSpacer");
  const _component_VBtn = _resolveComponent("VBtn");
  const _component_VToolbar = _resolveComponent("VToolbar");
  const _component_VDivider = _resolveComponent("VDivider");
  const _component_VAlert = _resolveComponent("VAlert");
  const _component_VSwitch = _resolveComponent("VSwitch");
  const _component_VCol = _resolveComponent("VCol");
  const _component_VRow = _resolveComponent("VRow");
  const _component_VSelect = _resolveComponent("VSelect");
  const _component_VTextField = _resolveComponent("VTextField");
  const _component_VCombobox = _resolveComponent("VCombobox");
  const _component_VTextarea = _resolveComponent("VTextarea");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_VToolbar, {
      density: "comfortable",
      color: "transparent"
    }, {
      default: _withCtx(() => [
        _cache[39] || (_cache[39] = _createElementVNode("div", { class: "text-h6 ms-3" }, "AI字幕生成配置", -1)),
        _createVNode(_component_VSpacer),
        _createVNode(_component_VBtn, {
          variant: "text",
          "prepend-icon": "mdi-format-list-bulleted",
          onClick: _cache[0] || (_cache[0] = $event => (emit('switch')))
        }, {
          default: _withCtx(() => [...(_cache[37] || (_cache[37] = [
            _createTextVNode("查看任务", -1)
          ]))]),
          _: 1
        }),
        _createVNode(_component_VBtn, {
          color: "primary",
          variant: "tonal",
          "prepend-icon": "mdi-content-save",
          loading: saving.value,
          onClick: save
        }, {
          default: _withCtx(() => [...(_cache[38] || (_cache[38] = [
            _createTextVNode("保存", -1)
          ]))]),
          _: 1
        }, 8, ["loading"]),
        _createVNode(_component_VBtn, {
          icon: "mdi-close",
          variant: "text",
          onClick: _cache[1] || (_cache[1] = $event => (emit('close')))
        })
      ]),
      _: 1
    }),
    _createVNode(_component_VDivider),
    _createElementVNode("div", _hoisted_2, [
      (error.value)
        ? (_openBlock(), _createBlock(_component_VAlert, {
            key: 0,
            class: "mb-4",
            type: "error",
            variant: "tonal",
            density: "compact",
            text: error.value
          }, null, 8, ["text"]))
        : _createCommentVNode("", true),
      _createElementVNode("section", _hoisted_3, [
        _cache[40] || (_cache[40] = _createElementVNode("div", { class: "section-title" }, "基础设置", -1)),
        _createVNode(_component_VRow, null, {
          default: _withCtx(() => [
            _createVNode(_component_VCol, {
              cols: "12",
              md: "6"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VSwitch, {
                  modelValue: config.generation_mode,
                  "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((config.generation_mode) = $event)),
                  label: "启用独立入库监控",
                  "true-value": "monitor",
                  "false-value": "fallback",
                  hint: "关闭后仍可接收字幕匹配联动任务和手动任务",
                  "persistent-hint": ""
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "3"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VSwitch, {
                  modelValue: config.enabled,
                  "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((config.enabled) = $event)),
                  label: "启用插件",
                  color: "primary",
                  "hide-details": ""
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "3"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VSwitch, {
                  modelValue: config.send_notify,
                  "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((config.send_notify) = $event)),
                  label: "发送通知",
                  "hide-details": ""
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_VRow, null, {
          default: _withCtx(() => [
            _createVNode(_component_VCol, {
              cols: "12",
              md: "3"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VSwitch, {
                  modelValue: config.clear_history,
                  "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((config.clear_history) = $event)),
                  label: "清理历史记录",
                  "hide-details": ""
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "3"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VSwitch, {
                  modelValue: config.process_new_only,
                  "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((config.process_new_only) = $event)),
                  label: "仅处理新增视频",
                  "hide-details": ""
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "3"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VSwitch, {
                  modelValue: config.run_now,
                  "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((config.run_now) = $event)),
                  label: "手动执行一次",
                  color: "secondary",
                  "hide-details": ""
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "3"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VSwitch, {
                  modelValue: config.translate_zh,
                  "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((config.translate_zh) = $event)),
                  label: "外语翻译成中文",
                  "hide-details": ""
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "3"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VSwitch, {
                  modelValue: config.skip_chinese,
                  "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => ((config.skip_chinese) = $event)),
                  label: "中文视频不翻译",
                  "hide-details": ""
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "3"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VSwitch, {
                  modelValue: config.enable_asr,
                  "onUpdate:modelValue": _cache[10] || (_cache[10] = $event => ((config.enable_asr) = $event)),
                  label: "允许 ASR 生成字幕",
                  "hide-details": ""
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _createElementVNode("section", _hoisted_4, [
        _cache[46] || (_cache[46] = _createElementVNode("div", { class: "section-title" }, "独立 LLM 配置", -1)),
        _createVNode(_component_VAlert, {
          type: "info",
          variant: "tonal",
          class: "mb-3",
          density: "comfortable"
        }, {
          default: _withCtx(() => [...(_cache[41] || (_cache[41] = [
            _createTextVNode(" AutoSubv3 使用独立 LLM 参数；这里只复刻 MoviePilot 智能助手的 Provider 目录、Base URL 预设、模型列表和 metadata 机制，不读取也不绑定 MP 智能助手当前填写值。 ", -1)
          ]))]),
          _: 1
        }),
        _createVNode(_component_VRow, null, {
          default: _withCtx(() => [
            _createVNode(_component_VCol, {
              cols: "12",
              md: "4"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VSelect, {
                  modelValue: config.llm_provider,
                  "onUpdate:modelValue": [
                    _cache[11] || (_cache[11] = $event => ((config.llm_provider) = $event)),
                    applyProviderDefaults
                  ],
                  items: providerItems.value,
                  "item-title": "title",
                  "item-value": "value",
                  label: "LLM Provider",
                  placeholder: "openai",
                  loading: loadingProviders.value
                }, null, 8, ["modelValue", "items", "loading"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "4"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VSelect, {
                  modelValue: config.llm_base_url_preset,
                  "onUpdate:modelValue": _cache[12] || (_cache[12] = $event => ((config.llm_base_url_preset) = $event)),
                  items: baseUrlPresetItems.value,
                  "item-title": "title",
                  "item-value": "value",
                  label: "Base URL 预设",
                  clearable: "",
                  placeholder: "使用 Provider 默认或自定义"
                }, null, 8, ["modelValue", "items"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "4"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VTextField, {
                  modelValue: config.llm_context_tokens,
                  "onUpdate:modelValue": _cache[13] || (_cache[13] = $event => ((config.llm_context_tokens) = $event)),
                  label: "上下文 Token 上限",
                  hint: contextLimitText.value || '可按模型 metadata 建议填写',
                  "persistent-hint": ""
                }, null, 8, ["modelValue", "hint"])
              ]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_VRow, null, {
          default: _withCtx(() => [
            _createVNode(_component_VCol, {
              cols: "12",
              md: "6"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VTextField, {
                  modelValue: config.llm_base_url,
                  "onUpdate:modelValue": _cache[14] || (_cache[14] = $event => ((config.llm_base_url) = $event)),
                  label: "LLM Base URL",
                  placeholder: "https://api.example.com/v1",
                  disabled: !baseUrlEditable.value
                }, null, 8, ["modelValue", "disabled"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "6"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VTextField, {
                  modelValue: config.llm_api_key,
                  "onUpdate:modelValue": _cache[15] || (_cache[15] = $event => ((config.llm_api_key) = $event)),
                  label: apiKeyLabel.value,
                  type: "password",
                  placeholder: apiKeyHint.value,
                  disabled: !supportsApiKey.value
                }, null, 8, ["modelValue", "label", "placeholder", "disabled"])
              ]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_VRow, { align: "center" }, {
          default: _withCtx(() => [
            _createVNode(_component_VCol, {
              cols: "12",
              md: "6"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VCombobox, {
                  "model-value": normalizeModelValue(config.llm_model),
                  items: modelItems.value,
                  "item-title": "title",
                  "item-value": "value",
                  label: "LLM模型名称",
                  placeholder: "选择或填写模型 ID",
                  "onUpdate:modelValue": _cache[16] || (_cache[16] = $event => (config.llm_model = normalizeModelValue($event)))
                }, null, 8, ["model-value", "items"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "6",
              class: "api-actions"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VBtn, {
                  color: "secondary",
                  variant: "tonal",
                  "prepend-icon": "mdi-cloud-search",
                  loading: loadingProviders.value,
                  disabled: loadingModels.value || testingModel.value || loadingMetadata.value || !apiReady.value,
                  onClick: fetchProviders
                }, {
                  default: _withCtx(() => [...(_cache[42] || (_cache[42] = [
                    _createTextVNode(" 获取Provider ", -1)
                  ]))]),
                  _: 1
                }, 8, ["loading", "disabled"]),
                _createVNode(_component_VBtn, {
                  color: "primary",
                  variant: "tonal",
                  "prepend-icon": "mdi-format-list-bulleted",
                  loading: loadingModels.value,
                  disabled: testingModel.value || loadingProviders.value || loadingMetadata.value || !apiReady.value,
                  onClick: fetchModels
                }, {
                  default: _withCtx(() => [...(_cache[43] || (_cache[43] = [
                    _createTextVNode(" 获取模型 ", -1)
                  ]))]),
                  _: 1
                }, 8, ["loading", "disabled"]),
                _createVNode(_component_VBtn, {
                  color: "secondary",
                  variant: "tonal",
                  "prepend-icon": "mdi-database-search",
                  loading: loadingMetadata.value,
                  disabled: loadingModels.value || loadingProviders.value || testingModel.value || !apiReady.value,
                  onClick: fetchMetadata
                }, {
                  default: _withCtx(() => [...(_cache[44] || (_cache[44] = [
                    _createTextVNode(" 模型能力 ", -1)
                  ]))]),
                  _: 1
                }, 8, ["loading", "disabled"]),
                _createVNode(_component_VBtn, {
                  color: "success",
                  variant: "tonal",
                  "prepend-icon": "mdi-check-circle-outline",
                  loading: testingModel.value,
                  disabled: loadingModels.value || loadingProviders.value || loadingMetadata.value || !apiReady.value,
                  onClick: testModel
                }, {
                  default: _withCtx(() => [...(_cache[45] || (_cache[45] = [
                    _createTextVNode(" 测试模型 ", -1)
                  ]))]),
                  _: 1
                }, 8, ["loading", "disabled"])
              ]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_VRow, null, {
          default: _withCtx(() => [
            _createVNode(_component_VCol, {
              cols: "12",
              md: "3"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VSwitch, {
                  modelValue: config.llm_use_proxy,
                  "onUpdate:modelValue": _cache[17] || (_cache[17] = $event => ((config.llm_use_proxy) = $event)),
                  label: "使用代理服务器",
                  "hide-details": ""
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "3"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VTextField, {
                  modelValue: config.llm_user_agent,
                  "onUpdate:modelValue": _cache[18] || (_cache[18] = $event => ((config.llm_user_agent) = $event)),
                  label: "User-Agent",
                  placeholder: "可选"
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "6"
            }, {
              default: _withCtx(() => [
                (apiError.value || apiMessage.value)
                  ? (_openBlock(), _createBlock(_component_VAlert, {
                      key: 0,
                      class: "api-feedback",
                      type: apiError.value ? 'error' : 'success',
                      variant: "tonal",
                      density: "compact",
                      text: apiError.value || apiMessage.value
                    }, null, 8, ["type", "text"]))
                  : _createCommentVNode("", true)
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _createElementVNode("section", _hoisted_5, [
        _cache[47] || (_cache[47] = _createElementVNode("div", { class: "section-title" }, "翻译参数", -1)),
        _createVNode(_component_VRow, null, {
          default: _withCtx(() => [
            _createVNode(_component_VCol, {
              cols: "12",
              md: "4"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VTextField, {
                  modelValue: config.context_window,
                  "onUpdate:modelValue": _cache[19] || (_cache[19] = $event => ((config.context_window) = $event)),
                  label: "上下文窗口大小",
                  placeholder: "5"
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "4"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VTextField, {
                  modelValue: config.max_retries,
                  "onUpdate:modelValue": _cache[20] || (_cache[20] = $event => ((config.max_retries) = $event)),
                  label: "LLM 请求重试次数",
                  placeholder: "3"
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "4"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VSwitch, {
                  modelValue: config.enable_batch,
                  "onUpdate:modelValue": _cache[21] || (_cache[21] = $event => ((config.enable_batch) = $event)),
                  label: "启用批量翻译",
                  "hide-details": ""
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_VRow, null, {
          default: _withCtx(() => [
            _createVNode(_component_VCol, {
              cols: "12",
              md: "6"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VTextField, {
                  modelValue: config.batch_size,
                  "onUpdate:modelValue": _cache[22] || (_cache[22] = $event => ((config.batch_size) = $event)),
                  label: "每批翻译行数",
                  placeholder: "20（建议不超过30）"
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "6"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VTextField, {
                  modelValue: config.parallel_workers,
                  "onUpdate:modelValue": _cache[23] || (_cache[23] = $event => ((config.parallel_workers) = $event)),
                  label: "并发线程数",
                  placeholder: "10"
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _createElementVNode("section", _hoisted_6, [
        _cache[48] || (_cache[48] = _createElementVNode("div", { class: "section-title" }, "Whisper 与输出", -1)),
        _createVNode(_component_VRow, null, {
          default: _withCtx(() => [
            _createVNode(_component_VCol, {
              cols: "12",
              md: "6"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VSelect, {
                  modelValue: config.asr_model_strategy,
                  "onUpdate:modelValue": _cache[24] || (_cache[24] = $event => ((config.asr_model_strategy) = $event)),
                  items: asrModelStrategies,
                  label: "Whisper 模型策略",
                  hint: "自动策略按选中的主音轨元数据决定，不扫描整片，也不会因少量混杂对白切换模型",
                  "persistent-hint": ""
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "6"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VSelect, {
                  modelValue: config.faster_whisper_model,
                  "onUpdate:modelValue": _cache[25] || (_cache[25] = $event => ((config.faster_whisper_model) = $event)),
                  items: whisperModels,
                  label: config.asr_model_strategy === 'manual' ? '手动 Whisper 模型' : '手动模式模型',
                  hint: config.asr_model_strategy === 'manual' ? '仅在手动策略下使用' : '切换到手动策略后生效',
                  "persistent-hint": ""
                }, null, 8, ["modelValue", "label", "hint"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "6"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VSelect, {
                  modelValue: config.subtitle_output_mode,
                  "onUpdate:modelValue": _cache[26] || (_cache[26] = $event => ((config.subtitle_output_mode) = $event)),
                  items: outputModes,
                  label: "字幕输出模式"
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_VRow, null, {
          default: _withCtx(() => [
            _createVNode(_component_VCol, {
              cols: "12",
              md: "4"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VTextField, {
                  modelValue: config.max_segment_duration,
                  "onUpdate:modelValue": _cache[27] || (_cache[27] = $event => ((config.max_segment_duration) = $event)),
                  label: "每段字幕最大时长（秒）",
                  placeholder: "8"
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "4"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VTextField, {
                  modelValue: config.max_segment_chars,
                  "onUpdate:modelValue": _cache[28] || (_cache[28] = $event => ((config.max_segment_chars) = $event)),
                  label: "每段字幕最大字符数",
                  placeholder: "50"
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "4"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VTextField, {
                  modelValue: config.file_size,
                  "onUpdate:modelValue": _cache[29] || (_cache[29] = $event => ((config.file_size) = $event)),
                  label: "文件最小大小（MB）",
                  placeholder: "10"
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_VRow, null, {
          default: _withCtx(() => [
            _createVNode(_component_VCol, {
              cols: "12",
              md: "6"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VSelect, {
                  modelValue: config.translate_preference,
                  "onUpdate:modelValue": _cache[30] || (_cache[30] = $event => ((config.translate_preference) = $event)),
                  items: preferences,
                  label: "字幕源语言偏好"
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "3"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VSwitch, {
                  modelValue: config.auto_detect_language,
                  "onUpdate:modelValue": _cache[31] || (_cache[31] = $event => ((config.auto_detect_language) = $event)),
                  label: "自动检测语言",
                  "hide-details": ""
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "3"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VSwitch, {
                  modelValue: config.proxy,
                  "onUpdate:modelValue": _cache[32] || (_cache[32] = $event => ((config.proxy) = $event)),
                  label: "使用代理下载模型",
                  "hide-details": ""
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _createElementVNode("section", _hoisted_7, [
        _cache[49] || (_cache[49] = _createElementVNode("div", { class: "section-title" }, "路径", -1)),
        _createVNode(_component_VRow, null, {
          default: _withCtx(() => [
            _createVNode(_component_VCol, { cols: "12" }, {
              default: _withCtx(() => [
                _createVNode(_component_VTextarea, {
                  modelValue: config.path_whitelist,
                  "onUpdate:modelValue": _cache[33] || (_cache[33] = $event => ((config.path_whitelist) = $event)),
                  label: "监控路径（每行一个）",
                  rows: 3,
                  placeholder: "/mnt/media/movies\n/downloads",
                  hint: "目录变化时自动触发字幕生成",
                  "persistent-hint": ""
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            }),
            _createVNode(_component_VCol, { cols: "12" }, {
              default: _withCtx(() => [
                _createVNode(_component_VTextarea, {
                  modelValue: config.path_list,
                  "onUpdate:modelValue": _cache[34] || (_cache[34] = $event => ((config.path_list) = $event)),
                  label: "媒体路径（手动执行时使用）",
                  rows: 3,
                  placeholder: "绝对路径，每行一个，支持文件和文件夹"
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _createElementVNode("div", _hoisted_8, [
        _createVNode(_component_VBtn, {
          variant: "text",
          "prepend-icon": "mdi-format-list-bulleted",
          onClick: _cache[35] || (_cache[35] = $event => (emit('switch')))
        }, {
          default: _withCtx(() => [...(_cache[50] || (_cache[50] = [
            _createTextVNode("查看任务", -1)
          ]))]),
          _: 1
        }),
        _createVNode(_component_VSpacer),
        _createVNode(_component_VBtn, {
          variant: "text",
          onClick: _cache[36] || (_cache[36] = $event => (emit('close')))
        }, {
          default: _withCtx(() => [...(_cache[51] || (_cache[51] = [
            _createTextVNode("关闭", -1)
          ]))]),
          _: 1
        }),
        _createVNode(_component_VBtn, {
          color: "primary",
          "prepend-icon": "mdi-content-save",
          loading: saving.value,
          onClick: save
        }, {
          default: _withCtx(() => [...(_cache[52] || (_cache[52] = [
            _createTextVNode("保存", -1)
          ]))]),
          _: 1
        }, 8, ["loading"])
      ])
    ])
  ]))
}
}

};
const Config = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-5162b9a6"]]);

export { Config as default };
