<template>
  <div class="container mx-auto p-6 h-full overflow-auto">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold">Admin Panel</h1>
      <p class="text-muted-foreground mt-1">Manage agents, tools, and configurations</p>
    </div>

    <!-- Tabs -->
    <Tabs v-model="activeTab" class="w-full">
      <TabsList class="grid w-full grid-cols-3 mb-6">
        <TabsTrigger value="agents">
          <Bot class="mr-2 h-4 w-4" />
          Agents
        </TabsTrigger>
        <TabsTrigger value="tools">
          <Wrench class="mr-2 h-4 w-4" />
          Tools
        </TabsTrigger>
        <TabsTrigger value="assignments">
          <Link2 class="mr-2 h-4 w-4" />
          Assignments
        </TabsTrigger>
      </TabsList>

      <!-- Agents Tab -->
      <TabsContent value="agents">
        <AgentsTable
          :agents="store.agents"
          :loading="store.loading"
          :error="store.error"
          @create="handleCreateAgent"
          @edit="handleEditAgent"
          @delete="handleDeleteAgent"
          @toggle-enabled="handleToggleAgentEnabled"
          @retry="store.fetchAgents"
        />
      </TabsContent>

      <!-- Tools Tab -->
      <TabsContent value="tools">
        <ToolsTable
          :tools="store.tools"
          :loading="store.loading"
          :error="store.error"
          @create="handleCreateTool"
          @edit="handleEditTool"
          @delete="handleDeleteTool"
          @toggle-enabled="handleToggleToolEnabled"
          @retry="store.fetchTools"
        />
      </TabsContent>

      <!-- Assignments Tab -->
      <TabsContent value="assignments">
        <ToolAssignments
          ref="assignmentsRef"
          :agents="store.agents"
          :tools="store.tools"
          :loading="store.loading"
          @assign="handleAssignTool"
          @remove="handleRemoveTool"
          @load-assignments="handleLoadAssignments"
        />
      </TabsContent>
    </Tabs>

    <!-- Agent Form Dialog -->
    <AgentForm
      :open="showAgentForm"
      :agent="selectedAgent"
      :submitting="formSubmitting"
      @update:open="showAgentForm = $event"
      @submit="handleAgentSubmit"
    />

    <!-- Tool Form Dialog -->
    <ToolForm
      :open="showToolForm"
      :tool="selectedTool"
      :submitting="formSubmitting"
      @update:open="showToolForm = $event"
      @submit="handleToolSubmit"
    />

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Bot, Wrench, Link2 } from 'lucide-vue-next'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import AgentsTable from '@/components/admin/AgentsTable.vue'
import AgentForm from '@/components/admin/AgentForm.vue'
import ToolsTable from '@/components/admin/ToolsTable.vue'
import ToolForm from '@/components/admin/ToolForm.vue'
import ToolAssignments from '@/components/admin/ToolAssignments.vue'
import { useAdminStore } from '@/stores/admin'
import type { AgentTypeResponse, ToolResponse, AgentTypeCreate, AgentTypeUpdate, ToolCreate, ToolUpdate, AgentToolAssignment } from '@/api/admin'

const store = useAdminStore()

const activeTab = ref('agents')
const showAgentForm = ref(false)
const showToolForm = ref(false)
const formSubmitting = ref(false)
const selectedAgent = ref<AgentTypeResponse | null>(null)
const selectedTool = ref<ToolResponse | null>(null)
const assignmentsRef = ref<InstanceType<typeof ToolAssignments>>()

onMounted(async () => {
  try {
    await Promise.all([store.fetchAgents(), store.fetchTools()])
  } catch (error) {
    console.error('Failed to load admin data:', error)
  }
})

// Agent Handlers
function handleCreateAgent() {
  selectedAgent.value = null
  showAgentForm.value = true
}

function handleEditAgent(agentId: number) {
  selectedAgent.value = store.agents.find((a) => a.id === agentId) || null
  showAgentForm.value = true
}

async function handleDeleteAgent(agentId: number) {
  const agent = store.agents.find((a) => a.id === agentId)
  if (!agent) return

  if (window.confirm(`Are you sure you want to delete the agent "${agent.display_name}"? This action cannot be undone.`)) {
    try {
      await store.deleteAgent(agentId)
      alert('Agent deleted successfully')
    } catch (error) {
      alert('Failed to delete agent: ' + (error instanceof Error ? error.message : 'Unknown error'))
    }
  }
}

async function handleToggleAgentEnabled(agentId: number) {
  try {
    await store.toggleAgentEnabled(agentId)
    // Success - no notification needed
  } catch (error) {
    alert('Failed to update agent: ' + (error instanceof Error ? error.message : 'Unknown error'))
  }
}

async function handleAgentSubmit(data: AgentTypeCreate | AgentTypeUpdate) {
  formSubmitting.value = true
  try {
    if (selectedAgent.value) {
      // Update
      await store.updateAgent(selectedAgent.value.id, data as AgentTypeUpdate)
      alert('Agent updated successfully')
    } else {
      // Create
      await store.createAgent(data as AgentTypeCreate)
      alert('Agent created successfully')
    }
    showAgentForm.value = false
  } catch (error) {
    alert('Operation failed: ' + (error instanceof Error ? error.message : 'Unknown error'))
  } finally {
    formSubmitting.value = false
  }
}

// Tool Handlers
function handleCreateTool() {
  selectedTool.value = null
  showToolForm.value = true
}

function handleEditTool(toolId: number) {
  selectedTool.value = store.tools.find((t) => t.id === toolId) || null
  showToolForm.value = true
}

async function handleDeleteTool(toolId: number) {
  const tool = store.tools.find((t) => t.id === toolId)
  if (!tool) return

  if (window.confirm(`Are you sure you want to delete the tool "${tool.name}"? This action cannot be undone.`)) {
    try {
      await store.deleteTool(toolId)
      alert('Tool deleted successfully')
    } catch (error) {
      alert('Failed to delete tool: ' + (error instanceof Error ? error.message : 'Unknown error'))
    }
  }
}

async function handleToggleToolEnabled(toolId: number) {
  try {
    await store.toggleToolEnabled(toolId)
    // Success - no notification needed
  } catch (error) {
    alert('Failed to update tool: ' + (error instanceof Error ? error.message : 'Unknown error'))
  }
}

async function handleToolSubmit(data: ToolCreate | ToolUpdate) {
  formSubmitting.value = true
  try {
    if (selectedTool.value) {
      // Update
      await store.updateTool(selectedTool.value.id, data as ToolUpdate)
      alert('Tool updated successfully')
    } else {
      // Create
      await store.createTool(data as ToolCreate)
      alert('Tool created successfully')
    }
    showToolForm.value = false
  } catch (error) {
    alert('Operation failed: ' + (error instanceof Error ? error.message : 'Unknown error'))
  } finally {
    formSubmitting.value = false
  }
}

// Assignment Handlers
async function handleLoadAssignments(agentId: number) {
  try {
    await store.fetchAgentToolAssignments(agentId)
    const configs = store.getAgentToolConfigs(agentId)
    assignmentsRef.value?.setAssignments(configs)
  } catch (error) {
    alert('Failed to load tool assignments')
  }
}

async function handleAssignTool(agentId: number, toolId: number, config: AgentToolAssignment) {
  try {
    await store.assignToolToAgent(agentId, config)
    alert('Tool assigned successfully')
  } catch (error) {
    alert('Failed to assign tool: ' + (error instanceof Error ? error.message : 'Unknown error'))
  }
}

async function handleRemoveTool(agentId: number, toolId: number) {
  try {
    await store.removeToolFromAgent(agentId, toolId)
    alert('Tool removed successfully')
  } catch (error) {
    alert('Failed to remove tool: ' + (error instanceof Error ? error.message : 'Unknown error'))
  }
}
</script>
