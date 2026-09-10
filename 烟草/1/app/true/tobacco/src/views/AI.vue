<template>
  <div class="ai-page">
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
          <div
            v-for="(message, index) in chatMessages"
            :key="index"
            class="message"
            :class="{ 'user-message-container': message.role === 'user', 'agent-message-container': message.role === 'assistant' }"
          >
            <div
              class="message-content-wrapper"
              :class="{
                'assistant-content-wrapper': message.role === 'assistant',
                'user-content-wrapper': message.role === 'user'
              }"
            >
              <img
                v-if="message.role === 'assistant'"
                :src="currentAgent.avatar"
                :alt="currentAgent.name"
                class="ai-icon"
              >
              <div
                :class="{ 'user-message': message.role === 'user', 'agent-message': message.role === 'assistant' }"
              >
                <template v-if="message.role === 'assistant' && message.welcome">
                  <p class="welcome-lead">{{ message.content }}</p>
                  <ol v-if="message.presets?.length" class="preset-ol">
                    <li
                      v-for="(q, i) in message.presets"
                      :key="i"
                      class="preset-li"
                      @click="sendPreset(q)"
                    >
                      {{ q }}
                    </li>
                  </ol>
                </template>
                <template v-else-if="message.role === 'assistant'">
                  <span class="agent-text-pre">{{ message.content }}</span>
                </template>
                <template v-else>{{ message.content }}</template>
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
            >
            <button type="button" @click="sendMessage" :disabled="isLoading" class="send-btn">
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
import { API_BASE } from '@/config/api';

const ALL_WELCOME_PRESETS = [
  '烤烟苗期与还苗期水肥管理要注意什么？',
  '如何区分烟草缺氮、缺钾的典型症状？',
  '大田期常见叶部病害（如病毒病、气候性斑点）怎样预防？',
  '烟田追肥氮磷钾大致比例与施用时期怎么把握？',
  '旺长期烟株徒长、叶片薄，可能和哪些因素有关？',
  '成熟期适时采烤要注意什么？',
  '烟田灌溉是沟灌好还是滴灌更合适？',
  '黑胫病、根腐类问题田间怎么早发现、早处理？',
  '烟青虫、蚜虫等虫害绿色防控有哪些做法？',
  '上部叶开片不好、叶面积小，可能缺什么或怎么调？',
  '移栽前整地、起垄与基肥施用有什么要点？',
  '气候性斑点、日灼等生理性叶斑如何与病害区分？',
  '烟田杂草防除要注意哪些药害与安全间隔？',
  '土壤 pH 偏酸或偏碱对烟草吸收养分有什么影响？',
  '打顶抹杈的时机对产量和品质有什么影响？',
  '无人机叶面追肥或施药时要注意什么？'
];

function pickRandomPresets(pool, count = 3) {
  const copy = [...pool];
  const n = Math.min(count, copy.length);
  const out = [];
  for (let i = 0; i < n; i++) {
    const idx = Math.floor(Math.random() * copy.length);
    out.push(copy.splice(idx, 1)[0]);
  }
  return out;
}

export default {
  data() {
    return {
      userInput: '',
      chatMessages: [
        {
          role: 'assistant',
          welcome: true,
          content: '您好！我是烟草种植咨询助手，可以为您解答例如：',
          presets: pickRandomPresets(ALL_WELCOME_PRESETS, 3)
        }
      ],
      isLoading: false,
      selectedAgentId: 'crop-doctor',
      agents: [
        { id: 'crop-doctor', name: 'AI 烟草种植助手', desc: '在线', avatar: aiIcon }
      ],
      userAvatar,
      aiIcon
    };
  },
  computed: {
    currentAgent() {
      return this.agents.find(a => a.id === this.selectedAgentId) || this.agents[0];
    }
  },
  methods: {
    async sendMessage() {
      const text = this.userInput.trim();
      if (!text || this.isLoading) return;
      this.userInput = '';
      await this.runConsult(text);
    },
    async sendPreset(text) {
      if (this.isLoading) return;
      await this.runConsult(text);
    },
    async runConsult(question) {
      this.chatMessages.push({ role: 'user', content: question });
      this.isLoading = true;
      try {
        const response = await axios.post(
          `${API_BASE}/ai/consult/`,
          { question },
          { headers: { 'Content-Type': 'application/json' }, timeout: 120000 }
        );

        const data = response.data;
        let text = '';

        if (Array.isArray(data)) {
          for (let i = data.length - 1; i >= 0; i--) {
            if (data[i] && data[i].role === 'assistant') {
              text = data[i].content || '';
              break;
            }
          }
        } else if (data && typeof data === 'object' && data.role === 'assistant') {
          text = data.content || '';
        } else if (data && typeof data === 'object' && Array.isArray(data.messages)) {
          const arr = data.messages;
          for (let i = arr.length - 1; i >= 0; i--) {
            if (arr[i] && arr[i].role === 'assistant') {
              text = arr[i].content || '';
              break;
            }
          }
        }

        if (!text) {
          console.error('无效的响应格式', data);
          throw new Error('响应数据格式错误');
        }

        this.chatMessages.push({ role: 'assistant', content: text });
        this.$nextTick(() => this.scrollToBottom());
      } catch (error) {
        console.error('请求出错:', error.message, error.code, error.response?.status);
        this.chatMessages.push({
          role: 'assistant',
          content: this.getErrorMessage(error)
        });
      } finally {
        this.isLoading = false;
        this.$nextTick(() => this.scrollToBottom());
      }
    },
    getErrorMessage(error) {
      if (error.response?.status === 500) return '服务器内部错误，请检查后台服务。';
      if (error.code === 'ECONNREFUSED') return '无法连接到服务器，请确保后台服务已启动。';
      if (error.code === 'ECONNABORTED' || String(error.message || '').includes('timeout')) {
        return '等待回复超时，模型较慢时可稍后再试。';
      }
      return '抱歉，请求出错，请稍后再试。';
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesWrapper;
        if (!container) return;
        container.scrollTop = container.scrollHeight;
      });
    }
  },
  watch: {
    chatMessages: { handler() { this.scrollToBottom(); }, deep: true }
  }
};
</script>

<style scoped>
.ai-page {
  height: calc(100vh - 136px);
  min-height: 0;
  padding: 6px;
  box-sizing: border-box;
}

.workspace-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  border-radius: 16px;
  overflow: hidden;
  background: linear-gradient(140deg, #0f5f3d, #188a57 48%, #25a76f);
  box-shadow: 0 14px 30px rgba(22, 84, 56, 0.24);
}

.agent-list-panel {
  display: none;
}

.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.chat-header {
  height: 56px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.22);
  background: rgba(255, 255, 255, 0.08);
}

.header-avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.95);
  padding: 4px;
  object-fit: contain;
  flex-shrink: 0;
}

.header-title {
  color: #effaf3;
  font-size: 15px;
  font-weight: 700;
}

.messages-wrapper {
  flex: 1;
  min-height: 0;
  padding: 12px;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  background: rgba(255, 255, 255, 0.1);
}

.message {
  display: flex;
  margin-bottom: 10px;
}

.user-message-container {
  justify-content: flex-end;
}

.agent-message-container {
  justify-content: flex-start;
}

.message-content-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  max-width: 100%;
}

.assistant-content-wrapper {
  align-items: flex-start;
}

.user-content-wrapper {
  align-items: flex-start;
}

.user-message,
.agent-message {
  max-width: 75vw;
  padding: 10px 12px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  color: #214533;
  word-break: break-word;
}

.user-message {
  background: #e7f8ef;
  border-top-right-radius: 4px;
}

.agent-message {
  background: #f1f5f9;
  border-top-left-radius: 4px;
}

.welcome-lead {
  margin: 0 0 8px;
}

.preset-ol {
  margin: 0;
  padding-left: 1.15em;
  list-style: decimal;
}

.preset-li {
  margin: 4px 0;
  color: #1f6b44;
  font-weight: 500;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.preset-li:active {
  opacity: 0.85;
}

.agent-text-pre {
  white-space: pre-wrap;
}

.ai-icon,
.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  flex-shrink: 0;
}

.ai-icon {
  object-fit: contain;
  background: rgba(255, 255, 255, 0.95);
  padding: 3px;
  box-sizing: border-box;
}

.user-avatar {
  object-fit: cover;
  border-radius: 50%;
}

.input-container {
  padding: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.26);
  background: rgba(255, 255, 255, 0.08);
}

.input-box-wrapper {
  display: flex;
  gap: 8px;
}

.input-box {
  flex: 1;
  min-width: 0;
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: rgba(255, 255, 255, 0.92);
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 14px;
  color: #203b2d;
}

.send-btn {
  border: none;
  border-radius: 10px;
  padding: 10px 14px;
  min-width: 66px;
  background: #f7ca4a;
  color: #42500e;
  font-weight: 700;
  cursor: pointer;
}

.send-btn:disabled {
  opacity: 0.6;
}

@media (min-width: 900px) {
  .ai-page {
    padding: 10px;
    height: calc(100vh - 104px);
  }

  .workspace-container {
    flex-direction: row;
  }

  .agent-list-panel {
    display: flex;
    width: 220px;
    flex-shrink: 0;
    flex-direction: column;
    border-right: 1px solid rgba(255, 255, 255, 0.22);
    background: rgba(255, 255, 255, 0.1);
  }

  .agent-list-header {
    height: 56px;
    display: flex;
    align-items: center;
    padding: 0 12px;
    color: #f0f9f2;
    font-size: 14px;
    font-weight: 700;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  }

  .agent-list {
    padding: 8px;
    overflow-y: auto;
  }

  .agent-item {
    display: flex;
    gap: 8px;
    align-items: center;
    border-radius: 10px;
    padding: 8px;
    color: #eff8f1;
    cursor: pointer;
  }

  .agent-item.is-active {
    background: rgba(255, 255, 255, 0.2);
  }

  .agent-avatar {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: #fff;
    padding: 4px;
  }

  .agent-name {
    font-size: 13px;
    font-weight: 700;
  }

  .agent-desc {
    font-size: 11px;
    opacity: 0.85;
  }

  .user-message,
  .agent-message {
    max-width: 520px;
  }
}
</style>
