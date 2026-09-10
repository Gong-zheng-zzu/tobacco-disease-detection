<template>
  <div class="pesticide-redirect" aria-hidden="true"></div>
</template>

<script>
export default {
  name: 'PesticideRedirect',
  mounted() {
    this.$router.replace({ path: '/fertilization' });
  }
};
</script>

<style scoped>
.pesticide-redirect {
  display: none;
}
</style>
