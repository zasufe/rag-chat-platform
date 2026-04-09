// API 基础配置
// 本地开发使用后端直连，生产环境使用 Nginx 代理
export const API_BASE = window.location.hostname === 'localhost' 
  ? 'http://172.16.25.187:8000' 
  : '/kb-api'

// API 端点
export const API_ENDPOINTS = {
  // 对话
  chatStream: `${API_BASE}/api/chat/stream`,
  chatTest: `${API_BASE}/api/chat/test`,
  
  // 知识库
  kbList: `${API_BASE}/api/kb`,
  kbDetail: (id: string) => `${API_BASE}/api/kb/${id}`,
  kbUpdate: (id: string) => `${API_BASE}/api/kb/${id}`,
  kbSearch: (id: string) => `${API_BASE}/api/kb/${id}/search`,
  
  // 文档
  docUpload: (kbId: string) => `${API_BASE}/api/kb/${kbId}/docs/upload`,
  docList: (kbId: string) => `${API_BASE}/api/kb/${kbId}/docs`,
  docDownload: (kbId: string, docId: string) => `${API_BASE}/api/kb/${kbId}/docs/${docId}/download`,
  docPreview: (kbId: string, docId: string) => `${API_BASE}/api/kb/${kbId}/docs/${docId}/preview`,
  docDelete: (kbId: string, docId: string) => `${API_BASE}/api/kb/${kbId}/docs/${docId}`,
  docUpdate: (kbId: string, docId: string) => `${API_BASE}/api/kb/${kbId}/docs/${docId}`,
  docReupload: (kbId: string, docId: string) => `${API_BASE}/api/kb/${kbId}/docs/${docId}/reupload`
}