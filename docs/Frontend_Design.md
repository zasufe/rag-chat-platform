# RAG 知识库系统 - 前端设计文档

**文档版本**: v2.0.0  
**创建日期**: 2026-04-09  
**设计师**: AI UI Designer

---

## 1. 设计概述

### 1.1 设计理念

- **简洁高效**: 专注于对话和知识管理核心功能
- **响应式**: 适配不同屏幕尺寸
- **流式体验**: 实时打字机效果，支持中断
- **可视化**: 知识库和文档状态清晰展示

### 1.2 设计语言

| 属性 | 值 |
|------|-----|
| **风格** | 现代、简洁、专业 |
| **主题** | 浅色主题 + 科技蓝点缀 |
| **情感** | 可信赖、智能、高效 |

---

## 2. 技术架构

### 2.1 技术栈

```
┌─────────────────────────────────────────┐
│           用户界面层                     │
│  Element Plus UI Components             │
├─────────────────────────────────────────┤
│           组件层                         │
│  Vue 3 Components (<script setup>)      │
├─────────────────────────────────────────┤
│           状态管理层                     │
│  Pinia Stores                           │
├─────────────────────────────────────────┤
│           逻辑层                         │
│  Composables (useChat, useKB)           │
├─────────────────────────────────────────┤
│           数据层                         │
│  Fetch API + SSE                        │
└─────────────────────────────────────────┘
```

### 2.2 目录结构

```
frontend/
├── src/
│   ├── main.ts                    # 应用入口
│   ├── App.vue                    # 根组件
│   │
│   ├── router/
│   │   └── index.ts               # 路由配置
│   │
│   ├── stores/                    # Pinia 状态管理
│   │   ├── kb.ts                  # 知识库状态
│   │   └── chat.ts                # 对话状态
│   │
│   ├── composables/               # 组合式函数
│   │   └── useChatStream.ts       # SSE 流式对话
│   │
│   ├── types/
│   │   └── index.ts               # TypeScript 类型定义
│   │
│   ├── assets/
│   │   └── config.ts              # API 配置
│   │
│   └── views/                     # 页面组件
│       ├── ChatView.vue           # 对话页面
│       └── KnowledgeBase/
│           ├── ListView.vue       # 知识库列表
│           └── DetailView.vue     # 知识库详情
│
├── package.json
├── vite.config.ts
└── tsconfig.json
```

---

## 3. 色彩系统

### 3.1 主色调

```
科技蓝 (Primary):
- #409EFF  (主按钮、链接、高亮)
- #66B1FF  (悬停)
- #337ECC  (点击)
- #ECF5FF  (背景)
```

### 3.2 功能色

```
成功 (Success):  #67C23A  (完成、正常)
警告 (Warning):  #E6A23C  (处理中、注意)
危险 (Danger):   #F56C6C  (错误、删除)
信息 (Info):     #909399  (提示、辅助)
```

### 3.3 中性色

```
标题：  #303133
正文：  #606266
辅助：  #909399
边框：  #DCDFE6
背景：  #F5F7FA
```

---

## 4. 字体系统

### 4.1 字体家族

```css
font-family: -apple-system, BlinkMacSystemFont,
             'Segoe UI', 'PingFang SC', 'Hiragino Sans GB',
             'Microsoft YaHei', sans-serif;
```

### 4.2 字号规范

| 用途 | 字号 | 字重 |
|------|------|------|
| 大标题 | 18px | 600 |
| 标题 | 16px | 500 |
| 正文 | 14px | 400 |
| 辅助 | 13px | 400 |
| 代码 | 13px | 400 (Consolas) |

---

## 5. 布局设计

### 5.1 整体布局

```
┌─────────────────────────────────────────────────────────┐
│  顶部导航栏 (Header) - 60px                             │
│  Logo | 页面标题 | 状态指示                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│                     主内容区                             │
│                  (Main Content)                         │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │                                                 │   │
│  │              页面内容                            │   │
│  │                                                 │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 5.2 对话页面布局

```
┌──────────────────────────────────────────────────────┐
│  AI 对话                          [知识库选择▼]      │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │                                                │ │
│  │  消息列表 (MessageList)                        │ │
│  │  ┌──────────────────────────────────────────┐ │ │
│  │  │ 👤 用户                                   │ │ │
│  │  │ 你好，介绍一下这个知识库                  │ │ │
│  │  └──────────────────────────────────────────┘ │ │
│  │  ┌──────────────────────────────────────────┐ │ │
│  │  │ 🤖 AI                                     │ │ │
│  │  │ 这是一个...[流式输出中...]                │ │ │
│  │  │ ───────────────────────────────────────  │ │ │
│  │  │ [📎 引用来源 3 条] [展开▼]                │ │ │
│  │  └──────────────────────────────────────────┘ │ │
│  │                                                │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  输入框                                         │ │
│  │  ┌──────────────────────────────────────────┐ │ │
│  │  │ 输入你的问题...                    [发送] │ │ │
│  │  └──────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

### 5.3 知识库列表页布局

```
┌──────────────────────────────────────────────────────┐
│  知识库管理               [+ 新建知识库]              │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐             │
│  │ 知识库  │  │ 文档数  │  │ 分块数  │  统计卡片   │
│  │   12   │  │   48    │  │  1256   │             │
│  └─────────┘  └─────────┘  └─────────┘             │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  知识库列表 (表格)                             │ │
│  │  ┌────┬──────┬────┬────┬──────┬─────────────┐│ │
│  │  │名称│ID    │文档│分块│时间  │操作         ││ │
│  │  ├────┼──────┼────┼────┼──────┼─────────────┤│ │
│  │  │测试│abc.. │ 5  │128 │10:23 │[进入] [删除]││ │
│  │  └────┴──────┴────┴────┴──────┴─────────────┘│ │
│  └────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

### 5.4 知识库详情页布局

```
┌──────────────────────────────────────────────────────┐
│  [← 返回]  测试知识库              ID: abc123...     │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  [📄 文档管理]  [🔍 检索测试]   (标签页)       │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  文档管理                                      │ │
│  │  ┌──────────────────────────────────────────┐ │ │
│  │  │  ┌────────────────────────────────────┐ │ │ │
│  │  │  │  拖拽文件到此处或点击上传          │ │ │ │
│  │  │  │  支持 PDF、Word、TXT 文件           │ │ │ │
│  │  │  └────────────────────────────────────┘ │ │ │
│  │  │                                         │ │ │
│  │  │  文档列表 (表格)                        │ │ │
│  │  │  - 文件名 | 大小 | 状态 | 操作          │ │ │
│  │  │  - contract.pdf | 2MB | ✅ | [预览]... │ │ │
│  │  └──────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

---

## 6. 组件设计

### 6.1 核心组件

#### ChatView (对话页面)

```vue
<template>
  <div class="chat-view">
    <!-- 顶部栏 -->
    <div class="header">
      <h2>AI 对话</h2>
      <el-select v-model="kbId" placeholder="选择知识库">
        <el-option label="不使用知识库" value="" />
        <el-option v-for="kb in kbList" :key="kb.id" 
                   :label="kb.name" :value="kb.id" />
      </el-select>
    </div>
    
    <!-- 消息列表 -->
    <MessageList :messages="messages" />
    
    <!-- 引用面板 -->
    <ReferencePanel v-if="references.length" :references="references" />
    
    <!-- 输入区域 -->
    <div class="input-area">
      <el-input v-model="input" 
                placeholder="输入问题..."
                @keyup.enter="sendMessage" />
      <el-button v-if="streaming" type="danger" @click="stop">
        停止
      </el-button>
      <el-button v-else type="primary" @click="sendMessage">
        发送
      </el-button>
    </div>
  </div>
</template>
```

#### MessageList (消息列表)

```vue
<template>
  <div class="message-list">
    <div v-for="(msg, idx) in messages" :key="idx" 
         :class="['message', msg.role]">
      <div class="avatar">
        <el-icon v-if="msg.role === 'user'"><User /></el-icon>
        <el-icon v-else><Cpu /></el-icon>
      </div>
      <div class="content">
        <div class="text" v-html="renderMarkdown(msg.content)" />
        <div v-if="msg.references" class="references">
          <el-tag size="small">📎 {{ msg.references.length }} 条引用</el-tag>
          <el-button link @click="showRefs = !showRefs">展开</el-button>
        </div>
      </div>
    </div>
  </div>
</template>
```

### 6.2 组件规范

| 组件 | 用途 | 属性 |
|------|------|------|
| KBSelector | 知识库选择器 | v-model, options |
| MessageList | 消息列表 | messages, streaming |
| ReferencePanel | 引用面板 | references |
| DocUpload | 文档上传 | kb-id, on-success |
| DocTable | 文档表格 | documents, loading |
| PDFPreview | PDF 预览 | url, visible |

---

## 7. 交互设计

### 7.1 对话流程

```
用户输入问题
     │
     ▼
┌─────────────┐
│ 点击发送    │
└─────────────┘
     │
     ▼
┌─────────────┐
│ 添加用户消息 │
└─────────────┘
     │
     ▼
┌─────────────┐
│ 发送 SSE 请求 │
└─────────────┘
     │
     ▼
┌─────────────┐
│ 流式接收响应 │
│ (打字机效果) │
└─────────────┘
     │
     ▼
┌─────────────┐
│ 显示引用来源 │
└─────────────┘
```

### 7.2 上传流程

```
选择文件
     │
     ▼
┌─────────────┐
│ 格式校验    │
└─────────────┘
     │
     ▼
┌─────────────┐
│ 上传文件    │
└─────────────┘
     │
     ▼
┌─────────────┐
│ 后台处理    │
│ (解析 + 分块) │
└─────────────┘
     │
     ▼
┌─────────────┐
│ 向量化入库  │
└─────────────┘
     │
     ▼
┌─────────────┐
│ 更新状态    │
└─────────────┘
```

### 7.3 状态反馈

| 状态 | 反馈方式 |
|------|----------|
| 加载中 | Loading Spinner |
| 成功 | Success Message (2s) |
| 失败 | Error Message (3s) |
| 确认 | Confirm Dialog |

---

## 8. 响应式设计

### 8.1 断点定义

```css
/* 手机 */
@media (max-width: 768px) {
  .chat-view { padding: 10px; }
  .message-list { max-height: calc(100vh - 200px); }
}

/* 平板 */
@media (min-width: 769px) and (max-width: 1200px) {
  .chat-view { max-width: 900px; margin: 0 auto; }
}

/* 桌面 */
@media (min-width: 1201px) {
  .chat-view { max-width: 1200px; margin: 0 auto; }
}
```

---

## 9. 动画设计

### 9.1 过渡动画

```css
/* 消息淡入 */
.message-enter-active {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 按钮悬停 */
.el-button:hover {
  transform: translateY(-1px);
  transition: transform 0.2s;
}
```

### 9.2 打字机效果

```css
.typing-cursor::after {
  content: '|';
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
```

---

## 10. 性能优化

### 10.1 代码分割

```typescript
// 路由懒加载
{
  path: '/kb/:id',
  component: () => import('@/views/KnowledgeBase/DetailView.vue')
}
```

### 10.2 虚拟滚动

```vue
<!-- 消息列表虚拟滚动 -->
<RecycleScroller
  :items="messages"
  :item-size="100"
  key-field="id"
/>
```

### 10.3 防抖节流

```typescript
// 输入框防抖
const debouncedSearch = debounce((query: string) => {
  // 搜索逻辑
}, 300)
```

---

## 11. 可访问性

### 11.1 ARIA 标签

```vue
<button aria-label="发送消息">
  <el-icon><Send /></el-icon>
</button>
```

### 11.2 键盘导航

- Tab 键切换焦点
- Enter 键发送消息
- Esc 键关闭弹窗

---

## 12. 构建配置

### 12.1 Vite 配置

```typescript
// vite.config.ts
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://172.16.25.187:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'element-plus': ['element-plus'],
          'vue': ['vue', 'vue-router', 'pinia']
        }
      }
    }
  }
})
```

---

## 13. 开发规范

### 13.1 代码风格

```typescript
// 使用 Composition API
<script setup lang="ts">
import { ref, computed } from 'vue'

// 类型定义
interface Props {
  messages: Message[]
}

// Props
const props = defineProps<Props>()

// 状态
const loading = ref(false)

// 计算属性
const count = computed(() => messages.length)

// 方法
function sendMessage() { ... }
</script>
```

### 13.2 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 组件 | PascalCase | ChatView.vue |
| 文件 | kebab-case | use-chat-stream.ts |
| 变量 | camelCase | const loading = ref() |
| 常量 | UPPER_SNAKE | const API_BASE = '...' |
| 类型 | PascalCase | interface Message |

---

**审批状态**: 已批准  
**更新日期**: 2026-04-09