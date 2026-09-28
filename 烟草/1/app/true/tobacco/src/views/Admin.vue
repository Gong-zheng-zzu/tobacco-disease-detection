<template>
  <div class="admin-page">
    <header class="page-head">
      <div><span class="eyebrow">管理员端</span><h1>用户与角色</h1></div>
      <button type="button" class="refresh" :disabled="loading" @click="loadData">刷新</button>
    </header>
    <p v-if="error" class="notice error" role="alert">{{ error }}</p>
    <p v-if="message" class="notice success" role="status">{{ message }}</p>
    <div v-if="loading" class="state">正在加载用户与角色...</div>
    <div v-else-if="!users.length" class="state">暂无用户</div>
    <section v-else class="user-list" aria-label="用户角色管理">
      <article v-for="user in users" :key="user.user_id" class="user-row">
        <div class="user-info">
          <strong>{{ user.username }}</strong>
          <small>{{ user.phone || '未填写手机号' }} · 当前：{{ (user.roles || []).map(role => role.name).join('、') || '未分配' }}</small>
        </div>
        <div class="role-actions">
          <div class="role-options">
            <label v-for="role in roles" :key="role.code" class="role-check">
              <input v-model="selections[user.user_id]" type="checkbox" :value="role.code" :disabled="saving === user.user_id">
              <span>{{ role.name }}</span>
            </label>
          </div>
          <button type="button" class="save" :disabled="saving === user.user_id || !isChanged(user)" @click="save(user)">
            {{ saving === user.user_id ? '保存中...' : '保存' }}
          </button>
        </div>
      </article>
    </section>
  </div>
</template>

<script>
import axios from 'axios';
import { API_BASE } from '@/config/api';

export default {
  data: () => ({ users: [], roles: [], selections: {}, loading: false, saving: null, error: '', message: '' }),
  mounted() { this.loadData(); },
  methods: {
    async loadData() {
      this.loading = true;
      this.error = '';
      try {
        const [users, roles] = await Promise.all([
          axios.get(`${API_BASE}/admin/users/`),
          axios.get(`${API_BASE}/roles/`),
        ]);
        this.users = users.data.data || [];
        this.roles = roles.data.data || [];
        this.selections = Object.fromEntries(this.users.map(user => [
          user.user_id, (user.roles || []).map(role => role.code),
        ]));
      } catch (error) {
        this.error = error.response?.data?.msg || '用户与角色加载失败，请重试';
      } finally {
        this.loading = false;
      }
    },
    isChanged(user) {
      const before = (user.roles || []).map(role => role.code).sort().join(',');
      const after = (this.selections[user.user_id] || []).slice().sort().join(',');
      return before !== after;
    },
    async save(user) {
      const selected = this.selections[user.user_id] || [];
      this.error = '';
      this.message = '';
      if (!selected.length) {
        this.error = `请为 ${user.username} 至少保留一个角色`;
        return;
      }
      const primary = selected.includes(user.primary_role) ? user.primary_role : selected[0];
      this.saving = user.user_id;
      try {
        await axios.post(`${API_BASE}/users/${user.user_id}/roles/`, {
          roles: selected, primary_role: primary,
        });
        this.message = `${user.username} 的角色已更新`;
        const response = await axios.get(`${API_BASE}/admin/users/`);
        this.users = response.data.data || [];
        this.selections = Object.fromEntries(this.users.map(item => [
          item.user_id, (item.roles || []).map(role => role.code),
        ]));
      } catch (error) {
        this.error = error.response?.data?.msg || '角色更新失败，请重试';
      } finally {
        this.saving = null;
      }
    },
  },
};
</script>

<style scoped>
.admin-page{max-width:1080px;margin:auto;color:#253d2e}.page-head{display:flex;justify-content:space-between;align-items:end;gap:16px;margin:8px 0 18px}.eyebrow{font-size:12px;color:#27865a;font-weight:700}.page-head h1{font-size:25px;margin:5px 0 0;color:#1b583c}.refresh,.save{border:1px solid #b8d3c2;border-radius:6px;background:#fff;color:#1b6a46;padding:8px 14px;font:inherit;font-size:13px;cursor:pointer}.refresh:disabled,.save:disabled{opacity:.5;cursor:default}.save{background:#1f8758;color:#fff;border-color:#1f8758;min-width:74px}.notice{padding:10px 12px;border-radius:6px;font-size:13px}.error{background:#fff4ed;color:#8e4b2e}.success{background:#eaf5ee;color:#206445}.state{padding:28px 16px;border:1px solid #dcebe1;border-radius:6px;background:#fff;color:#6d8172;text-align:center}.user-list{border:1px solid #dcebe1;border-radius:6px;background:#fff;padding:0 16px}.user-row{display:flex;justify-content:space-between;gap:20px;align-items:center;border-bottom:1px solid #edf3ee;padding:16px 0}.user-row:last-child{border-bottom:0}.user-info{min-width:180px}.user-info strong{font-size:14px}.user-info small{display:block;margin-top:6px;color:#6e8275;font-size:12px;line-height:1.5}.role-actions{display:flex;align-items:center;justify-content:flex-end;gap:15px;min-width:0}.role-options{display:flex;flex-wrap:wrap;gap:8px 13px;justify-content:flex-end}.role-check{display:flex;align-items:center;gap:4px;color:#486956;font-size:12px;white-space:nowrap;cursor:pointer}.role-check input{accent-color:#1f8758;margin:0}.refresh:focus-visible,.save:focus-visible,.role-check input:focus-visible{outline:2px solid #257a50;outline-offset:2px}@media(max-width:760px){.user-row{display:block}.role-actions{margin-top:13px;justify-content:space-between}.role-options{justify-content:flex-start}}@media(max-width:480px){.role-actions{align-items:flex-start;flex-direction:column}.save{align-self:flex-end}}
</style>
