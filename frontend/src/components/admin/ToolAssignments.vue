<template>
  <div class="space-y-4">
    <!-- Header -->
    <div>
      <h3 class="text-lg font-semibold">Tool Assignments</h3>
      <p class="text-sm text-muted-foreground">Manage which tools are available to each agent</p>
    </div>

    <!-- Agent Selection -->
    <div>
      <Label for="agent">Select Agent</Label>
      <Select v-model="selectedAgentId" @update:model-value="handleAgentChange">
        <SelectTrigger>
          <SelectValue placeholder="Choose an agent" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem v-for="agent in agents" :key="agent.id" :value="String(agent.id)">
            {{ agent.display_name }}
          </SelectItem>
        </SelectContent>
      </Select>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-8">
      <p class="text-muted-foreground">Loading assignments...</p>
    </div>

    <!-- No Agent Selected -->
    <div v-else-if="!selectedAgentId" class="text-center py-12">
      <Settings class="mx-auto h-12 w-12 text-muted-foreground mb-4" />
      <h3 class="text-lg font-semibold mb-2">Select an Agent</h3>
      <p class="text-muted-foreground">
        Choose an agent to manage its tool assignments
      </p>
    </div>

    <!-- Assignments -->
    <div v-else class="space-y-4">
      <!-- Add Tool Button -->
      <div class="flex justify-between items-center">
        <p class="text-sm text-muted-foreground">
          {{ assignedToolIds.size }} of {{ tools.length }} tools assigned
        </p>
        <Button @click="showAddDialog = true" size="sm">
          <Plus class="mr-2 h-4 w-4" />
          Assign Tool
        </Button>
      </div>

      <!-- Assigned Tools -->
      <div v-if="assignedToolIds.size > 0" class="space-y-2">
        <Card
          v-for="toolId in Array.from(assignedToolIds)"
          :key="toolId"
          class="p-4"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <Wrench class="h-5 w-5 text-muted-foreground" />
              <div>
                <p class="font-medium">{{ getToolName(toolId) }}</p>
                <p class="text-sm text-muted-foreground">{{ getToolCategory(toolId) }}</p>
              </div>
            </div>
            <Button
              size="sm"
              variant="ghost"
              @click="handleRemoveTool(toolId)"
              class="text-destructive hover:text-destructive"
            >
              <Trash2 class="h-4 w-4" />
            </Button>
          </div>
        </Card>
      </div>

      <!-- No Assignments -->
      <div v-else class="text-center py-8 border-2 border-dashed rounded-lg">
        <p class="text-muted-foreground">No tools assigned yet</p>
        <Button @click="showAddDialog = true" size="sm" variant="outline" class="mt-4">
          Assign First Tool
        </Button>
      </div>
    </div>

    <!-- Add Tool Dialog -->
    <Dialog :open="showAddDialog" @update:open="showAddDialog = $event">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Assign Tool</DialogTitle>
          <DialogDescription>
            Select a tool to assign to this agent
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-4">
          <div>
            <Label for="tool">Tool</Label>
            <Select v-model="selectedToolId">
              <SelectTrigger>
                <SelectValue placeholder="Choose a tool" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem
                  v-for="tool in availableTools"
                  :key="tool.id"
                  :value="String(tool.id)"
                >
                  {{ tool.name }} ({{ tool.category }})
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="flex items-center space-x-2">
            <Checkbox
              id="enabled_for_agent"
              :checked="assignmentConfig.enabled_for_agent"
              @update:checked="assignmentConfig.enabled_for_agent = $event"
            />
            <Label for="enabled_for_agent" class="font-normal cursor-pointer">
              Enabled for this agent
            </Label>
          </div>

          <div class="flex items-center space-x-2">
            <Checkbox
              id="allow_use"
              :checked="assignmentConfig.allow_use"
              @update:checked="assignmentConfig.allow_use = $event"
            />
            <Label for="allow_use" class="font-normal cursor-pointer">
              Allow usage
            </Label>
          </div>

          <div class="flex items-center space-x-2">
            <Checkbox
              id="requires_approval"
              :checked="assignmentConfig.requires_approval"
              @update:checked="assignmentConfig.requires_approval = $event"
            />
            <Label for="requires_approval" class="font-normal cursor-pointer">
              Requires approval
            </Label>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" @click="showAddDialog = false">Cancel</Button>
          <Button @click="handleAssignTool" :disabled="!selectedToolId">Assign</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Settings, Wrench, Plus, Trash2 } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card.ts'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { AgentTypeResponse, ToolResponse, AgentToolConfigResponse } from '@/api/admin'

const props = defineProps<{
  agents: AgentTypeResponse[]
  tools: ToolResponse[]
  loading: boolean
}>()

const emit = defineEmits<{
  assign: [agentId: number, toolId: number, config: any]
  remove: [agentId: number, toolId: number]
  loadAssignments: [agentId: number]
}>()

const selectedAgentId = ref<string>()
const selectedToolId = ref<string>()
const showAddDialog = ref(false)
const assignmentConfig = ref({
  enabled_for_agent: true,
  allow_use: true,
  requires_approval: false,
})

// This would be loaded from the store
const assignedToolIds = ref<Set<number>>(new Set())

const availableTools = computed(() => {
  return props.tools.filter((tool) => !assignedToolIds.value.has(tool.id))
})

function handleAgentChange(agentId: string) {
  assignedToolIds.value.clear()
  if (agentId) {
    emit('loadAssignments', Number(agentId))
  }
}

function handleAssignTool() {
  if (!selectedAgentId.value || !selectedToolId.value) return

  emit('assign', Number(selectedAgentId.value), Number(selectedToolId.value), {
    tool_id: Number(selectedToolId.value),
    ...assignmentConfig.value,
  })

  assignedToolIds.value.add(Number(selectedToolId.value))
  showAddDialog.value = false
  selectedToolId.value = undefined
  assignmentConfig.value = {
    enabled_for_agent: true,
    allow_use: true,
    requires_approval: false,
  }
}

function handleRemoveTool(toolId: number) {
  if (!selectedAgentId.value) return

  emit('remove', Number(selectedAgentId.value), toolId)
  assignedToolIds.value.delete(toolId)
}

function getToolName(toolId: number): string {
  const tool = props.tools.find((t) => t.id === toolId)
  return tool?.name || 'Unknown Tool'
}

function getToolCategory(toolId: number): string {
  const tool = props.tools.find((t) => t.id === toolId)
  return tool?.category || ''
}

// Expose method to update assignments from parent
defineExpose({
  setAssignments(assignments: AgentToolConfigResponse[]) {
    assignedToolIds.value = new Set(assignments.map((a) => a.tool_id))
  },
})
</script>
