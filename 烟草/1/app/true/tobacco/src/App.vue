<template>
  <div id="app" :class="{ 'workspace-shell': $route.path === '/workspaces' }">
    <Nav v-if="showNav" />
    <div class="main-content" :class="{ 'no-nav': !showNav }">
      <router-view />
    </div>
  </div>
</template>

<script>
import Nav from '@/components/Nav.vue';

export default {
  components: { Nav },
  computed: {
    showNav() {
      return !['/login', '/register', '/workspaces'].includes(this.$route.path);
    }
  }
};
</script>

<style scoped>
#app {
  position: relative;
  min-height: 100vh;
  background: linear-gradient(180deg, #e8f5e9 0%, #f1f8e9 100%);
}

#app.workspace-shell {
  background: #f6f8f5;
}

.workspace-shell .main-content.no-nav {
  padding: 0;
}

.main-content {
  margin-top: 64px;
  padding: 10px 10px calc(64px + env(safe-area-inset-bottom, 0px));
  min-height: calc(100vh - 64px);
  background-color: transparent;
  box-sizing: border-box;
}

.main-content.no-nav {
  margin-top: 0;
  padding-bottom: 0;
}

@media (min-width: 1024px) {
  .main-content {
    margin-top: 64px;
    padding: 14px 16px calc(72px + env(safe-area-inset-bottom, 0px));
  }
}
</style>
