import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const {createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,createElementVNode:_createElementVNode,openBlock:_openBlock,createBlock:_createBlock} = await importShared('vue');


const {reactive,watch} = await importShared('vue');


const _sfc_main = {
  __name: 'Config',
  props: { initialConfig: { type: Object, default: () => ({}) } },
  emits: ['save', 'close'],
  setup(__props, { emit: __emit }) {

const props = __props;
const emit = __emit;
const form = reactive({ ...props.initialConfig });
watch(() => props.initialConfig, v => Object.assign(form, v || {}), { deep: true });
function save() { emit('save', { ...form }); }

return (_ctx, _cache) => {
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_switch = _resolveComponent("v-switch");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_divider = _resolveComponent("v-divider");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_textarea = _resolveComponent("v-textarea");
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
        default: _withCtx(() => [...(_cache[21] || (_cache[21] = [
          _createTextVNode("BT/RSS 番剧订阅中心设置", -1)
        ]))]),
        _: 1
      }),
      _createVNode(_component_v_card_text, null, {
        default: _withCtx(() => [
          _createVNode(_component_v_alert, {
            type: "info",
            variant: "tonal",
            class: "mb-4"
          }, {
            default: _withCtx(() => [...(_cache[22] || (_cache[22] = [
              _createTextVNode(" 主链路定位为 BT/RSS 动漫源候选准入与插件私有订阅管理；RSS 是补充来源，发布组不阻塞下载；真人/动漫识别冲突进入异常队列。 ", -1)
            ]))]),
            _: 1
          }),
          _createVNode(_component_v_row, null, {
            default: _withCtx(() => [
              _createVNode(_component_v_col, {
                cols: "12",
                md: "4"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_switch, {
                    modelValue: form.enabled,
                    "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((form.enabled) = $event)),
                    label: "启用插件"
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
                    modelValue: form.onlyonce,
                    "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((form.onlyonce) = $event)),
                    label: "立即刷新一次 RSS"
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
                    modelValue: form.auto_download,
                    "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((form.auto_download) = $event)),
                    label: "自动下载通过准入的候选"
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
                default: _withCtx(() => [...(_cache[23] || (_cache[23] = [
                  _createElementVNode("div", { class: "text-subtitle-2 font-weight-bold" }, "资源来源与初筛", -1)
                ]))]),
                _: 1
              }),
              _createVNode(_component_v_col, {
                cols: "12",
                md: "6"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_text_field, {
                    modelValue: form.cron,
                    "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((form.cron) = $event)),
                    label: "RSS 补充刷新周期",
                    hint: "RSS 是补充来源，不是唯一主入口",
                    "persistent-hint": ""
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
                    modelValue: form.save_path,
                    "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((form.save_path) = $event)),
                    label: "下载保存目录"
                  }, null, 8, ["modelValue"])
                ]),
                _: 1
              }),
              _createVNode(_component_v_col, { cols: "12" }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_textarea, {
                    modelValue: form.rss_urls,
                    "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((form.rss_urls) = $event)),
                    label: "RSS / BT 来源地址",
                    rows: "4",
                    hint: "这些来源按用户筛选过的动漫/特摄源处理",
                    "persistent-hint": ""
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
                    modelValue: form.include,
                    "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((form.include) = $event)),
                    label: "包含规则"
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
                    modelValue: form.exclude,
                    "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((form.exclude) = $event)),
                    label: "排除规则"
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
                    modelValue: form.size_range,
                    "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((form.size_range) = $event)),
                    label: "种子大小(GB)"
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
                    modelValue: form.proxy,
                    "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => ((form.proxy) = $event)),
                    label: "RSS 使用代理"
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
                default: _withCtx(() => [...(_cache[24] || (_cache[24] = [
                  _createElementVNode("div", { class: "text-subtitle-2 font-weight-bold" }, "动漫/特摄准入", -1)
                ]))]),
                _: 1
              }),
              _createVNode(_component_v_col, {
                cols: "12",
                md: "4"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_switch, {
                    modelValue: form.auto_discover_airing,
                    "onUpdate:modelValue": _cache[10] || (_cache[10] = $event => ((form.auto_discover_airing) = $event)),
                    label: "自动发现当期新番"
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
                    modelValue: form.airing_window_days,
                    "onUpdate:modelValue": _cache[11] || (_cache[11] = $event => ((form.airing_window_days) = $event)),
                    label: "新番发现窗口天数"
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
                    modelValue: form.early_episode_max,
                    "onUpdate:modelValue": _cache[12] || (_cache[12] = $event => ((form.early_episode_max) = $event)),
                    label: "新番早期集上限"
                  }, null, 8, ["modelValue"])
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
                    default: _withCtx(() => [...(_cache[25] || (_cache[25] = [
                      _createTextVNode("发布组只用于统计、评分和后续整季包替换，不作为等待下载的阻塞条件。", -1)
                    ]))]),
                    _: 1
                  })
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
                  _createElementVNode("div", { class: "text-subtitle-2 font-weight-bold" }, "下载、入库与整季包替换", -1)
                ]))]),
                _: 1
              }),
              _createVNode(_component_v_col, { cols: "12" }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_alert, {
                    type: "success",
                    variant: "tonal",
                    density: "compact"
                  }, {
                    default: _withCtx(() => [...(_cache[27] || (_cache[27] = [
                      _createTextVNode("转移成功并确认入库后，插件会删除 qB 下载任务但保留源文件；订阅完结后按间隔监控同一发布者整季包，替换失败保留原单集记录。", -1)
                    ]))]),
                    _: 1
                  })
                ]),
                _: 1
              }),
              _createVNode(_component_v_col, {
                cols: "12",
                md: "6"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_switch, {
                    modelValue: form.cleanup_after_library,
                    "onUpdate:modelValue": _cache[13] || (_cache[13] = $event => ((form.cleanup_after_library) = $event)),
                    label: "入库后删除下载器任务（保留源文件）"
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
                    modelValue: form.failure_cooldown_hours,
                    "onUpdate:modelValue": _cache[14] || (_cache[14] = $event => ((form.failure_cooldown_hours) = $event)),
                    label: "失败状态冷却小时",
                    hint: "只记录页面状态和日志，不发送 MoviePilot 消息",
                    "persistent-hint": ""
                  }, null, 8, ["modelValue"])
                ]),
                _: 1
              }),
              _createVNode(_component_v_col, {
                cols: "12",
                md: "6"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_switch, {
                    modelValue: form.replacement_watch_enabled,
                    "onUpdate:modelValue": _cache[15] || (_cache[15] = $event => ((form.replacement_watch_enabled) = $event)),
                    label: "完结后监控同组整季包替换"
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
                    modelValue: form.replacement_check_minutes,
                    "onUpdate:modelValue": _cache[16] || (_cache[16] = $event => ((form.replacement_check_minutes) = $event)),
                    label: "整季包检查间隔分钟"
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
                default: _withCtx(() => [...(_cache[28] || (_cache[28] = [
                  _createElementVNode("div", { class: "text-subtitle-2 font-weight-bold" }, "保留数量", -1)
                ]))]),
                _: 1
              }),
              _createVNode(_component_v_col, {
                cols: "12",
                md: "4"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_text_field, {
                    modelValue: form.candidate_limit,
                    "onUpdate:modelValue": _cache[17] || (_cache[17] = $event => ((form.candidate_limit) = $event)),
                    label: "候选保留数量"
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
                    modelValue: form.history_limit,
                    "onUpdate:modelValue": _cache[18] || (_cache[18] = $event => ((form.history_limit) = $event)),
                    label: "历史保留数量"
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
                    modelValue: form.recognition_issue_limit,
                    "onUpdate:modelValue": _cache[19] || (_cache[19] = $event => ((form.recognition_issue_limit) = $event)),
                    label: "识别异常保留数量"
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
            onClick: _cache[20] || (_cache[20] = $event => (emit('close')))
          }, {
            default: _withCtx(() => [...(_cache[29] || (_cache[29] = [
              _createTextVNode("取消", -1)
            ]))]),
            _: 1
          }),
          _createVNode(_component_v_btn, {
            color: "primary",
            onClick: save
          }, {
            default: _withCtx(() => [...(_cache[30] || (_cache[30] = [
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
