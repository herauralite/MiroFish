<template>
  <div class="map-wrap">
    <svg viewBox="0 0 100 100" class="map">
      <defs>
        <pattern id="district-hatch" width="2" height="2" patternUnits="userSpaceOnUse">
          <path d="M0,0 L2,2" stroke="#ffffff" stroke-width="0.12" opacity="0.28" />
        </pattern>
      </defs>

      <rect x="0" y="0" width="100" height="100" fill="#3a5a28" />

      <rect
        v-for="(road, idx) in arterialRoads"
        :key="`arterial-${idx}`"
        :x="road.x"
        :y="road.y"
        :width="road.width"
        :height="road.height"
        fill="#4a4a4a"
      />
      <rect
        v-for="(road, idx) in collectorRoads"
        :key="`collector-${idx}`"
        :x="road.x"
        :y="road.y"
        :width="road.width"
        :height="road.height"
        fill="#5d5d5d"
        opacity="0.85"
      />

      <rect
        v-for="(walk, idx) in sidewalks"
        :key="`walk-${idx}`"
        :x="walk.x"
        :y="walk.y"
        :width="walk.width"
        :height="walk.height"
        fill="#c7c1aa"
        opacity="0.45"
      />

      <path
        v-for="(stripe, idx) in laneStripes"
        :key="`lane-${idx}`"
        :d="stripe"
        stroke="#f7e587"
        stroke-width="0.35"
        stroke-dasharray="2.4,1.8"
        opacity="0.72"
      />

      <rect
        v-for="(feature, idx) in waterFeatures"
        :key="`water-${idx}`"
        :x="feature.x"
        :y="feature.y"
        :width="feature.width"
        :height="feature.height"
        :rx="feature.radius"
        fill="#2f85b3"
        opacity="0.88"
      />

      <circle
        v-for="(park, idx) in greenSpaces"
        :key="`park-${idx}`"
        :cx="park.cx"
        :cy="park.cy"
        :r="park.r"
        fill="#58aa38"
      />

      <rect
        v-for="(block, idx) in urbanBlocks"
        :key="`block-${idx}`"
        :x="block.x"
        :y="block.y"
        :width="block.width"
        :height="block.height"
        :fill="block.fill"
        rx="0.6"
      />

      <circle
        v-for="(dot, idx) in districtTextureDots"
        :key="`texture-${idx}`"
        :cx="dot.x"
        :cy="dot.y"
        r="0.26"
        fill="#e7e4d8"
        opacity="0.45"
      />

      <g v-for="district in districts" :key="district.district_id">
        <path
          v-if="shapeFor(district.map_region_key)"
          :d="shapeFor(district.map_region_key).path"
          :fill="districtFill(district)"
          stroke="#24323d"
          :stroke-width="hoveredDistrictId === district.district_id ? 0.7 : 0.45"
          :opacity="districtOpacity(district)"
          @mouseenter="hoveredDistrictId = district.district_id"
          @mouseleave="hoveredDistrictId = ''"
          @click="$emit('select-district', district.district_id)"
        />
        <path
          v-if="shapeFor(district.map_region_key)"
          :d="shapeFor(district.map_region_key).path"
          fill="url(#district-hatch)"
          opacity="0.28"
        />

        <circle
          v-if="districtSignal(district.district_id)?.watch"
          :cx="shapeFor(district.map_region_key).label.x"
          :cy="shapeFor(district.map_region_key).label.y"
          r="3"
          fill="none"
          stroke="#ffd166"
          stroke-width="0.38"
          stroke-dasharray="1.2,0.9"
          opacity="0.9"
        />

        <circle
          v-if="districtSignal(district.district_id)?.aftermath"
          :cx="shapeFor(district.map_region_key).label.x"
          :cy="shapeFor(district.map_region_key).label.y"
          r="4.1"
          fill="none"
          stroke="#7cd992"
          stroke-width="0.33"
          opacity="0.7"
        />

        <text
          v-if="shapeFor(district.map_region_key)"
          :x="shapeFor(district.map_region_key).label.x"
          :y="shapeFor(district.map_region_key).label.y"
          font-size="1.9"
          :fill="districtTextColor(district)"
          text-anchor="middle"
          font-weight="700"
        >{{ district.name }}</text>
      </g>

      <circle
        v-for="row in pressureHaloes"
        :key="`pressure-${row.district_id}`"
        :cx="row.x"
        :cy="row.y"
        :r="row.radius"
        fill="none"
        :stroke="row.stroke"
        stroke-width="0.32"
        opacity="0.7"
      />

      <g v-for="service in serviceNodes" :key="service.id">
        <rect
          :x="service.x - 0.6"
          :y="service.y - 0.6"
          :width="serviceSize(service)"
          :height="serviceSize(service)"
          :fill="serviceColor(service.kind)"
          :opacity="serviceOpacity(service)"
          @mouseenter="hoveredServiceId = service.id"
          @mouseleave="hoveredServiceId = ''"
          rx="0.2"
        />
        <title>{{ service.kind }}</title>
      </g>

      <circle
        v-for="resident in residentMarkers"
        :key="resident.person_id"
        :cx="resident.x"
        :cy="resident.y"
        :r="markerRadius(resident.person_id)"
        :fill="markerFill(resident.person_id)"
        stroke="#ffcad5"
        stroke-width="0.12"
        @click="$emit('select-resident', resident.person_id)"
      />
      <circle
        v-for="resident in highlightedResidents"
        :key="`resident-halo-${resident.person_id}`"
        :cx="resident.x"
        :cy="resident.y"
        :r="resident.person_id === selectedResidentId ? 1.05 : 0.86"
        fill="none"
        :stroke="resident.person_id === selectedResidentId ? '#ffffff' : '#ffd166'"
        stroke-width="0.12"
        opacity="0.9"
      />
    </svg>

    <div class="readback-chip">
      <span>Watch {{ spatialReadback?.summary?.watchCount || 0 }}</span>
      <span>Pressure {{ spatialReadback?.summary?.pressureCount || 0 }}</span>
      <span>Aftermath {{ spatialReadback?.summary?.aftermathCount || 0 }}</span>
      <span>Service nodes {{ spatialReadback?.summary?.activeServiceNodes || 0 }}</span>
    </div>
    <div class="hover-chip" v-if="hoverDistrictSignal">
      <strong>{{ hoverDistrictSignal.name }}</strong>
      <span>pressure {{ hoverDistrictSignal.pressure.toFixed(2) }}</span>
      <span v-if="hoverDistrictSignal.watch">watch</span>
      <span v-if="hoverDistrictSignal.aftermath">aftermath</span>
      <span>institutions {{ hoverDistrictSignal.institutionCount || 0 }}</span>
    </div>
    <div class="selection-chip" v-if="selectedContext">
      <div class="line"><strong>{{ selectedDistrict?.name }}</strong> · {{ selectedContext.signal }}</div>
      <div class="line">Hot: {{ selectedContext.whyHot?.[0] || selectedContext.topWatchReason || 'No dominant localized driver yet.' }}</div>
      <div class="line">Watch {{ selectedContext.watched ? 'yes' : 'no' }} · Aftermath {{ selectedContext.aftermathPresent ? 'yes' : 'no' }}</div>
      <div class="line">Service context: {{ selectedContext.serviceContext?.serviceKinds?.slice(0, 3).join(', ') || 'limited context' }}</div>
      <div class="line">Nearby: {{ selectedContext.serviceContext?.nearbyDistricts?.map((row) => row.name).slice(0, 2).join(' · ') || 'no nearby districts mapped' }}</div>
      <div class="line">Next check: {{ selectedContext.checkNext?.[0] || 'continue watchlist monitoring' }}</div>
    </div>
    <div class="resident-chip" v-if="selectedResidentContext">
      <div class="line"><strong>Resident focus</strong> · {{ selectedResidentContext.district_name }}</div>
      <div class="line">Watched resident {{ selectedResidentContext.isWatchedResident ? 'yes' : 'no' }} · Watched area {{ selectedResidentContext.inWatchedArea ? 'yes' : 'no' }}</div>
      <div class="line">Aftermath touches district {{ selectedResidentContext.aftermathTouchesDistrict ? 'yes' : 'no' }} · Signal {{ selectedResidentContext.districtSignal }}</div>
      <div class="line">Nearby relevance: {{ selectedResidentContext.serviceContext?.relevantKinds?.join(', ') || 'limited context' }}</div>
    </div>
    <div class="household-chip" v-if="selectedHouseholdContext">
      <div class="line"><strong>Household anchor</strong> · {{ selectedHouseholdContext.district_name }}</div>
      <div class="line">Watched area {{ selectedHouseholdContext.inWatchedArea ? 'yes' : 'no' }} · Aftermath {{ selectedHouseholdContext.aftermathTouchesDistrict ? 'yes' : 'no' }}</div>
      <div class="line">Watch-linked residents {{ selectedHouseholdContext.watchedResidentCount || 0 }} · District pressure {{ selectedHouseholdContext.districtPressure?.toFixed?.(2) ?? selectedHouseholdContext.districtPressure }}</div>
      <div class="line">Service relevance: {{ selectedHouseholdContext.serviceContext?.relevantKinds?.slice(0, 4).join(', ') || 'limited context' }}</div>
    </div>
    <div class="institution-chip" v-if="selectedInstitutionContext?.length">
      <div class="line"><strong>Institution anchor</strong> · {{ selectedInstitutionContext[0].district_name }}</div>
      <div class="line">Watched-area links {{ selectedInstitutionContext.filter((row) => row.inWatchedArea).length }} · Aftermath links {{ selectedInstitutionContext.filter((row) => row.aftermathTouchesDistrict).length }}</div>
      <div class="line">Service ecology: {{ selectedInstitutionContext[0].ecosystem?.localKinds?.slice(0, 3).join(', ') || 'limited context' }}</div>
      <div class="line">Top institution: {{ selectedInstitutionContext[0].name }} ({{ selectedInstitutionContext[0].relevanceSummary?.operational }}, {{ selectedInstitutionContext[0].relevanceSummary?.pressure }})</div>
    </div>
    <div class="focus-chip" v-if="focusReadback">
      <div class="line"><strong>Operator focus</strong> · {{ focusReadback.selected?.district_name }}</div>
      <div class="line">Coherence: signal {{ focusReadback.coherence?.district_signal }} · watch {{ boolLabel(focusReadback.coherence?.district_watch) }} · aftermath {{ boolLabel(focusReadback.coherence?.district_aftermath) }}</div>
      <div class="line">Priority: {{ priorityLine }}</div>
      <div class="line">Resident/service: {{ residentServiceLine }}</div>
      <div class="line">Institution link: {{ institutionLinkLine }}</div>
      <div class="line">Next check: {{ nextCheckLine }}</div>
      <div class="line subtle">Why now: {{ nextCheckWhyLine }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import {
  arterialRoads,
  collectorRoads,
  districtTextureDots,
  greenSpaces,
  laneStripes,
  mapRegions,
  sidewalks,
  urbanBlocks,
  waterFeatures,
} from '../../../lib/auralite/mapRegions'

const props = defineProps({
  districts: Array,
  residentMarkers: Array,
  selectedDistrictId: String,
  selectedResidentId: String,
  spatialReadback: { type: Object, default: () => ({}) },
  residentSpatialReadback: { type: Object, default: () => ({}) },
  householdSpatialReadback: { type: Object, default: () => ({}) },
  institutionSpatialReadback: { type: Object, default: () => ({}) },
  operatorFocusReadback: { type: Object, default: () => ({}) },
})
defineEmits(['select-district', 'select-resident'])
const hoveredDistrictId = ref('')
const hoveredServiceId = ref('')

const shapeFor = (key) => mapRegions.find((r) => r.regionKey === key)
const districtSignal = (districtId) => (props.spatialReadback?.districtSignals || []).find((row) => row.district_id === districtId)
const selectedDistrict = computed(() => (props.districts || []).find((row) => row.district_id === props.selectedDistrictId) || null)
const selectedContext = computed(() => props.spatialReadback?.selectedDistrictContext || null)
const selectedResidentContext = computed(() => props.residentSpatialReadback?.selectedResidentContext || null)
const selectedHouseholdContext = computed(() => props.householdSpatialReadback?.selectedHouseholdContext || null)
const selectedInstitutionContext = computed(() => props.institutionSpatialReadback?.selectedInstitutionContext || [])
const focusReadback = computed(() => props.operatorFocusReadback || null)
const highlightedResidents = computed(() => (props.residentMarkers || []).filter((resident) =>
  resident.person_id === props.selectedResidentId || props.spatialReadback?.watchResidentIds?.includes(resident.person_id)))
const priorityLine = computed(() => focusReadback.value?.priorities?.districtDriver || 'no dominant district driver surfaced yet')
const residentServiceLine = computed(() => focusReadback.value?.priorities?.residentServiceRelevance || 'no high-relevance resident/household service tie yet')
const institutionLinkLine = computed(() => focusReadback.value?.priorities?.topInstitutionLink || 'no dominant institution link surfaced yet')
const nextCheckLine = computed(() =>
  focusReadback.value?.priorities?.nextCheck?.what
  || (focusReadback.value?.relevance?.nextChecks || []).slice(0, 1).join(' · ')
  || 'continue watchlist monitoring')
const nextCheckWhyLine = computed(() => focusReadback.value?.priorities?.nextCheck?.why || 'best immediate follow-up is still forming')
const boolLabel = (value) => (value ? 'yes' : 'no')

const serviceNodes = computed(() => props.spatialReadback?.serviceNodes || [])
const hoverDistrictSignal = computed(() => {
  const districtId = hoveredDistrictId.value || props.selectedDistrictId
  const district = (props.districts || []).find((row) => row.district_id === districtId)
  const signal = districtSignal(districtId)
  if (!district || !signal) return null
  return { ...signal, name: district.name }
})

const districtFill = (district) => {
  const shape = shapeFor(district.map_region_key)
  if (!shape) return '#d9e2ec'
  if (props.selectedDistrictId === district.district_id) return '#ffcb6b'
  const signal = districtSignal(district.district_id)
  if (signal?.pressure >= 0.7) return '#b86a6a'
  if (signal?.signal === 'stabilizing') return '#6b9c78'
  return shape.tone
}
const districtOpacity = (district) => {
  if (!hoveredDistrictId.value) return 0.75
  return hoveredDistrictId.value === district.district_id ? 0.92 : 0.45
}
const districtTextColor = (district) => {
  if (props.selectedDistrictId === district.district_id || hoveredDistrictId.value === district.district_id) return '#ffffff'
  return '#e5edf5'
}

const pressureHaloes = computed(() => (props.spatialReadback?.districtSignals || [])
  .filter((row) => row.pressure >= 0.45)
  .map((row) => {
    const shape = shapeFor(row.map_region_key)
    return {
      district_id: row.district_id,
      x: shape?.label?.x || 50,
      y: shape?.label?.y || 50,
      radius: 2.8 + row.pressure * 2.1,
      stroke: row.signal === 'deteriorating' ? '#ff7b7b' : '#f1a94e',
    }
  }))

const serviceColor = (kind) => ({
  service: '#f9f871',
  healthcare: '#7ed9ff',
  transit: '#ffd166',
  community: '#c7f9cc',
  employment: '#f29e4c',
  housing: '#d7b8ff',
}[kind] || '#f1f1f1')
const serviceDistrictId = (service) => {
  if (service?.district_id) return service.district_id
  const regions = props.districts || []
  let nearest = null
  let bestDistance = Number.POSITIVE_INFINITY
  regions.forEach((district) => {
    const region = shapeFor(district.map_region_key)
    if (!region) return
    const distance = Math.hypot(region.label.x - service.x, region.label.y - service.y)
    if (distance < bestDistance) {
      bestDistance = distance
      nearest = district.district_id
    }
  })
  return nearest
}
const serviceOpacity = (service) => {
  if (hoveredServiceId.value === service.id) return 1
  if (!props.selectedDistrictId) return 0.86
  return serviceDistrictId(service) === props.selectedDistrictId ? 0.95 : 0.35
}
const serviceSize = (service) => (hoveredServiceId.value === service.id ? 1.45 : 1.2)
const markerRadius = (personId) => {
  if (personId === props.selectedResidentId) return 0.6
  return props.spatialReadback?.watchResidentIds?.includes(personId) ? 0.52 : 0.42
}
const markerFill = (personId) => {
  if (personId === props.selectedResidentId) return '#ffffff'
  return props.spatialReadback?.watchResidentIds?.includes(personId) ? '#ffd166' : '#ef476f'
}
</script>

<style scoped>
.map-wrap { border: 1px solid #2d4431; background: #1d2b1f; height: 70vh; border-radius: 8px; overflow: hidden; position: relative; }
.map { width: 100%; height: 100%; }
.readback-chip {
  position: absolute;
  left: 10px;
  bottom: 10px;
  background: rgba(12, 16, 22, 0.8);
  border: 1px solid rgba(113, 141, 165, 0.6);
  color: #dce5ec;
  border-radius: 8px;
  font-size: 11px;
  display: flex;
  gap: 8px;
  padding: 5px 8px;
}
.hover-chip,.selection-chip,.resident-chip,.household-chip,.institution-chip{
  position:absolute;right:10px;background:rgba(10,14,20,.84);border:1px solid rgba(126,153,171,.6);color:#dce5ec;border-radius:8px;font-size:11px;padding:6px 8px;display:flex;gap:8px;flex-wrap:wrap;max-width:44%;
}
.hover-chip{top:10px}
.selection-chip{bottom:44px;display:block}
.resident-chip{bottom:124px;display:block}
.household-chip{bottom:204px;display:block}
.institution-chip{bottom:284px;display:block}
.focus-chip{
  position:absolute;right:10px;bottom:44px;background:rgba(10,14,20,.92);border:1px solid rgba(255,203,107,.68);
  color:#f7f7f7;border-radius:8px;font-size:11px;padding:8px 10px;display:block;max-width:44%;
}
.selection-chip,.resident-chip,.household-chip,.institution-chip{display:none}
.line{margin:2px 0}
.subtle{opacity:.86}
</style>
