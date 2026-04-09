import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { KnowledgeBase } from '@/types'
import { API_ENDPOINTS } from '@/assets/config'

export const useKBStore = defineStore('kb', () => {
  // 状态
  const knowledgeBases = ref<KnowledgeBase[]>([])
  const currentKB = ref<KnowledgeBase | null>(null)
  const loading = ref(false)
  
  // 计算属性
  const kbOptions = computed(() => [
    { value: '', label: '不使用知识库' },
    ...knowledgeBases.value.map(kb => ({
      value: kb.id,
      label: `${kb.name} (${kb.id.slice(0, 8)})`
    }))
  ])
  
  // 获取知识库列表
  async function fetchKBList() {
    loading.value = true
    try {
      const res = await fetch(API_ENDPOINTS.kbList)
      const data = await res.json()
      knowledgeBases.value = data.items || []
    } catch (e) {
      console.error('获取知识库列表失败', e)
    } finally {
      loading.value = false
    }
  }
  
  // 创建知识库
  async function createKB(name: string) {
    try {
      const res = await fetch(API_ENDPOINTS.kbList, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      })
      const data = await res.json()
      if (data.code === 0) {
        await fetchKBList()
        return data.data.kb_id
      }
      return null
    } catch (e) {
      console.error('创建知识库失败', e)
      return null
    }
  }
  
  // 删除知识库
  async function deleteKB(id: string) {
    try {
      const res = await fetch(API_ENDPOINTS.kbDetail(id), {
        method: 'DELETE'
      })
      const data = await res.json()
      if (data.code === 0) {
        await fetchKBList()
        return true
      }
      return false
    } catch (e) {
      console.error('删除知识库失败', e)
      return false
    }
  }
  
  // 设置当前知识库
  function setCurrentKB(kb: KnowledgeBase | null) {
    currentKB.value = kb
  }
  
  return {
    knowledgeBases,
    currentKB,
    loading,
    kbOptions,
    fetchKBList,
    createKB,
    deleteKB,
    setCurrentKB
  }
})