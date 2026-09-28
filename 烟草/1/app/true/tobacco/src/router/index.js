// src/router/index.js
import { createRouter, createWebHashHistory } from 'vue-router';
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
import DronePath from '../views/DronePath.vue';
import AI from '../views/AI.vue';
import Recognition from '../views/Recognition.vue';
import Workspaces from '../views/Workspaces.vue';
import WorkspaceDashboard from '../views/WorkspaceDashboard.vue';
import Harvest from '../views/Harvest.vue';
import Curing from '../views/Curing.vue';
import Quality from '../views/Quality.vue';
import Admin from '../views/Admin.vue';

const routes = [
  { path: '/login', name: 'login', component: Login, meta: { guest: true } },
  { path: '/register', name: 'register', component: Register, meta: { guest: true } },
  { path: '/workspaces', name: 'workspaces', component: Workspaces },
  { path: '/workspace-dashboard', name: 'workspace-dashboard', component: WorkspaceDashboard },
  { path: '/harvest', name: 'harvest', component: Harvest, meta: { roles: ['harvest', 'admin'] } },
  { path: '/curing', name: 'curing', component: Curing, meta: { roles: ['curing', 'admin'] } },
  { path: '/quality', name: 'quality', component: Quality, meta: { roles: ['quality', 'admin'] } },
  { path: '/admin', name: 'admin', component: Admin, meta: { roles: ['admin'] } },
  {
    path: '/',
    name: 'home',
    component: Home, meta: { roles: ['grower'] }
  },
  {
    path: '/fertilization',
    name: 'fertilization',
    component: Fertilization, meta: { roles: ['grower'] }
  },
  {
    path: '/pesticide',
    name: 'pesticide',
    component: Pesticide, meta: { roles: ['plant_protection'] }
  },
  {
    path: '/device',
    name: 'device',
    component: Device, meta: { roles: ['grower', 'plant_protection'] }
  },
  {
    path: '/analysis',
    name: 'analysis',
    component: AnalysisLayout, meta: { roles: ['grower', 'plant_protection'] },
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
    component: Strategy, meta: { roles: ['grower'] }
  },
  {
    path: '/recognition',
    name: 'recognition',
    component: Recognition, meta: { roles: ['grower', 'plant_protection'] }
  },
  {
    path: '/drone-path',
    name: 'drone-path',
    component: DronePath, meta: { roles: ['grower'] }
  },
  {
    path: '/ai',
    name: 'ai',
    component: AI, meta: { roles: ['grower', 'plant_protection', 'harvest', 'curing', 'quality', 'admin'] }
  }
];

const router = createRouter({
  history: createWebHashHistory(),
  routes
});

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token');
  if (to.meta.guest && token) return next('/');
  if (!to.meta.guest && !token) return next('/login');
  if (to.path === '/workspaces') return next();
  if (to.path === '/workspace-dashboard') {
    const roles = JSON.parse(localStorage.getItem('roles') || '[]');
    if (!roles.length) return next('/login');
    const active = localStorage.getItem('activeRole');
    if (active && !roles.some(role => role.code === active)) localStorage.removeItem('activeRole');
    return next();
  }
  if (to.meta.roles) {
    const roles = JSON.parse(localStorage.getItem('roles') || '[]').map(role => role.code);
    const active = localStorage.getItem('activeRole');
    const allowed = active ? [active] : roles;
    if (!to.meta.roles.some(role => allowed.includes(role))) return next('/workspace-dashboard');
  }
  next();
});

export default router;
