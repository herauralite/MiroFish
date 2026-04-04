<template>
  <div class="panel">
    <h3>Explainability Hooks</h3>
    <div v-for="artifact in artifactCards" :key="artifact.key" class="artifact-card">
      <div class="artifact-title">{{ artifact.label }}</div>
      <p class="line" v-if="artifact.meta">{{ artifact.meta }}</p>
      <p class="line"><strong>What changed:</strong> {{ summarizeChanges(artifact.data.what_changed) }}</p>
      <p class="line"><strong>Why:</strong> {{ (artifact.data.why_changed || [])[0] || '—' }}</p>
      <p class="line"><strong>Top systems:</strong> {{ summarizeSystems(artifact.data.top_system_contributors) }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  artifacts: { type: Object, default: () => ({}) },
})

const artifactCards = computed(() => {
  const currentWorld = props.artifacts?.current_world_state || {}
  const lastIntervention = props.artifacts?.last_intervention || {}
  const latestComparison = props.artifacts?.latest_comparison_run || {}
  return [
    {
      key: 'world',
      label: 'Current world state',
      meta: currentWorld.world_time || '',
      data: currentWorld,
    },
    {
      key: 'intervention',
      label: 'Last intervention',
      meta: lastIntervention.intervention_id ? `${lastIntervention.intervention_id} · ${lastIntervention.applied_at || ''}` : 'none',
      data: lastIntervention,
    },
    {
      key: 'comparison',
      label: 'Latest comparison run',
      meta: latestComparison.generated_at ? `${latestComparison.baseline_label || 'baseline'} → ${latestComparison.current_label || 'current'}` : 'none',
      data: latestComparison,
    },
  ]
})

const summarizeChanges = (changes = {}) => {
  const entries = Object.entries(changes || {}).slice(0, 3)
  if (!entries.length) return '—'
  return entries.map(([key, value]) => `${key}: ${value}`).join(' | ')
}

const summarizeSystems = (systems = []) => {
  if (!systems?.length) return '—'
  return systems.slice(0, 3).map((entry) => {
    if (typeof entry === 'string') return entry
    const label = entry.system || entry.name || 'system'
    const value = entry.score ?? entry.pressure_delta
    return value === undefined ? label : `${label} (${value})`
  }).join(', ')
}
</script>

<style scoped>
.panel{border:1px solid #ddd;padding:10px;background:#fff}
.artifact-card{border:1px solid #efefef;background:#fafafa;padding:8px;margin-top:8px}
.artifact-title{font-weight:700;font-size:12px}
.line{margin:4px 0;font-size:12px}
</style>
