// src/main.js
import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import axios from 'axios';

axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  const activeRole = localStorage.getItem('activeRole');
  if (activeRole) config.headers['X-Active-Role'] = activeRole;
  return config;
});

const app = createApp(App);
app.use(router);
app.mount('#app');
