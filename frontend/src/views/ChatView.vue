<template>
  <div class="chat-view">
    <!-- 顶部工具栏 -->
    <div class="chat-header">
      <div class="kb-selector">
        <span class="label">知识库：</span>
        <el-select v-model="chatStore.currentKBId" placeholder="选择知识库" @change="handleKBChange">
          <el-option label="不使用知识库" value="" />
          <el-option
            v-for="kb in kbStore.knowledgeBases"
            :key="kb.id"
            :label="`${kb.name} (${kb.total_chunks} 块)`"
            :value="kb.id"
          />
        </el-select>
      </div>
      <div class="actions">
        <el-button @click="chatStore.clearMessages" :disabled="chatStore.messages.length === 0">
          清空对话
        </el-button>
        <el-button type="primary" @click="$router.push('/kb')">
          知识库管理
        </el-button>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="message-list" ref="messageListRef">
      <div v-if="chatStore.messages.length === 0" class="empty-state">
        <el-icon :size="48"><ChatDotRound /></el-icon>
        <p>开始对话吧！</p>
        <p class="hint">选择知识库可获得更准确的回答</p>
      </div>

      <div
        v-for="(msg, idx) in chatStore.messages"
        :key="idx"
        :class="['message', msg.role]"
      >
        <div class="avatar">
          {{ msg.role === 'user' ? '我' : 'AI' }}
        </div>
        <div class="content">
          <div class="text" v-html="renderMarkdown(msg.content)"></div>
          
          <!-- 引用来源 -->
          <div v-if="msg.references && msg.references.length > 0" class="references">
            <el-collapse>
              <el-collapse-item title="📖 参考来源">
                <div
                  v-for="(ref, rIdx) in msg.references"
                  :key="rIdx"
                  class="reference-item"
                >
                  <div class="ref-header">
                    <span class="source">[{{ rIdx + 1 }}] {{ ref.source }}</span>
                    <span class="similarity">{{ (ref.similarity * 100).toFixed(1) }}%</span>
                  </div>
                  <div class="ref-content">{{ ref.content.slice(0, 200) }}...</div>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </div>
      </div>

      <!-- 加载中 -->
      <div v-if="chatStore.isStreaming && !chatStore.currentContent" class="message assistant">
        <div class="avatar">AI</div>
        <div class="content">
          <el-skeleton :rows="2" animated />
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="3"
        placeholder="输入问题，按 Enter 发送，Shift+Enter 换行"
        :disabled="chatStore.isStreaming"
        @keydown.enter.exact="handleSend"
      />
      <div class="input-actions">
        <span class="hint">知识库: {{ currentKBName }}</span>
        <div>
          <el-button
            v-if="chatStore.isStreaming"
            type="danger"
            @click="stopGeneration"
          >
            停止生成
          </el-button>
          <el-button
            v-else
            type="primary"
            @click="handleSend"
            :disabled="!inputText.trim()"
          >
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { ChatDotRound } from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'
import { useKBStore } from '@/stores/kb'
import { useChatStream } from '@/composables/useChatStream'

const chatStore = useChatStore()
const kbStore = useKBStore()
const { sendMessage, stopGeneration } = useChatStream()

const inputText = ref('')
const messageListRef = ref<HTMLElement | null>(null)

// 当前知识库名称
const currentKBName = computed(() => {
  if (!chatStore.currentKBId) return '未选择'
  const kb = kbStore.knowledgeBases.find(k => k.id === chatStore.currentKBId)
  return kb?.name || '未知'
})

// 加载知识库列表
onMounted(() => {
  kbStore.fetchKBList()
})

// 滚动到底部
function scrollToBottom() {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

// 监听消息变化，自动滚动
watch(() => chatStore.messages.length, scrollToBottom)
watch(() => chatStore.currentContent, scrollToBottom)

// 发送消息
function handleSend() {
  if (!inputText.value.trim() || chatStore.isStreaming) return
  
  const text = inputText.value.trim()
  inputText.value = ''
  
  sendMessage({
    messages: chatStore.messages.slice(0, -1).map(m => ({
      role: m.role,
      content: m.content
    })),
    code: '',
    text,
    kb_id: chatStore.currentKBId || undefined,
    use_kb: !!chatStore.currentKBId,
    top_k: 3
  })
}

// 知识库切换
function handleKBChange() {
  chatStore.clearMessages()
}

// 简单的 Markdown 渲染
function renderMarkdown(text: string): string {
  if (!text) return ''
  
  return text
    // 代码块
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>')
    // 行内代码
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // 粗体
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    // 斜体
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    // 换行
    .replace(/\n/g, '<br>')
}
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.kb-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.kb-selector .label {
  font-weight: 500;
  color: #606266;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #909399;
}

.empty-state .hint {
  font-size: 14px;
  margin-top: 8px;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #409eff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  flex-shrink: 0;
}

.message.user .avatar {
  background: #67c23a;
}

.content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.message.user .content {
  background: #409eff;
  color: #fff;
}

.text {
  line-height: 1.6;
}

.text :deep(pre) {
  background: #282c34;
  color: #abb2bf;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 10px 0;
}

.text :deep(code) {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: monospace;
}

.message.user .text :deep(code) {
  background: rgba(255,255,255,0.2);
}

.references {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #eee;
}

.reference-item {
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 8px;
}

.ref-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.source {
  font-weight: 500;
  color: #409eff;
}

.similarity {
  color: #909399;
  font-size: 12px;
}

.ref-content {
  font-size: 13px;
  color: #606266;
}

.input-area {
  padding: 16px 20px;
  background: #fff;
  border-top: 1px solid #e4e7ed;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.input-actions .hint {
  color: #909399;
  font-size: 13px;
}
</style>