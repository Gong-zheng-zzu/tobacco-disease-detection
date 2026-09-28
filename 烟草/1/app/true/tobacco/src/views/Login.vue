<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand"><h1>叶擎慧航</h1><p>烟草生产协同平台</p></div>
      <form @submit.prevent="handleLogin">
        <label>用户名<input v-model.trim="form.username" autocomplete="username" required></label>
        <label>密码<input v-model="form.password" type="password" autocomplete="current-password" required></label>
        <div class="captcha-row"><label>验证码<input v-model.trim="form.captcha_code" maxlength="5" autocomplete="off" required></label><button type="button" class="captcha-image" @click="loadCaptcha"><img v-if="captchaImage" :src="captchaImage" alt="图形验证码"><span v-else>加载中</span></button></div>
        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>
        <button class="primary-btn" :disabled="loading || captchaLoading">{{ loading ? '登录中...' : '登录' }}</button>
        <router-link to="/register" class="auth-link">没有账号？去注册</router-link>
      </form>
    </div>
  </div>
</template>
<script>
import axios from 'axios'; import { API_BASE } from '@/config/api';
export default { data:()=>({ form:{username:'',password:'',captcha_id:'',captcha_code:''},captchaImage:'',captchaLoading:false,loading:false,errorMsg:'' }), mounted(){this.loadCaptcha();}, methods:{
  async loadCaptcha(){this.captchaLoading=true;try{const r=await axios.get(`${API_BASE}/auth/captcha/`);this.form.captcha_id=r.data.data.captcha_id;this.form.captcha_code='';this.captchaImage=r.data.data.image;}catch{this.errorMsg='验证码加载失败，请重试';}finally{this.captchaLoading=false;}},
  async handleLogin(){this.errorMsg='';this.loading=true;try{const r=await axios.post(`${API_BASE}/login/`,this.form);if(r.data.code!==200)throw new Error(r.data.msg||'登录失败');localStorage.setItem('token',r.data.token);localStorage.setItem('userId',String(r.data.user_id));localStorage.setItem('username',r.data.username||this.form.username);const me=await axios.get(`${API_BASE}/me/`);const roles=me.data.data.roles||[];localStorage.setItem('roles',JSON.stringify(roles));const target=roles.length!==1?'/workspaces':(['harvest','curing','quality','admin'].includes(roles[0]?.code)?'/workspace-dashboard':'/');this.$router.replace(target);}catch(e){this.errorMsg=e.response?.status===429?'失败次数过多，请稍后再试':e.response?.data?.msg||e.message||'网络错误，请重试';await this.loadCaptcha();}finally{this.loading=false;}}
}};
</script>
<style scoped>
.auth-page{min-height:100vh;display:grid;place-items:center;padding:20px;background:linear-gradient(145deg,#e9f6ed,#f7fbf7)}.auth-card{width:min(100%,390px);padding:34px;background:#fff;border:1px solid #dcece2;border-radius:16px;box-shadow:0 16px 44px rgba(28,93,58,.12)}.auth-brand{text-align:center;margin-bottom:26px}.auth-brand h1{margin:0;color:#196d49;font-size:25px}.auth-brand p{margin:7px 0 0;color:#71907f;font-size:13px}label{display:block;margin:0 0 15px;color:#315b45;font-size:13px;font-weight:600}input{display:block;width:100%;box-sizing:border-box;margin-top:7px;padding:11px 12px;border:1px solid #cfe2d5;border-radius:8px;font:inherit;font-weight:400}.captcha-row{display:grid;grid-template-columns:1fr 148px;gap:10px;align-items:end}.captcha-image{height:44px;margin-bottom:15px;padding:0;border:1px solid #cfe2d5;background:#f4fbf6;border-radius:8px;overflow:hidden}.captcha-image img{width:100%;height:100%;object-fit:cover}.captcha-image span{color:#668875;font-size:12px}.primary-btn{width:100%;padding:12px;border:0;border-radius:8px;background:#1f8758;color:#fff;font-weight:700}.primary-btn:disabled{opacity:.6}.auth-link{display:block;margin-top:17px;text-align:center;color:#31845b;font-size:13px}.error-msg{color:#c33b3b;font-size:13px;margin:0 0 12px}
</style>
