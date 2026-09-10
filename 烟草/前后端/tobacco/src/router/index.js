// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import Home from '../views/Home.vue';
import Login from '../views/Login.vue';
import Register from '../views/Register.vue';
import Fertilization from '../views/Fertilization.vue';
import Pesticide from '../views/Pesticide.vue';
import Device from '../views/Device.vue';
import AnalysisLayout from '../views/AnalysisLayout.vue';
import Analysis from '../views/Analysis.vue';
import AnalysisDisease from '../views/AnalysisDisease.vue';
import Strategy from '../views/Strategy.vue';
import AI from '../views/AI.vue';

const routes = [
  { path: '/login', name: 'login', component: Login, meta: { guest: true } },
  { path: '/register', name: 'register', component: Register, meta: { guest: true } },
  {
    path: '/',
    name: 'home',
    component: Home
  },
  {
    path: '/fertilization',
    name: 'fertilization',
    component: Fertilization
  },
  {
    path: '/pesticide',
    name: 'pesticide',
    component: Pesticide
  },
  {
    path: '/device',
    name: 'device',
    component: Device
  },
  {
    path: '/analysis',
    name: 'analysis',
    component: AnalysisLayout,
    redirect: '/analysis/deficiency',
    children: [
      {
        path: 'deficiency',
        name: 'analysis-deficiency',
        component: Analysis
      },
      {
        path: 'disease',
        name: 'analysis-disease',
        component: AnalysisDisease
      }
    ]
  },
  {
    path: '/strategy',
    name: 'strategy',
    component: Strategy
  },
  {
    path: '/ai',
    name: 'ai',
    component: AI
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token');
  if (to.meta.guest) {
    if (token && (to.path === '/login' || to.path === '/register')) {
      next('/');
    } else {
      next();
    }
  } else {
    if (!token && to.path !== '/login') {
      next('/login');
    } else {
      next();
    }
  }
});

export default router;