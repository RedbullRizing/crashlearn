import { defineConfig } from 'vite-plus'

export default defineConfig({
  publicDir: '../recordings',
  server: { open: true },
  build: {
    target: 'esnext',
    chunkSizeWarningLimit: 700,
    rolldownOptions: {
      output: {
        codeSplitting: { groups: [{ name: 'three', test: /node_modules[\\/]three/ }] },
      },
    },
  },
})
