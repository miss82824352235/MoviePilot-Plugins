import { importShared } from './__federation_fn_import-JrT3xvdd.js';

function unwrapResponse(payload) {
  if (payload == null) return payload
  if (typeof payload !== 'object') return payload
  if (Object.prototype.hasOwnProperty.call(payload, 'success') && payload.success === false) {
    const err = new Error(payload.message || '请求失败');
    err.response = payload;
    err.success = false;
    err.data = payload.data;
    throw err
  }
  if (Object.prototype.hasOwnProperty.call(payload, 'data') && Object.prototype.hasOwnProperty.call(payload, 'success')) {
    return payload.data
  }
  return payload
}

function getPluginApi(api, path, params = {}) {
  const pluginId = 'DiscRemuxPlugin';
  return api.get(`plugin/${pluginId}/${path}`, { params }).then((res) => unwrapResponse(res?.data ?? res))
}

function postPluginApi(api, path, body = {}) {
  const pluginId = 'DiscRemuxPlugin';
  return api.post(`plugin/${pluginId}/${path}`, body).then((res) => unwrapResponse(res?.data ?? res))
}

function normalizeError(err) {
  if (!err) return '未知错误'
  if (err.response?.message) return err.response.message
  if (err.message) return err.message
  return String(err)
}

const _export_sfc = (sfc, props) => {
  const target = sfc.__vccOpts || sfc;
  for (const [key, val] of props) {
    target[key] = val;
  }
  return target;
};

const {toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementVNode:_createElementVNode,createVNode:_createVNode,createElementBlock:_createElementBlock,renderList:_renderList,Fragment:_Fragment,withModifiers:_withModifiers,normalizeClass:_normalizeClass} = await importShared('vue');


const _hoisted_1 = { class: "disc-console" };
const _hoisted_2 = { class: "d-flex flex-wrap align-center justify-space-between ga-3" };
const _hoisted_3 = { class: "text-caption mt-2 opacity-80" };
const _hoisted_4 = { class: "d-flex flex-wrap ga-2" };
const _hoisted_5 = { class: "text-h6" };
const _hoisted_6 = { class: "text-h6" };
const _hoisted_7 = { class: "text-h6" };
const _hoisted_8 = { class: "text-h6" };
const _hoisted_9 = { class: "text-h6" };
const _hoisted_10 = { class: "text-h6" };
const _hoisted_11 = { class: "d-flex flex-wrap align-center ga-2 control-bar" };
const _hoisted_12 = {
  key: 2,
  class: "text-center text-medium-emphasis py-10"
};
const _hoisted_13 = { class: "d-flex align-start ga-3" };
const _hoisted_14 = { class: "flex-grow-1 min-w-0" };
const _hoisted_15 = { class: "d-flex flex-wrap align-center ga-2 mb-1" };
const _hoisted_16 = { class: "text-subtitle-1 font-weight-bold text-truncate" };
const _hoisted_17 = { class: "text-caption text-medium-emphasis text-truncate mb-2" };
const _hoisted_18 = { class: "d-flex flex-wrap ga-3 text-caption mb-2" };
const _hoisted_19 = { class: "text-body-2" };
const _hoisted_20 = {
  key: 0,
  class: "text-caption text-error mt-1"
};

const {computed,onBeforeUnmount,onMounted,reactive,ref} = await importShared('vue');


const _sfc_main = {
  __name: 'Page',
  props: {
  api: { type: Object, required: true },
},
  setup(__props) {

const props = __props;

const loading = ref(false);
const acting = ref(false);
const error = ref('');
const toast = ref('');
const status = reactive({
  current_task_id: null,
  queue_size: 0,
  worker_running: false,
  worker_count: 0,
  max_workers: 0,
  counts: {},
  tasks: [],
  updated_at: '',
  plugin: {},
});
const selected = ref(new Set());
const confirmDialog = reactive({
  open: false,
  action: '',
  title: '',
  message: '',
});
let timer = null;

const tasks = computed(() => status.tasks || []);
const selectedIds = computed(() => Array.from(selected.value));
const allSelected = computed(() => tasks.value.length > 0 && selectedIds.value.length === tasks.value.length);
const someSelected = computed(() => selectedIds.value.length > 0 && !allSelected.value);
const counts = computed(() => status.counts || {});
const activeCount = computed(() => {
  const c = counts.value;
  return (c.waiting || 0) + (c.scanning || 0) + (c.remuxing || 0) + (c.normalizing || 0) + (c.transferring || 0) + (c.verifying || 0) + (c.paused || 0)
});

const statusColor = {
  waiting: 'info',
  scanning: 'info',
  remuxing: 'primary',
  normalizing: 'primary',
  transferring: 'secondary',
  verifying: 'secondary',
  paused: 'warning',
  success: 'success',
  failed: 'error',
  skipped: 'grey',
  terminated: 'error',
  interrupted: 'warning',
};

const statusText = {
  waiting: '等待中',
  scanning: '扫描中',
  remuxing: '重封装',
  normalizing: '规范轨道',
  transferring: '整理入库',
  verifying: '验证中',
  paused: '已暂停',
  success: '成功',
  failed: '失败',
  skipped: '已跳过',
  terminated: '已终止',
  interrupted: '已中断',
};

function showToast(msg) {
  toast.value = msg;
  setTimeout(() => {
    if (toast.value === msg) toast.value = '';
  }, 3200);
}

function formatBytes(n) {
  const num = Number(n || 0);
  if (!num) return '-'
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let v = num;
  let i = 0;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i += 1;
  }
  return `${v.toFixed(i === 0 ? 0 : 1)} ${units[i]}`
}

function formatDuration(sec) {
  const s = Math.max(0, Math.floor(Number(sec || 0)));
  if (!s) return '-'
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const r = s % 60;
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m ${r}s`
  return `${r}s`
}

function formatEta(sec) {
  if (sec == null || sec === '' || Number.isNaN(Number(sec))) return '计算中'
  return formatDuration(sec)
}

function isSelected(id) {
  return selected.value.has(id)
}

function toggleSelect(id) {
  const next = new Set(selected.value);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  selected.value = next;
}

function toggleSelectAll() {
  if (allSelected.value) {
    selected.value = new Set();
    return
  }
  selected.value = new Set(tasks.value.map((t) => t.id));
}

async function refresh() {
  loading.value = true;
  error.value = '';
  try {
    const data = await getPluginApi(props.api, 'status');
    Object.assign(status, data || {});
    // 清理已不存在的选中项
    const ids = new Set((status.tasks || []).map((t) => t.id));
    selected.value = new Set(Array.from(selected.value).filter((id) => ids.has(id)));
  } catch (e) {
    error.value = normalizeError(e);
  } finally {
    loading.value = false;
  }
}

function openConfirm(action) {
  if (!selectedIds.value.length && action !== 'clear_finished') {
    showToast('请先选择任务');
    return
  }
  const map = {
    skip: {
      title: '确认跳过',
      message: '跳过会安全停止所选任务并继续队列下一项，不会删除源原盘。',
    },
    terminate: {
      title: '确认终止',
      message: '终止会停止所选任务并标记为已终止，不会删除源原盘和未验证输出。',
    },
    clear_finished: {
      title: '清理结束任务',
      message: '仅清理成功/失败/跳过/终止等结束记录，不影响运行中任务。',
    },
  };
  confirmDialog.action = action;
  confirmDialog.title = map[action]?.title || '确认操作';
  confirmDialog.message = map[action]?.message || '确认执行该操作？';
  confirmDialog.open = true;
}

async function doControl(action, confirm = false) {
  if (!selectedIds.value.length && !['clear_finished'].includes(action)) {
    showToast('请先选择任务');
    return
  }
  acting.value = true;
  error.value = '';
  try {
    const body = {
      action,
      task_ids: selectedIds.value,
      select_all: false,
      confirm,
    };
    if (action === 'clear_finished') {
      body.task_ids = [];
    }
    const data = await postPluginApi(props.api, 'task_control', body);
    showToast(data?.message || data?.data?.message || `动作 ${action} 完成`);
    confirmDialog.open = false;
    await refresh();
  } catch (e) {
    const msg = normalizeError(e);
    if (e?.response?.data?.need_confirm || /confirm=true/.test(msg)) {
      openConfirm(action);
    } else {
      error.value = msg;
      showToast(msg);
    }
  } finally {
    acting.value = false;
  }
}

async function confirmDanger() {
  const action = confirmDialog.action;
  confirmDialog.open = false;
  await doControl(action, true);
}

async function enqueueScan() {
  acting.value = true;
  error.value = '';
  try {
    await postPluginApi(props.api, 'enqueue_scan', { confirm: true });
    showToast('已提交扫描入队');
    await refresh();
  } catch (e) {
    error.value = normalizeError(e);
    showToast(error.value);
  } finally {
    acting.value = false;
  }
}

onMounted(async () => {
  await refresh();
  timer = setInterval(refresh, 3000);
});

onBeforeUnmount(() => {
  if (timer) clearInterval(timer);
});

return (_ctx, _cache) => {
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_checkbox = _resolveComponent("v-checkbox");
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_progress_linear = _resolveComponent("v-progress-linear");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_card_actions = _resolveComponent("v-card-actions");
  const _component_v_dialog = _resolveComponent("v-dialog");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    (toast.value)
      ? (_openBlock(), _createBlock(_component_v_alert, {
          key: 0,
          type: "success",
          variant: "tonal",
          density: "compact",
          class: "mb-3"
        }, {
          default: _withCtx(() => [
            _createTextVNode(_toDisplayString(toast.value), 1)
          ]),
          _: 1
        }))
      : _createCommentVNode("", true),
    (error.value)
      ? (_openBlock(), _createBlock(_component_v_alert, {
          key: 1,
          type: "error",
          variant: "tonal",
          density: "compact",
          class: "mb-3",
          closable: "",
          "onClick:close": _cache[0] || (_cache[0] = $event => (error.value = ''))
        }, {
          default: _withCtx(() => [
            _createTextVNode(_toDisplayString(error.value), 1)
          ]),
          _: 1
        }))
      : _createCommentVNode("", true),
    _createVNode(_component_v_card, {
      class: "mb-4 hero-card",
      variant: "tonal",
      color: "primary"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card_text, { class: "pa-4 pa-md-5" }, {
          default: _withCtx(() => [
            _createElementVNode("div", _hoisted_2, [
              _createElementVNode("div", null, [
                _cache[9] || (_cache[9] = _createElementVNode("div", { class: "text-h6 font-weight-bold" }, "蓝光原盘重封装任务台", -1)),
                _cache[10] || (_cache[10] = _createElementVNode("div", { class: "text-body-2 opacity-90 mt-1" }, " 源文件 ISO/BDMV → MakeMKV → 轨道规范 → MP 硬链接入库 ", -1)),
                _createElementVNode("div", _hoisted_3, " 版本 " + _toDisplayString(status.plugin?.version || '-') + " · 队列 " + _toDisplayString(status.queue_size || 0) + " · Worker " + _toDisplayString(status.worker_count ?? 0) + "/" + _toDisplayString(status.max_workers || status.plugin?.max_workers || 2) + " · 磁盘保护 " + _toDisplayString(status.plugin?.min_free_space_gb || 120) + "GB · 更新 " + _toDisplayString(status.updated_at || '-'), 1)
              ]),
              _createElementVNode("div", _hoisted_4, [
                _createVNode(_component_v_btn, {
                  color: "surface",
                  variant: "flat",
                  loading: loading.value,
                  onClick: refresh
                }, {
                  default: _withCtx(() => [...(_cache[11] || (_cache[11] = [
                    _createTextVNode(" 刷新 ", -1)
                  ]))]),
                  _: 1
                }, 8, ["loading"]),
                _createVNode(_component_v_btn, {
                  color: "surface",
                  variant: "flat",
                  loading: acting.value,
                  onClick: enqueueScan
                }, {
                  default: _withCtx(() => [...(_cache[12] || (_cache[12] = [
                    _createTextVNode(" 扫描入队 ", -1)
                  ]))]),
                  _: 1
                }, 8, ["loading"])
              ])
            ])
          ]),
          _: 1
        })
      ]),
      _: 1
    }),
    _createVNode(_component_v_row, {
      class: "mb-2",
      dense: ""
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_col, {
          cols: "6",
          sm: "4",
          md: "2"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              variant: "tonal",
              class: "stat-card"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_text, { class: "py-3" }, {
                  default: _withCtx(() => [
                    _cache[13] || (_cache[13] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "活动中", -1)),
                    _createElementVNode("div", _hoisted_5, _toDisplayString(activeCount.value), 1)
                  ]),
                  _: 1
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_v_col, {
          cols: "6",
          sm: "4",
          md: "2"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              variant: "tonal",
              color: "primary",
              class: "stat-card"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_text, { class: "py-3" }, {
                  default: _withCtx(() => [
                    _cache[14] || (_cache[14] = _createElementVNode("div", { class: "text-caption" }, "重封装", -1)),
                    _createElementVNode("div", _hoisted_6, _toDisplayString(counts.value.remuxing || 0), 1)
                  ]),
                  _: 1
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_v_col, {
          cols: "6",
          sm: "4",
          md: "2"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              variant: "tonal",
              color: "warning",
              class: "stat-card"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_text, { class: "py-3" }, {
                  default: _withCtx(() => [
                    _cache[15] || (_cache[15] = _createElementVNode("div", { class: "text-caption" }, "暂停", -1)),
                    _createElementVNode("div", _hoisted_7, _toDisplayString(counts.value.paused || 0), 1)
                  ]),
                  _: 1
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_v_col, {
          cols: "6",
          sm: "4",
          md: "2"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              variant: "tonal",
              color: "success",
              class: "stat-card"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_text, { class: "py-3" }, {
                  default: _withCtx(() => [
                    _cache[16] || (_cache[16] = _createElementVNode("div", { class: "text-caption" }, "成功", -1)),
                    _createElementVNode("div", _hoisted_8, _toDisplayString(counts.value.success || 0), 1)
                  ]),
                  _: 1
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_v_col, {
          cols: "6",
          sm: "4",
          md: "2"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              variant: "tonal",
              color: "error",
              class: "stat-card"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_text, { class: "py-3" }, {
                  default: _withCtx(() => [
                    _cache[17] || (_cache[17] = _createElementVNode("div", { class: "text-caption" }, "失败", -1)),
                    _createElementVNode("div", _hoisted_9, _toDisplayString(counts.value.failed || 0), 1)
                  ]),
                  _: 1
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_v_col, {
          cols: "6",
          sm: "4",
          md: "2"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              variant: "tonal",
              class: "stat-card"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_text, { class: "py-3" }, {
                  default: _withCtx(() => [
                    _cache[18] || (_cache[18] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "跳过/终止", -1)),
                    _createElementVNode("div", _hoisted_10, _toDisplayString((counts.value.skipped || 0) + (counts.value.terminated || 0)), 1)
                  ]),
                  _: 1
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }),
    _createVNode(_component_v_card, {
      class: "mb-4",
      variant: "flat"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card_text, { class: "pa-3" }, {
          default: _withCtx(() => [
            _createElementVNode("div", _hoisted_11, [
              _createVNode(_component_v_checkbox, {
                "model-value": allSelected.value,
                indeterminate: someSelected.value,
                label: "全选",
                "hide-details": "",
                density: "compact",
                "onUpdate:modelValue": toggleSelectAll
              }, null, 8, ["model-value", "indeterminate"]),
              _createVNode(_component_v_chip, {
                size: "small",
                variant: "tonal"
              }, {
                default: _withCtx(() => [
                  _createTextVNode("已选 " + _toDisplayString(selectedIds.value.length), 1)
                ]),
                _: 1
              }),
              _createVNode(_component_v_spacer),
              _createVNode(_component_v_btn, {
                size: "small",
                variant: "tonal",
                disabled: !selectedIds.value.length || acting.value,
                onClick: _cache[1] || (_cache[1] = $event => (doControl('pause')))
              }, {
                default: _withCtx(() => [...(_cache[19] || (_cache[19] = [
                  _createTextVNode("暂停", -1)
                ]))]),
                _: 1
              }, 8, ["disabled"]),
              _createVNode(_component_v_btn, {
                size: "small",
                variant: "tonal",
                color: "primary",
                disabled: !selectedIds.value.length || acting.value,
                onClick: _cache[2] || (_cache[2] = $event => (doControl('resume')))
              }, {
                default: _withCtx(() => [...(_cache[20] || (_cache[20] = [
                  _createTextVNode("继续", -1)
                ]))]),
                _: 1
              }, 8, ["disabled"]),
              _createVNode(_component_v_btn, {
                size: "small",
                variant: "tonal",
                color: "warning",
                disabled: !selectedIds.value.length || acting.value,
                onClick: _cache[3] || (_cache[3] = $event => (openConfirm('skip')))
              }, {
                default: _withCtx(() => [...(_cache[21] || (_cache[21] = [
                  _createTextVNode("跳过", -1)
                ]))]),
                _: 1
              }, 8, ["disabled"]),
              _createVNode(_component_v_btn, {
                size: "small",
                variant: "tonal",
                color: "error",
                disabled: !selectedIds.value.length || acting.value,
                onClick: _cache[4] || (_cache[4] = $event => (openConfirm('terminate')))
              }, {
                default: _withCtx(() => [...(_cache[22] || (_cache[22] = [
                  _createTextVNode("终止", -1)
                ]))]),
                _: 1
              }, 8, ["disabled"]),
              _createVNode(_component_v_btn, {
                size: "small",
                variant: "text",
                disabled: acting.value,
                onClick: _cache[5] || (_cache[5] = $event => (openConfirm('clear_finished')))
              }, {
                default: _withCtx(() => [...(_cache[23] || (_cache[23] = [
                  _createTextVNode("清理结束", -1)
                ]))]),
                _: 1
              }, 8, ["disabled"])
            ])
          ]),
          _: 1
        })
      ]),
      _: 1
    }),
    (!tasks.value.length)
      ? (_openBlock(), _createElementBlock("div", _hoisted_12, " 当前没有任务。可点“扫描入队”，或等待监听下载器命中 ISO/BDMV。 "))
      : _createCommentVNode("", true),
    _createVNode(_component_v_row, { dense: "" }, {
      default: _withCtx(() => [
        (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(tasks.value, (task) => {
          return (_openBlock(), _createBlock(_component_v_col, {
            key: task.id,
            cols: "12"
          }, {
            default: _withCtx(() => [
              _createVNode(_component_v_card, {
                class: _normalizeClass(["task-card", { selected: isSelected(task.id) }]),
                variant: "outlined",
                onClick: $event => (toggleSelect(task.id))
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_card_text, { class: "pa-4" }, {
                    default: _withCtx(() => [
                      _createElementVNode("div", _hoisted_13, [
                        _createVNode(_component_v_checkbox, {
                          "model-value": isSelected(task.id),
                          "hide-details": "",
                          density: "compact",
                          class: "mt-0",
                          onClick: _cache[6] || (_cache[6] = _withModifiers(() => {}, ["stop"])),
                          "onUpdate:modelValue": $event => (toggleSelect(task.id))
                        }, null, 8, ["model-value", "onUpdate:modelValue"]),
                        _createElementVNode("div", _hoisted_14, [
                          _createElementVNode("div", _hoisted_15, [
                            _createElementVNode("div", _hoisted_16, _toDisplayString(task.title), 1),
                            _createVNode(_component_v_chip, {
                              size: "x-small",
                              color: statusColor[task.status] || 'default',
                              variant: "tonal"
                            }, {
                              default: _withCtx(() => [
                                _createTextVNode(_toDisplayString(statusText[task.status] || task.status), 1)
                              ]),
                              _: 2
                            }, 1032, ["color"]),
                            _createVNode(_component_v_chip, {
                              size: "x-small",
                              variant: "outlined"
                            }, {
                              default: _withCtx(() => [
                                _createTextVNode(_toDisplayString((task.disc_type || 'unknown').toUpperCase()), 1)
                              ]),
                              _: 2
                            }, 1024),
                            _createVNode(_component_v_chip, {
                              size: "x-small",
                              variant: "text"
                            }, {
                              default: _withCtx(() => [
                                _createTextVNode(_toDisplayString(task.mode || '-'), 1)
                              ]),
                              _: 2
                            }, 1024)
                          ]),
                          _createElementVNode("div", _hoisted_17, _toDisplayString(task.source_path), 1),
                          _createElementVNode("div", _hoisted_18, [
                            _createElementVNode("span", null, "进度 " + _toDisplayString(Number(task.progress || 0).toFixed(1)) + "%", 1),
                            _createElementVNode("span", null, "已用 " + _toDisplayString(formatDuration(task.elapsed_seconds)), 1),
                            _createElementVNode("span", null, "ETA " + _toDisplayString(formatEta(task.eta_seconds)), 1),
                            _createElementVNode("span", null, "源大小 " + _toDisplayString(formatBytes(task.source_size)), 1)
                          ]),
                          _createVNode(_component_v_progress_linear, {
                            "model-value": Number(task.progress || 0),
                            height: "10",
                            rounded: "",
                            color: statusColor[task.status] || 'primary',
                            class: "mb-2"
                          }, null, 8, ["model-value", "color"]),
                          _createElementVNode("div", _hoisted_19, _toDisplayString(task.message || task.stage || '-'), 1),
                          (task.error)
                            ? (_openBlock(), _createElementBlock("div", _hoisted_20, _toDisplayString(task.error), 1))
                            : _createCommentVNode("", true)
                        ])
                      ])
                    ]),
                    _: 2
                  }, 1024)
                ]),
                _: 2
              }, 1032, ["class", "onClick"])
            ]),
            _: 2
          }, 1024))
        }), 128))
      ]),
      _: 1
    }),
    _createVNode(_component_v_dialog, {
      modelValue: confirmDialog.open,
      "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((confirmDialog.open) = $event)),
      "max-width": "480"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, null, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(confirmDialog.title), 1)
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(confirmDialog.message), 1)
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  variant: "text",
                  onClick: _cache[7] || (_cache[7] = $event => (confirmDialog.open = false))
                }, {
                  default: _withCtx(() => [...(_cache[24] || (_cache[24] = [
                    _createTextVNode("取消", -1)
                  ]))]),
                  _: 1
                }),
                _createVNode(_component_v_btn, {
                  color: "error",
                  variant: "flat",
                  loading: acting.value,
                  onClick: confirmDanger
                }, {
                  default: _withCtx(() => [...(_cache[25] || (_cache[25] = [
                    _createTextVNode("确认", -1)
                  ]))]),
                  _: 1
                }, 8, ["loading"])
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"])
  ]))
}
}

};
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-f0444d1d"]]);

export { Page as default };
