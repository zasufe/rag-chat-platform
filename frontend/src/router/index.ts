import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/chat'
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/ChatView.vue'),
    meta: { title: 'AI 对话' }
  },
  {
    path: '/kb',
    name: 'KnowledgeBase',
    component: () => import('@/views/KnowledgeBase/ListView.vue'),
    meta: { title: '知识库管理' }
  },
  {
    path: '/kb/:id',
    name: 'KnowledgeBaseDetail',
    component: () => import('@/views/KnowledgeBase/DetailView.vue'),
    meta: { title: '知识库详情' }
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router