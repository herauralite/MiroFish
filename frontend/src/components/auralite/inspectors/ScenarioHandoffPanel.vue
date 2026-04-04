<template>
  <section class="handoff" v-if="handoff?.artifact_type || sessionContinuity?.artifact_type">
    <div class="head">
      <h3>Scenario handoff</h3>
      <span class="chip">{{ handoff?.world_time || sessionContinuity?.world_time || '—' }}</span>
    </div>

    <p class="line"><strong>What happened:</strong> {{ handoff?.what_happened_so_far?.summary || 'No compact handoff summary yet.' }}</p>
    <p class="line"><strong>Matters now:</strong> {{ mattersNowLine }}</p>
    <p class="line"><strong>Watch next:</strong> {{ watchNextLine }}</p>
    <p class="line"><strong>Trend balance:</strong> {{ trendLine }}</p>

    <div class="continuity" v-if="sessionContinuity?.artifact_type">
      <h4>Operator session continuity</h4>
      <p class="line"><strong>Resume focus:</strong> {{ sessionContinuity?.resume_focus?.what_happened || '—' }}</p>
      <ul>
        <li v-for="item in (sessionContinuity?.resume_stack?.recent_timeline || []).slice(-3).reverse()" :key="item.moment_id || item.world_time">
          {{ item.world_time || '—' }} · {{ item.text || item.moment_type }}
        </li>
      </ul>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  handoff: { type: Object, default: () => ({}) },
  sessionContinuity: { type: Object, default: () => ({}) },
})

const mattersNowLine = computed(() => {
  const matters = props.handoff?.what_matters_now || {}
  const district = (matters.districts || [])[0]
  const resident = (matters.residents_households || [])[0]
  const system = (matters.systems || [])[0]
  const parts = []
  if (district) parts.push(`district ${district.label || district.district_id}`)
  if (resident) parts.push(`resident/hh ${resident.resident_name || resident.resident_id || resident.household_id}`)
  if (system) parts.push(`system ${system.system}`)
  return parts.join(' · ') || '—'
})

const watchNextLine = computed(() => (props.handoff?.watch_next || []).slice(0, 2).join(' · ') || '—')

const trendLine = computed(() => {
  const trend = props.handoff?.trend_balance || {}
  const label = (trend.label || 'mixed_or_flat').replaceAll('_', ' ')
  return `${label} (stabilizing ${trend.stabilizing_signals || 0} / deteriorating ${trend.deteriorating_signals || 0})`
})
</script>

<style scoped>
.handoff{border:1px solid #ececec;background:#fff;padding:10px}
.head{display:flex;justify-content:space-between;align-items:center}
.chip{font-size:11px;background:#f3f5f8;border-radius:10px;padding:2px 8px;color:#344054}
.line{margin:6px 0;font-size:12px}
.continuity{margin-top:8px;border-top:1px dashed #d5dae1;padding-top:8px}
ul{margin:6px 0 0;padding-left:18px}
li{font-size:12px;line-height:1.35}
h4{margin:0 0 4px;font-size:12px}
</style>
