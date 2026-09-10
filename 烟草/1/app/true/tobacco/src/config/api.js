const hostFromEnv = (import.meta.env.VITE_API_HOST || '').trim();

// Default keeps local dev behavior; build-time can override with VITE_API_HOST.
export const API_HOST = hostFromEnv || 'http://118.178.111.224:8081';
export const API_BASE = `${API_HOST}/api`;
