<script setup>
import { computed } from 'vue'

const props = defineProps({
  rootTab: { type: String, required: true },
  medias: { type: Array, default: () => [] },
  mediaTotal: { type: Number, default: 0 },
  mediaPage: { type: Number, default: 1 },
  mediaPageSize: { type: Number, default: 24 },
  searching: { type: Boolean, default: false },
  formatMediaType: { type: Function, required: true },
  mediaLabel: { type: Function, required: true },
  mediaStat: { type: Function, required: true },
  posterImageSrc: { type: Function, required: true },
  posterLoading: { type: Function, required: true },
  posterFetchPriority: { type: Function, required: true },
})

const pageCount = computed(() => Math.max(1, Math.ceil((props.mediaTotal || 0) / props.mediaPageSize)))
const rangeStart = computed(() => props.mediaTotal ? ((props.mediaPage - 1) * props.mediaPageSize) + 1 : 0)
const rangeEnd = computed(() => Math.min(props.mediaPage * props.mediaPageSize, props.mediaTotal || 0))

defineEmits([
  'select-media',
  'mark-poster-failed',
  'go-to-page',
  'set-page-size',
])
</script>

<template>
  <section v-if="rootTab === 'match' && medias.length" class="media-browser" aria-label="本地资源">
    <div class="media-list">
      <button
        v-for="(media, index) in medias"
        :key="media.id"
        class="media-card"
        @click="$emit('select-media', media)"
      >
        <div class="poster-frame">
          <img
            v-if="posterImageSrc(media)"
            :src="posterImageSrc(media)"
            :alt="mediaLabel(media)"
            :loading="posterLoading(index)"
            :fetchpriority="posterFetchPriority(index)"
            decoding="async"
            draggable="false"
            @error="$emit('mark-poster-failed', media)"
          >
          <span v-else>{{ formatMediaType(media.media_type) }}</span>
        </div>
        <div class="media-copy">
          <div class="media-type">{{ formatMediaType(media.media_type) }}</div>
          <h3>{{ mediaLabel(media) }}</h3>
          <p>{{ mediaStat(media) }}</p>
        </div>
      </button>
    </div>

    <footer class="pager-row">
      <div class="pager-summary">
        <span>每页 <button v-for="size in [24, 50, 80]" :key="size" type="button" :class="{ active: mediaPageSize === size }" @click="$emit('set-page-size', size)">{{ size }}</button></span>
        <span>{{ rangeStart }}–{{ rangeEnd }} / {{ mediaTotal }}</span>
      </div>
      <div class="pager-controls">
        <VBtn icon="mdi-page-first" size="small" variant="text" :disabled="searching || mediaPage <= 1" @click="$emit('go-to-page', 1)" />
        <VBtn icon="mdi-chevron-left" size="small" variant="text" :disabled="searching || mediaPage <= 1" @click="$emit('go-to-page', mediaPage - 1)" />
        <strong>{{ mediaPage }} / {{ pageCount }}</strong>
        <VBtn icon="mdi-chevron-right" size="small" variant="text" :disabled="searching || mediaPage >= pageCount" @click="$emit('go-to-page', mediaPage + 1)" />
        <VBtn icon="mdi-page-last" size="small" variant="text" :disabled="searching || mediaPage >= pageCount" @click="$emit('go-to-page', pageCount)" />
      </div>
    </footer>
  </section>

  <div v-else-if="rootTab === 'match'" class="empty-state">
    {{ searching ? '正在读取本地资源...' : '输入关键词搜索；留空搜索会显示最近整理的视频。' }}
  </div>
</template>

<style scoped>
.media-browser {
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  min-height: min(620px, calc(100dvh - 330px));
  overflow: hidden;
  border: 1px solid var(--smu-border);
  border-radius: 28px;
  background: var(--smu-card-bg-strong);
  box-shadow: var(--smu-shadow);
}

.media-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(152px, 1fr));
  gap: 16px;
  min-height: 0;
  padding: 20px;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
}

.media-card {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  width: 100%;
  min-width: 0;
  padding: 0;
  overflow: hidden;
  border: 1px solid var(--smu-border);
  border-radius: 18px;
  background: var(--smu-card-bg);
  color: inherit;
  text-align: left;
  transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
}

.media-card:hover {
  transform: translateY(-2px);
  border-color: var(--smu-border-active);
  background: var(--smu-card-bg-hover);
}

.poster-frame {
  display: grid;
  width: 100%;
  aspect-ratio: 2 / 3;
  place-items: center;
  overflow: hidden;
  background: var(--smu-poster-bg);
  color: var(--smu-accent);
}

.poster-frame img {
  display: block;
  width: 100%;
  height: 100%;
  background: var(--smu-poster-bg);
  object-fit: cover;
}

.media-copy {
  min-width: 0;
  padding: 10px 11px 12px;
}

.media-copy h3 {
  display: -webkit-box;
  margin: 4px 0 5px;
  overflow: hidden;
  font-size: 14px;
  line-height: 1.35;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.media-copy p {
  display: block;
  margin: 0;
  overflow: hidden;
  color: var(--smu-text-muted);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.media-type {
  color: var(--smu-accent);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.11em;
  text-transform: uppercase;
}

.pager-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  min-height: 58px;
  padding: 8px 16px;
  border-top: 1px solid var(--smu-border);
  background: var(--smu-card-bg-strong);
  color: var(--smu-text-muted);
  font-size: 13px;
}

.pager-summary,
.pager-controls {
  display: flex;
  align-items: center;
  gap: 6px;
}

.pager-summary button {
  padding: 1px 5px;
  border-radius: 5px;
  color: inherit;
  font: inherit;
}

.pager-summary button.active {
  background: var(--smu-accent-soft);
  color: var(--smu-accent);
  font-weight: 700;
}

.empty-state {
  padding: 28px 18px;
  border-radius: 22px;
  background: var(--smu-card-bg-soft);
  color: var(--smu-text-muted);
  text-align: center;
}

@media (max-width: 700px) {
  .media-browser {
    min-height: calc(100dvh - 290px);
    border-radius: 22px;
  }

  .media-list {
    grid-template-columns: repeat(auto-fill, minmax(132px, 1fr));
    gap: 12px;
    padding: 14px;
  }

  .pager-row {
    display: grid;
    justify-content: stretch;
    padding: 8px 10px;
  }

  .pager-summary,
  .pager-controls {
    justify-content: center;
  }
}
</style>