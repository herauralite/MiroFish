<template>
  <div class="panel">
    <h3>Intervention History</h3>
    <p v-if="!history.length" class="hint">No interventions applied yet.</p>
    <ul v-else class="history-list">
      <li v-for="entry in recentHistory" :key="entry.intervention_id">
        <div class="line"><strong>{{ entry.intervention_id }}</strong> · {{ entry.applied_at }}</div>
        <div class="line">changes: {{ entry.change_count }} | notes: {{ entry.notes || '—' }}</div>
        <div class="line">
          Δ pressure: {{ entry.effects?.delta_summary?.household_pressure_index ?? 0 }} |
          Δ service: {{ entry.effects?.delta_summary?.service_access_score ?? 0 }} |
          Δ stressed districts: {{ entry.effects?.delta_summary?.stressed_districts ?? 0 }}
        </div>
      </li>
    </ul>

    <h4>Scenario Snapshots</h4>
    <p class="hint">Capture baseline, apply intervention, then load snapshots for inspect/compare.</p>
    <ul class="history-list" v-if="snapshots.length">
      <li v-for="snapshot in snapshots" :key="snapshot.snapshot_id" class="snapshot-item">
        <div class="line"><strong>{{ snapshot.snapshot_name }}</strong> ({{ snapshot.label }})</div>
        <div class="line">{{ snapshot.captured_at }} · sim-time {{ snapshot.world_time }}</div>
        <button @click="$emit('load-snapshot', snapshot.snapshot_id)">Load</button>
        <button @click="$emit('compare-to-snapshot', snapshot.snapshot_id)">Compare to baseline</button>
      </li>
    </ul>
    <p v-else class="hint">No scenario snapshots yet.</p>

    <div v-if="comparisonReport?.aftermath_hooks?.length" class="comparison-hooks">
      <h4>Comparison aftermath hooks</h4>
      <ul>
        <li v-for="(hook, idx) in comparisonReport.aftermath_hooks" :key="`${hook.kind}-${idx}`">{{ hook.text }}</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  history: { type: Array, default: () => [] },
  snapshots: { type: Array, default: () => [] },
  comparisonReport: { type: Object, default: () => ({}) },
})
defineEmits(['load-snapshot', 'compare-to-snapshot'])

const recentHistory = computed(() => [...props.history].reverse().slice(0, 6))
</script>

<style scoped>
.panel{border:1px solid #ddd;padding:10px;background:#fff}
.history-list{list-style:none;padding:0;margin:8px 0;display:flex;flex-direction:column;gap:8px}
.history-list li{border:1px solid #ececec;padding:8px;background:#fafafa}
.line{font-size:12px;margin:2px 0}
.hint{font-size:12px;color:#666}
.snapshot-item button{margin-top:6px;padding:4px 8px}
.snapshot-item button + button{margin-left:6px}
.comparison-hooks{margin-top:10px;border-top:1px solid #ececec;padding-top:8px}
.comparison-hooks ul{margin:6px 0 0;padding-left:18px}
</style>
