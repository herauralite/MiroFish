import { mapRegions } from './mapRegions'

const INSTITUTION_KIND_MAP = {
  employer: 'employment',
  landlord: 'housing',
  transit: 'transit',
  healthcare: 'healthcare',
  service_access: 'service',
}

const LOCATION_KIND_MAP = {
  transit: 'transit',
  service: 'service',
  work: 'employment',
  leisure: 'community',
}

const toNumber = (value, fallback = 0) => {
  const n = Number(value)
  return Number.isFinite(n) ? n : fallback
}

const normalizeText = (value) => String(value || '').trim().toLowerCase()

const districtResolver = (districts = []) => {
  const districtById = new Map(districts.map((district) => [district.district_id, district]))
  const districtByName = new Map(districts.map((district) => [normalizeText(district.name), district]))

  const resolveDistrictId = (row) => {
    if (!row) return null
    if (row.district_id && districtById.has(row.district_id)) return row.district_id
    const named = normalizeText(row.label || row.district_label || row.name)
    if (named && districtByName.has(named)) return districtByName.get(named).district_id
    return null
  }

  return { districtById, districtByName, resolveDistrictId }
}

const serviceContextByDistrict = ({ districts = [], institutions = [], locations = [] }) => {
  const context = {}
  const byDistrict = new Map(districts.map((district) => [district.district_id, district]))
  const institutionRowsByDistrict = new Map(districts.map((district) => [district.district_id, []]))

  institutions.forEach((institution) => {
    if (!institutionRowsByDistrict.has(institution.district_id)) return
    institutionRowsByDistrict.get(institution.district_id).push(institution)
  })

  const regionByDistrict = new Map(districts.map((district) => [
    district.district_id,
    mapRegions.find((region) => region.regionKey === district.map_region_key) || null,
  ]))

  const nearestDistrictIds = (districtId) => {
    const origin = regionByDistrict.get(districtId)?.label
    if (!origin) return []
    return districts
      .filter((row) => row.district_id !== districtId)
      .map((row) => {
        const target = regionByDistrict.get(row.district_id)?.label
        if (!target) return null
        return {
          district_id: row.district_id,
          distance: Math.hypot(target.x - origin.x, target.y - origin.y),
        }
      })
      .filter(Boolean)
      .sort((a, b) => a.distance - b.distance)
      .slice(0, 2)
      .map((row) => row.district_id)
  }

  const locationSupportByDistrict = new Map(districts.map((district) => [district.district_id, new Set()]))
  locations.forEach((location) => {
    if (!locationSupportByDistrict.has(location.district_id)) return
    const mapped = LOCATION_KIND_MAP[location.type]
    if (mapped) locationSupportByDistrict.get(location.district_id).add(mapped)
  })

  districts.forEach((district) => {
    const institutionRows = institutionRowsByDistrict.get(district.district_id) || []
    const kinds = {}
    let totalPressure = 0

    institutionRows.forEach((institution) => {
      const kind = INSTITUTION_KIND_MAP[institution.institution_type]
      if (!kind) return
      kinds[kind] = kinds[kind] || { kind, count: 0, avgAccess: 0, avgPressure: 0 }
      kinds[kind].count += 1
      kinds[kind].avgAccess += toNumber(institution.access_score)
      kinds[kind].avgPressure += toNumber(institution.pressure_index)
      totalPressure += toNumber(institution.pressure_index)
    })

    const kindRows = Object.values(kinds)
      .map((row) => ({
        ...row,
        avgAccess: row.count ? +(row.avgAccess / row.count).toFixed(3) : 0,
        avgPressure: row.count ? +(row.avgPressure / row.count).toFixed(3) : 0,
      }))
      .sort((a, b) => b.count - a.count || b.avgPressure - a.avgPressure)

    const nearbyDistricts = nearestDistrictIds(district.district_id)
      .map((nearId) => byDistrict.get(nearId))
      .filter(Boolean)
      .map((row) => ({ district_id: row.district_id, name: row.name }))

    const locationSupport = [...(locationSupportByDistrict.get(district.district_id) || [])]

    context[district.district_id] = {
      institutionCount: institutionRows.length,
      averageInstitutionPressure: institutionRows.length ? +(totalPressure / institutionRows.length).toFixed(3) : 0,
      localKinds: kindRows,
      nearbyDistricts,
      locationSupport,
      serviceKinds: [...new Set([...kindRows.map((row) => row.kind), ...locationSupport])],
    }
  })

  return context
}

const serviceNodesFromLocations = (locations = []) => locations
  .filter((location) => LOCATION_KIND_MAP[location.type])
  .slice(0, 120)
  .map((location) => ({
    id: `node-${location.location_id}`,
    x: toNumber(location.x, 50),
    y: toNumber(location.y, 50),
    district_id: location.district_id,
    kind: LOCATION_KIND_MAP[location.type],
  }))

export const buildSpatialReadback = ({ world = {}, selectedDistrictId = '', latestDistrictShifts = [] }) => {
  const districts = world.districts || []
  const institutions = world.institutions || []
  const locations = world.locations || []
  const reportingArtifacts = world.reporting_state?.artifacts || world.scenario_state?.reporting_views || {}

  const { districtById, resolveDistrictId } = districtResolver(districts)
  const watchlist = reportingArtifacts.monitoring_watchlist || {}
  const stability = reportingArtifacts.stability_signals || {}
  const feedbackLoop = reportingArtifacts.intervention_feedback_loop || {}
  const handoff = reportingArtifacts.scenario_handoff || {}
  const zoneRef = feedbackLoop.aftermath?.dominant_zone_ref || {}

  const watchDistrictRows = watchlist.districts_to_watch || []
  const watchDistrictIds = new Set(watchDistrictRows.map((row) => resolveDistrictId(row)).filter(Boolean))

  const aftermath = feedbackLoop.aftermath || {}
  const dominantZoneLabel = typeof aftermath?.dominant_zone === 'string' ? aftermath.dominant_zone : aftermath?.dominant_zone?.label
  const aftermathDistrictIds = new Set([
    zoneRef?.district_id,
    resolveDistrictId({ label: dominantZoneLabel }),
    ...((aftermath?.operator_checks || []).map((row) => resolveDistrictId(row))),
  ].filter(Boolean))

  const watchResidentIds = (watchlist.residents_households_to_watch || [])
    .map((row) => row?.person_id || row?.resident_id)
    .filter(Boolean)

  const stabilityByDistrict = new Map((stability.districts || []).map((row) => [row.district_id, row.signal]))
  const shiftByDistrict = new Map((latestDistrictShifts || []).map((row) => [row.district_id, Math.abs(toNumber(row.pressure_delta))]))
  const districtServiceContext = serviceContextByDistrict({ districts, institutions, locations })

  const districtSignals = districts.map((district) => {
    const pressureBase = toNumber(district.pressure_index)
    const shiftPressure = shiftByDistrict.get(district.district_id) || 0
    const pressure = Math.min(1, pressureBase + (shiftPressure * 0.7))
    const serviceContext = districtServiceContext[district.district_id] || {}
    return {
      district_id: district.district_id,
      map_region_key: district.map_region_key,
      watch: watchDistrictIds.has(district.district_id),
      aftermath: aftermathDistrictIds.has(district.district_id),
      signal: stabilityByDistrict.get(district.district_id) || 'mixed',
      pressure,
      institutionCount: serviceContext.institutionCount || 0,
    }
  })

  const selectedSignal = districtSignals.find((row) => row.district_id === selectedDistrictId) || null
  const selectedServiceContext = districtServiceContext[selectedDistrictId] || null
  const selectedWatchRow = watchDistrictRows.find((row) => resolveDistrictId(row) === selectedDistrictId) || null
  const selectedDistrict = districtById.get(selectedDistrictId) || null
  const actionChecks = [
    ...((handoff.decision_support?.check_next || [])),
    ...((feedbackLoop.check_next || [])),
    ...((watchlist.watch_next || [])),
  ].filter(Boolean)
  const dedupedChecks = [...new Set(actionChecks)].slice(0, 3)

  const selectedDistrictContext = selectedDistrictId ? {
    district_id: selectedDistrictId,
    whyHot: (selectedDistrict?.derived_summary?.pressure_drivers || []).slice(0, 2),
    watched: watchDistrictIds.has(selectedDistrictId),
    aftermathPresent: aftermathDistrictIds.has(selectedDistrictId),
    pressure: selectedSignal?.pressure || 0,
    signal: selectedSignal?.signal || 'mixed',
    topWatchReason: selectedWatchRow?.watch_reason || null,
    watchUrgency: selectedWatchRow?.urgency || null,
    serviceContext: selectedServiceContext || {
      institutionCount: 0,
      serviceKinds: [],
      nearbyDistricts: [],
      localKinds: [],
      averageInstitutionPressure: 0,
      locationSupport: [],
    },
    checkNext: dedupedChecks,
  } : null

  return {
    districtSignals,
    watchResidentIds,
    watchDistrictIds: [...watchDistrictIds],
    aftermathDistrictIds: [...aftermathDistrictIds],
    handoffPriority: (handoff.watch_summary?.districts || []).map((row) => row?.district_id).filter(Boolean),
    selectedDistrictContext,
    serviceNodes: serviceNodesFromLocations(locations),
    summary: {
      watchCount: watchDistrictIds.size + watchResidentIds.length,
      pressureCount: districtSignals.filter((row) => row.pressure >= 0.45).length,
      aftermathCount: aftermathDistrictIds.size,
      activeServiceNodes: locations.filter((location) => location.type === 'service' || location.type === 'transit').length,
    },
  }
}

const districtNameMap = (districts = []) => new Map(districts.map((district) => [district.district_id, district.name]))

const residentServiceInstitutionContext = ({ resident = {}, institutionsById = new Map(), districtServiceContext = {} }) => {
  const attached = [
    institutionsById.get(resident.employer_id),
    institutionsById.get(resident.transit_service_id),
    institutionsById.get(resident.service_provider_id),
  ].filter(Boolean)

  const dominantInstitutionKinds = [...new Set(attached
    .map((institution) => INSTITUTION_KIND_MAP[institution.institution_type] || institution.institution_type)
    .filter(Boolean))]

  const districtKinds = districtServiceContext?.serviceKinds || []
  const blendedKinds = [...new Set([...dominantInstitutionKinds, ...districtKinds])].slice(0, 4)

  return {
    nearbyInstitutions: attached.slice(0, 3).map((institution) => ({
      institution_id: institution.institution_id,
      name: institution.name,
      type: institution.institution_type,
      access_score: toNumber(institution.access_score),
      pressure_index: toNumber(institution.pressure_index),
    })),
    relevantKinds: blendedKinds,
  }
}

export const buildResidentSpatialReadback = ({
  world = {},
  spatialReadback = {},
  selectedResidentId = '',
}) => {
  const persons = world.persons || []
  const districts = world.districts || []
  const households = world.households || []
  const institutions = world.institutions || []
  const reportingArtifacts = world.reporting_state?.artifacts || world.scenario_state?.reporting_views || {}
  const stability = reportingArtifacts.stability_signals || {}

  const districtNames = districtNameMap(districts)
  const householdsById = new Map(households.map((household) => [household.household_id, household]))
  const institutionsById = new Map(institutions.map((institution) => [institution.institution_id, institution]))
  const watchResidentIds = new Set(spatialReadback.watchResidentIds || [])
  const aftermathDistrictIds = new Set(spatialReadback.aftermathDistrictIds || [])
  const watchedDistrictIds = new Set(spatialReadback.watchDistrictIds || [])
  const districtServiceContext = spatialReadback.selectedDistrictContext?.district_id
    ? {
      [spatialReadback.selectedDistrictContext.district_id]: spatialReadback.selectedDistrictContext.serviceContext || {},
    }
    : serviceContextByDistrict({ districts, institutions, locations: world.locations || [] })

  const stabilityByDistrict = new Map((stability.districts || []).map((row) => [row.district_id, row.signal]))
  const residentRows = persons.map((resident) => {
    const household = householdsById.get(resident.household_id) || {}
    const residentDistrictId = resident.district_id
    const isWatchedResident = watchResidentIds.has(resident.person_id)
    const watchedDistrict = watchedDistrictIds.has(residentDistrictId)
    const aftermathTouchesDistrict = aftermathDistrictIds.has(residentDistrictId)
    const districtSignal = stabilityByDistrict.get(residentDistrictId) || 'mixed'
    const services = residentServiceInstitutionContext({
      resident,
      institutionsById,
      districtServiceContext: districtServiceContext[residentDistrictId] || {},
    })

    return {
      resident_id: resident.person_id,
      district_id: residentDistrictId,
      district_name: districtNames.get(residentDistrictId) || residentDistrictId,
      current_location_id: resident.current_location_id,
      inWatchedArea: watchedDistrict,
      isWatchedResident,
      aftermathTouchesDistrict,
      districtSignal,
      household_pressure: toNumber(household.pressure_index),
      serviceContext: services,
    }
  })

  const residentById = new Map(residentRows.map((row) => [row.resident_id, row]))

  return {
    residentContextById: residentById,
    selectedResidentContext: selectedResidentId ? residentById.get(selectedResidentId) || null : null,
  }
}
