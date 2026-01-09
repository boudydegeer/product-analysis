<script setup lang="ts">
import { SidebarProvider, SidebarInset, SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import AppSidebar from '@/components/dashboard/AppSidebar.vue'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const breadcrumbs = computed(() => {
  const path = route.path
  const parts = path.split('/').filter(Boolean)

  if (parts.length === 0) {
    return [{ name: 'Dashboard', path: '/' }]
  }

  return parts.map((part, index) => {
    const path = '/' + parts.slice(0, index + 1).join('/')
    const name = part.charAt(0).toUpperCase() + part.slice(1)
    return { name, path }
  })
})
</script>

<template>
  <SidebarProvider class="h-screen">
    <AppSidebar />
    <SidebarInset class="flex flex-col h-screen overflow-hidden">
      <header class="flex h-16 shrink-0 items-center gap-2 border-b bg-background transition-[width,height] ease-linear group-has-[[data-collapsible=icon]]/sidebar-wrapper:h-12">
        <div class="flex items-center gap-2 px-4">
          <SidebarTrigger class="-ml-1" />
          <Separator orientation="vertical" class="mr-2 h-4" />
          <Breadcrumb>
            <BreadcrumbList>
              <template v-for="(crumb, index) in breadcrumbs" :key="crumb.path">
                <BreadcrumbItem v-if="index < breadcrumbs.length - 1">
                  <BreadcrumbLink as-child>
                    <router-link :to="crumb.path">{{ crumb.name }}</router-link>
                  </BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbItem v-else>
                  <BreadcrumbPage>{{ crumb.name }}</BreadcrumbPage>
                </BreadcrumbItem>
                <BreadcrumbSeparator v-if="index < breadcrumbs.length - 1" />
              </template>
            </BreadcrumbList>
          </Breadcrumb>
        </div>
      </header>
      <div class="flex-1 min-h-0 overflow-hidden">
        <router-view class="h-full" />
      </div>
    </SidebarInset>
  </SidebarProvider>
</template>
