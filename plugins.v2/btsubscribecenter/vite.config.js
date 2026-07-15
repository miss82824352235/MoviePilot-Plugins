import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import federation from '@originjs/vite-plugin-federation'
import { readdirSync, rmSync } from 'node:fs'

function removeUnreachableSharedAssets() {
  return {
    name: 'remove-unreachable-shared-assets',
    closeBundle() {
      rmSync(new URL('./dist/assets/__federation_shared_vuetify', import.meta.url), { recursive: true, force: true })
      for (const file of readdirSync(new URL('./dist/assets', import.meta.url))) {
        if (file.startsWith('__federation_shared_vuetify') || file.startsWith('__federation_shared_vuetify_')) {
          rmSync(new URL(`./dist/assets/${file}`, import.meta.url), { force: true })
        }
      }
    },
  }
}

export default defineConfig({
  plugins: [
    vue(),
    federation({
      name: 'BTSubscribeCenter',
      filename: 'remoteEntry.js',
      exposes: {
        './Page': './src/components/Page.vue',
        './Config': './src/components/Config.vue',
        './AppPage': './src/components/AppPage.vue',
      },
      shared: {
        vue: { requiredVersion: false, generate: false },
        vuetify: { requiredVersion: false, generate: false, singleton: true },
        'vuetify/styles': { requiredVersion: false, generate: false, singleton: true },
      },
      format: 'esm',
    }),
    removeUnreachableSharedAssets(),
  ],
  build: { target: 'esnext', minify: false, cssCodeSplit: true },
  css: {
    postcss: {
      plugins: [
        { postcssPlugin: 'internal:charset-removal', AtRule: { charset: atRule => { if (atRule.name === 'charset') atRule.remove() } } },
        { postcssPlugin: 'vuetify-filter', Root(root) { root.walkRules(rule => { if (rule.selector && (rule.selector.includes('.v-') || rule.selector.includes('.mdi-') || rule.selector.includes('.v_'))) rule.remove() }) } },
      ],
    },
  },
})
