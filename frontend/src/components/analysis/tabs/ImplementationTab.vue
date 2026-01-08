<script setup lang="ts">
import type { AnalysisImplementation } from '@/types/analysis'
import MarkdownRenderer from '@/components/shared/MarkdownRenderer.vue'

defineProps<{
  implementation: AnalysisImplementation
}>()
</script>

<template>
  <div class="space-y-6">
    <!-- Architecture Section -->
    <div v-if="implementation.architecture && Object.keys(implementation.architecture).length > 0" class="space-y-2">
      <h3 class="text-lg font-semibold">Architecture</h3>
      <div class="space-y-3">
        <div v-if="implementation.architecture.pattern" class="space-y-1">
          <div class="text-sm text-muted-foreground">Pattern</div>
          <MarkdownRenderer :content="implementation.architecture.pattern" />
        </div>
        <div v-if="implementation.architecture.components && implementation.architecture.components.length > 0" class="space-y-1">
          <div class="text-sm text-muted-foreground">Components</div>
          <ul class="list-disc list-inside space-y-1">
            <li v-for="(component, index) in implementation.architecture.components" :key="index">
              {{ component }}
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Technical Details Section -->
    <div v-if="implementation.technical_details && implementation.technical_details.length > 0" class="space-y-2">
      <h3 class="text-lg font-semibold">Technical Details</h3>
      <div class="space-y-4">
        <div v-for="(detail, index) in implementation.technical_details" :key="index" class="border rounded-lg p-4">
          <div class="font-medium mb-2">{{ detail.category }}</div>
          <div class="mb-2">
            <MarkdownRenderer :content="detail.description" />
          </div>
          <div v-if="detail.code_locations && detail.code_locations.length > 0" class="text-sm">
            <span class="text-muted-foreground">Code locations:</span>
            <ul class="list-disc list-inside mt-1">
              <li v-for="(location, idx) in detail.code_locations" :key="idx" class="font-mono text-xs">
                {{ location }}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Data Flow Section -->
    <div v-if="implementation.data_flow && Object.keys(implementation.data_flow).length > 0" class="space-y-2">
      <h3 class="text-lg font-semibold">Data Flow</h3>
      <div class="space-y-3">
        <MarkdownRenderer v-if="implementation.data_flow.description" :content="implementation.data_flow.description" />
        <div v-if="implementation.data_flow.steps && implementation.data_flow.steps.length > 0">
          <ol class="list-decimal list-inside space-y-2">
            <li v-for="(step, index) in implementation.data_flow.steps" :key="index" class="text-muted-foreground">
              {{ step }}
            </li>
          </ol>
        </div>
      </div>
    </div>
  </div>
</template>
