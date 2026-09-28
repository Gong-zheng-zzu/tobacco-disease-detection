<template>
  <div class="auth-page"><div class="auth-card">
    <div class="auth-brand"><h1>创建工作账号</h1><p>注册后由管理员分配工作角色</p></div>
    <form @submit.prevent="handleRegister">
      <label>用户名<input v-model.trim="form.username" minlength="3" maxlength="16" placeholder="3-16位中文、字母、数字或下划线" autocomplete="username" required></label>
      <label>手机号<input v-model.trim="form.phone" inputmode="tel" pattern="1[3-9][0-9]{9}" maxlength="11" placeholder="请输入11位手机号" autocomplete="tel" required></label>
      <label>密码<input v-model="form.password1" type="password" minlength="10" maxlength="128" placeholder="至少10位，包含字母和数字" autocomplete="new-password" required></label>
      <label>确认密码<input v-model="form.password2" type="password" minlength="10" maxlength="128" autocomplete="new-password" required></label>
      <div class="captcha-row"><label>验证码<input v-model.trim="form.captcha_code" maxlength="5" autocomplete="off" required></label><button type="button" class="captcha-image" @click="loadCaptcha"><img v-if="captchaImage" :src="captchaImage" alt="图形验证码"><span v-else>加载中</span></button></div>
      <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p><button class="primary-btn" :disabled="loading">{{ loading ? '注册中...' : '注册' }}</button><router-link to="/login" class="auth-link">已有账号？去登录</router-link>
    </form>
  </div></div>
</template>
<script>
import axios from 'axios'; import { API_BASE } from '@/config/api';
export default { data:()=>({ form:{username:'',phone:'',password1:'',password2:'',captcha_id:'',captcha_code:''},captchaImage:'',loading:false,errorMsg:'' }), mounted(){this.loadCaptcha();}, methods:{
  async loadCaptcha(){try{const r=await axios.get(`${API_BASE}/auth/captcha/`);this.form.captcha_id=r.data.data.captcha_id;this.form.captcha_code='';this.captchaImage=r.data.data.image;}catch{this.errorMsg='验证码加载失败，请重试';}},
  async handleRegister(){this.errorMsg='';if(!/^(?=.*[A-Za-z])(?=.*\d).{10,128}$/.test(this.form.password1)){this.errorMsg='密码至少10位，且同时包含字母和数字';return;}if(this.form.password1!==this.form.password2){this.errorMsg='两次密码不一致';return;}this.loading=true;try{const r=await axios.post(`${API_BASE}/register/`,this.form);if(r.data.code!==200)throw new Error(r.data.msg||'注册失败');alert('注册成功，请等待管理员分配角色后登录');this.$router.replace('/login');}catch(e){this.errorMsg=e.response?.status===429?'操作过于频繁，请稍后再试':e.response?.data?.msg||e.message||'网络错误，请重试';await this.loadCaptcha();}finally{this.loading=false;}}
}};
</script>
<style scoped>
.auth-page{min-height:100vh;display:grid;place-items:center;padding:20px;background:linear-gradient(145deg,#e9f6ed,#f7fbf7)}.auth-card{width:min(100%,390px);padding:34px;background:#fff;border:1px solid #dcece2;border-radius:16px;box-shadow:0 16px 44px rgba(28,93,58,.12)}.auth-brand{text-align:center;margin-bottom:24px}.auth-brand h1{margin:0;color:#196d49;font-size:24px}.auth-brand p{margin:7px 0;color:#71907f;font-size:13px}label{display:block;margin:0 0 13px;color:#315b45;font-size:13px;font-weight:600}input{display:block;width:100%;box-sizing:border-box;margin-top:7px;padding:10px 12px;border:1px solid #cfe2d5;border-radius:8px;font:inherit;font-weight:400}.captcha-row{display:grid;grid-template-columns:1fr 148px;gap:10px;align-items:end}.captcha-image{height:42px;margin-bottom:13px;padding:0;border:1px solid #cfe2d5;background:#f4fbf6;border-radius:8px;overflow:hidden}.captcha-image img{width:100%;height:100%;object-fit:cover}.captcha-image span{font-size:12px;color:#668875}.primary-btn{width:100%;padding:12px;border:0;border-radius:8px;background:#1f8758;color:#fff;font-weight:700}.primary-btn:disabled{opacity:.6}.auth-link{display:block;margin-top:16px;text-align:center;color:#31845b;font-size:13px}.error-msg{color:#c33b3b;font-size:13px}
</style>
