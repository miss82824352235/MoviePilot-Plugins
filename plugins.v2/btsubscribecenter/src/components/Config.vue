<script setup>
import { reactive, watch } from 'vue'
const props = defineProps({ initialConfig: { type: Object, default: () => ({}) } })
const emit = defineEmits(['save', 'close'])
const form = reactive({ ...props.initialConfig })
watch(() => props.initialConfig, v => Object.assign(form, v || {}), { deep: true })
function save() { emit('save', { ...form }) }
</script>
<template>
  <v-card class="pa-2" variant="flat">
    <v-card-title>BT/RSS 番剧订阅中心设置</v-card-title>
    <v-card-text>
      <v-alert type="info" variant="tonal" class="mb-4">
        主链路定位为 BT/RSS 动漫源候选准入与插件私有订阅管理；RSS 是补充来源，发布组不阻塞下载；真人/动漫识别冲突进入异常队列。
      </v-alert>
      <v-row>
        <v-col cols="12" md="4"><v-switch v-model="form.enabled" label="启用插件" /></v-col>
        <v-col cols="12" md="4"><v-switch v-model="form.onlyonce" label="立即刷新一次 RSS" /></v-col>
        <v-col cols="12" md="4"><v-switch v-model="form.auto_download" label="自动下载通过准入的候选" /></v-col>

        <v-col cols="12"><v-divider class="my-2" /></v-col>
        <v-col cols="12"><div class="text-subtitle-2 font-weight-bold">资源来源与初筛</div></v-col>
        <v-col cols="12" md="6"><v-text-field v-model="form.cron" label="RSS 补充刷新周期" hint="RSS 是补充来源，不是唯一主入口" persistent-hint /></v-col>
        <v-col cols="12" md="6"><v-text-field v-model="form.save_path" label="下载保存目录" /></v-col>
        <v-col cols="12"><v-textarea v-model="form.rss_urls" label="RSS / BT 来源地址" rows="4" hint="这些来源按用户筛选过的动漫/特摄源处理" persistent-hint /></v-col>
        <v-col cols="12" md="6"><v-text-field v-model="form.include" label="包含规则" /></v-col>
        <v-col cols="12" md="6"><v-text-field v-model="form.exclude" label="排除规则" /></v-col>
        <v-col cols="12" md="4"><v-text-field v-model="form.size_range" label="种子大小(GB)" /></v-col>
        <v-col cols="12" md="4"><v-switch v-model="form.proxy" label="RSS 使用代理" /></v-col>

        <v-col cols="12"><v-divider class="my-2" /></v-col>
        <v-col cols="12"><div class="text-subtitle-2 font-weight-bold">动漫/特摄准入</div></v-col>
        <v-col cols="12" md="4"><v-switch v-model="form.auto_discover_airing" label="自动发现当期新番" /></v-col>
        <v-col cols="12" md="4"><v-text-field v-model="form.airing_window_days" label="新番发现窗口天数" /></v-col>
        <v-col cols="12" md="4"><v-text-field v-model="form.early_episode_max" label="新番早期集上限" /></v-col>
        <v-col cols="12"><v-alert type="warning" variant="tonal" density="compact">发布组只用于统计、评分和后续整季包替换，不作为等待下载的阻塞条件。</v-alert></v-col>

        <v-col cols="12"><v-divider class="my-2" /></v-col>
        <v-col cols="12"><div class="text-subtitle-2 font-weight-bold">下载、入库与整季包替换</div></v-col>
        <v-col cols="12"><v-alert type="success" variant="tonal" density="compact">转移成功并确认入库后，插件会删除 qB 下载任务但保留源文件；订阅完结后按间隔监控同一发布者整季包，替换失败保留原单集记录。</v-alert></v-col>
        <v-col cols="12" md="6"><v-switch v-model="form.cleanup_after_library" label="入库后删除下载器任务（保留源文件）" /></v-col>
        <v-col cols="12" md="6"><v-text-field v-model="form.failure_cooldown_hours" label="失败状态冷却小时" hint="只记录页面状态和日志，不发送 MoviePilot 消息" persistent-hint /></v-col>
        <v-col cols="12" md="6"><v-switch v-model="form.replacement_watch_enabled" label="完结后监控同组整季包替换" /></v-col>
        <v-col cols="12" md="6"><v-text-field v-model="form.replacement_check_minutes" label="整季包检查间隔分钟" /></v-col>

        <v-col cols="12"><v-divider class="my-2" /></v-col>
        <v-col cols="12"><div class="text-subtitle-2 font-weight-bold">保留数量</div></v-col>
        <v-col cols="12" md="4"><v-text-field v-model="form.candidate_limit" label="候选保留数量" /></v-col>
        <v-col cols="12" md="4"><v-text-field v-model="form.history_limit" label="历史保留数量" /></v-col>
        <v-col cols="12" md="4"><v-text-field v-model="form.recognition_issue_limit" label="识别异常保留数量" /></v-col>
      </v-row>
    </v-card-text>
    <v-card-actions><v-spacer /><v-btn variant="text" @click="emit('close')">取消</v-btn><v-btn color="primary" @click="save">保存</v-btn></v-card-actions>
  </v-card>
</template>
