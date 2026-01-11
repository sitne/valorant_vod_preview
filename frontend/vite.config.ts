import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/analyze': 'http://localhost:8000',
      '/status': 'http://localhost:8000',
      '/stop': 'http://localhost:8000',
      '/rounds': 'http://localhost:8000',
      '/static': 'http://localhost:8000',
    }
  }
})
