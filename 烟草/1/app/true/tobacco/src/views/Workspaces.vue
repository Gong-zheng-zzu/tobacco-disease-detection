<template>
  <div class="workspace-page">
    <header class="page-bar">
      <div class="brand"><span class="brand-mark"><Leaf :size="19" :stroke-width="2.2" /></span><span>叶擎慧航</span><span class="brand-divider"></span><span class="brand-section">工作台</span></div>
      <div class="account"><UserRound :size="16" /><span>{{ username }}</span><button type="button" class="logout" title="退出登录" aria-label="退出登录" @click="logout"><LogOut :size="17" /></button></div>
    </header>

    <main class="content">
      <div class="heading"><div><p class="eyebrow">工作端选择</p><h1>选择工作岗位</h1><p class="intro">{{ username }}，请选择本次要处理的工作。</p></div><span v-if="roles.length" class="role-count">已开通 {{ roles.length }} 个岗位</span></div>

      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <div v-if="roles.length" class="workspace-layout">
        <section class="role-section" aria-labelledby="production-heading">
          <div class="section-heading"><h2 id="production-heading">生产作业</h2><span>田间到收购</span></div>
          <div v-if="productionRoles.length" class="role-list">
            <button v-for="role in productionRoles" :key="role.code" type="button" class="role-row" :disabled="!!entering" @click="enter(role)">
              <span class="role-icon" :class="role.code"><component :is="roleIcon(role.code)" :size="21" :stroke-width="1.9" /></span>
              <span class="role-text"><strong>{{ roleTitle(role) }}</strong><small>{{ roleDescription(role) }}</small></span>
              <span v-if="entering === role.code" class="entering">进入中</span><ChevronRight v-else class="chevron" :size="19" />
            </button>
          </div>
          <p v-else class="empty-group">当前账号暂无生产岗位权限。</p>
        </section>

        <aside class="side-column">
          <section v-if="adminRole" class="role-section" aria-labelledby="admin-heading">
            <div class="section-heading"><h2 id="admin-heading">管理</h2><span>系统配置</span></div>
            <button type="button" class="role-row admin-row" :disabled="!!entering" @click="enter(adminRole)">
              <span class="role-icon admin"><ShieldCheck :size="21" :stroke-width="1.9" /></span>
              <span class="role-text"><strong>管理员端</strong><small>账号权限与业务总览</small></span>
              <span v-if="entering === 'admin'" class="entering">进入中</span><ChevronRight v-else class="chevron" :size="19" />
            </button>
          </section>
          <section class="account-panel" aria-label="当前账号"><span class="panel-label">当前账号</span><div class="account-name"><UserRound :size="17" /><strong>{{ username }}</strong></div><p>工作记录将关联到此账号。可在页面顶部随时切换已开通的岗位。</p></section>
        </aside>
      </div>
      <section v-else class="pending"><ShieldCheck :size="28" /><h2>尚未分配岗位</h2><p>请联系管理员开通工作权限。</p><button type="button" @click="logout">退出登录</button></section>
    </main>
  </div>
</template>

<script>
import axios from 'axios';
import { Leaf, Sprout, Bug, Scissors, Thermometer, ClipboardCheck, ShieldCheck, ChevronRight, LogOut, UserRound } from '@lucide/vue';
import { API_BASE } from '@/config/api';

const roleOrder = ['grower', 'plant_protection', 'harvest', 'curing', 'quality'];
const roleDetails = {
  grower: { title: '种植端', description: '地块、农情与施肥作业', icon: Sprout },
  plant_protection: { title: '植保端', description: '病虫害识别与防治记录', icon: Bug },
  harvest: { title: '采叶 / 采收端', description: '采收批次、叶位与鲜重', icon: Scissors },
  curing: { title: '烘烤端', description: '烤房、阶段与温湿度', icon: Thermometer },
  quality: { title: '收购 / 质检端', description: '称重、分级与批次追溯', icon: ClipboardCheck },
};

export default {
  components: { Leaf, ShieldCheck, ChevronRight, LogOut, UserRound },
  data: () => ({ entering: '', error: '' }),
  computed: {
    username() { return localStorage.getItem('username') || '当前用户'; },
    roles() { try { return JSON.parse(localStorage.getItem('roles') || '[]'); } catch { return []; } },
    productionRoles() { return roleOrder.map(code => this.roles.find(role => role.code === code)).filter(Boolean); },
    adminRole() { return this.roles.find(role => role.code === 'admin'); },
  },
  methods: {
    roleTitle(role) { return roleDetails[role.code]?.title || role.name; },
    roleDescription(role) { return roleDetails[role.code]?.description || role.description; },
    roleIcon(code) { return roleDetails[code]?.icon || Leaf; },
    async enter(role) {
      if (this.entering) return;
      this.entering = role.code;
      this.error = '';
      try {
        await axios.post(`${API_BASE}/me/active-role/`, { role: role.code });
        localStorage.setItem('activeRole', role.code);
        window.dispatchEvent(new CustomEvent('role-change', { detail: role.code }));
        this.$router.replace(['grower', 'plant_protection'].includes(role.code) ? '/' : '/workspace-dashboard');
      } catch (error) {
        this.error = error.response?.data?.msg || '岗位切换失败，请检查网络后重试。';
      } finally { this.entering = ''; }
    },
    logout() { ['token', 'userId', 'username', 'roles', 'activeRole'].forEach(key => localStorage.removeItem(key)); this.$router.replace('/login'); },
  },
};
</script>

<style scoped>
:global(body){margin:0}
.workspace-page{min-height:100vh;background:#f6f8f5;color:#21372b}.page-bar{height:64px;box-sizing:border-box;border-bottom:1px solid #e4eae2;background:#fff;display:flex;align-items:center;justify-content:space-between;padding:0 max(24px,calc((100vw - 1160px)/2));gap:16px}.brand,.account{display:flex;align-items:center;gap:9px}.brand{font-size:15px;font-weight:700;color:#183e2a}.brand-mark{width:30px;height:30px;display:grid;place-items:center;border-radius:6px;background:#277447;color:#fff}.brand-divider{height:17px;width:1px;background:#ccd8ce;margin:0 3px}.brand-section{font-size:13px;font-weight:500;color:#687c6d}.account{font-size:12px;color:#506756}.logout{width:32px;height:32px;padding:0;display:grid;place-items:center;border:1px solid #e1e9df;border-radius:6px;color:#607669;background:#fff;margin-left:9px}.logout:hover{background:#f1f6f0;color:#245f3a}.content{max-width:1160px;margin:0 auto;padding:54px 24px 90px}.heading{display:flex;align-items:end;justify-content:space-between;gap:20px;margin-bottom:29px}.eyebrow{margin:0 0 9px;color:#497c58;font-size:12px;font-weight:700}.heading h1{font-size:29px;line-height:1.25;margin:0;font-weight:700;color:#1d3425}.intro{margin:10px 0 0;color:#6e8072;font-size:14px}.role-count{font-size:12px;color:#607666;border:1px solid #d8e4d8;background:#fff;border-radius:4px;padding:7px 10px;white-space:nowrap}.workspace-layout{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(280px,1fr);gap:34px;align-items:start}.section-heading{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #dbe5dc;padding-bottom:11px;margin-bottom:12px}.section-heading h2{margin:0;color:#324c38;font-size:14px;font-weight:700}.section-heading span{font-size:12px;color:#8a9a8c}.role-list{display:grid;gap:8px}.role-row{width:100%;min-height:76px;box-sizing:border-box;padding:13px 17px;border:1px solid #e0e8df;border-radius:6px;background:#fff;display:flex;align-items:center;gap:16px;text-align:left;color:#263d2e;box-shadow:none;transition:border-color .18s,background .18s,transform .18s}.role-row:hover:not(:disabled){background:#fff;border-color:#8aac91;transform:translateX(2px)}.role-row:focus-visible,.logout:focus-visible{outline:2px solid #317e4c;outline-offset:2px}.role-row:disabled{opacity:.68;cursor:wait}.role-icon{flex:none;display:grid;place-items:center;width:42px;height:42px;border-radius:6px;background:#e8f1e8;color:#39724a}.role-icon.plant_protection{background:#edf1e5;color:#657a36}.role-icon.harvest{background:#f4eee4;color:#9a7440}.role-icon.curing{background:#f3ebe7;color:#a2684e}.role-icon.quality{background:#e9eff1;color:#527484}.role-icon.admin{background:#e9eeec;color:#49685b}.role-text{display:flex;flex-direction:column;gap:5px;min-width:0;flex:1}.role-text strong{font-size:15px;font-weight:650;line-height:1.3}.role-text small{font-size:12px;color:#76887a;line-height:1.4}.chevron{flex:none;color:#8fa394}.entering{font-size:12px;color:#39734c;white-space:nowrap}.side-column{display:grid;gap:20px}.admin-row{min-height:76px}.account-panel{padding:22px 23px;background:#edf3ec;border:1px solid #e2ebe0;border-radius:6px}.panel-label{font-size:12px;color:#68816e}.account-name{display:flex;align-items:center;gap:9px;margin-top:15px;color:#31553a;font-size:14px}.account-panel p{margin:13px 0 0;color:#6d806f;font-size:12px;line-height:1.7}.empty-group{font-size:13px;color:#829084}.pending{max-width:460px;padding:30px;background:#fff;border:1px solid #e0e8df;border-radius:6px;color:#476a50}.pending h2{font-size:18px;color:#234a30;margin:13px 0 5px}.pending p{font-size:13px;color:#6e8072}.pending button{background:#277447;border-radius:6px;padding:9px 15px;font-size:13px}.error{margin:0 0 18px;padding:11px 14px;background:#fff3ed;border-left:3px solid #bb6d4f;color:#914b32;font-size:13px}@media(max-width:780px){.content{padding:34px 20px 70px}.workspace-layout{grid-template-columns:1fr;gap:25px}.side-column{grid-template-columns:1fr 1fr;align-items:start}.page-bar{padding:0 20px}}@media(max-width:560px){.content{padding:30px 16px 55px}.page-bar{height:58px;padding:0 16px}.account>span{max-width:80px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.heading{align-items:start;flex-direction:column;gap:12px;margin-bottom:24px}.heading h1{font-size:24px}.intro{font-size:13px}.workspace-layout{gap:24px}.side-column{grid-template-columns:1fr;gap:16px}.role-row{min-height:72px;padding:12px}.role-icon{width:38px;height:38px}.role-text strong{font-size:14px}}
</style>
