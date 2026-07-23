<template>
  <div class="swu-config">
    <v-alert type="info" variant="tonal" density="comfortable" class="mb-4">
      字幕网页上传器通过桥接「海拉鲁字幕大师魔改版 / 字幕匹配」完成上传、在线、外挂管理与 AI 任务。
      TG 入口命令：/subweb
    </v-alert>
    <v-row dense>
      <v-col cols="12" md="6">
        <v-switch v-model="local.enabled" label="启用插件" color="primary" hide-details density="comfortable" />
      </v-col>
      <v-col cols="12" md="6">
        <v-switch v-model="local.tg_entry_enabled" label="启用 TG /subweb 入口" color="primary" hide-details density="comfortable" />
      </v-col>
      <v-col cols="12" md="6">
        <v-switch v-model="local.legacy_api_enabled" label="保留旧硬链接目录 API" color="warning" hide-details density="comfortable" />
      </v-col>
      <v-col cols="12" md="6">
        <v-text-field
          v-model.number="local.session_timeout"
          type="number"
          label="会话超时（秒）"
          density="comfortable"
          variant="outlined"
          hide-details
        />
      </v-col>
      <v-col cols="12">
        <v-text-field
          v-model="local.console_title"
          label="操作台标题"
          density="comfortable"
          variant="outlined"
          hide-details
        />
      </v-col>
      <v-col cols="12">
        <v-text-field
          v-model="local.console_base_url"
          label="操作台基础地址（公网/局域网，供 TG 打开）"
          hint="例如 https://mp.example.com，不要填 127.0.0.1"
          persistent-hint
          density="comfortable"
          variant="outlined"
        />
      </v-col>
      <v-col cols="12">
        <v-text-field
          v-model="local.root_path"
          label="旧版硬链接根路径（可选）"
          density="comfortable"
          variant="outlined"
          hide-details
        />
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['update:modelValue', 'change'])

const local = reactive({
  enabled: true,
  console_title: '字幕控制台',
  session_timeout: 3600,
  tg_entry_enabled: true,
  legacy_api_enabled: false,
  console_base_url: '',
  root_path: '',
  ...props.modelValue,
})

watch(
  local,
  () => {
    const payload = { ...local }
    emit('update:modelValue', payload)
    emit('change', payload)
  },
  { deep: true },
)
</script>

<style scoped>
.swu-config {
  padding: 4px 0 12px;
}
</style>
