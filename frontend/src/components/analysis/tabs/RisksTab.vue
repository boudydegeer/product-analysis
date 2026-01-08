<script setup lang="ts">
import type { AnalysisRisks } from '@/types/analysis'

defineProps<{
  risks: AnalysisRisks
}>()

const getSeverityColor = (severity: string) => {
  const colors: Record<string, string> = {
    critical: 'text-red-600 border-red-600',
    high: 'text-orange-600 border-orange-600',
    medium: 'text-yellow-600 border-yellow-600',
    low: 'text-blue-600 border-blue-600',
  }
  return colors[severity.toLowerCase()] || 'text-gray-600 border-gray-600'
}
</script>

<template>
  <div class="space-y-6">
    <!-- Technical Risks Section -->
    <div v-if="risks.technical_risks && risks.technical_risks.length > 0" class="space-y-2">
      <h3 class="text-lg font-semibold">Technical Risks</h3>
      <div class="space-y-3">
        <div v-for="(risk, index) in risks.technical_risks" :key="index" class="border rounded-lg p-4">
          <div class="flex items-start gap-3">
            <span :class="['px-2 py-1 text-xs font-medium rounded-md border', getSeverityColor(risk.severity)]">
              {{ risk.severity }}
            </span>
            <div class="flex-1">
              <p class="text-base mb-2">{{ risk.description }}</p>
              <p v-if="risk.impact" class="text-sm text-muted-foreground">Impact: {{ risk.impact }}</p>
              <p v-if="risk.recommendation" class="text-sm text-muted-foreground mt-1">
                Recommendation: {{ risk.recommendation }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Security Concerns Section -->
    <div v-if="risks.security_concerns && risks.security_concerns.length > 0" class="space-y-2">
      <h3 class="text-lg font-semibold">Security Concerns</h3>
      <div class="space-y-3">
        <div v-for="(concern, index) in risks.security_concerns" :key="index" class="border rounded-lg p-4">
          <div class="flex items-start gap-3">
            <span :class="['px-2 py-1 text-xs font-medium rounded-md border', getSeverityColor(concern.severity)]">
              {{ concern.severity }}
            </span>
            <div class="flex-1">
              <p class="text-base mb-2">{{ concern.description }}</p>
              <div v-if="concern.cwe" class="text-sm text-muted-foreground">CWE: {{ concern.cwe }}</div>
              <p v-if="concern.impact" class="text-sm text-muted-foreground">Impact: {{ concern.impact }}</p>
              <p v-if="concern.recommendation" class="text-sm text-muted-foreground mt-1">
                Recommendation: {{ concern.recommendation }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Scalability Issues Section -->
    <div v-if="risks.scalability_issues && risks.scalability_issues.length > 0" class="space-y-2">
      <h3 class="text-lg font-semibold">Scalability Issues</h3>
      <div class="space-y-3">
        <div v-for="(issue, index) in risks.scalability_issues" :key="index" class="border rounded-lg p-4">
          <div class="flex items-start gap-3">
            <span :class="['px-2 py-1 text-xs font-medium rounded-md border', getSeverityColor(issue.severity)]">
              {{ issue.severity }}
            </span>
            <div class="flex-1">
              <p class="text-base mb-2">{{ issue.description }}</p>
              <p v-if="issue.impact" class="text-sm text-muted-foreground">Impact: {{ issue.impact }}</p>
              <p v-if="issue.recommendation" class="text-sm text-muted-foreground mt-1">
                Recommendation: {{ issue.recommendation }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Mitigation Strategies Section -->
    <div v-if="risks.mitigation_strategies && risks.mitigation_strategies.length > 0" class="space-y-2">
      <h3 class="text-lg font-semibold">Mitigation Strategies</h3>
      <ul class="list-disc list-inside space-y-2">
        <li v-for="(strategy, index) in risks.mitigation_strategies" :key="index" class="text-muted-foreground">
          {{ strategy }}
        </li>
      </ul>
    </div>
  </div>
</template>
