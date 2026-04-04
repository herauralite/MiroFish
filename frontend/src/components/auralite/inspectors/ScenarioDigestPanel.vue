<template>
  <section class="digest" v-if="digest || keyActorEscalation">
    <h3>Scenario digest</h3>
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
  </section>
</template>

<script setup>
defineProps({
  digest: { type: Object, default: () => ({}) },
  keyActorEscalation: { type: Object, default: () => ({}) },
})

const formatScore = (value) => Number(value || 0).toFixed(3)
</script>

<style scoped>
.digest{border:1px solid #ececec;background:#fff;padding:10px}
.line{margin:6px 0 10px}
.grid{display:grid;grid-template-columns:1fr;gap:8px}
ul{margin:6px 0 0;padding-left:18px}
li{font-size:12px;line-height:1.4}
h4{margin:6px 0 2px;font-size:12px}
</style>
