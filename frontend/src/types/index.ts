// 消息类型
export interface Message {
  role: 'system' | 'user' | 'assistant'
  content: string
  timestamp?: number
  references?: ReferenceChunk[]
}

// 引用块
export interface ReferenceChunk {
  content: string
  source: string
  doc_id: string
  similarity: number
}

// 对话请求
export interface ChatRequest {
  messages: Message[]
  code: string
  text: string
  kb_id?: string
  use_kb: boolean
  top_k: number
}

// SSE 响应
export interface ChatStreamChunk {
  type: 'delta' | 'done' | 'error' | 'reference'
  content?: string
  references?: ReferenceChunk[]
  error?: string
}

// 知识库
export interface KnowledgeBase {
  id: string
  name: string
  document_count: number
  total_chunks: number
  created_at: string
  updated_at: string
}

// 文档
export interface DocumentItem {
  doc_id: string
  filename: string
  file_size: number
  chunks_count: number
  mime_type: string
  uploaded_at: string
  status: 'processing' | 'completed' | 'failed'
  error_msg?: string
  description?: string  // 文件描述
}

// 上传进度
export interface UploadProgress {
  file: File
  progress: number
  status: 'uploading' | 'parsing' | 'done' | 'error'
  doc_id?: string
}

// API 响应
export interface ApiResponse<T = any> {
  code: number
  message?: string
  data?: T
}