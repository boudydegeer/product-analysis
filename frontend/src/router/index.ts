import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import DashboardLayout from '@/layouts/DashboardLayout.vue'
import DashboardView from '@/views/DashboardView.vue'
import FeaturesView from '@/views/FeaturesView.vue'
import AnalysisView from '@/views/AnalysisView.vue'
import SettingsView from '@/views/SettingsView.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: DashboardLayout,
    children: [
      {
        path: '',
        name: 'dashboard',
        component: DashboardView,
        meta: { title: 'Dashboard' }
      },
      {
        path: 'features',
        name: 'features',
        component: FeaturesView,
        meta: { title: 'Features' }
      },
      {
        path: 'analysis/:id',
        name: 'analysis',
        component: AnalysisView,
        meta: { title: 'Analysis' }
      },
      {
        path: 'settings',
        name: 'settings',
        component: SettingsView,
        meta: { title: 'Settings' }
      },
      {
        path: 'brainstorm',
        name: 'brainstorm-list',
        component: () => import('@/views/BrainstormListView.vue'),
        meta: { title: 'Brainstorming' },
      },
      {
        path: 'brainstorm/:id',
        name: 'brainstorm-detail',
        component: () => import('@/views/BrainstormDetailView.vue'),
        meta: { title: 'Brainstorming Session' },
      },
      {
        path: 'ideas',
        name: 'ideas',
        component: () => import('@/views/IdeasView.vue'),
        meta: { title: 'Ideas' },
      },
      {
        path: 'ideas/:id',
        name: 'idea-detail',
        component: () => import('@/views/IdeaDetailView.vue'),
        meta: { title: 'Idea Details' },
      },
      {
        path: 'admin',
        name: 'admin',
        component: () => import('@/views/AdminView.vue'),
        meta: { title: 'Admin Panel' },
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
