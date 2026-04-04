<template>
  <div class="auralite-view">
    <AuraliteHUD
      :city="world.city"
      :world="world.world"
      :last-snapshot-id="lastSnapshotId"
      @start="start"
      @pause="pause"
      @tick="tick"
      @speed="speed"
      @save="saveSnapshot"
      @load="loadSnapshot"
    />
    <div class="layout">
      <AuraliteMap
        :districts="world.districts || []"
        :resident-markers="residentMarkers"
        :selected-district-id="selectedDistrictId"
        @select-district="selectDistrict"
        @select-resident="selectResident"
      />
      <div class="inspectors">
        <DistrictInspector :district="selectedDistrict" />
        <ResidentInspector :resident="selectedResident" :household="selectedHousehold" :institutions="selectedResidentInstitutions" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import AuraliteHUD from '../components/auralite/HUD/AuraliteHUD.vue'
import AuraliteMap from '../components/auralite/map/AuraliteMap.vue'
import DistrictInspector from '../components/auralite/inspectors/DistrictInspector.vue'
import ResidentInspector from '../components/auralite/inspectors/ResidentInspector.vue'
import {
  controlAuraliteRuntime,
  getAuraliteWorld,
  tickAuraliteRuntime,
  saveAuraliteWorld,
  loadAuraliteWorld,
} from '../lib/auralite/api'

const world = ref({})
const selectedDistrictId = ref('')
const selectedResidentId = ref('')
const lastSnapshotId = ref('')
let timer = null

const loadWorld = async () => {
  world.value = await getAuraliteWorld()
  if (!selectedDistrictId.value && world.value.districts?.length) {
    selectedDistrictId.value = world.value.districts[0].district_id
  }
}

const residentMarkers = computed(() => {
  const byLoc = new Map((world.value.locations || []).map((l) => [l.location_id, l]))
  const simMinute = new Date(world.value.world?.current_time || Date.now()).getMinutes()
  return (world.value.persons || []).map((p, idx) => {
    const loc = byLoc.get(p.current_location_id)
    const j = ((idx + simMinute) % 7) / 12
    return { person_id: p.person_id, x: (loc?.x || 0) + j, y: (loc?.y || 0) + j }
  })
})

const selectedDistrict = computed(() => (world.value.districts || []).find((d) => d.district_id === selectedDistrictId.value))
const selectedResident = computed(() => (world.value.persons || []).find((p) => p.person_id === selectedResidentId.value))
const selectedHousehold = computed(() => {
  const resident = selectedResident.value
  if (!resident) return null
  return (world.value.households || []).find((h) => h.household_id === resident.household_id) || null
})

const selectedResidentInstitutions = computed(() => {
  const resident = selectedResident.value
  if (!resident) return []
  const institutionsById = new Map((world.value.institutions || []).map((i) => [i.institution_id, i]))
  return [
    institutionsById.get(resident.employer_id),
    institutionsById.get(resident.transit_service_id),
    institutionsById.get(resident.service_provider_id),
    institutionsById.get(selectedHousehold.value?.landlord_id),
  ].filter(Boolean)
})

const selectDistrict = (id) => { selectedDistrictId.value = id }
const selectResident = (id) => { selectedResidentId.value = id }

const start = async () => { await controlAuraliteRuntime({ action: 'start' }); await loadWorld() }
const pause = async () => { await controlAuraliteRuntime({ action: 'pause' }); await loadWorld() }
const speed = async (value) => { await controlAuraliteRuntime({ action: 'speed', time_speed: value }); await loadWorld() }
const tick = async () => { await tickAuraliteRuntime({ minutes: 15 }); await loadWorld() }

const saveSnapshot = async () => {
  const data = await saveAuraliteWorld({ snapshot_id: 'latest' })
  lastSnapshotId.value = data.snapshot_id
}

const loadSnapshot = async () => {
  if (!lastSnapshotId.value) return
  await loadAuraliteWorld({ snapshot_id: lastSnapshotId.value })
  await loadWorld()
}

onMounted(async () => {
  await loadWorld()
  timer = setInterval(loadWorld, 3000)
})
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.auralite-view{padding:12px;background:#f0f2f4;min-height:100vh}
.layout{display:grid;grid-template-columns: 1fr 340px;gap:12px;margin-top:12px}
.inspectors{display:flex;flex-direction:column;gap:12px}
</style>
