<template>
  <div class="search-test">
    <el-card>
      <template #header>
        <span>检索测试</span>
      </template>
      
      <el-form @submit.prevent="handleSearch">
        <el-form-item label="查询内容">
          <el-input
            v-model="query"
            type="textarea"
            :rows="3"
            placeholder="输入测试问题"
          />
        </el-form-item>
        <el-form-item label="返回数量">
          <el-input-number v-model="topK" :min="1" :max="10" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch" :loading="loading">
            检索
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 检索结果 -->
    <div v-if="results.length > 0" class="results">
      <h3>检索结果 ({{ results.length }} 条)</h3>
      <el-card v-for="(item, idx) in results" :key="idx" class="result-item">
        <div class="result-header">
          <span class="source">[{{ idx + 1 }}] {{ item.source }}</span>
          <el-tag>相似度: {{ (item.similarity * 100).toFixed(1) }}%</el-tag>
        </div>
        <div class="result-content">{{ item.content }}</div>
      </el-card>
    </div>

    <el-empty v-else-if="!loading" description="输入查询内容进行检索测试" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { API_ENDPOINTS } from '@/assets/config'
import type { ReferenceChunk } from '@/types'

const props = defineProps<{
  kbId: string
}>()

const query = ref('')
const topK = ref(3)
const loading = ref(false)
const results = ref<ReferenceChunk[]>([])

async function handleSearch() {
  if (!query.value.trim()) {
    ElMessage.warning('请输入查询内容')
    return
  }
  
  loading.value = true
  try {
    const res = await fetch(API_ENDPOINTS.kbSearch(props.kbId), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query.value,
        top_k: topK.value
      })
    })
    
    const data = await res.json()
    if (data.code === 0) {
      results.value = data.data.chunks || []
    } else {
      ElMessage.error('检索失败')
    }
  } catch (e) {
    ElMessage.error('检索失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.search-test {
  padding: 20px 0;
}

.results {
  margin-top: 20px;
}

.results h3 {
  margin-bottom: 16px;
  color: #303133;
}

.result-item {
  margin-bottom: 16px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.source {
  font-weight: 500;
  color: #409eff;
}

.result-content {
  color: #606266;
  line-height: 1.6;
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
}
</style>