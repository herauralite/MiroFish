<template>
  <div class="panel">
    <div class="head">
      <h3>Scenario Outcome</h3>
      <span class="badge" :class="`badge-${outcome.condition_direction || 'flat'}`">
        {{ outcome.condition_direction || 'flat' }}
      </span>
    </div>
    <p class="meta">{{ outcome.scenario_name || 'default-baseline' }} · {{ outcome.world_time || '—' }}</p>
    <p class="line"><strong>Overall:</strong> {{ (outcome.why_changed || [])[0] || 'No major run-level shift yet.' }}</p>
    <p class="line"><strong>District shifts:</strong> {{ districtLine }}</p>
    <p class="line"><strong>Top systems:</strong> {{ systemsLine }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  outcome: { type: Object, default: () => ({}) },
})

const districtLine = computed(() => {
  const rows = props.outcome?.top_shifted_districts || []
  if (!rows.length) return '—'
  return rows.slice(0, 3).map((row) => `${row.name || row.district_id} (${row.shift_score})`).join(', ')
})

const systemsLine = computed(() => {
  const rows = props.outcome?.top_system_contributors || []
  if (!rows.length) return '—'
  return rows.slice(0, 3).map((row) => `${row.system} (${row.score})`).join(', ')
})
</script>

<style scoped>
.panel{border:1px solid #ddd;padding:10px;background:#fff}
.head{display:flex;justify-content:space-between;align-items:center}
h3{margin:0;font-size:14px}
.meta{margin:4px 0 8px 0;font-size:11px;color:#666}
.line{margin:4px 0;font-size:12px}
.badge{font-size:11px;padding:2px 6px;border-radius:10px;color:#fff;text-transform:capitalize}
.badge-improved{background:#1c8c4d}
.badge-worsened{background:#b73d3d}
.badge-mixed{background:#8b6f1e}
.badge-flat{background:#555}
</style>
