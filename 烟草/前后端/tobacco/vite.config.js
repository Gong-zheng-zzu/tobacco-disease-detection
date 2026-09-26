import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';
import mkcert from 'vite-plugin-mkcert';
import path from 'path';

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), '');
    const proxyTarget = env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000';

    // GitHub Codespaces 环境检测。
    // 转发层已经提供 HTTPS，容器内再启用自签证书反而会导致握手失败，
    // 所以 Codespaces 下走 http，由 GitHub 的转发域名对外提供 HTTPS
    // （摄像头 getUserMedia 依赖的 secure context 由转发层满足）。
    const isCodespaces = !!env.CODESPACES;

    return {
        plugins: isCodespaces ? [vue()] : [vue(), mkcert()],
        server: {
            https: !isCodespaces,
            host: true,
            port: 5173,
            // Vite 6 默认拒绝非白名单 Host，Codespaces 转发域名必须显式允许
            allowedHosts: ['.app.github.dev', '.github.dev', 'localhost', '127.0.0.1'],
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
