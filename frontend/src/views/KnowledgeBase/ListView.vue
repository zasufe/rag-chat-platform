<template>
  <div class="kb-list-view">
    <!-- 统计卡片 -->
    <div class="stats-row">
      <el-card class="stat-card">
        <div class="stat-value">{{ kbStore.knowledgeBases.length }}</div>
        <div class="stat-label">知识库总数</div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-value">{{ totalDocs }}</div>
        <div class="stat-label">文档总数</div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-value">{{ totalChunks }}</div>
        <div class="stat-label">文档块总数</div>
      </el-card>
    </div>

    <!-- 操作栏 -->
    <div class="toolbar">
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon> 新建知识库
      </el-button>
    </div>

    <!-- 表格 -->
    <el-table :data="kbStore.knowledgeBases" v-loading="kbStore.loading" stripe>
      <el-table-column prop="name" label="名称" min-width="150">
        <template #default="{ row }">
          <div class="name-cell">
            <span>{{ row.name }}</span>
            <el-button type="primary" link size="small" @click="openEditDialog(row)">
              <el-icon><Edit /></el-icon>
            </el-button>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="id" label="ID" width="280">
        <template #default="{ row }">
          <el-text type="info" size="small">{{ row.id }}</el-text>
        </template>
      </el-table-column>
      <el-table-column prop="document_count" label="文档数" width="100" align="center" />
      <el-table-column prop="total_chunks" label="分块数" width="100" align="center" />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="enterDetail(row.id)">
            进入
          </el-button>
          <el-button type="danger" link @click="handleDelete(row.id)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建弹窗 -->
    <el-dialog v-model="showCreateDialog" title="新建知识库" width="400px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="createForm.name" placeholder="请输入知识库名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">
          创建
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="showEditDialog" title="修改知识库名称" width="400px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="editForm.name" placeholder="请输入新的知识库名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleEdit" :loading="editing">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit } from '@element-plus/icons-vue'
import { useKBStore } from '@/stores/kb'
import { API_ENDPOINTS } from '@/assets/config'

const router = useRouter()
const kbStore = useKBStore()

const showCreateDialog = ref(false)
const createForm = ref({ name: '' })
const creating = ref(false)

const showEditDialog = ref(false)
const editForm = ref({ id: '', name: '' })
const editing = ref(false)

// 统计
const totalDocs = computed(() => 
  kbStore.knowledgeBases.reduce((sum, kb) => sum + kb.document_count, 0)
)
const totalChunks = computed(() => 
  kbStore.knowledgeBases.reduce((sum, kb) => sum + kb.total_chunks, 0)
)

onMounted(() => {
  kbStore.fetchKBList()
})

// 格式化日期
function formatDate(date: string | Date) {
  const d = new Date(date)
  return d.toLocaleString('zh-CN')
}

// 打开编辑弹窗
function openEditDialog(row: any) {
  editForm.value = { id: row.id, name: row.name }
  showEditDialog.value = true
}

// 创建知识库
async function handleCreate() {
  if (!createForm.value.name.trim()) {
    ElMessage.warning('请输入知识库名称')
    return
  }
  
  creating.value = true
  const id = await kbStore.createKB(createForm.value.name)
  creating.value = false
  
  if (id) {
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    createForm.value.name = ''
  } else {
    ElMessage.error('创建失败')
  }
}

// 编辑知识库名称
async function handleEdit() {
  if (!editForm.value.name.trim()) {
    ElMessage.warning('请输入知识库名称')
    return
  }
  
  editing.value = true
  try {
    const res = await fetch(API_ENDPOINTS.kbUpdate(editForm.value.id), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: editForm.value.name })
    })
    const data = await res.json()
    
    if (data.code === 0) {
      ElMessage.success('修改成功')
      showEditDialog.value = false
      kbStore.fetchKBList()
    } else {
      ElMessage.error('修改失败')
    }
  } catch (e) {
    ElMessage.error('修改失败')
  } finally {
    editing.value = false
  }
}

// 删除知识库
async function handleDelete(id: string) {
  try {
    await ElMessageBox.confirm('确定要删除该知识库吗？所有文档将被删除。', '警告', {
      type: 'warning'
    })
    
    const success = await kbStore.deleteKB(id)
    if (success) {
      ElMessage.success('删除成功')
    } else {
      ElMessage.error('删除失败')
    }
  } catch {}
}

// 进入详情
function enterDetail(id: string) {
  router.push(`/kb/${id}`)
}
</script>

<style scoped>
.kb-list-view {
  padding: 20px;
}

.stats-row {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  flex: 1;
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.toolbar {
  margin-bottom: 16px;
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.name-cell span {
  flex: 1;
}
</style>