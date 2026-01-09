<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold">Tools</h3>
        <p class="text-sm text-muted-foreground">Manage available tools for agents</p>
      </div>
      <Button @click="$emit('create')">
        <Plus class="mr-2 h-4 w-4" />
        New Tool
      </Button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-8">
      <p class="text-muted-foreground">Loading tools...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-8">
      <p class="text-destructive">{{ error }}</p>
      <Button @click="$emit('retry')" variant="outline" class="mt-4">Retry</Button>
    </div>

    <!-- Empty State -->
    <div v-else-if="tools.length === 0" class="text-center py-12">
      <Wrench class="mx-auto h-12 w-12 text-muted-foreground mb-4" />
      <h3 class="text-lg font-semibold mb-2">No Tools Yet</h3>
      <p class="text-muted-foreground mb-4">
        Create your first tool to extend agent capabilities
      </p>
      <Button @click="$emit('create')">Create Tool</Button>
    </div>

    <!-- Tools by Category -->
    <div v-else class="space-y-6">
      <div v-for="(categoryTools, category) in toolsByCategory" :key="category">
        <h4 class="text-md font-semibold mb-3 capitalize">{{ category }}</h4>
        <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Card
            v-for="tool in categoryTools"
            :key="tool.id"
            class="hover:shadow-md transition-shadow"
          >
            <CardHeader class="pb-3">
              <div class="flex items-start justify-between">
                <div>
                  <CardTitle class="text-md">{{ tool.name }}</CardTitle>
                  <p class="text-xs text-muted-foreground mt-1">{{ tool.tool_type }}</p>
                </div>
                <Badge :variant="tool.enabled ? 'default' : 'secondary'">
                  {{ tool.enabled ? 'Enabled' : 'Disabled' }}
                </Badge>
              </div>
            </CardHeader>

            <CardContent class="space-y-3">
              <p class="text-sm text-muted-foreground line-clamp-2">
                {{ tool.description }}
              </p>

              <div class="flex flex-wrap gap-1">
                <Badge
                  v-for="tag in tool.tags.slice(0, 3)"
                  :key="tag"
                  variant="outline"
                  class="text-xs"
                >
                  {{ tag }}
                </Badge>
                <Badge v-if="tool.tags.length > 3" variant="outline" class="text-xs">
                  +{{ tool.tags.length - 3 }}
                </Badge>
              </div>

              <div class="flex flex-wrap gap-2">
                <Badge v-if="tool.is_dangerous" variant="destructive" class="text-xs">
                  Dangerous
                </Badge>
                <Badge v-if="tool.requires_approval" variant="secondary" class="text-xs">
                  Requires Approval
                </Badge>
                <Badge variant="outline" class="text-xs">v{{ tool.version }}</Badge>
              </div>

              <div class="flex items-center justify-end gap-2 pt-2 border-t">
                <Button
                  size="sm"
                  variant="ghost"
                  @click.stop="$emit('toggleEnabled', tool.id)"
                  :title="tool.enabled ? 'Disable' : 'Enable'"
                >
                  <Power class="h-4 w-4" :class="tool.enabled ? 'text-green-500' : ''" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  @click.stop="$emit('edit', tool.id)"
                  title="Edit"
                >
                  <Pencil class="h-4 w-4" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  @click.stop="$emit('delete', tool.id)"
                  title="Delete"
                  class="text-destructive hover:text-destructive"
                >
                  <Trash2 class="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Wrench, Plus, Power, Pencil, Trash2 } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { ToolResponse } from '@/api/admin'

const props = defineProps<{
  tools: ToolResponse[]
  loading: boolean
  error: string | null
}>()

defineEmits<{
  create: []
  edit: [toolId: number]
  delete: [toolId: number]
  toggleEnabled: [toolId: number]
  retry: []
}>()

const toolsByCategory = computed(() => {
  const grouped: Record<string, ToolResponse[]> = {}
  for (const tool of props.tools) {
    if (!grouped[tool.category]) {
      grouped[tool.category] = []
    }
    grouped[tool.category].push(tool)
  }
  return grouped
})
</script>
