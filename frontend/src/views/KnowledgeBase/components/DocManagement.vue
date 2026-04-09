<template>
  <div class="doc-management">
    <!-- 上传区域 -->
    <div class="upload-section">
      <el-upload
        :action="uploadUrl"
        :headers="uploadHeaders"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :before-upload="beforeUpload"
        :show-file-list="false"
        drag
        multiple
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 PDF、Word、TXT 文件，单文件最大 50MB
          </div>
        </template>
      </el-upload>
    </div>

    <!-- 文档列表 -->
    <el-table :data="documents" v-loading="loading" stripe>
      <el-table-column prop="filename" label="文件名" min-width="180" />
      <el-table-column prop="description" label="描述" min-width="200">
        <template #default="{ row }">
          <span v-if="row.description">{{ row.description }}</span>
          <el-text v-else type="info" size="small">无描述</el-text>
        </template>
      </el-table-column>
      <el-table-column prop="file_size" label="大小" width="90">
        <template #default="{ row }">
          {{ formatSize(row.file_size) }}
        </template>
      </el-table-column>
      <el-table-column prop="chunks_count" label="分块数" width="80" align="center" />
      <el-table-column prop="status" label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="uploaded_at" label="上传时间" width="160">
        <template #default="{ row }">
          {{ formatDate(row.uploaded_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="editDescription(row)">
            描述
          </el-button>
          <el-button type="warning" link size="small" @click="openReupload(row)">
            重传
          </el-button>
          <el-button type="primary" link size="small" @click="previewDoc(row)">
            预览
          </el-button>
          <el-button type="primary" link size="small" @click="downloadDoc(row)">
            下载
          </el-button>
          <el-button type="danger" link size="small" @click="deleteDoc(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 预览弹窗 -->
    <el-dialog v-model="previewVisible" title="文档预览" width="80%" top="5vh">
      <div v-if="previewType === 'pdf'" class="pdf-preview">
        <iframe :src="previewUrl" width="100%" height="70vh"></iframe>
      </div>
      <div v-else class="text-preview">
        <pre>{{ previewContent }}</pre>
      </div>
    </el-dialog>

    <!-- 描述编辑弹窗 -->
    <el-dialog v-model="descDialogVisible" title="编辑文档描述" width="500px">
      <el-form :model="descForm" label-width="80px">
        <el-form-item label="描述">
          <el-input
            v-model="descForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入文档描述（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="descDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveDescription" :loading="savingDesc">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 重新上传弹窗 -->
    <el-dialog v-model="reuploadDialogVisible" title="重新上传文档" width="500px">
      <el-form :model="reuploadForm" label-width="100px">
        <el-form-item label="当前文件">
          <el-text>{{ reuploadForm.filename }}</el-text>
        </el-form-item>
        <el-form-item label="选择新文件">
          <input
            type="file"
            ref="reuploadFileInput"
            @change="handleReuploadFileChange"
            accept=".pdf,.doc,.docx,.txt,.md"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="reuploadForm.description"
            type="textarea"
            :rows="2"
            placeholder="可选"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reuploadDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleReupload" :loading="reuploading">
          重新上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { API_ENDPOINTS } from '@/assets/config'
import type { DocumentItem } from '@/types'

const props = defineProps<{
  kbId: string
}>()

const loading = ref(false)
const documents = ref<DocumentItem[]>([])

const previewVisible = ref(false)
const previewType = ref<'pdf' | 'text'>('text')
const previewUrl = ref('')
const previewContent = ref('')

const descDialogVisible = ref(false)
const descForm = ref({ doc_id: '', description: '' })
const savingDesc = ref(false)

const reuploadDialogVisible = ref(false)
const reuploadForm = ref({ doc_id: '', filename: '', selectedFile: null as File | null, description: '' })
const reuploading = ref(false)
const reuploadFileInput = ref<HTMLInputElement | null>(null)

// 上传地址
const uploadUrl = computed(() => API_ENDPOINTS.docUpload(props.kbId))
const uploadHeaders = computed(() => ({}))

onMounted(() => {
  fetchDocuments()
})

// 获取文档列表
async function fetchDocuments() {
  loading.value = true
  try {
    const res = await fetch(API_ENDPOINTS.docList(props.kbId))
    const data = await res.json()
    if (data.code === 0) {
      documents.value = data.data.items || []
    }
  } catch (e) {
    console.error('获取文档列表失败', e)
  } finally {
    loading.value = false
  }
}

// 上传前检查
function beforeUpload(file: File) {
  const ext = file.name.split('.').pop()?.toLowerCase()
  const allowed = ['pdf', 'docx', 'doc', 'txt', 'md']
  
  if (!allowed.includes(ext || '')) {
    ElMessage.error('不支持的文件类型')
    return false
  }
  
  if (file.size > 50 * 1024 * 1024) {
    ElMessage.error('文件大小超过 50MB')
    return false
  }
  
  return true
}

// 上传成功
function handleUploadSuccess(response: any) {
  if (response.code === 0) {
    ElMessage.success('上传成功，正在处理中')
    setTimeout(fetchDocuments, 2000)
  } else {
    ElMessage.error(response.message || '上传失败')
  }
}

// 上传失败
function handleUploadError() {
  ElMessage.error('上传失败')
}

// 编辑描述
function editDescription(doc: DocumentItem) {
  descForm.value = { doc_id: doc.doc_id, description: doc.description || '' }
  descDialogVisible.value = true
}

// 保存描述
async function saveDescription() {
  savingDesc.value = true
  try {
    const res = await fetch(API_ENDPOINTS.docUpdate(props.kbId, descForm.value.doc_id), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description: descForm.value.description })
    })
    const data = await res.json()
    
    if (data.code === 0) {
      ElMessage.success('保存成功')
      descDialogVisible.value = false
      fetchDocuments()
    } else {
      ElMessage.error('保存失败')
    }
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    savingDesc.value = false
  }
}

// 打开重新上传
function openReupload(doc: DocumentItem) {
  reuploadForm.value = {
    doc_id: doc.doc_id,
    filename: doc.filename,
    selectedFile: null,
    description: doc.description || ''
  }
  reuploadDialogVisible.value = true
}

// 处理文件选择
function handleReuploadFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    reuploadForm.value.selectedFile = target.files[0]
  }
}

// 执行重新上传
async function handleReupload() {
  if (!reuploadForm.value.selectedFile) {
    ElMessage.warning('请选择文件')
    return
  }
  
  const file = reuploadForm.value.selectedFile
  const ext = file.name.split('.').pop()?.toLowerCase()
  const allowed = ['pdf', 'docx', 'doc', 'txt', 'md']
  
  if (!allowed.includes(ext || '')) {
    ElMessage.error('不支持的文件类型')
    return
  }
  
  if (file.size > 50 * 1024 * 1024) {
    ElMessage.error('文件大小超过 50MB')
    return
  }
  
  reuploading.value = true
  
  const formData = new FormData()
  formData.append('file', file)
  if (reuploadForm.value.description) {
    formData.append('description', reuploadForm.value.description)
  }
  
  try {
    const res = await fetch(API_ENDPOINTS.docReupload(props.kbId, reuploadForm.value.doc_id), {
      method: 'POST',
      body: formData
    })
    const data = await res.json()
    
    if (data.code === 0) {
      ElMessage.success('重新上传成功，正在处理中')
      reuploadDialogVisible.value = false
      setTimeout(fetchDocuments, 2000)
    } else {
      ElMessage.error(data.message || '重新上传失败')
    }
  } catch (e) {
    ElMessage.error('重新上传失败')
  } finally {
    reuploading.value = false
  }
}

// 预览文档
async function previewDoc(doc: DocumentItem) {
  try {
    const res = await fetch(API_ENDPOINTS.docPreview(props.kbId, doc.doc_id))
    const data = await res.json()
    
    if (data.code === 0) {
      if (data.data.type === 'pdf') {
        previewType.value = 'pdf'
        previewUrl.value = API_ENDPOINTS.docDownload(props.kbId, doc.doc_id)
      } else {
        previewType.value = 'text'
        previewContent.value = data.data.content
      }
      previewVisible.value = true
    }
  } catch (e) {
    ElMessage.error('预览失败')
  }
}

// 下载文档
function downloadDoc(doc: DocumentItem) {
  const url = API_ENDPOINTS.docDownload(props.kbId, doc.doc_id)
  window.open(url, '_blank')
}

// 删除文档
async function deleteDoc(doc: DocumentItem) {
  try {
    await ElMessageBox.confirm('确定要删除该文档吗？', '警告', { type: 'warning' })
    
    const res = await fetch(API_ENDPOINTS.docDelete(props.kbId, doc.doc_id), {
      method: 'DELETE'
    })
    const data = await res.json()
    
    if (data.code === 0) {
      ElMessage.success('删除成功')
      fetchDocuments()
    } else {
      ElMessage.error('删除失败')
    }
  } catch {}
}

// 格式化
function formatSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

function formatDate(date: string) {
  return new Date(date).toLocaleString('zh-CN')
}

function statusType(status: string) {
  return { processing: 'warning', completed: 'success', failed: 'danger' }[status] || 'info'
}

function statusText(status: string) {
  return { processing: '处理中', completed: '完成', failed: '失败' }[status] || status
}
</script>

<style scoped>
.doc-management {
  padding: 20px 0;
}

.upload-section {
  margin-bottom: 20px;
}

.pdf-preview iframe {
  border: none;
}

.text-preview pre {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  overflow: auto;
  max-height: 60vh;
  white-space: pre-wrap;
}
</style>