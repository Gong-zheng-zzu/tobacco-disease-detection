<template>
  <div id="app">
    <div class="workspace-container">
      <aside class="agent-list-panel">
        <div class="agent-list-header">智能体列表</div>
        <div class="agent-list">
          <div
            v-for="agent in agents"
            :key="agent.id"
            class="agent-item"
            :class="{ 'is-active': selectedAgentId === agent.id }"
            @click="selectedAgentId = agent.id"
          >
            <img :src="agent.avatar" :alt="agent.name" class="agent-avatar">
            <div class="agent-meta">
              <div class="agent-name">{{ agent.name }}</div>
              <div class="agent-desc">{{ agent.desc }}</div>
            </div>
          </div>
        </div>
      </aside>

      <section class="chat-panel">
        <div class="chat-header">
          <img :src="currentAgent.avatar" :alt="currentAgent.name" class="header-avatar">
          <div class="header-title">{{ currentAgent.name }}</div>
        </div>

        <div class="messages-wrapper" ref="messagesWrapper">
          <div v-for="(message, index) in chatMessages" :key="index" class="message" :class="{ 'user-message-container': message.role === 'user', 'agent-message-container': message.role === 'assistant' }">
            <div class="message-content-wrapper">
              <img
                v-if="message.role === 'assistant'"
                :src="currentAgent.avatar"
                :alt="currentAgent.name"
                class="ai-icon"
              >
              <div
                :class="{ 'user-message': message.role === 'user', 'agent-message': message.role === 'assistant' }"
                :style="{ 'font-size': message.role === 'user' ? userMessageFontSize : agentMessageFontSize }"
              >
                {{ message.content }}
              </div>
              <img
                v-if="message.role === 'user'"
                :src="userAvatar"
                alt="user avatar"
                class="user-avatar"
              >
            </div>
          </div>
        </div>

        <div class="input-container">
          <div class="input-box-wrapper">
            <input
              v-model="userInput"
              placeholder="请输入烟草种植相关的问题，如施肥、病虫害防治、田间管理等"
              @keyup.enter="sendMessage"
              :disabled="isLoading"
              class="input-box"
            />
            <button @click="sendMessage" :disabled="isLoading" class="send-btn">
              {{ isLoading ? '发送中...' : '发送' }}
            </button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import userAvatar from '@/assets/icons/user-avatar.png';
import aiIcon from '@/assets/icons/ai-icon.png';

export default {
  data() {
    return {
      userInput: '',
      chatMessages: [],
      isLoading: false,
      userMessageFontSize: '15px', 
      agentMessageFontSize: '15px',
      selectedAgentId: 'crop-doctor',
      agents: [
        { id: 'crop-doctor', name: '智能助手', desc: '在线', avatar: aiIcon },
      ],
      userAvatar,
      aiIcon
    };
  },
  computed: {
    currentAgent() {
      return this.agents.find(agent => agent.id === this.selectedAgentId) || this.agents[0];
    },
  },
  methods: {
    async sendMessage() {
      if (this.userInput.trim() === '') return;

      const userMessage = { role: 'user', content: this.userInput };
      this.chatMessages.push(userMessage);

      const requestData = { question: this.userInput };
      this.isLoading = true;

      try {
        const response = await axios.post(
          '/api/ai/consult/',
          requestData,
          { headers: { 'Content-Type': 'application/json' }, timeout: 20000 }
        );

        if (typeof response.data === 'object' && response.data.role === 'assistant') {
          this.chatMessages.push(response.data);
        } else if (Array.isArray(response.data)) {
          const agentMessages = response.data.filter(msg => msg.role === 'assistant');
          this.chatMessages = this.chatMessages.concat(agentMessages);
        } else {
          console.error('无效的响应格式，需包含assistant角色', response.data);
          throw new Error('响应数据格式错误');
        }

        this.$nextTick(() => this.scrollToBottom());

      } catch (error) {
        console.error('请求出错:', error.message);
        const errorMessage = this.getErrorMessage(error);
        this.chatMessages.push({ role: 'assistant', content: errorMessage });
      } finally {
        this.isLoading = false;
        this.userInput = '';
      }
    },
    getErrorMessage(error) {
      if (error.response?.status === 500) return '服务器内部错误，请检查后台服务。';
      if (error.code === 'ECONNREFUSED') return '无法连接到服务器，请确保后台服务已启动。';
      return '抱歉，请求出错，请稍后再试。';
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesWrapper;
        if (!container) return;
        container.scrollTop = container.scrollHeight;
      });
    },
  },
  watch: {
    chatMessages: { handler() { this.scrollToBottom(); }, deep: true }
  },
};
</script>

<style scoped>
#app {
  max-width: 1280px;
  margin: 14px auto;
  padding: 12px;
  height: calc(100vh - 100px);
  min-height: 620px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  border-radius: 14px;
  background:
    linear-gradient(160deg, rgba(16, 74, 35, 0.78), rgba(12, 48, 28, 0.76)),
    repeating-linear-gradient(
      -12deg,
      rgba(118, 176, 75, 0.32) 0px,
      rgba(118, 176, 75, 0.32) 18px,
      rgba(76, 130, 54, 0.25) 18px,
      rgba(76, 130, 54, 0.25) 36px
    ),
    radial-gradient(circle at 20% 15%, rgba(215, 239, 169, 0.28), transparent 36%),
    radial-gradient(circle at 85% 80%, rgba(154, 209, 108, 0.2), transparent 34%);
  background-blend-mode: overlay, normal, screen, normal;
  box-shadow: 0 18px 36px rgba(8, 24, 15, 0.28);
}

.workspace-container {
  display: flex;
  height: 100%;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.28);
}

.agent-list-panel {
  width: 280px;
  background: rgba(255, 255, 255, 0.12);
  border-right: 1px solid rgba(255, 255, 255, 0.24);
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(14px) saturate(140%);
  -webkit-backdrop-filter: blur(14px) saturate(140%);
}

.agent-list-header {
  height: 62px;
  display: flex;
  align-items: center;
  padding: 0 14px;
  color: #111111;
  font-size: 15px;
  font-weight: 600;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  box-sizing: border-box;
}

.agent-list {
  padding: 8px;
  overflow-y: auto;
}

.agent-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 8px;
  border-radius: 8px;
  cursor: pointer;
  color: #111111;
  transition: background 0.2s ease, color 0.2s ease;
}

.agent-item:hover {
  background: rgba(255, 255, 255, 0.16);
}

.agent-item.is-active {
  background: rgba(47, 158, 92, 0.68);
  color: #111111;
}

.agent-avatar {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  padding: 4px;
  background: #ffffff;
  object-fit: cover;
  box-sizing: border-box;
  margin-top: 1px;
}

.agent-meta {
  min-width: 0;
}

.agent-name {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.agent-desc {
  margin-top: 2px;
  font-size: 12px;
  opacity: 0.8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(14px) saturate(140%);
  -webkit-backdrop-filter: blur(14px) saturate(140%);
}

.chat-header {
  height: 62px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.1);
}

.header-avatar {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  padding: 4px;
  background: #ffffff;
  box-sizing: border-box;
}

.header-title {
  color: #eef6ef;
  font-size: 16px;
  font-weight: 600;
}

.messages-wrapper {
  flex: 1;
  padding: 14px;
  background: rgba(255, 255, 255, 0.06);
  overflow-y: auto;
}

.message {
  margin: 10px 0;
  display: flex;
  align-items: flex-start;
}

.user-message-container {
  justify-content: flex-end;
}

.agent-message-container {
  justify-content: flex-start;
}

.message-content-wrapper {
  display: flex;
  align-items: flex-start;
}

/* 用户消息：内容和头像从左到右排列 */
.user-message-container .message-content-wrapper {
  flex-direction: row;
}

/* 智能体消息：图标和内容从左到右排列 */
.agent-message-container .message-content-wrapper {
  flex-direction: row;
}

.user-message, .agent-message {
  padding: 12px 18px;
  border-radius: 10px;
  max-width: 70%;
  word-wrap: break-word;
  color: #23342a;
}

.user-message {
  background-color: rgba(228, 247, 235, 0.9);
}

.agent-message {
  background-color: rgba(240, 246, 255, 0.88);
}

.user-avatar, .ai-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

/* 智能体图标在消息左侧 */
.ai-icon {
  margin-right: 10px;
  order: 1; /* 确保图标在消息内容之前 */
  padding: 4px;
  background: #ffffff;
  box-sizing: border-box;
}

/* 智能体消息内容在图标之后 */
.agent-message {
  order: 2;
}

/* 用户头像在消息右侧 */
.user-avatar {
  margin-left: 10px;
}

.input-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 10px 12px;
  height: 72px;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.1);
  border-top: 1px solid rgba(255, 255, 255, 0.22);
}

.input-box-wrapper {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 10px;
  z-index: 1;
}

.input-box {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid rgba(255, 255, 255, 0.48);
  border-radius: 10px;
  font-size: 14px;
  background-color: rgba(255, 255, 255, 0.66);
  transition: border-color 0.3s;
  height: 44px;
  color: #1f2a21;
}

.input-box::placeholder {
  color: rgba(42, 63, 45, 0.7);
}

.send-btn {
  position: static;
  flex-shrink: 0;
  padding: 10px 20px;
  font-size: 15px;
  font-weight: 600;
  background-color: #f2c84b;
  color: #ffffff;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  box-shadow: 0 6px 14px rgba(83, 64, 8, 0.25);
}

.send-btn:hover:not(:disabled) {
  background-color: #e8bb35;
}

.send-btn:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

@media (max-width: 900px) {
  .agent-list-panel {
    width: 220px;
  }
}
</style>