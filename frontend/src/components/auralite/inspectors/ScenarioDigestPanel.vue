<template>
  <section class="digest" v-if="digest || keyActorEscalation || monitoringWatchlist || stabilitySignals || operatorBrief">
    <h3>Scenario digest</h3>
    <div class="operator-brief" v-if="operatorBrief?.what_happened">
      <p class="line"><strong>What happened:</strong> {{ timelineSummaryLine }}</p>
      <p class="line subtle"><strong>Role:</strong> {{ operatorSurfaceRoles.digest }}</p>
      <p class="line emphasis"><strong>Focus lane:</strong> {{ compactDistrictWhat }} → {{ compactNextCheckWhat }}</p>
      <div class="signal-pills">
        <span class="pill conf">Conf {{ focusSignals.confidence }}</span>
        <span class="pill stab">Stable {{ focusSignals.stability }}</span>
        <span class="pill next">Next {{ focusSignals.nextCheck }}</span>
      </div>
      <p class="line"><strong>Action cue:</strong> {{ actionCueLine }}</p>
      <p class="line"><strong>Scope:</strong> {{ scopeLine }}</p>
      <p class="line subtle clamp-2"><strong>Why now:</strong> {{ whyNowLine }}</p>
      <p class="line subtle"><strong>Evidence:</strong> {{ evidenceBundleLine }}</p>
      <p class="line"><strong>Trend:</strong> {{ trendCompanionLine }}</p>
    </div>
    <p class="line"><strong>Scenario track:</strong> {{ digestTimelineLine }}</p>

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
import {
  buildFocusExplainability,
  fallbackFocusCopy,
  formatCompactFocusLine,
  formatScenarioCompanionLine,
  formatScenarioTimelineLine,
  formatEvidenceBundleLine,
  formatFocusSignalSet,
  formatScenarioPriorityLine,
  formatScenarioScopeLine,
  formatScenarioWhyNowLine,
  operatorSurfaceRoles,
} from '../../../lib/auralite/operatorFocusFormatting'

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
const timelineSummaryLine = computed(() => formatScenarioTimelineLine(
  props.operatorBrief?.what_happened,
  'No compact scenario summary yet.',
))
const digestTimelineLine = computed(() => formatScenarioTimelineLine(
  props.digest?.what_happened_overall,
  'No digest summary yet.',
))
const watchNowLine = computed(() => {
  const watch = props.operatorBrief?.watch_now || {}
  const district = (watch.districts || [])[0]
  const resident = (watch.residents_households || [])[0]
  const system = (watch.systems || [])[0]
  return formatScenarioPriorityLine({
    district: district?.label || district?.district_id,
    resident: resident?.resident_name || resident?.resident_id,
    system: system?.system,
  })
})
const actionCueLine = computed(() => formatScenarioTimelineLine(
  props.operatorBrief?.main_problem_now || watchNowLine.value,
  'No immediate action cue yet.',
))
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
const focusConfidencePayload = computed(() => props.operatorBrief?.focus_confidence || props.operatorBrief?.focus_prioritization?.confidence || {})
const focusEvidencePayload = computed(() => props.operatorBrief?.focus_evidence || props.operatorBrief?.focus_prioritization?.evidence || {})
const focusExplainability = computed(() => buildFocusExplainability({
  priorities: {
    districtDriver: props.operatorBrief?.focus_prioritization?.current_district_driver || fallbackFocusCopy.district,
    residentServiceRelevance: props.operatorBrief?.focus_prioritization?.resident_household_service_relevance || fallbackFocusCopy.resident,
    topInstitutionLink: props.operatorBrief?.focus_prioritization?.top_institution_link || fallbackFocusCopy.institution,
    topSystem: props.operatorBrief?.focus_prioritization?.top_system || null,
    nextCheck: {
      what: checkNextLine.value || fallbackFocusCopy.nextCheck,
      why: props.operatorBrief?.next_check_why || props.operatorBrief?.focus_prioritization?.next_check_why || fallbackFocusCopy.nextCheckWhy,
    },
    evidence: focusEvidencePayload.value,
  },
}))
const focusSignals = computed(() => formatFocusSignalSet(focusConfidencePayload.value))
const compactDistrictWhat = computed(() => formatCompactFocusLine(focusExplainability.value?.district?.what))
const compactResidentWhat = computed(() => formatCompactFocusLine(focusExplainability.value?.resident?.what))
const compactInstitutionWhat = computed(() => formatCompactFocusLine(focusExplainability.value?.institution?.what))
const compactNextCheckWhat = computed(() => formatCompactFocusLine(focusExplainability.value?.nextCheck?.what))
const scopeLine = computed(() => formatScenarioScopeLine({
  resident: compactResidentWhat.value,
  institution: compactInstitutionWhat.value,
}))
const whyNowLine = computed(() => formatScenarioWhyNowLine({
  districtWhy: focusExplainability.value?.district?.why,
  nextCheckWhy: focusExplainability.value?.nextCheck?.why,
}))
const evidenceBundleLine = computed(() => formatEvidenceBundleLine(focusEvidencePayload.value || {}))
const trendSplitLine = computed(() => {
  const split = props.operatorBrief?.stabilizing_vs_deteriorating || {}
  const stabilizing = split.stabilizing_count ?? 0
  const deteriorating = split.deteriorating_count ?? 0
  const stableTop = split.stabilizing_top ? `stable ${split.stabilizing_top}` : null
  const riskTop = split.deteriorating_top ? `risk ${split.deteriorating_top}` : null
  return [`${stabilizing}/${deteriorating}`, stableTop, riskTop].filter(Boolean).join(' · ') || stabilityNowLine.value
})
const trendCompanionLine = computed(() => formatScenarioCompanionLine({
  trend: trendSplitLine.value,
  matters: props.operatorBrief?.matters_most_now || whoMattersLine.value,
}))
</script>

<style scoped>
.digest{border:1px solid #ececec;background:#fff;padding:10px}
.line{margin:4px 0 8px}
.grid{display:grid;grid-template-columns:1fr;gap:8px}
ul{margin:6px 0 0;padding-left:18px}
li{font-size:12px;line-height:1.4}
h4{margin:6px 0 2px;font-size:12px}
.compact-grid{margin-top:4px}
.subtle{color:#667085}
.emphasis{font-weight:600}
.signal-pills{display:flex;gap:6px;flex-wrap:wrap;margin:2px 0 4px}
.pill{display:inline-flex;align-items:center;padding:1px 6px;border-radius:999px;font-size:10.5px;font-weight:600}
.pill.conf{background:#fff2cc;color:#8a5a00}
.pill.stab{background:#e7f6ff;color:#055a7a}
.pill.next{background:#e9f8ec;color:#1d6b34}
.clamp-2{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
@media (max-width: 980px) {
  .digest{padding:8px}
  .line{font-size:11.5px;line-height:1.35}
}
</style>
