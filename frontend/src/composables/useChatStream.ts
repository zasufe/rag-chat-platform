import { ref } from 'vue'
import type { ChatRequest, ChatStreamChunk } from '@/types'
import { API_ENDPOINTS } from '@/assets/config'
import { useChatStore } from '@/stores/chat'

export function useChatStream() {
  const chatStore = useChatStore()
  const error = ref<string | null>(null)
  const abortController = ref<AbortController | null>(null)
  
  // 发送消息
  async function sendMessage(params: ChatRequest) {
    error.value = null
    chatStore.setStreaming(true)
    
    // 添加用户消息
    chatStore.addMessage({
      role: 'user',
      content: params.text
    })
    
    // 添加空的 AI 消息
    chatStore.addMessage({
      role: 'assistant',
      content: ''
    })
    
    abortController.value = new AbortController()
    
    try {
      const response = await fetch(API_ENDPOINTS.chatStream, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
        signal: abortController.value.signal
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      
      while (reader) {
        const { done, value } = await reader.read()
        if (done) break
        
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''
        
        for (const line of lines) {
          if (!line.trim()) continue
          
          // 解析 SSE 事件
          const eventMatch = line.match(/^event:\s*(\w+)\ndata:\s*(.+)$/s)
          if (eventMatch) {
            const eventType = eventMatch[1]
            const dataStr = eventMatch[2]
            
            try {
              const data: ChatStreamChunk = JSON.parse(dataStr)
              
              if (eventType === 'message' && data.type === 'delta' && data.content) {
                chatStore.currentContent += data.content
                chatStore.updateLastMessage(chatStore.currentContent)
              } else if (eventType === 'reference' && data.references) {
                chatStore.setReferences(data.references)
              } else if (eventType === 'done') {
                chatStore.setStreaming(false)
              } else if (eventType === 'error') {
                error.value = data.error || '未知错误'
                chatStore.updateLastMessage(`错误: ${error.value}`)
                chatStore.setStreaming(false)
              }
            } catch (e) {
              console.error('解析 SSE 数据失败', e)
            }
          }
        }
      }
      
    } catch (e: any) {
      if (e.name === 'AbortError') {
        console.log('用户中断了请求')
      } else {
        error.value = e.message
        chatStore.updateLastMessage(`错误: ${e.message}`)
      }
    } finally {
      chatStore.setStreaming(false)
      abortController.value = null
    }
  }
  
  // 停止生成
  function stopGeneration() {
    if (abortController.value) {
      abortController.value.abort()
    }
  }
  
  return {
    error,
    sendMessage,
    stopGeneration
  }
}