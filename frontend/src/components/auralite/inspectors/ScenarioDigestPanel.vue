<template>
  <section class="digest" v-if="digest || keyActorEscalation || monitoringWatchlist || stabilitySignals || operatorBrief">
    <h3>Scenario digest</h3>
    <div class="operator-brief" v-if="operatorBrief?.what_happened">
      <p class="line"><strong>What happened:</strong> {{ operatorBrief.what_happened }}</p>
      <p class="line"><strong>Who matters:</strong> {{ whoMattersLine }}</p>
      <p class="line"><strong>Watch now:</strong> {{ watchNowLine }}</p>
      <p class="line"><strong>Stability:</strong> {{ stabilityNowLine }}</p>
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
</script>

<style scoped>
.digest{border:1px solid #ececec;background:#fff;padding:10px}
.line{margin:6px 0 10px}
.grid{display:grid;grid-template-columns:1fr;gap:8px}
ul{margin:6px 0 0;padding-left:18px}
li{font-size:12px;line-height:1.4}
h4{margin:6px 0 2px;font-size:12px}
.compact-grid{margin-top:4px}
</style>
