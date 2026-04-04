<template>
  <section class="digest" v-if="digest || keyActorEscalation || monitoringWatchlist || stabilitySignals || operatorBrief">
    <h3>Scenario digest</h3>
    <div class="operator-brief" v-if="operatorBrief?.what_happened">
      <p class="line"><strong>What happened:</strong> {{ operatorBrief.what_happened }}</p>
      <p class="line"><strong>Main problem:</strong> {{ operatorBrief.main_problem_now || watchNowLine }}</p>
      <p class="line"><strong>Matters most:</strong> {{ operatorBrief.matters_most_now || whoMattersLine }}</p>
      <p class="line"><strong>District driver:</strong> {{ focusPriorityLine.district }}</p>
      <p class="line"><strong>Resident/household service relevance:</strong> {{ focusPriorityLine.resident }}</p>
      <p class="line"><strong>Institution link:</strong> {{ focusPriorityLine.institution }}</p>
      <p class="line"><strong>Immediate next check:</strong> {{ checkNextLine }}</p>
      <p class="line"><strong>Focus confidence:</strong> {{ focusConfidenceLine }}</p>
      <p class="line"><strong>Focus stability:</strong> {{ focusStabilityLine }}</p>
      <p class="line"><strong>Next check support:</strong> {{ nextCheckSupportLine }}</p>
      <p class="line subtle"><strong>Evidence:</strong> district {{ districtEvidenceLine }} · resident/household {{ residentEvidenceLine }} · institution {{ institutionEvidenceLine }} · next check {{ nextCheckEvidenceLine }}</p>
      <p class="line subtle"><strong>Why this check:</strong> {{ nextCheckWhyLine }}</p>
      <p class="line"><strong>Trend split:</strong> {{ trendSplitLine }}</p>
    </div>
    <p class="line"><strong>What happened:</strong> {{ digest?.what_happened_overall || 'No digest summary yet.' }}</p>

    <div class="grid">
      <div>
        <h4>Districts that mattered</h4>
        <ul>
          <li v-for="row in (digest?.districts_that_mattered || []).slice(0, 3)" :key="row.district_id || row.name">
            {{ row.name || row.district_id }} · shift {{ formatScore(row.shift_score) }}
          </li>
        </ul>
      </div>
      <div>
        <h4>Residents/households</h4>
        <ul>
          <li v-for="row in (digest?.residents_households_that_mattered || []).slice(0, 3)" :key="row.resident_id || row.household_id">
            {{ row.resident_name || row.resident_id }} · hh {{ row.household_id || '—' }}
          </li>
        </ul>
      </div>
      <div>
        <h4>Systems</h4>
        <ul>
          <li v-for="row in (digest?.systems_that_mattered || []).slice(0, 3)" :key="row.system">
            {{ row.system }} · {{ formatScore(row.score) }}
          </li>
        </ul>
      </div>
    </div>

    <div>
      <h4>Watch next</h4>
      <ul>
        <li v-for="(item, idx) in (digest?.watch_next || []).slice(0, 3)" :key="idx">{{ item }}</li>
      </ul>
    </div>

    <div>
      <h4>Key actor escalation</h4>
      <ul>
        <li v-for="row in (keyActorEscalation?.high_priority_actors || []).slice(0, 5)" :key="`${row.actor_type}-${row.actor_id}`">
          {{ row.label || row.actor_id }} · {{ row.actor_type }} · score {{ formatScore(row.score) }}
        </li>
      </ul>
    </div>

    <div class="grid compact-grid">
      <div>
        <h4>Watchlist · districts</h4>
        <ul>
          <li v-for="row in (monitoringWatchlist?.districts_to_watch || []).slice(0, 3)" :key="row.district_id">
            {{ row.label }} · {{ row.urgency }} · {{ formatScore(row.watch_score) }}
          </li>
        </ul>
      </div>
      <div>
        <h4>Watchlist · residents/households</h4>
        <ul>
          <li v-for="row in (monitoringWatchlist?.residents_households_to_watch || []).slice(0, 3)" :key="row.resident_id || row.household_id">
            {{ row.resident_name || row.resident_id }} · {{ row.urgency }} · {{ formatScore(row.watch_score) }}
          </li>
        </ul>
      </div>
      <div>
        <h4>Watchlist · systems</h4>
        <ul>
          <li v-for="row in (monitoringWatchlist?.systems_to_watch || []).slice(0, 3)" :key="row.system">
            {{ row.system }} · {{ row.urgency }} · {{ formatScore(row.watch_score) }}
          </li>
        </ul>
      </div>
    </div>

    <div class="grid compact-grid">
      <div>
        <h4>Stability · districts</h4>
        <ul>
          <li v-for="row in (stabilitySignals?.districts || []).slice(0, 3)" :key="row.district_id">
            {{ row.label }} · {{ trendLabel(row.signal) }} ({{ formatScore(row.score) }})
          </li>
        </ul>
      </div>
      <div>
        <h4>Stability · residents/households</h4>
        <ul>
          <li v-for="row in (stabilitySignals?.residents_households || []).slice(0, 3)" :key="row.resident_id || row.household_id">
            {{ row.label }} · {{ trendLabel(row.signal) }} ({{ formatScore(row.score) }})
          </li>
        </ul>
      </div>
      <div>
        <h4>Stability · systems</h4>
        <ul>
          <li v-for="row in (stabilitySignals?.systems || []).slice(0, 3)" :key="row.system">
            {{ row.system }} · {{ trendLabel(row.signal) }} ({{ formatScore(row.delta) }})
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  digest: { type: Object, default: () => ({}) },
  keyActorEscalation: { type: Object, default: () => ({}) },
  monitoringWatchlist: { type: Object, default: () => ({}) },
  stabilitySignals: { type: Object, default: () => ({}) },
  operatorBrief: { type: Object, default: () => ({}) },
})

const formatScore = (value) => Number(value || 0).toFixed(3)
const trendLabel = (value) => {
  if (value === 'stabilizing') return 'stabilizing'
  if (value === 'deteriorating') return 'deteriorating'
  return 'holding flat'
}
const whoMattersLine = computed(() => {
  const rows = props.operatorBrief?.who_matters || []
  if (!rows.length) return '—'
  return rows.map((row) => row.label || row.actor_id).join(', ')
})
const watchNowLine = computed(() => {
  const watch = props.operatorBrief?.watch_now || {}
  const district = (watch.districts || [])[0]
  const resident = (watch.residents_households || [])[0]
  const system = (watch.systems || [])[0]
  const parts = []
  if (district) parts.push(`district ${district.label || district.district_id}`)
  if (resident) parts.push(`resident/hh ${resident.resident_name || resident.resident_id}`)
  if (system) parts.push(`system ${system.system}`)
  return parts.join(' · ') || '—'
})
const stabilityNowLine = computed(() => {
  const stable = props.operatorBrief?.stability_now || {}
  const district = (stable.districts || [])[0]
  const resident = (stable.residents_households || [])[0]
  const system = (stable.systems || [])[0]
  const parts = []
  if (district) parts.push(`district ${district.label}: ${trendLabel(district.signal)}`)
  if (resident) parts.push(`resident/hh ${resident.label}: ${trendLabel(resident.signal)}`)
  if (system) parts.push(`system ${system.system}: ${trendLabel(system.signal)}`)
  return parts.join(' · ') || '—'
})
const checkNextLine = computed(() => (props.operatorBrief?.check_next || []).slice(0, 1).join(' · ') || '—')
const nextCheckWhyLine = computed(() => props.operatorBrief?.next_check_why || props.operatorBrief?.focus_prioritization?.next_check_why || 'Immediate rationale is still forming.')
const focusPriorityLine = computed(() => {
  const focus = props.operatorBrief?.focus_prioritization || {}
  return {
    district: focus.current_district_driver || 'No dominant district driver surfaced yet.',
    resident: focus.resident_household_service_relevance || 'No high-relevance resident/household service tie yet.',
    institution: focus.top_institution_link || 'No dominant institution/service path flagged.',
  }
})
const focusConfidencePayload = computed(() => props.operatorBrief?.focus_confidence || props.operatorBrief?.focus_prioritization?.confidence || {})
const focusEvidencePayload = computed(() => props.operatorBrief?.focus_evidence || props.operatorBrief?.focus_prioritization?.evidence || {})
const focusConfidenceLine = computed(() => {
  const level = focusConfidencePayload.value?.focus_confidence_level || 'weak'
  const score = Number.isFinite(Number(focusConfidencePayload.value?.focus_confidence_score))
    ? Number(focusConfidencePayload.value?.focus_confidence_score).toFixed(2)
    : '0.00'
  return `${level} (${score})`
})
const focusStabilityLine = computed(() => (focusConfidencePayload.value?.focus_stability || 'tentative').replaceAll('_', ' '))
const nextCheckSupportLine = computed(() => (focusConfidencePayload.value?.next_check_support || 'weakly_supported').replaceAll('_', ' '))
const districtEvidenceLine = computed(() => Number(focusEvidencePayload.value?.district_driver?.watch_score || 0).toFixed(2))
const residentEvidenceLine = computed(() => Number(focusEvidencePayload.value?.resident_household_relevance?.watch_score || 0).toFixed(2))
const institutionEvidenceLine = computed(() => Number(focusEvidencePayload.value?.institution_link?.watch_score || 0).toFixed(2))
const nextCheckEvidenceLine = computed(() => focusEvidencePayload.value?.next_check?.source || 'limited')
const trendSplitLine = computed(() => {
  const split = props.operatorBrief?.stabilizing_vs_deteriorating || {}
  const stabilizing = split.stabilizing_count ?? 0
  const deteriorating = split.deteriorating_count ?? 0
  const stableTop = split.stabilizing_top ? `stable ${split.stabilizing_top}` : null
  const riskTop = split.deteriorating_top ? `risk ${split.deteriorating_top}` : null
  return [`${stabilizing}/${deteriorating}`, stableTop, riskTop].filter(Boolean).join(' · ') || stabilityNowLine.value
})
</script>

<style scoped>
.digest{border:1px solid #ececec;background:#fff;padding:10px}
.line{margin:6px 0 10px}
.grid{display:grid;grid-template-columns:1fr;gap:8px}
ul{margin:6px 0 0;padding-left:18px}
li{font-size:12px;line-height:1.4}
h4{margin:6px 0 2px;font-size:12px}
.compact-grid{margin-top:4px}
.subtle{color:#667085}
</style>
