<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <h1>叶擎慧航</h1>
        <p>烟草种植管理系统</p>
      </div>
      <form class="login-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label>用户名</label>
          <input v-model="form.username" type="text" placeholder="请输入用户名" required>
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="form.password" type="password" placeholder="请输入密码" required>
        </div>
        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>
        <button type="submit" class="btn-login" :disabled="loading">{{ loading ? '登录中...' : '登录' }}</button>
        <router-link to="/register" class="link-register">没有账号？去注册</router-link>
      </form>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      form: { username: '', password: '' },
      errorMsg: '',
      loading: false
    };
  },
  methods: {
    async handleLogin() {
      this.errorMsg = '';
      this.loading = true;
      try {
        const res = await axios.post('/api/login/', this.form);
        if (res.data.code === 200) {
          localStorage.setItem('token', res.data.token);
          localStorage.setItem('userId', String(res.data.user_id));
          localStorage.setItem('username', res.data.username || this.form.username);
          this.$router.replace('/');
        } else {
          this.errorMsg = res.data.msg || '登录失败';
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
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 50%, #a5d6a7 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-card {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(45, 90, 61, 0.2);
  padding: 40px;
  width: 100%;
  max-width: 380px;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  font-size: 28px;
  color: #2d5a3d;
  margin: 0 0 8px;
}

.login-header p {
  font-size: 14px;
  color: #558b2f;
  margin: 0;
}

.login-form .form-group {
  margin-bottom: 20px;
}

.login-form label {
  display: block;
  font-size: 14px;
  color: #2d5a3d;
  margin-bottom: 8px;
}

.login-form input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #c8e6c9;
  border-radius: 8px;
  font-size: 15px;
  box-sizing: border-box;
}

.login-form input:focus {
  outline: none;
  border-color: #66bb6a;
  box-shadow: 0 0 0 2px rgba(102, 187, 106, 0.2);
}

.error-msg {
  color: #c62828;
  font-size: 13px;
  margin: 0 0 12px;
}

.btn-login {
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

.btn-login:hover:not(:disabled) {
  opacity: 0.95;
}

.btn-login:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.link-register {
  display: block;
  text-align: center;
  color: #558b2f;
  font-size: 14px;
  text-decoration: none;
}

.link-register:hover {
  text-decoration: underline;
}
</style>
