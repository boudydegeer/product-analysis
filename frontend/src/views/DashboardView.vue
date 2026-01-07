<template>
  <div class="space-y-6">
    <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card class="p-6">
        <h3 class="text-sm font-medium text-muted-foreground">Total Features</h3>
        <p class="text-3xl font-bold mt-2">{{ store.features.length }}</p>
      </Card>
      <Card class="p-6">
        <h3 class="text-sm font-medium text-muted-foreground">In Analysis</h3>
        <p class="text-3xl font-bold mt-2">{{ analyzingCount }}</p>
      </Card>
      <Card class="p-6">
        <h3 class="text-sm font-medium text-muted-foreground">Approved</h3>
        <p class="text-3xl font-bold mt-2">{{ approvedCount }}</p>
      </Card>
      <Card class="p-6">
        <h3 class="text-sm font-medium text-muted-foreground">Completed</h3>
        <p class="text-3xl font-bold mt-2">{{ completedCount }}</p>
      </Card>
    </div>

    <Card class="p-6">
      <h2 class="text-xl font-semibold mb-4">Recent Features</h2>
      <div v-if="store.features.length > 0" class="space-y-3">
        <div
          v-for="feature in recentFeatures"
          :key="feature.id"
          class="flex items-center justify-between py-2 border-b last:border-0"
        >
          <div>
            <p class="font-medium">{{ feature.name }}</p>
            <p class="text-sm text-muted-foreground">{{ feature.id }}</p>
          </div>
          <Badge :variant="getStatusVariant(feature.status)">
            {{ feature.status }}
          </Badge>
        </div>
      </div>
      <p v-else class="text-muted-foreground">No features yet</p>
    </Card>

    <div class="flex justify-center">
      <Button @click="$router.push('/features')" size="lg">
        Go to Features
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useFeaturesStore } from '@/stores/features'
import Card from '@/components/ui/card.vue'
import Badge from '@/components/ui/badge.vue'
import Button from '@/components/ui/button.vue'
import type { FeatureStatus } from '@/types/feature'

const store = useFeaturesStore()

onMounted(() => {
  store.fetchFeatures()
})

const analyzingCount = computed(() =>
  store.features.filter((f) => f.status === 'analyzing').length
)

const approvedCount = computed(() =>
  store.features.filter((f) => f.status === 'approved').length
)

const completedCount = computed(() =>
  store.features.filter((f) => f.status === 'completed').length
)

const recentFeatures = computed(() => store.features.slice(0, 5))

function getStatusVariant(status: FeatureStatus): 'default' | 'secondary' | 'destructive' | 'outline' {
  if (status === 'approved' || status === 'completed') return 'default'
  if (status === 'analyzing' || status === 'in_progress') return 'secondary'
  if (status === 'rejected') return 'destructive'
  return 'outline'
}
</script>
