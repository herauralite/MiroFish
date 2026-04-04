<template>
  <div class="panel">
    <h3>Scenario History + Saved Insights</h3>
    <p class="hint">Readback keeps backend ordering: current-state shift, baseline comparison, run outcome, then saved moments.</p>

    <div class="focus-grid">
      <div class="focus-card">
        <strong>Current-state shift</strong>
        <p>{{ formatDelta('tick_to_tick') }}</p>
      </div>
      <div class="focus-card">
        <strong>Baseline comparison</strong>
        <p>{{ formatDelta('baseline_to_current') }}</p>
      </div>
      <div class="focus-card">
        <strong>Run outcome</strong>
        <p>{{ formatDelta('scenario_start_to_current') }}</p>
      </div>
    </div>

    <div class="filters">
      <select v-model="activeSourceType">
        <option value="">All sources</option>
        <option v-for="row in sourceTypeOptions" :key="row" :value="row">{{ row }}</option>
      </select>
      <select v-model="activeDirection">
        <option value="">All directions</option>
        <option v-for="row in directionOptions" :key="row" :value="row">{{ row }}</option>
      </select>
      <select v-model="activeScenarioName">
        <option value="">All scenarios</option>
        <option v-for="row in scenarioOptions" :key="row" :value="row">{{ row }}</option>
      </select>
    </div>

    <div class="timeline">
      <h4>Timeline groups</h4>
      <p class="hint" v-if="!timelineGroups.length">No grouped moments yet.</p>
      <ul v-else class="list compact">
        <li v-for="group in timelineGroups" :key="group.group">
          <div class="row"><strong>{{ group.label }}</strong> · {{ group.count }} events</div>
          <div class="row">{{ group.latest_world_time || '—' }} · {{ group.latest_text }}</div>
        </li>
      </ul>
    </div>

    <div class="timeline">
      <h4>Replay readback</h4>
      <p class="hint" v-if="!recentTimeline.length">No scenario moments recorded yet.</p>
      <ul v-else class="list compact">
        <li v-for="item in recentTimeline" :key="item.moment_id">
          <div class="row"><strong>#{{ item.order || '—' }}</strong> · {{ item.moment_category || item.moment_type }} · {{ item.world_time || '—' }}</div>
          <div class="row">{{ item.text || item.replay_text || item.note || 'Scenario moment captured.' }}</div>
        </li>
      </ul>
    </div>

    <h4>Saved insight cards</h4>
    <p class="hint" v-if="!filteredInsights.length">No saved scenario insights match filters.</p>
    <ul v-else class="list">
      <li v-for="item in filteredInsights" :key="item.insight_id">
        <div class="row"><strong>#{{ item.timeline_order || '—' }}</strong> · <strong>{{ item.scenario_name }}</strong> · {{ item.world_time || '—' }}</div>
        <div class="row">{{ item.source_type || item.source }} · {{ item.direction || item.condition_direction }}</div>
        <div class="row">{{ item.what_happened }}</div>
        <div class="row">districts: {{ summarizeDistricts(item.districts_that_mattered) }}</div>
        <div class="row">systems: {{ summarizeSystems(item.systems_that_mattered) }}</div>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  insights: { type: Array, default: () => [] },
  timeline: { type: Array, default: () => [] },
  runOutcome: { type: Object, default: () => ({}) },
  reportingViews: { type: Object, default: () => ({}) },
  filterCatalog: { type: Object, default: () => ({}) },
})

const activeSourceType = ref('')
const activeDirection = ref('')
const activeScenarioName = ref('')

const sourceTypeOptions = computed(() => props.filterCatalog?.source_types || [])
const directionOptions = computed(() => props.filterCatalog?.directions || [])
const scenarioOptions = computed(() => props.filterCatalog?.scenario_names || [])

const recentTimeline = computed(() => {
  const replayMoments = props.reportingViews?.timeline_replay?.moments || []
  if (replayMoments.length) return [...replayMoments].reverse().slice(0, 8)
  return [...props.timeline].reverse().slice(0, 8)
})
const timelineGroups = computed(() => props.reportingViews?.timeline_groups || [])
const filteredInsights = computed(() => [...props.insights]
  .filter((item) => !activeSourceType.value || (item.source_type || 'system') === activeSourceType.value)
  .filter((item) => !activeDirection.value || (item.direction || item.condition_direction || 'flat') === activeDirection.value)
  .filter((item) => !activeScenarioName.value || (item.scenario_name || 'default-baseline') === activeScenarioName.value)
  .reverse()
  .slice(0, 8))

const summarizeDistricts = (rows = []) => {
  if (!rows.length) return '—'
  return rows.slice(0, 3).map((row) => `${row.name || row.district_id} (${Number(row.shift_score || 0).toFixed(3)})`).join(', ')
}

const summarizeSystems = (rows = []) => {
  if (!rows.length) return '—'
  return rows.slice(0, 3).map((row) => `${row.system} (${Number(row.score || 0).toFixed(3)})`).join(', ')
}

const formatDelta = (key) => {
  const view = props.runOutcome?.comparison_views?.[key] || {}
  if (view.available === false) return 'Not available yet.'
  const delta = view.what_changed || {}
  return `Pressure ${Number(delta.household_pressure_index || 0).toFixed(3)} · Service ${Number(delta.service_access_score || 0).toFixed(3)} · Employment ${Number(delta.employment_rate || 0).toFixed(3)}`
}
</script>

<style scoped>
.panel{border:1px solid #ddd;padding:10px;background:#fff}
.focus-grid{display:grid;grid-template-columns:repeat(1,minmax(0,1fr));gap:6px;margin:8px 0}
.focus-card{border:1px solid #ececec;background:#fafafa;padding:6px}
.focus-card p{margin:4px 0 0;font-size:12px}
.filters{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;margin-bottom:8px}
.filters select{font-size:12px;padding:4px}
.timeline{border-top:1px solid #ececec;border-bottom:1px solid #ececec;padding:6px 0;margin:8px 0}
.timeline h4,.panel h4{margin:4px 0;font-size:12px}
.hint{font-size:12px;color:#666}
.list{list-style:none;padding:0;margin:8px 0;display:flex;flex-direction:column;gap:8px}
.list li{border:1px solid #ececec;padding:8px;background:#fafafa}
.list.compact li{padding:6px}
.row{font-size:12px;margin:2px 0}
</style>
