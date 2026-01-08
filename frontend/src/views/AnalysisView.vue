<template>
  <div class="space-y-6">
    <!-- Header with back button -->
    <div class="flex items-center gap-4">
      <Button variant="ghost" size="sm" @click="router.back()">
        <ChevronLeft class="h-4 w-4 mr-2" />
        Back
      </Button>
      <div class="flex-1">
        <h1 class="text-2xl font-semibold">{{ featureName || 'Feature Analysis' }}</h1>
        <p class="text-sm text-muted-foreground">Feature ID: {{ featureId }}</p>
      </div>
    </div>

    <!-- Analysis Content -->
    <Card class="p-6">
      <LoadingState v-if="analysisStore.loading" />
      <AnalyzingState v-else-if="analysisStore.currentAnalysis?.status === 'analyzing'" />
      <FailedState v-else-if="analysisStore.currentAnalysis?.status === 'failed'" />
      <NoAnalysisState v-else-if="!analysisStore.currentAnalysis" />

      <div v-else-if="isCompleted && analysisDetail">
        <Tabs default-value="overview" class="w-full">
          <TabsList class="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="implementation">Implementation</TabsTrigger>
            <TabsTrigger value="risks">Risks</TabsTrigger>
            <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <OverviewTab :overview="analysisDetail.overview" />
          </TabsContent>

          <TabsContent value="implementation">
            <ImplementationTab :implementation="analysisDetail.implementation" />
          </TabsContent>

          <TabsContent value="risks">
            <RisksTab :risks="analysisDetail.risks" />
          </TabsContent>

          <TabsContent value="recommendations">
            <RecommendationsTab :recommendations="analysisDetail.recommendations" />
          </TabsContent>
        </Tabs>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useFeaturesStore } from '@/stores/features'
import { useAnalysisStore } from '@/stores/analysis'
import type { AnalysisDetail } from '@/types/analysis'
import Card from '@/components/ui/card.vue'
import Button from '@/components/ui/button.vue'
import { ChevronLeft } from 'lucide-vue-next'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import OverviewTab from '@/components/analysis/tabs/OverviewTab.vue'
import ImplementationTab from '@/components/analysis/tabs/ImplementationTab.vue'
import RisksTab from '@/components/analysis/tabs/RisksTab.vue'
import RecommendationsTab from '@/components/analysis/tabs/RecommendationsTab.vue'
import LoadingState from '@/components/analysis/states/LoadingState.vue'
import NoAnalysisState from '@/components/analysis/states/NoAnalysisState.vue'
import FailedState from '@/components/analysis/states/FailedState.vue'
import AnalyzingState from '@/components/analysis/states/AnalyzingState.vue'

const route = useRoute()
const router = useRouter()
const featuresStore = useFeaturesStore()
const analysisStore = useAnalysisStore()

const featureId = computed(() => route.params.id as string)

const featureName = computed(() => {
  const feature = featuresStore.features.find(f => f.id === featureId.value)
  return feature?.name || ''
})

const isCompleted = computed(() => {
  return analysisStore.currentAnalysis?.status === 'completed'
})

const analysisDetail = computed(() => {
  if (analysisStore.currentAnalysis?.status === 'completed') {
    return analysisStore.currentAnalysis as AnalysisDetail
  }
  return null
})

// Fetch analysis when component mounts or featureId changes
watch(
  featureId,
  (id) => {
    if (id) {
      analysisStore.fetchAnalysis(id)
    }
  },
  { immediate: true }
)

onMounted(() => {
  // Ensure features are loaded to get the feature name
  if (featuresStore.features.length === 0) {
    featuresStore.fetchFeatures()
  }
})
</script>
