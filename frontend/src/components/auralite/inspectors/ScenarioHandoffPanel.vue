<template>
  <section class="handoff" v-if="handoff?.artifact_type || sessionContinuity?.artifact_type || interventionFeedback?.artifact_type">
    <div class="head">
      <h3>Scenario handoff</h3>
      <span class="chip">{{ handoff?.world_time || sessionContinuity?.world_time || '—' }}</span>
    </div>

    <div class="grid">
      <p class="line"><strong>What happened:</strong> {{ handoff?.what_happened_so_far?.summary || 'No compact handoff summary yet.' }}</p>
      <p class="line"><strong>Main problem:</strong> {{ handoff?.decision_support?.main_problem_now || mattersNowLine }}</p>
      <p class="line"><strong>Matters now:</strong> {{ handoff?.decision_support?.matters_most_now || mattersNowLine }}</p>
      <p class="line"><strong>District driver:</strong> {{ focusPriorityLine.district }}</p>
      <p class="line"><strong>Resident/service relevance:</strong> {{ focusPriorityLine.resident }}</p>
      <p class="line"><strong>Institution link:</strong> {{ focusPriorityLine.institution }}</p>
      <p class="line"><strong>Check next:</strong> {{ decisionCheckLine }}</p>
      <p class="line subtle"><strong>Why this check:</strong> {{ decisionCheckWhyLine }}</p>
      <p class="line"><strong>Trend:</strong> {{ trendLine }}</p>
    </div>
    <p class="line signal-row">
      <strong>Stability:</strong>
      <span class="badge ok">{{ stabilizingLine }}</span>
      <span class="badge risk">{{ deterioratingLine }}</span>
    </p>
    <div class="loop" v-if="interventionFeedback?.artifact_type">
      <h4>Action loop</h4>
      <p class="line"><strong>Action:</strong> {{ interventionFeedback.intervention_id || 'No recent intervention id.' }}</p>
      <p class="line"><strong>Outcome:</strong> {{ interventionOutcomeLine }}</p>
      <p class="line"><strong>Aftermath:</strong> {{ interventionAftermathLine }}</p>
      <p class="line"><strong>Most affected:</strong> {{ interventionAffectedLine }}</p>
      <p class="line"><strong>Follow-through:</strong> {{ interventionFollowThroughLine }}</p>
      <p class="line"><strong>Next checks:</strong> {{ interventionChecksLine }}</p>
    </div>

    <div class="continuity" v-if="sessionContinuity?.artifact_type">
      <h4>Operator session continuity</h4>
      <p class="line"><strong>Resume now:</strong> {{ sessionContinuity?.resume_focus?.what_happened || '—' }}</p>
      <p class="line"><strong>Priority:</strong> {{ resumeMattersLine }}</p>
      <p class="line"><strong>Watch:</strong> {{ continuityWatchLine }}</p>
      <p class="line subtle"><strong>History:</strong> {{ continuityHistoryLine }}</p>
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
  interventionFeedback: { type: Object, default: () => ({}) },
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

const decisionCheckLine = computed(() => {
  const checks = props.handoff?.decision_support?.check_next || props.handoff?.watch_next || []
  return checks.slice(0, 1).join(' · ') || '—'
})
const decisionCheckWhyLine = computed(() => (
  props.handoff?.decision_support?.next_check_why
  || props.handoff?.focus_prioritization?.next_check_why
  || 'Immediate rationale is still forming.'
))
const focusPriorityLine = computed(() => {
  const focus = props.handoff?.focus_prioritization || {}
  return {
    district: focus.current_district_driver || 'No dominant district driver surfaced yet.',
    resident: focus.resident_household_service_relevance || 'No high-relevance resident/household service tie yet.',
    institution: focus.top_institution_link || 'No dominant institution/service path flagged.',
  }
})

const trendLine = computed(() => {
  const trend = props.handoff?.trend_balance || {}
  const label = (trend.label || 'mixed_or_flat').replaceAll('_', ' ')
  return `${label} (stabilizing ${trend.stabilizing_signals || 0} / deteriorating ${trend.deteriorating_signals || 0})`
})

const stabilizingLine = computed(() => {
  const row = (props.handoff?.trend_balance?.systems || []).find(item => item.signal === 'stabilizing')
  return row ? `stabilizing: ${row.system || 'system'}` : 'stabilizing: no dominant signal'
})

const deterioratingLine = computed(() => {
  const row = (props.handoff?.trend_balance?.systems || []).find(item => item.signal === 'deteriorating')
  return row ? `deteriorating: ${row.system || 'system'}` : 'deteriorating: no dominant signal'
})

const resumeMattersLine = computed(() => {
  const matters = props.sessionContinuity?.resume_focus?.what_matters_now || {}
  const actor = (matters.priority_actors || [])[0]
  const district = (matters.districts || [])[0]
  const system = (matters.systems || [])[0]
  const parts = []
  if (actor) parts.push(`actor ${actor.label || actor.actor_id}`)
  if (district) parts.push(`district ${district.label || district.district_id}`)
  if (system) parts.push(`system ${system.system}`)
  return parts.join(' · ') || '—'
})

const continuityWatchLine = computed(
  () => (props.sessionContinuity?.resume_focus?.watch_next || []).slice(0, 2).join(' · ') || decisionCheckLine.value || '—',
)

const continuityHistoryLine = computed(() => {
  const state = props.sessionContinuity?.history_state || {}
  const entries = state.entries ?? 0
  const reason = (state.capture_reason || '—').replaceAll('_', ' ')
  const capturedNow = state.captured_this_refresh ? 'captured now' : 'no new capture'
  return `${entries} entries · ${capturedNow} · ${reason}`
})

const interventionOutcomeLine = computed(() => {
  const readback = props.interventionFeedback?.readback || {}
  const signal = props.interventionFeedback?.effect_signal || 'unclear'
  const effectLine = readback.effect_line || `Intervention looks ${signal}.`
  const changedLine = readback.what_changed_line || 'No compact delta readback yet.'
  return `${effectLine} ${changedLine}`
})

const interventionAffectedLine = computed(() => {
  const affected = props.interventionFeedback?.most_affected || {}
  const district = (affected.districts || [])[0]
  const residents = (affected.residents_households || []).find((row) => row.label === 'residents_touched')
  const households = (affected.residents_households || []).find((row) => row.label === 'households_touched')
  const systems = (affected.systems || []).slice(0, 2)
  const parts = []
  if (district) parts.push(`district ${district.name || district.district_id}`)
  if (residents) parts.push(`residents ${residents.count}`)
  if (households) parts.push(`households ${households.count}`)
  if (systems.length) parts.push(`systems ${systems.join(', ')}`)
  return parts.join(' · ') || '—'
})

const interventionAftermathLine = computed(() => {
  const aftermath = props.interventionFeedback?.aftermath || {}
  const status = (aftermath.status || 'unclear').replaceAll('_', ' ')
  const ticks = aftermath.ticks_observed ?? 0
  const persistence = aftermath.persistence_index
  const persistenceText = Number.isFinite(persistence) ? Number(persistence).toFixed(2) : '—'
  return `${status} · ${ticks} ticks · persistence ${persistenceText}`
})

const interventionFollowThroughLine = computed(() => {
  const readback = props.interventionFeedback?.readback || {}
  return readback.follow_through_line || readback.persistence_line || '—'
})

const interventionChecksLine = computed(
  () => (props.interventionFeedback?.check_next || []).slice(0, 2).join(' · ') || decisionCheckLine.value || '—',
)
</script>

<style scoped>
.handoff{border:1px solid #ececec;background:#fff;padding:10px}
.head{display:flex;justify-content:space-between;align-items:center}
.chip{font-size:11px;background:#f3f5f8;border-radius:10px;padding:2px 8px;color:#344054}
.line{margin:6px 0;font-size:12px}
.grid{display:grid;grid-template-columns:1fr;gap:2px}
.signal-row{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.badge{font-size:11px;padding:2px 6px;border-radius:8px}
.badge.ok{background:#ecfdf3;color:#027a48}
.badge.risk{background:#fef3f2;color:#b42318}
.continuity{margin-top:8px;border-top:1px dashed #d5dae1;padding-top:8px}
.loop{margin-top:8px;border-top:1px dashed #d5dae1;padding-top:8px}
ul{margin:6px 0 0;padding-left:18px}
li{font-size:12px;line-height:1.35}
h4{margin:0 0 4px;font-size:12px}
.subtle{color:#667085}
</style>
