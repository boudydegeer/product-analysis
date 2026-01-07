<template>
  <div class="flex h-screen bg-background">
    <!-- Sidebar -->
    <aside
      :class="cn(
        'border-r bg-background transition-all duration-300',
        isCollapsed ? 'w-16' : 'w-64'
      )"
    >
      <div class="flex h-full flex-col">
        <!-- Header -->
        <div class="flex h-16 items-center border-b px-4">
          <button
            @click="toggleSidebar"
            class="rounded-lg p-2 hover:bg-accent"
          >
            <Menu class="h-5 w-5" />
          </button>
          <h1 v-if="!isCollapsed" class="ml-3 text-lg font-semibold">
            Product Analysis
          </h1>
        </div>

        <!-- Navigation -->
        <nav class="flex-1 space-y-1 p-2">
          <router-link
            v-for="item in navigation"
            :key="item.name"
            :to="item.path"
            v-slot="{ isActive }"
            custom
          >
            <a
              :href="item.path"
              @click.prevent="$router.push(item.path)"
              :class="cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )"
            >
              <component :is="item.icon" class="h-5 w-5 flex-shrink-0" />
              <span v-if="!isCollapsed">{{ item.name }}</span>
            </a>
          </router-link>
        </nav>

        <!-- User Profile Section -->
        <div class="border-t p-4">
          <div :class="cn('flex items-center gap-3', isCollapsed && 'justify-center')">
            <div class="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground">
              <User class="h-4 w-4" />
            </div>
            <div v-if="!isCollapsed" class="flex-1 overflow-hidden">
              <p class="text-sm font-medium truncate">User</p>
              <p class="text-xs text-muted-foreground truncate">user@example.com</p>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <div class="flex flex-1 flex-col overflow-hidden">
      <!-- Top Bar -->
      <header class="flex h-16 items-center border-b bg-background px-6">
        <h2 class="text-2xl font-bold">{{ currentPageTitle }}</h2>
      </header>

      <!-- Content Area -->
      <main class="flex-1 overflow-y-auto p-6">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Menu, LayoutDashboard, Package, BarChart3, Settings, User } from 'lucide-vue-next'
import { cn } from '@/lib/utils'

const route = useRoute()
const isCollapsed = ref(false)

const navigation = [
  {
    name: 'Dashboard',
    path: '/',
    icon: LayoutDashboard,
  },
  {
    name: 'Features',
    path: '/features',
    icon: Package,
  },
  {
    name: 'Analysis',
    path: '/analysis',
    icon: BarChart3,
  },
  {
    name: 'Settings',
    path: '/settings',
    icon: Settings,
  },
]

const currentPageTitle = computed(() => {
  return route.meta.title as string || 'Dashboard'
})

function toggleSidebar() {
  isCollapsed.value = !isCollapsed.value
}
</script>
