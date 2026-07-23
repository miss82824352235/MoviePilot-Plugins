import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

const {createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,openBlock:_openBlock,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "swu-config" };

const {reactive,watch} = await importShared('vue');



const _sfc_main = {
  __name: 'Config',
  props: {
  modelValue: { type: Object, default: () => ({}) },
},
  emits: ['update:modelValue', 'change'],
  setup(__props, { emit: __emit }) {

const props = __props;
const emit = __emit;

const local = reactive({
  enabled: true,
  console_title: '字幕控制台',
  session_timeout: 3600,
  tg_entry_enabled: true,
  legacy_api_enabled: false,
  console_base_url: '',
  root_path: '',
  ...props.modelValue,
});

watch(
  local,
  () => {
    const payload = { ...local };
    emit('update:modelValue', payload);
    emit('change', payload);
  },
  { deep: true },
);

return (_ctx, _cache) => {
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_switch = _resolveComponent("v-switch");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_row = _resolveComponent("v-row");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_v_alert, {
      type: "info",
      variant: "tonal",
      density: "comfortable",
      class: "mb-4"
    }, {
      default: _withCtx(() => [...(_cache[7] || (_cache[7] = [
        _createTextVNode(" 字幕网页上传器通过桥接「海拉鲁字幕大师魔改版 / 字幕匹配」完成上传、在线、外挂管理与 AI 任务。 TG 入口命令：/subweb ", -1)
      ]))]),
      _: 1
    }),
    _createVNode(_component_v_row, { dense: "" }, {
      default: _withCtx(() => [
        _createVNode(_component_v_col, {
          cols: "12",
          md: "6"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_switch, {
              modelValue: local.enabled,
              "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((local.enabled) = $event)),
              label: "启用插件",
              color: "primary",
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
            _createVNode(_component_v_switch, {
              modelValue: local.tg_entry_enabled,
              "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((local.tg_entry_enabled) = $event)),
              label: "启用 TG /subweb 入口",
              color: "primary",
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
            _createVNode(_component_v_switch, {
              modelValue: local.legacy_api_enabled,
              "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((local.legacy_api_enabled) = $event)),
              label: "保留旧硬链接目录 API",
              color: "warning",
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
              modelValue: local.session_timeout,
              "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((local.session_timeout) = $event)),
              modelModifiers: { number: true },
              type: "number",
              label: "会话超时（秒）",
              density: "comfortable",
              variant: "outlined",
              "hide-details": ""
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        }),
        _createVNode(_component_v_col, { cols: "12" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_text_field, {
              modelValue: local.console_title,
              "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((local.console_title) = $event)),
              label: "操作台标题",
              density: "comfortable",
              variant: "outlined",
              "hide-details": ""
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        }),
        _createVNode(_component_v_col, { cols: "12" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_text_field, {
              modelValue: local.console_base_url,
              "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((local.console_base_url) = $event)),
              label: "操作台基础地址（公网/局域网，供 TG 打开）",
              hint: "例如 https://mp.example.com，不要填 127.0.0.1",
              "persistent-hint": "",
              density: "comfortable",
              variant: "outlined"
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        }),
        _createVNode(_component_v_col, { cols: "12" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_text_field, {
              modelValue: local.root_path,
              "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((local.root_path) = $event)),
              label: "旧版硬链接根路径（可选）",
              density: "comfortable",
              variant: "outlined",
              "hide-details": ""
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        })
      ]),
      _: 1
    })
  ]))
}
}

};
const Config = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-2d210d5e"]]);

export { Config as default };
