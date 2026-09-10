<template>
  <div class="nav-shell">
    <header class="top-bar">
      <div class="brand">
        <img :src="brandLogo" alt="" class="logo">
        <span class="title">叶擎慧航</span>
      </div>
      <div class="user-actions">
        <span class="username">{{ username || '用户' }}</span>
        <button class="logout-btn" @click="logout">退出</button>
      </div>
    </header>

    <nav class="bottom-tab">
      <button
        v-for="item in navItems"
        :key="item.path"
        class="tab-item"
        :class="{ active: isCurrentPath(item.path) }"
        @click="goToPage(item.path)"
      >
        <img :src="item.icon" alt="nav-icon" class="tab-icon">
        <span>{{ item.title }}</span>
      </button>
    </nav>
  </div>
</template>

<script>
import brandLogo from '@/assets/icons/brand-logo.png';
import homeIcon from '@/assets/icons/home-icon.png';
import fertilizationIcon from '@/assets/icons/fertilization-icon.png';
import deviceIcon from '@/assets/icons/device-icon.png';
import aiIcon from '@/assets/icons/ai-icon.png';
import strategyIcon from '@/assets/icons/strategy-icon.png';
import droneIcon from '@/assets/icons/sensor_icon/drone-icon.png';
import searchIcon from '@/assets/icons/search-icon.png';

export default {
  data() {
    return {
      brandLogo,
      username: localStorage.getItem('username') || '',
      navItems: [
        { path: '/', icon: homeIcon, title: '首页' },
        { path: '/recognition', icon: searchIcon, title: '识别' },
        { path: '/fertilization', icon: fertilizationIcon, title: '作业' },
        { path: '/device', icon: deviceIcon, title: '设备' },
        { path: '/strategy', icon: strategyIcon, title: '策略' },
        { path: '/drone-path', icon: droneIcon, title: '无人机' },
        { path: '/ai', icon: aiIcon, title: 'AI' }
      ]
    };
  },
  methods: {
    goToPage(path) {
      if (this.$route.path !== path) {
        this.$router.push(path);
      }
    },
    isCurrentPath(path) {
      if (path === '/') {
        return this.$route.path === '/';
      }
      if (path === '/fertilization') {
        return this.$route.path === '/fertilization' || this.$route.path === '/pesticide';
      }
      if (path === '/analysis/deficiency') {
        return this.$route.path.startsWith('/analysis');
      }
      return this.$route.path === path;
    },
    logout() {
      localStorage.removeItem('token');
      localStorage.removeItem('userId');
      localStorage.removeItem('username');
      this.$router.push('/login');
    }
  }
};
</script>

<style scoped>
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  background: linear-gradient(100deg, #1d8f62, #2cb478);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  box-shadow: 0 4px 14px rgba(18, 88, 57, 0.22);
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo {
  width: 32px;
  height: 32px;
  object-fit: contain;
}

.title {
  color: #fff;
  font-size: 17px;
  font-weight: 700;
}

.user-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #fff;
}

.username {
  font-size: 11px;
  opacity: 0.95;
}

.logout-btn {
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: rgba(255, 255, 255, 0.14);
  color: #fff;
  border-radius: 999px;
  padding: 5px 11px;
  font-size: 11px;
  cursor: pointer;
}

.bottom-tab {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  min-height: 56px;
  padding: 6px 6px calc(8px + env(safe-area-inset-bottom, 0px));
  background: #ffffff;
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 4px;
  border-top: 1px solid #dfebe3;
  box-shadow: 0 -4px 14px rgba(20, 49, 33, 0.08);
  z-index: 1000;
  box-sizing: border-box;
}

.tab-item {
  border: none;
  background: transparent;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  color: #6d8578;
  font-size: 10px;
  padding: 4px 1px;
}

.tab-item.active {
  background: #e9f7ef;
  color: #1f8758;
  font-weight: 700;
}

.tab-icon {
  width: 19px;
  height: 19px;
  object-fit: contain;
}

@media (min-width: 980px) {
  .top-bar {
    padding: 10px 16px;
  }

  .title {
    font-size: 18px;
  }

  .username {
    font-size: 12px;
  }

  .bottom-tab {
    max-width: 740px;
    left: 50%;
    transform: translateX(-50%);
    border-radius: 14px 14px 0 0;
  }
}
</style>
