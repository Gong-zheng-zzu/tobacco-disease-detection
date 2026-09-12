import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';
// import mkcert from 'vite-plugin-mkcert';
import path from 'path';

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), '');
    const proxyTarget = env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000';

    return {
        plugins: [vue()],
        server: {
            // https: true,
            host: true,
            port: 5173,
            proxy: {
                '/api': {
                    target: proxyTarget,
                    changeOrigin: true
                }
            }
        },
        resolve: {
            alias: {
                '@': path.resolve(__dirname, 'src')
            }
        }
    };
});