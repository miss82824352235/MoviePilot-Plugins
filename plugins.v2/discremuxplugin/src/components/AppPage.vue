<script setup>
import Page from './Page.vue'

const props = defineProps({
  api: { type: Object, required: true },
})
</script>

<template>
  <Page :api="props.api" />
</template>
