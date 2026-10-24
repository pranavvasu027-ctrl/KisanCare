import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api/v1/disease-detection': {
        target: process.env.VITE_DISEASE_API_URL || 'http://localhost:8002',
        changeOrigin: true,
      },
      '/api/v1/specialists': {
        target: process.env.VITE_DISEASE_API_URL || 'http://localhost:8002',
        changeOrigin: true,
      },
      '/api/v1/diagnose': {
        target: process.env.VITE_DISEASE_API_URL || 'http://localhost:8002',
        changeOrigin: true,
      },
      '/api': {
        target: process.env.VITE_API_BASE_URL || 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
