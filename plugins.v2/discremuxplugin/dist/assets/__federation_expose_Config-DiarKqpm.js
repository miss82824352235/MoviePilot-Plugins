import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const {createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,createElementVNode:_createElementVNode,openBlock:_openBlock,createBlock:_createBlock} = await importShared('vue');


const {reactive,watch} = await importShared('vue');



const _sfc_main = {
  __name: 'Config',
  props: {
  initialConfig: { type: Object, default: () => ({}) },
},
  emits: ['save', 'close'],
  setup(__props, { emit: __emit }) {

const props = __props;
const emit = __emit;

const form = reactive({
  history_enabled: false,
  run_once: false,
  library_scan_enabled: false,
  library_scan_run_once: false,
  library_scan_cron: '30 3 * * *',
  source_root: '/PT/mp/源文件',
  source_roots: '/PT/mp/源文件\n/PT/ms/源文件',
  library_root: '/PT/mp/硬链接',
  library_roots: '/PT/mp/硬链接\n/PT/ms/硬链接',
  library_scan_max_items: 50,
  max_workers: 2,
  recent_days: 7,
  min_mkv_size_gb: 5,
  min_free_space_gb: 120,
  movies_only: true,
  source_disc_action: 'delete',
  library_disc_action: 'delete',
  refresh_media_server: true,
  cron_schedule: '0 3 * * *',
  intercept_enabled: false,
  intercept_transfer_mkv: true,
  normalize_tracks: true,
  reset_video_language: true,
  ...props.initialConfig,
});

watch(
  () => props.initialConfig,
  (v) => Object.assign(form, v || {}),
  { deep: true },
);

function save() {
  emit('save', { ...form });
}

return (_ctx, _cache) => {
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_switch = _resolveComponent("v-switch");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_divider = _resolveComponent("v-divider");
  const _component_v_textarea = _resolveComponent("v-textarea");
  const _component_v_select = _resolveComponent("v-select");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_card_actions = _resolveComponent("v-card-actions");
  const _component_v_card = _resolveComponent("v-card");

  return (_openBlock(), _createBlock(_component_v_card, {
    class: "pa-2",
    variant: "flat"
  }, {
    default: _withCtx(() => [
      _createVNode(_component_v_card_title, null, {
        default: _withCtx(() => [...(_cache[22] || (_cache[22] = [
          _createTextVNode("蓝光原盘重封装设置", -1)
        ]))]),
        _: 1
      }),
      _createVNode(_component_v_card_text, null, {
        default: _withCtx(() => [
          _createVNode(_component_v_alert, {
            type: "info",
            variant: "tonal",
            class: "mb-4",
            density: "compact"
          }, {
            default: _withCtx(() => [...(_cache[23] || (_cache[23] = [
              _createTextVNode(" 只从源文件目录查找 ISO/BDMV，重封装后通过 MoviePilot 硬链接入库。任务进度与控制请在插件详情页任务台查看。 ", -1)
            ]))]),
            _: 1
          }),
          _createVNode(_component_v_row, null, {
            default: _withCtx(() => [
              _createVNode(_component_v_col, { cols: "12" }, {
                default: _withCtx(() => [...(_cache[24] || (_cache[24] = [
                  _createElementVNode("div", { class: "text-subtitle-2 font-weight-bold" }, "监听与扫描", -1)
                ]))]),
                _: 1
              }),
              _createVNode(_component_v_col, {
                cols: "12",
                md: "4"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_switch, {
                    modelValue: form.intercept_enabled,
                    "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((form.intercept_enabled) = $event)),
                    label: "监听下载器原盘并接管整理",
                    "hide-details": ""
                  }, null, 8, ["modelValue"])
                ]),
                _: 1
              }),
              _createVNode(_component_v_col, {
                cols: "12",
                md: "4"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_switch, {
                    modelValue: form.intercept_transfer_mkv,
                    "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((form.intercept_transfer_mkv) = $event)),
                    label: "重封装后自动硬链接整理",
                    "hide-details": ""
                  }, null, 8, ["modelValue"])
                ]),
                _: 1
              }),
              _createVNode(_component_v_col, {
                cols: "12",
                md: "4"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_switch, {
                    modelValue: form.library_scan_enabled,
                    "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((form.library_scan_enabled) = $event)),
                    label: "启用源文件原盘扫描",
                    "hide-details": ""
                  }, null, 8, ["modelValue"])
                ]),
                _: 1
              }),
              _createVNode(_component_v_col, {
                cols: "12",
                md: "4"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_switch, {
                    modelValue: form.library_scan_run_once,
                    "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((form.library_scan_run_once) = $event)),
                    label: "立即扫描一次",
                    "hide-details": ""
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
                    modelValue: form.library_scan_interval_minutes,
                    "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((form.library_scan_interval_minutes) = $event)),
                    modelModifiers: { number: true },
                    type: "number",
                    label: "源文件补扫间隔(分钟)",
                    hint: "默认10；0=使用Cron",
                    "persistent-hint": "",
                    density: "comfortable"
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
                    modelValue: form.library_scan_cron,
                    "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((form.library_scan_cron) = $event)),
                    label: "扫描 Cron(间隔0时)",
                    "hide-details": "",
                    density: "comfortable"
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
                    modelValue: form.library_scan_max_items,
                    "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((form.library_scan_max_items) = $event)),
                    modelModifiers: { number: true },
                    type: "number",
                    label: "单次最多入队",
                    "hide-details": "",
                    density: "comfortable"
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
                    modelValue: form.max_workers,
                    "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((form.max_workers) = $event)),
                    modelModifiers: { number: true },
                    type: "number",
                    label: "并行 Worker 数",
                    hint: "建议1-2；空间紧张时用1",
                    "persistent-hint": "",
                    density: "comfortable"
                  }, null, 8, ["modelValue"])
                ]),
                _: 1
              }),
              _createVNode(_component_v_col, { cols: "12" }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_divider, { class: "my-2" })
                ]),
                _: 1
              }),
              _createVNode(_component_v_col, { cols: "12" }, {
                default: _withCtx(() => [...(_cache[25] || (_cache[25] = [
                  _createElementVNode("div", { class: "text-subtitle-2 font-weight-bold" }, "目录边界", -1)
                ]))]),
                _: 1
              }),
              _createVNode(_component_v_col, {
                cols: "12",
                md: "6"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_textarea, {
                    modelValue: form.source_roots,
                    "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((form.source_roots) = $event)),
                    label: "源文件根目录（每行一个）",
                    rows: "3",
                    "hide-details": "",
                    density: "comfortable"
                  }, null, 8, ["modelValue"])
                ]),
                _: 1
              }),
              _createVNode(_component_v_col, {
                cols: "12",
                md: "6"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_textarea, {
                    modelValue: form.library_roots,
                    "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => ((form.library_roots) = $event)),
                    label: "硬链接库根目录（仅发现/映射）",
                    rows: "3",
                    "hide-details": "",
                    density: "comfortable"
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
                    modelValue: form.source_root,
                    "onUpdate:modelValue": _cache[10] || (_cache[10] = $event => ((form.source_root) = $event)),
                    label: "默认源文件根",
                    "hide-details": "",
                    density: "comfortable"
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
                    modelValue: form.library_root,
                    "onUpdate:modelValue": _cache[11] || (_cache[11] = $event => ((form.library_root) = $event)),
                    label: "默认硬链接库根",
                    "hide-details": "",
                    density: "comfortable"
                  }, null, 8, ["modelValue"])
                ]),
                _: 1
              }),
              _createVNode(_component_v_col, { cols: "12" }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_divider, { class: "my-2" })
                ]),
                _: 1
              }),
              _createVNode(_component_v_col, { cols: "12" }, {
                default: _withCtx(() => [...(_cache[26] || (_cache[26] = [
                  _createElementVNode("div", { class: "text-subtitle-2 font-weight-bold" }, "处理策略", -1)
                ]))]),
                _: 1
              }),
              _createVNode(_component_v_col, {
                cols: "12",
                md: "4"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_switch, {
                    modelValue: form.movies_only,
                    "onUpdate:modelValue": _cache[12] || (_cache[12] = $event => ((form.movies_only) = $event)),
                    label: "只处理电影",
                    "hide-details": ""
                  }, null, 8, ["modelValue"])
                ]),
                _: 1
              }),
              _createVNode(_component_v_col, {
                cols: "12",
                md: "4"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_switch, {
                    modelValue: form.normalize_tracks,
                    "onUpdate:modelValue": _cache[13] || (_cache[13] = $event => ((form.normalize_tracks) = $event)),
                    label: "规范音轨/字幕命名",
                    "hide-details": ""
                  }, null, 8, ["modelValue"])
                ]),
                _: 1
              }),
              _createVNode(_component_v_col, {
                cols: "12",
                md: "4"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_switch, {
                    modelValue: form.reset_video_language,
                    "onUpdate:modelValue": _cache[14] || (_cache[14] = $event => ((form.reset_video_language) = $event)),
                    label: "视频轨语言设为 und",
                    "hide-details": ""
                  }, null, 8, ["modelValue"])
                ]),
                _: 1
              }),
              _createVNode(_component_v_col, {
                cols: "12",
                md: "4"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_switch, {
                    modelValue: form.refresh_media_server,
                    "onUpdate:modelValue": _cache[15] || (_cache[15] = $event => ((form.refresh_media_server) = $event)),
                    label: "整理后刷新媒体库",
                    "hide-details": ""
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
                    modelValue: form.min_mkv_size_gb,
                    "onUpdate:modelValue": _cache[16] || (_cache[16] = $event => ((form.min_mkv_size_gb) = $event)),
                    modelModifiers: { number: true },
                    type: "number",
                    label: "跳过阈值(GB)",
                    "hide-details": "",
                    density: "comfortable"
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
                    modelValue: form.min_free_space_gb,
                    "onUpdate:modelValue": _cache[17] || (_cache[17] = $event => ((form.min_free_space_gb) = $event)),
                    modelModifiers: { number: true },
                    type: "number",
                    label: "最低剩余空间(GB)",
                    hint: "低于阈值跳过重封装，避免写满磁盘",
                    "persistent-hint": "",
                    density: "comfortable"
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
                    modelValue: form.source_disc_action,
                    "onUpdate:modelValue": _cache[18] || (_cache[18] = $event => ((form.source_disc_action) = $event)),
                    items: [
              { title: '保留源原盘', value: 'keep' },
              { title: '删除源原盘并清理下载器任务', value: 'delete' },
            ],
                    label: "源文件原盘处理",
                    "hide-details": "",
                    density: "comfortable"
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
                    modelValue: form.library_disc_action,
                    "onUpdate:modelValue": _cache[19] || (_cache[19] = $event => ((form.library_disc_action) = $event)),
                    items: [
              { title: '保留旧入库原盘', value: 'keep' },
              { title: '写 .ignore', value: 'ignore' },
              { title: '删除旧入库原盘', value: 'delete' },
            ],
                    label: "硬链接库旧原盘处理",
                    "hide-details": "",
                    density: "comfortable"
                  }, null, 8, ["modelValue"])
                ]),
                _: 1
              }),
              _createVNode(_component_v_col, { cols: "12" }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_divider, { class: "my-2" })
                ]),
                _: 1
              }),
              _createVNode(_component_v_col, { cols: "12" }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_alert, {
                    type: "warning",
                    variant: "tonal",
                    density: "compact"
                  }, {
                    default: _withCtx(() => [...(_cache[27] || (_cache[27] = [
                      _createTextVNode(" 历史整理模式已停用提示位：`history_enabled` 仅兼容旧配置，实际不从硬链接库直接重封装。 ", -1)
                    ]))]),
                    _: 1
                  })
                ]),
                _: 1
              }),
              _createVNode(_component_v_col, {
                cols: "12",
                md: "4"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_switch, {
                    modelValue: form.history_enabled,
                    "onUpdate:modelValue": _cache[20] || (_cache[20] = $event => ((form.history_enabled) = $event)),
                    label: "兼容：历史模式开关",
                    "hide-details": ""
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
            onClick: _cache[21] || (_cache[21] = $event => (emit('close')))
          }, {
            default: _withCtx(() => [...(_cache[28] || (_cache[28] = [
              _createTextVNode("取消", -1)
            ]))]),
            _: 1
          }),
          _createVNode(_component_v_btn, {
            color: "primary",
            onClick: save
          }, {
            default: _withCtx(() => [...(_cache[29] || (_cache[29] = [
              _createTextVNode("保存", -1)
            ]))]),
            _: 1
          })
        ]),
        _: 1
      })
    ]),
    _: 1
  }))
}
}

};

export { _sfc_main as default };
