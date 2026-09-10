<template>
  <div>
    <header class="header">
      <div class="logo-container">
        <img :src="brandLogo" alt="" class="logo">
        <h1 class="title">叶擎慧航</h1>
      </div>
        <div class="user-center">
          <span class="username">{{ username || '用户' }}</span>
          <span class="logout-btn" @click="logout">退出登录</span>
        </div>
    </header>

    <nav class="nav">
      <ul class="nav-list">
        <li
          v-for="(item, index) in navItems"
          :key="index"
          class="nav-item-wrapper"
        >
          <div
            class="nav-item"
            :class="{ active: isCurrentPath(item.path) }"
            @click="handleNavClick(item)"
          >
            <img :src="item.icon" alt="nav-icon" class="nav-icon">
            <span class="nav-title">{{ item.title }}</span>
            <span v-if="item.children" class="expand-icon">{{ isMenuExpanded(item.path) ? '▾' : '▸' }}</span>
          </div>
          <ul v-if="item.children && isMenuExpanded(item.path)" class="sub-nav-list">
            <li
              v-for="(child, cIndex) in item.children"
              :key="cIndex"
              class="sub-nav-item"
              :class="{ active: isCurrentPath(child.path) }"
              @click.stop="goToPage(child.path)"
            >
              {{ child.title }}
            </li>
          </ul>
        </li>
      </ul>
    </nav>
  </div>
</template>

<script>
import brandLogo from '@/assets/icons/brand-logo.png';
import homeIcon from '@/assets/icons/home-icon.png';
import fertilizationIcon from '@/assets/icons/fertilization-icon.png';
import pesticideIcon from '@/assets/icons/pesticide-icon.svg';
import deviceIcon from '@/assets/icons/device-icon.png';
import analysisIcon from '@/assets/icons/analysis-icon.png';
import strategyIcon from '@/assets/icons/strategy-icon.png';
import aiIcon from '@/assets/icons/ai-icon.png';

export default {
  data() {
    return {
      brandLogo,
      username: localStorage.getItem('username') || '',
      expandedMenus: {},
      navItems: [
        { path: '/', icon: homeIcon, title: '首页' },
        { path: '/fertilization', icon: fertilizationIcon, title: '施肥记录' },
        { path: '/pesticide', icon: pesticideIcon, title: '农药记录' },
        { path: '/device', icon: deviceIcon, title: '设备管理' },
        {
          path: '/analysis',
          icon: analysisIcon,
          title: '数据分析',
          children: [
            { path: '/analysis/deficiency', title: '缺素情况' },
            { path: '/analysis/disease', title: '病害情况' }
          ]
        },
        { path: '/strategy', icon: strategyIcon, title: '智能策略' },
        { path: '/ai', icon: aiIcon, title: 'AI咨询' }
      ]
    };
  },
  created() {
    if (this.$route.path.startsWith('/analysis')) {
      this.expandedMenus['/analysis'] = true;
    }
  },
  methods: {
    goToPage(path) {
      if (this.$route.path !== path) {
        this.$router.push(path);
      }
    },
    handleNavClick(item) {
      if (item.children) {
        this.expandedMenus[item.path] = !this.expandedMenus[item.path];
        if (this.expandedMenus[item.path] && !this.$route.path.startsWith(item.path)) {
          this.goToPage(item.path);
        }
        return;
      }
      this.goToPage(item.path);
    },
    isMenuExpanded(path) {
      return !!this.expandedMenus[path];
    },
    isCurrentPath(path) {
      if (path === '/') return this.$route.path === '/';
      return this.$route.path === path || this.$route.path.startsWith(`${path}/`);
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
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background: linear-gradient(90deg, #66bb6a 0%, #81c784 100%);
  width: 100%;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(45, 90, 61, 0.2);
}

.logo-container { display: flex; align-items: center; gap: 10px; }
.logo { height: 36px; width: auto; object-fit: contain; display: block; }
.title { font-size: 24px; color: #fff; font-weight: bold; }

.user-center {
  display: flex;
  align-items: center;
  gap: 16px;
  color: #fff;
}
.username { font-size: 14px; }
.logout-btn {
  font-size: 13px;
  cursor: pointer;
  opacity: 0.9;
}
.logout-btn:hover { text-decoration: underline; }

.nav {
  width: 160px;
  background: #f1f8e9;
  position: fixed;
  top: 50px;
  left: 0;
  bottom: 0;
  padding-top: 20px;
  border-right: 1px solid #c8e6c9;
}

.nav-list { list-style: none; }

.nav-item-wrapper {
  display: block;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  cursor: pointer;
  transition: background-color 0.3s, color 0.3s;
  color: #2d5a3d;
}

.nav-item:hover {
  background-color: #66bb6a;
  color: #fff;
}

.nav-item.active {
  background-color: #66bb6a;
  color: #fff;
}

.nav-icon { height: 25px; object-fit: contain; }

.nav-title {
  white-space: nowrap;
  word-break: keep-all;
  flex-shrink: 0;
}

.expand-icon {
  margin-left: auto;
  font-size: 14px;
}

.sub-nav-list {
  list-style: none;
  margin: 0;
  padding: 0 0 6px;
}

.sub-nav-item {
  padding: 9px 20px 9px 55px;
  cursor: pointer;
  color: #2d5a3d;
  transition: background-color 0.3s, color 0.3s;
  font-size: 14px;
}

.sub-nav-item:hover,
.sub-nav-item.active {
  background-color: #81c784;
  color: #fff;
}
</style>
