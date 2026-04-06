<template>
  <div class="panel">
    <h3>Intervention History</h3>
    <div v-if="interventionFeedback?.artifact_type" class="feedback">
      <div class="line"><strong>Readback:</strong> {{ interventionFeedback.readback?.effect_line }} {{ interventionFeedback.readback?.what_changed_line }}</div>
      <div class="line"><strong>Aftermath:</strong> {{ aftermathLine }}</div>
      <div class="line"><strong>Follow-through:</strong> {{ followThroughLine }}</div>
      <div class="line"><strong>Most affected:</strong> {{ affectedLine }}</div>
      <div class="line"><strong>Check next:</strong> {{ checkNextLine }}</div>
    </div>
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
    <div v-if="comparisonReport?.operator_compare_lines?.length" class="comparison-hooks">
      <h4>Compare diagnostics</h4>
      <ul>
        <li v-for="(line, idx) in comparisonReport.operator_compare_lines" :key="`diag-${idx}`">{{ line }}</li>
      </ul>
      <div class="line"><strong>Sequence:</strong> {{ comparisonReport?.checkpoint_readback?.sequence_signal || '—' }}</div>
      <div class="line"><strong>Checkpoint:</strong> {{ comparisonReport?.checkpoint_readback?.checkpoint_status || '—' }}</div>
      <div class="line">
        <strong>Drag ticks:</strong>
        neighbor {{ comparisonReport?.checkpoint_readback?.continuation_neighbor_drag_ticks ?? 0 }} ·
        social {{ comparisonReport?.checkpoint_readback?.continuation_social_drag_ticks ?? 0 }}
      </div>
      <div class="line"><strong>Divergence driver:</strong> {{ comparisonReport?.checkpoint_readback?.divergence_driver || '—' }}</div>
      <div class="line"><strong>Path pair:</strong> {{ comparisonReport?.compare_checkpoint_matrix?.checkpoint_vs_live || '—' }}</div>
      <div class="line">
        <strong>Baseline state:</strong>
        {{ comparisonReport?.path_readback?.baseline_path_state?.state_kind || '—' }}
        @ {{ comparisonReport?.path_readback?.baseline_path_state?.world_time || 'n/a' }}
      </div>
      <div class="line">
        <strong>Current state:</strong>
        {{ comparisonReport?.path_readback?.current_path_state?.state_kind || '—' }}
        @ {{ comparisonReport?.path_readback?.current_path_state?.world_time || 'n/a' }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  history: { type: Array, default: () => [] },
  snapshots: { type: Array, default: () => [] },
  comparisonReport: { type: Object, default: () => ({}) },
  interventionFeedback: { type: Object, default: () => ({}) },
})
defineEmits(['load-snapshot', 'compare-to-snapshot'])

const recentHistory = computed(() => [...props.history].reverse().slice(0, 6))
const affectedLine = computed(() => {
  const affected = props.interventionFeedback?.most_affected || {}
  const topDistrict = (affected.districts || [])[0]
  const touched = affected.residents_households || []
  const residentCount = (touched.find((row) => row.label === 'residents_touched') || {}).count
  const householdCount = (touched.find((row) => row.label === 'households_touched') || {}).count
  const leadSystem = (affected.systems || [])[0]
  const parts = []
  if (topDistrict) parts.push(topDistrict.name || topDistrict.district_id)
  if (residentCount !== undefined) parts.push(`residents ${residentCount}`)
  if (householdCount !== undefined) parts.push(`households ${householdCount}`)
  if (leadSystem) parts.push(`system ${leadSystem}`)
  return parts.join(' · ') || '—'
})
const checkNextLine = computed(() => (props.interventionFeedback?.check_next || []).slice(0, 2).join(' · ') || '—')
const aftermathLine = computed(() => {
  const aftermath = props.interventionFeedback?.aftermath || {}
  const status = (aftermath.status || 'unclear').replaceAll('_', ' ')
  const ticks = aftermath.ticks_observed ?? 0
  const persistence = Number.isFinite(aftermath.persistence_index) ? Number(aftermath.persistence_index).toFixed(2) : '—'
  const zone = aftermath.dominant_zone || 'none'
  return `${status} · ${ticks} ticks · persistence ${persistence} · zone ${zone}`
})
const followThroughLine = computed(() =>
  props.interventionFeedback?.readback?.follow_through_line
  || props.interventionFeedback?.readback?.persistence_line
  || '—',
)
</script>

<style scoped>
.panel{border:1px solid #ddd;padding:10px;background:#fff}
.feedback{border:1px solid #ececec;background:#f8fafc;padding:8px;margin:8px 0}
.history-list{list-style:none;padding:0;margin:8px 0;display:flex;flex-direction:column;gap:8px}
.history-list li{border:1px solid #ececec;padding:8px;background:#fafafa}
.line{font-size:12px;margin:2px 0}
.hint{font-size:12px;color:#666}
.snapshot-item button{margin-top:6px;padding:4px 8px}
.snapshot-item button + button{margin-left:6px}
.comparison-hooks{margin-top:10px;border-top:1px solid #ececec;padding-top:8px}
.comparison-hooks ul{margin:6px 0 0;padding-left:18px}
</style>
