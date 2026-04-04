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
  const defs = [
    ['current_world_state', 'Current world state'],
    ['scenario_outcome', 'Scenario outcome'],
    ['last_intervention', 'Last intervention'],
    ['latest_comparison_run', 'Latest comparison run'],
    ['resident_focus', 'Resident focus'],
    ['household_focus', 'Household focus'],
  ]
  return defs.map(([key, label]) => {
    const data = props.artifacts?.[key] || {}
    let meta = ''
    if (key === 'current_world_state') meta = data.world_time || ''
    if (key === 'scenario_outcome') meta = data.scenario_name ? `${data.scenario_name} · ${data.world_time || ''}` : 'none'
    if (key === 'last_intervention') meta = data.intervention_id ? `${data.intervention_id} · ${data.applied_at || ''}` : 'none'
    if (key === 'latest_comparison_run') meta = data.generated_at ? `${data.baseline_label || 'baseline'} → ${data.current_label || 'current'}` : 'none'
    if (key === 'resident_focus') meta = data.label ? `${data.label} (${data.resident_id || 'resident'})` : 'none'
    if (key === 'household_focus') meta = data.household_id ? `${data.household_id} · ${data.label || ''}` : 'none'
    return { key, label, meta, data }
  })
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
