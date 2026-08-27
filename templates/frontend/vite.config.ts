import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import Components from 'unplugin-vue-components/vite'
import { NaiveUiResolver } from 'unplugin-vue-components/resolvers'
import { fileURLToPath, URL } from 'node:url'
import { uiMockPlugin } from './mock/server'

export default defineConfig(({ mode }) => {
  // 只加载 VITE_* 前缀的环境变量（不读 CI 密钥等）
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  return {
    plugins: [
      tailwindcss(),
      vue(),
      // UI 预览模式（--only ui 生成，无后端）：dev 时用 mock API，admin/admin 可登录
      ...(env.VITE_USE_MOCK === 'true' ? [uiMockPlugin()] : []),
      Components({
        resolvers: [NaiveUiResolver()],
        dts: 'components.d.ts',
      }),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      host: '0.0.0.0',
      port: 3000,
      proxy: {
        '/api': {
          target: env.VITE_PROXY_TARGET || 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
      rollupOptions: {
        output: {
          manualChunks: {
            vue: ['vue', 'vue-router', 'pinia'],
            naive: ['naive-ui'],
          },
        },
      },
    },
  }
})
