const hostFromEnv = (import.meta.env.VITE_API_HOST || '').trim();

// The packaged Android app needs a stable absolute API endpoint. Local and
// staging builds can still override it with VITE_API_HOST at build time.
const DEFAULT_API_HOST = 'https://8.152.4.105';
export const API_HOST = (hostFromEnv || DEFAULT_API_HOST).replace(/\/$/, '');
export const API_BASE = `${API_HOST}/api`;
