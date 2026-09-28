<template>
  <div id="app" :class="{ 'workspace-shell': $route.path === '/workspaces' }">
    <Nav v-if="showNav" />
    <ToastHost />
    <div class="main-content" :class="{ 'no-nav': !showNav }">
      <router-view />
    </div>
  </div>
</template>

<script>
import Nav from '@/components/Nav.vue';
import ToastHost from '@/components/ToastHost.vue';

export default {
  components: { Nav, ToastHost },
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
  background: var(--color-page);
}

#app.workspace-shell {
  background: #f6f8f5;
}

.workspace-shell .main-content.no-nav {
  padding: 0;
}

.main-content {
  margin-top: var(--header-h);
  padding: 10px 10px calc(64px + env(safe-area-inset-bottom, 0px));
  min-height: calc(100vh - var(--header-h));
  background-color: transparent;
  box-sizing: border-box;
}

.main-content.no-nav {
  margin-top: 0;
  padding-bottom: 0;
}

@media (min-width: 1024px) {
  .main-content {
    margin-top: var(--header-h);
    padding: 14px 16px calc(72px + env(safe-area-inset-bottom, 0px));
  }
}
</style>
