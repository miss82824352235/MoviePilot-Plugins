<script setup>
import { onMounted, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginBase: { type: Object, required: true },
})

const loading = ref(false)
const requesting = ref(false)
const error = ref('')
const notice = ref('')
const status = ref({})

function unwrap(response) {
  return response?.data?.data || response?.data || {}
}

function errorMessage(error, fallback) {
  return error?.response?.data?.detail || error?.message || fallback
}

async function loadStatus() {
  loading.value = true
  error.value = ''
  try {
    status.value = unwrap(await props.api.get(`${props.pluginBase}/runtime_update/status`))
  } catch (caught) {
    error.value = errorMessage(caught, '读取运行库更新状态失败')
  } finally {
    loading.value = false
  }
}

async function requestCheck() {
  if (requesting.value || !status.value.installed) return
  requesting.value = true
  error.value = ''
  notice.value = ''
  try {
    const result = unwrap(await props.api.post(`${props.pluginBase}/runtime_update/check`, {}))
    notice.value = result.message || '已请求检查更新'
    await loadStatus()
  } catch (caught) {
    error.value = errorMessage(caught, '请求运行库检查失败')
  } finally {
    requesting.value = false
  }
}

onMounted(loadStatus)
</script>

<template>
  <VCard class="mb-4" variant="tonal">
    <VCardTitle class="d-flex align-center text-subtitle-1 py-3">
      <VIcon class="mr-2" icon="mdi-update" />
      Whisper 运行库维护
      <VSpacer />
      <VChip :color="status.installed ? 'success' : 'warning'" size="small" variant="flat">
        {{ status.installed ? '已安装' : '未安装' }}
      </VChip>
    </VCardTitle>
    <VCardText class="pt-0">
      <div class="text-body-2 mb-2">{{ status.message || '正在读取宿主机更新器状态…' }}</div>
      <div v-if="status.installed" class="text-caption text-medium-emphasis">
        faster-whisper：{{ status.faster_whisper_version || '未知' }}
        <span class="mx-2">·</span>
        CTranslate2：{{ status.ctranslate2_version || '未知' }}
        <span v-if="status.checked_at" class="mx-2">·</span>
        <span v-if="status.checked_at">上次检查：{{ status.checked_at }}</span>
      </div>
      <div v-else class="text-caption text-medium-emphasis">{{ status.install_hint }}</div>
      <VAlert v-if="error" class="mt-3" density="compact" type="error" variant="tonal" :text="error" />
      <VAlert v-if="notice" class="mt-3" density="compact" type="success" variant="tonal" :text="notice" />
    </VCardText>
    <VCardActions class="pt-0 px-4 pb-3">
      <VBtn :loading="loading" size="small" variant="text" @click="loadStatus">刷新状态</VBtn>
      <VBtn :disabled="!status.installed" :loading="requesting" color="primary" size="small" variant="flat" @click="requestCheck">
        手动检查更新
      </VBtn>
      <span class="text-caption text-medium-emphasis ml-2">检查或升级均会在有任务时自动延后。</span>
    </VCardActions>
  </VCard>
</template>
