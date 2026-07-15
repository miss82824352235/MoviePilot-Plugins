import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock} = await importShared('vue');


const {reactive,watch} = await importShared('vue');



const _sfc_main = {
  __name: 'Config',
  props: { initialConfig: { type: Object, default: () => ({}) } },
  emits: ['save', 'close', 'switch'],
  setup(__props, { emit: __emit }) {

const props = __props;
const emit = __emit;
const form = reactive({
  enabled: false,
  tg_entry_enabled: true,
  legacy_api_enabled: false,
  console_title: '字幕操作台',
  session_timeout: 3600,
  console_base_url: '',
  root_path: '',
});

watch(() => props.initialConfig, value => Object.assign(form, value || {}), { immediate: true, deep: true });
function save() { emit('save', { ...form }); }

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_switch = _resolveComponent("v-switch");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_card_actions = _resolveComponent("v-card-actions");
  const _component_v_card = _resolveComponent("v-card");

  return (_openBlock(), _createBlock(_component_v_card, {
    class: "subweb-config",
    variant: "flat"
  }, {
    default: _withCtx(() => [
      _createVNode(_component_v_card_title, { class: "d-flex align-center ga-2" }, {
        default: _withCtx(() => [
          _createVNode(_component_v_icon, {
            icon: "mdi-closed-caption-outline",
            color: "primary"
          }),
          _cache[8] || (_cache[8] = _createElementVNode("span", null, "字幕操作台设置", -1))
        ]),
        _: 1
      }),
      _createVNode(_component_v_card_text, null, {
        default: _withCtx(() => [
          _createVNode(_component_v_alert, {
            type: "info",
            variant: "tonal",
            class: "mb-4"
          }, {
            default: _withCtx(() => [...(_cache[9] || (_cache[9] = [
              _createTextVNode(" Vue 联邦 UI 已启用。TG /subweb 入口、桥接 API 与写操作确认保护保持不变。 ", -1)
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
                    color: "primary",
                    label: "启用插件",
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
                    modelValue: form.tg_entry_enabled,
                    "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((form.tg_entry_enabled) = $event)),
                    color: "primary",
                    label: "启用 /subweb 入口",
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
                    modelValue: form.legacy_api_enabled,
                    "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((form.legacy_api_enabled) = $event)),
                    color: "warning",
                    label: "保留旧硬链接 API",
                    "hide-details": ""
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
                    modelValue: form.console_title,
                    "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((form.console_title) = $event)),
                    label: "操作台标题",
                    variant: "outlined",
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
                    modelValue: form.session_timeout,
                    "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((form.session_timeout) = $event)),
                    modelModifiers: { number: true },
                    label: "会话超时（秒）",
                    type: "number",
                    variant: "outlined",
                    density: "comfortable"
                  }, null, 8, ["modelValue"])
                ]),
                _: 1
              }),
              _createVNode(_component_v_col, { cols: "12" }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_text_field, {
                    modelValue: form.console_base_url,
                    "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((form.console_base_url) = $event)),
                    label: "操作台外部访问地址",
                    placeholder: "https://mp.example.com",
                    hint: "TG 按钮必须使用手机可访问的 MoviePilot 地址；不要填写 127.0.0.1/localhost。",
                    "persistent-hint": "",
                    variant: "outlined",
                    density: "comfortable"
                  }, null, 8, ["modelValue"])
                ]),
                _: 1
              }),
              _createVNode(_component_v_col, { cols: "12" }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_text_field, {
                    modelValue: form.root_path,
                    "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((form.root_path) = $event)),
                    label: "旧硬链接根目录（仅旧 API 使用）",
                    placeholder: "/mnt/link",
                    variant: "outlined",
                    density: "comfortable"
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
      _createVNode(_component_v_card_actions, { class: "px-4 pb-4" }, {
        default: _withCtx(() => [
          _createVNode(_component_v_spacer),
          _createVNode(_component_v_btn, {
            variant: "text",
            onClick: _cache[7] || (_cache[7] = $event => (emit('close')))
          }, {
            default: _withCtx(() => [...(_cache[10] || (_cache[10] = [
              _createTextVNode("关闭", -1)
            ]))]),
            _: 1
          }),
          _createVNode(_component_v_btn, {
            color: "primary",
            variant: "flat",
            onClick: save
          }, {
            default: _withCtx(() => [...(_cache[11] || (_cache[11] = [
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
const Config = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-9e314db2"]]);

export { Config as default };
