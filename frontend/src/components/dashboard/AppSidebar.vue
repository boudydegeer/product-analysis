<script setup lang="ts">
import {
  BookOpen,
  Bot,
  BarChart3,
  Frame,
  LayoutDashboard,
  Lightbulb,
  Map,
  MessageSquare,
  Package,
  PieChart,
  Settings,
  Settings2,
  SquareTerminal,
} from 'lucide-vue-next'

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from '@/components/ui/sidebar'
import NavMain from './NavMain.vue'
import NavProjects from './NavProjects.vue'
import NavUser from './NavUser.vue'
import TeamSwitcher from './TeamSwitcher.vue'

// This is sample data.
const data = {
  user: {
    name: 'Product Team',
    email: 'team@example.com',
    avatar: '/avatars/shadcn.jpg',
  },
  navMain: [
    {
      title: 'Dashboard',
      url: '/',
      icon: LayoutDashboard,
      isActive: true,
    },
    {
      title: 'Features',
      url: '/features',
      icon: Package,
      items: [
        {
          title: 'All Features',
          url: '/features',
        },
        {
          title: 'Add Feature',
          url: '/features?add=true',
        },
      ],
    },
    {
      title: 'Analysis',
      url: '/analysis',
      icon: BarChart3,
      items: [
        {
          title: 'View Reports',
          url: '/analysis',
        },
        {
          title: 'Export Data',
          url: '/analysis/export',
        },
      ],
    },
    {
      title: 'Ideas',
      url: '/ideas',
      icon: Lightbulb,
    },
    {
      title: 'Brainstorming',
      url: '/brainstorm',
      icon: MessageSquare,
    },
    {
      title: 'Settings',
      url: '/settings',
      icon: Settings,
    },
    {
      title: 'Admin',
      url: '/admin',
      icon: Settings2,
    },
  ],
  projects: [
    {
      name: 'Design Engineering',
      url: '#',
      icon: Frame,
    },
    {
      name: 'Sales & Marketing',
      url: '#',
      icon: PieChart,
    },
    {
      name: 'Travel',
      url: '#',
      icon: Map,
    },
  ],
}
</script>

<template>
  <Sidebar collapsible="icon">
    <SidebarHeader>
      <TeamSwitcher />
    </SidebarHeader>
    <SidebarContent>
      <NavMain :items="data.navMain" />
      <NavProjects :projects="data.projects" />
    </SidebarContent>
    <SidebarFooter>
      <NavUser :user="data.user" />
    </SidebarFooter>
    <SidebarRail />
  </Sidebar>
</template>
