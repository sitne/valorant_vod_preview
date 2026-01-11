import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api/analyze': 'http://localhost:8000',
      '/api/status': 'http://localhost:8000',
      '/api/stop': 'http://localhost:8000',
      '/api/rounds': 'http://localhost:8000',
      '/api/sessions': 'http://localhost:8000',
      '/static': 'http://localhost:8000',
      '/sessions': 'http://localhost:8000',
    }
  }
})
