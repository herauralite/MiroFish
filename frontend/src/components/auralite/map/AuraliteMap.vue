<template>
  <div class="map-wrap">
    <svg viewBox="0 0 100 100" class="map">
      <rect x="0" y="0" width="100" height="100" fill="#eef2f5" />

      <path
        v-for="(road, idx) in arterialRoads"
        :key="`road-${idx}`"
        :d="road"
        fill="none"
        stroke="#c4ccd4"
        stroke-width="1.4"
        stroke-linecap="round"
      />

      <path :d="riverPath" fill="#b7d8f5" opacity="0.85" />

      <g v-for="district in districts" :key="district.district_id">
        <path
          v-if="shapeFor(district.map_region_key)"
          :d="shapeFor(district.map_region_key).path"
          :fill="selectedDistrictId === district.district_id ? '#ffcb6b' : '#d9e2ec'"
          stroke="#495867"
          stroke-width="0.7"
          @click="$emit('select-district', district.district_id)"
        />
        <text
          v-if="shapeFor(district.map_region_key)"
          :x="labelX(shapeFor(district.map_region_key).path)"
          :y="labelY(shapeFor(district.map_region_key).path)"
          font-size="2.4"
          fill="#1f2933"
          text-anchor="middle"
        >{{ district.name }}</text>
      </g>

      <circle
        v-for="resident in residentMarkers"
        :key="resident.person_id"
        :cx="resident.x"
        :cy="resident.y"
        r="0.55"
        fill="#ef476f"
        @click="$emit('select-resident', resident.person_id)"
      />
    </svg>
  </div>
</template>

<script setup>
import { arterialRoads, mapRegions, riverPath } from '../../../lib/auralite/mapRegions'

defineProps({ districts: Array, residentMarkers: Array, selectedDistrictId: String })
defineEmits(['select-district', 'select-resident'])

const shapeFor = (key) => mapRegions.find((r) => r.regionKey === key)

const centroid = (path) => {
  const points = path.match(/\d+(?:\.\d+)?,\d+(?:\.\d+)?/g) || []
  const xy = points.map((p) => p.split(',').map(Number))
  const n = xy.length || 1
  const sum = xy.reduce((acc, [x, y]) => [acc[0] + x, acc[1] + y], [0, 0])
  return [sum[0] / n, sum[1] / n]
}

const labelX = (path) => centroid(path)[0]
const labelY = (path) => centroid(path)[1]
</script>

<style scoped>
.map-wrap { border: 1px solid #d0d7de; background: #fff; height: 70vh; }
.map { width: 100%; height: 100%; }
</style>
