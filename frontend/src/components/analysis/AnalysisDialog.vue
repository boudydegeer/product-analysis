<script setup lang="ts">
import { watch, computed } from 'vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useAnalysisStore } from '@/stores/analysis'
import OverviewTab from './tabs/OverviewTab.vue'
import ImplementationTab from './tabs/ImplementationTab.vue'
import RisksTab from './tabs/RisksTab.vue'
import RecommendationsTab from './tabs/RecommendationsTab.vue'
import LoadingState from './states/LoadingState.vue'
import NoAnalysisState from './states/NoAnalysisState.vue'
import FailedState from './states/FailedState.vue'
import AnalyzingState from './states/AnalyzingState.vue'

interface Props {
  open: boolean
  featureId: string
  featureName: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:open': [value: boolean]
}>()

const analysisStore = useAnalysisStore()

// Fetch analysis when dialog opens
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen && props.featureId) {
      analysisStore.fetchAnalysis(props.featureId)
    } else if (!isOpen) {
      analysisStore.clearAnalysis()
    }
  },
  { immediate: true }
)

const isCompleted = computed(() => {
  return analysisStore.currentAnalysis?.status === 'completed'
})

const formattedDate = computed(() => {
  if (!isCompleted.value || !analysisStore.currentAnalysis) return ''
  const analyzedAt = (analysisStore.currentAnalysis as any).analyzed_at
  if (!analyzedAt) return ''
  return new Date(analyzedAt).toLocaleString()
})

function handleRequestAnalysis() {
  // Emit event to parent to trigger analysis
  emit('update:open', false)
  // Could also call API directly here
}

function handleRetry() {
  analysisStore.fetchAnalysis(props.featureId)
}
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="max-w-5xl max-h-[90vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle>{{ featureName }}</DialogTitle>
        <DialogDescription v-if="formattedDate">
          Analyzed {{ formattedDate }}
        </DialogDescription>
      </DialogHeader>

      <!-- Loading State -->
      <LoadingState v-if="analysisStore.loading" />

      <!-- Error State -->
      <div v-else-if="analysisStore.error" class="mt-6">
        <FailedState :message="analysisStore.error" @retry="handleRetry" />
      </div>

      <!-- No Analysis State -->
      <div
        v-else-if="analysisStore.currentAnalysis?.status === 'no_analysis'"
        class="mt-6"
      >
        <NoAnalysisState @request-analysis="handleRequestAnalysis" />
      </div>

      <!-- Analyzing State -->
      <div
        v-else-if="analysisStore.currentAnalysis?.status === 'analyzing'"
        class="mt-6"
      >
        <AnalyzingState
          :started-at="(analysisStore.currentAnalysis as any).started_at"
        />
      </div>

      <!-- Failed State -->
      <div
        v-else-if="analysisStore.currentAnalysis?.status === 'failed'"
        class="mt-6"
      >
        <FailedState
          :message="(analysisStore.currentAnalysis as any).message"
          @retry="handleRetry"
        />
      </div>

      <!-- Success State - Show Tabs -->
      <Tabs v-else-if="isCompleted" default-value="overview" class="mt-6">
        <TabsList class="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="implementation">Implementation</TabsTrigger>
          <TabsTrigger value="risks">Risks & Warnings</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" class="mt-6">
          <OverviewTab :overview="(analysisStore.currentAnalysis as any).overview" />
        </TabsContent>

        <TabsContent value="implementation" class="mt-6">
          <ImplementationTab
            :implementation="(analysisStore.currentAnalysis as any).implementation"
          />
        </TabsContent>

        <TabsContent value="risks" class="mt-6">
          <RisksTab :risks="(analysisStore.currentAnalysis as any).risks" />
        </TabsContent>

        <TabsContent value="recommendations" class="mt-6">
          <RecommendationsTab
            :recommendations="(analysisStore.currentAnalysis as any).recommendations"
          />
        </TabsContent>
      </Tabs>
    </DialogContent>
  </Dialog>
</template>
