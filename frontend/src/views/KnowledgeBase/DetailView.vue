<template>
  <div class="kb-detail-view">
    <!-- 顶部导航 -->
    <div class="header">
      <el-button @click="$router.push('/kb')">
        <el-icon><ArrowLeft /></el-icon> 返回列表
      </el-button>
      <h2>{{ kbInfo?.name || '知识库详情' }}</h2>
      <div class="header-actions">
        <span class="kb-id" v-if="kbInfo">ID: {{ kbInfo.id?.slice(0, 8) }}</span>
      </div>
    </div>

    <!-- 标签页 -->
    <div class="content-wrapper">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="📄 文档管理" name="docs">
          <DocManagement v-if="activeTab === 'docs' && kbId" :kb-id="kbId" />
        </el-tab-pane>
        <el-tab-pane label="🔍 检索测试" name="search">
          <SearchTest v-if="activeTab === 'search' && kbId" :kb-id="kbId" />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import DocManagement from './components/DocManagement.vue'
import SearchTest from './components/SearchTest.vue'
import { API_ENDPOINTS } from '@/assets/config'

const route = useRoute()
const router = useRouter()
const kbId = ref<string>('')
const activeTab = ref('docs')
const kbInfo = ref<any>(null)

onMounted(async () => {
  // 获取路由参数中的 kb_id
  kbId.value = route.params.id as string
  
  if (!kbId.value) {
    ElMessage.error('知识库 ID 无效')
    router.push('/kb')
    return
  }
  
  // 获取知识库信息
  await fetchKBInfo()
})

async function fetchKBInfo() {
  try {
    const res = await fetch(API_ENDPOINTS.kbDetail(kbId.value))
    const data = await res.json()
    if (data.code === 0) {
      kbInfo.value = data.data
    } else {
      ElMessage.error('获取知识库信息失败')
    }
  } catch (e) {
    console.error('获取知识库信息失败', e)
  }
}

function handleTabChange(name: string) {
  // 切换标签页
}
</script>

<style scoped>
.kb-detail-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.header h2 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.kb-id {
  color: #909399;
  font-size: 13px;
  font-family: monospace;
}

.content-wrapper {
  flex: 1;
  padding: 20px;
  overflow: auto;
}

.content-wrapper :deep(.el-tabs) {
  height: 100%;
}

.content-wrapper :deep(.el-tabs__content) {
  height: calc(100% - 55px);
  overflow: auto;
}

.content-wrapper :deep(.el-tab-pane) {
  height: 100%;
}
</style>