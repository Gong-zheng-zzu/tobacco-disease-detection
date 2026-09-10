<template>
  <div class="register-page">
    <div class="register-card">
      <div class="register-header">
        <h1>叶擎慧航</h1>
        <p>烟草种植管理系统</p>
      </div>
      <form class="register-form" @submit.prevent="handleRegister">
        <div class="form-group">
          <label>用户名</label>
          <input v-model="form.username" type="text" placeholder="请输入用户名" required>
        </div>
        <div class="form-group">
          <label>手机号</label>
          <input v-model="form.phone" type="tel" placeholder="请输入手机号" required>
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="form.password1" type="password" placeholder="请输入密码" required>
        </div>
        <div class="form-group">
          <label>确认密码</label>
          <input v-model="form.password2" type="password" placeholder="请再次输入密码" required>
        </div>
        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>
        <button type="submit" class="btn-register" :disabled="loading">{{ loading ? '注册中...' : '注册' }}</button>
        <router-link to="/login" class="link-login">已有账号？去登录</router-link>
      </form>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      form: { username: '', phone: '', password1: '', password2: '' },
      errorMsg: '',
      loading: false
    };
  },
  methods: {
    async handleRegister() {
      this.errorMsg = '';
      if (this.form.password1 !== this.form.password2) {
        this.errorMsg = '两次密码不一致';
        return;
      }
      this.loading = true;
      try {
        const res = await axios.post('/api/register/', {
          username: this.form.username,
          phone: this.form.phone,
          password1: this.form.password1,
          password2: this.form.password2
        });
        if (res.data.code === 200) {
          alert('注册成功，请登录');
          this.$router.replace('/login');
        } else {
          this.errorMsg = typeof res.data.msg === 'string' ? res.data.msg : JSON.stringify(res.data.msg);
        }
      } catch (e) {
        this.errorMsg = e.response?.data?.msg || '网络错误，请重试';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 50%, #a5d6a7 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.register-card {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(45, 90, 61, 0.2);
  padding: 40px;
  width: 100%;
  max-width: 380px;
}

.register-header {
  text-align: center;
  margin-bottom: 28px;
}

.register-header h1 {
  font-size: 24px;
  color: #2d5a3d;
  margin: 0 0 8px;
}

.register-header p {
  font-size: 13px;
  color: #558b2f;
  margin: 0;
}

.register-form .form-group {
  margin-bottom: 16px;
}

.register-form label {
  display: block;
  font-size: 14px;
  color: #2d5a3d;
  margin-bottom: 6px;
}

.register-form input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #c8e6c9;
  border-radius: 8px;
  font-size: 15px;
  box-sizing: border-box;
}

.register-form input:focus {
  outline: none;
  border-color: #66bb6a;
}

.error-msg {
  color: #c62828;
  font-size: 13px;
  margin: 0 0 12px;
}

.btn-register {
  width: 100%;
  padding: 12px;
  background: linear-gradient(90deg, #66bb6a, #81c784);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  margin-bottom: 16px;
}

.btn-register:hover:not(:disabled) {
  opacity: 0.95;
}

.btn-register:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.link-login {
  display: block;
  text-align: center;
  color: #558b2f;
  font-size: 14px;
  text-decoration: none;
}

.link-login:hover {
  text-decoration: underline;
}
</style>
