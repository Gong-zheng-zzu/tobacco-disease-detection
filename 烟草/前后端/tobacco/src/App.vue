<template>
  <div id="app">
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
      return !['/login', '/register'].includes(this.$route.path);
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

.main-content {
  margin-left: 160px;
  margin-top: 50px;
  padding: 10px;
  min-height: calc(100vh - 50px);
  background-color: transparent;
}

.main-content.no-nav {
  margin-left: 0;
  margin-top: 0;
}

@media (max-width: 1024px) {
  .main-content {
    margin-left: 0;
    padding: 10px;
  }
}
</style>
