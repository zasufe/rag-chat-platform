import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Message, ReferenceChunk } from '@/types'

export const useChatStore = defineStore('chat', () => {
  // 状态
  const messages = ref<Message[]>([])
  const currentKBId = ref<string>('')
  const isStreaming = ref(false)
  const currentContent = ref('')
  const currentReferences = ref<ReferenceChunk[]>([])
  
  // 添加消息
  function addMessage(message: Message) {
    messages.value.push({
      ...message,
      timestamp: Date.now()
    })
  }
  
  // 更新最后一条消息
  function updateLastMessage(content: string) {
    if (messages.value.length > 0) {
      const last = messages.value[messages.value.length - 1]
      if (last.role === 'assistant') {
        last.content = content
      }
    }
  }
  
  // 设置引用
  function setReferences(refs: ReferenceChunk[]) {
    currentReferences.value = refs
    if (messages.value.length > 0) {
      const last = messages.value[messages.value.length - 1]
      if (last.role === 'assistant') {
        last.references = refs
      }
    }
  }
  
  // 清空消息
  function clearMessages() {
    messages.value = []
    currentContent.value = ''
    currentReferences.value = []
  }
  
  // 设置知识库
  function setKBId(kbId: string) {
    currentKBId.value = kbId
    // 切换知识库时清空对话
    clearMessages()
  }
  
  // 设置流状态
  function setStreaming(status: boolean) {
    isStreaming.value = status
    if (!status) {
      currentContent.value = ''
    }
  }
  
  return {
    messages,
    currentKBId,
    isStreaming,
    currentContent,
    currentReferences,
    addMessage,
    updateLastMessage,
    setReferences,
    clearMessages,
    setKBId,
    setStreaming
  }
})