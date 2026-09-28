<template>
  <div class="workspace-page"><header><p class="eyebrow">叶擎慧航 · 工作台</p><h1>选择你的工作端</h1><p class="sub">当前账号拥有多个角色，进入后可随时切换。</p></header>
    <section v-if="roles.length" class="workspace-grid"><button v-for="role in roles" :key="role.code" class="workspace-card" @click="enter(role)"><span class="role-mark">{{ role.name.slice(0,1) }}</span><span><strong>{{ role.name }}</strong><small>{{ role.description }}</small></span><span class="arrow">›</span></button></section><section v-else class="pending"><strong>账号等待分配工作角色</strong><p>请联系管理员开通种植、植保、采收、烘烤、质检或管理员工作端。</p><button @click="logout">退出登录</button></section>
  </div>
</template>
<script>
export default { computed:{roles(){return JSON.parse(localStorage.getItem('roles')||'[]');}}, methods:{enter(role){localStorage.setItem('activeRole',role.code);window.dispatchEvent(new CustomEvent('role-change',{detail:role.code}));this.$router.replace(['grower','plant_protection'].includes(role.code)?'/' : '/workspace-dashboard');},logout(){localStorage.clear();this.$router.replace('/login');}}};
</script>
<style scoped>
.workspace-page{max-width:900px;margin:0 auto;padding:24px 4px}.eyebrow{color:#25845a;font-size:12px;font-weight:700;letter-spacing:.08em}.workspace-page h1{margin:8px 0;color:#184f38;font-size:30px}.sub{color:#718779}.workspace-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:28px}.workspace-card{display:flex;align-items:center;gap:14px;text-align:left;padding:18px;background:#fff;border:1px solid #d8e9de;border-radius:12px;color:#224f39;box-shadow:0 5px 20px rgba(22,83,49,.06)}.workspace-card:hover{border-color:#60b982;background:#f8fcf9}.role-mark{display:grid;place-items:center;width:42px;height:42px;border-radius:12px;background:#e6f5eb;color:#238258;font-weight:800}.workspace-card strong,.workspace-card small{display:block}.workspace-card small{margin-top:5px;color:#779184;font-size:12px}.arrow{margin-left:auto;font-size:24px;color:#77a287}@media(max-width:600px){.workspace-grid{grid-template-columns:1fr}.workspace-page h1{font-size:25px}}
.pending{margin-top:28px;padding:28px;background:#fff;border:1px solid #d8e9de;border-radius:12px;color:#315b45}.pending p{color:#789081;font-size:13px}.pending button{border:0;border-radius:7px;background:#1f8758;color:#fff;padding:9px 14px}
</style>
