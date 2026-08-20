import { createRouter, createWebHistory } from 'vue-router'

import ChatView from '../views/ChatView.vue'
import DocumentsView from '../views/DocumentsView.vue'
import EvaluationsView from '../views/EvaluationsView.vue'
import SettingsView from '../views/SettingsView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'chat', component: ChatView },
    { path: '/documents', name: 'documents', component: DocumentsView },
    { path: '/evaluations', name: 'evaluations', component: EvaluationsView },
    { path: '/settings', name: 'settings', component: SettingsView },
  ],
})

export default router
