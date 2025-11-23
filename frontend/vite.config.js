import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    watch: {
      usePolling: true, // Necesario para que el Hot Reload funcione bien en Docker (especialmente en Windows/WSL)
    },
    host: true, // Escuchar en todas las interfaces (0.0.0.0)
    strictPort: true,
    port: 5173, 
  }
})