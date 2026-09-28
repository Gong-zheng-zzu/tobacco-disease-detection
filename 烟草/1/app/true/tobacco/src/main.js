// src/main.js
import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import axios from 'axios';
import './style.css';

axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  const activeRole = localStorage.getItem('activeRole');
  if (activeRole) config.headers['X-Active-Role'] = activeRole;
  return config;
});

axios.interceptors.response.use(undefined, (error) => {
  if (error.response?.status === 401 && localStorage.getItem('token')) {
    ['token', 'userId', 'username', 'roles', 'activeRole'].forEach(key => localStorage.removeItem(key));
    if (router.currentRoute.value.path !== '/login') router.replace('/login');
  }
  return Promise.reject(error);
});

const app = createApp(App);
app.use(router);
app.mount('#app');
