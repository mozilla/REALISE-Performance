import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: ['3c77-132-205-11-56.ngrok-free.app'],
    proxy: {
      '/api': {
        target: 'https://treeherder.mozilla.org/api/performance/summary/?repository=autoland&signature=5304496&framework=1&interval=1209600&all_data=true&replicates=false',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      }
    }
  }
})