import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    host: '0.0.0.0',
    port: 3002
    proxy: {
      '/api': {
        target: 'http://172.16.25.187:8000',
        changeOrigin: true
      }
    }
  }
})