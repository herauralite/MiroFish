import { mapRegions } from './mapRegions'
import { buildFocusExplainability, fallbackFocusCopy } from './operatorFocusFormatting'

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
const districtSignalMap = (districtSignals = []) => new Map((districtSignals || []).map((row) => [row.district_id, row]))

const districtSpatialFlags = ({ districtId = '', watchedDistrictIds = new Set(), aftermathDistrictIds = new Set(), stabilityByDistrict = new Map() }) => ({
  inWatchedArea: watchedDistrictIds.has(districtId),
  aftermathTouchesDistrict: aftermathDistrictIds.has(districtId),
  districtSignal: stabilityByDistrict.get(districtId) || 'mixed',
})

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
    const districtFlags = districtSpatialFlags({
      districtId: residentDistrictId,
      watchedDistrictIds,
      aftermathDistrictIds,
      stabilityByDistrict,
    })
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
      inWatchedArea: districtFlags.inWatchedArea,
      isWatchedResident,
      aftermathTouchesDistrict: districtFlags.aftermathTouchesDistrict,
      districtSignal: districtFlags.districtSignal,
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

const householdServiceInstitutionContext = ({
  household = {},
  memberResidents = [],
  institutionsById = new Map(),
  districtServiceContext = {},
}) => {
  const attachedInstitutions = [
    institutionsById.get(household.landlord_id),
    ...memberResidents.flatMap((resident) => [
      institutionsById.get(resident.employer_id),
      institutionsById.get(resident.transit_service_id),
      institutionsById.get(resident.service_provider_id),
    ]),
  ].filter(Boolean)

  const uniqueInstitutions = [...new Map(attachedInstitutions.map((institution) => [institution.institution_id, institution])).values()]
  const institutionKinds = [...new Set(uniqueInstitutions
    .map((institution) => INSTITUTION_KIND_MAP[institution.institution_type] || institution.institution_type)
    .filter(Boolean))]
  const districtKinds = districtServiceContext?.serviceKinds || []
  const relevantKinds = [...new Set([...institutionKinds, ...districtKinds])].slice(0, 5)

  return {
    relevantKinds,
    nearbyInstitutions: uniqueInstitutions.slice(0, 4).map((institution) => ({
      institution_id: institution.institution_id,
      name: institution.name,
      type: institution.institution_type,
      access_score: toNumber(institution.access_score),
      pressure_index: toNumber(institution.pressure_index),
    })),
    institutionCount: uniqueInstitutions.length,
  }
}

export const buildHouseholdSpatialReadback = ({
  world = {},
  spatialReadback = {},
  residentSpatialReadback = {},
  selectedResidentId = '',
}) => {
  const persons = world.persons || []
  const households = world.households || []
  const districts = world.districts || []
  const institutions = world.institutions || []
  const reportingArtifacts = world.reporting_state?.artifacts || world.scenario_state?.reporting_views || {}
  const watchlist = reportingArtifacts.monitoring_watchlist || {}
  const stability = reportingArtifacts.stability_signals || {}

  const districtsById = new Map(districts.map((district) => [district.district_id, district]))
  const districtNames = districtNameMap(districts)
  const institutionsById = new Map(institutions.map((institution) => [institution.institution_id, institution]))
  const residentsByHousehold = new Map()
  persons.forEach((resident) => {
    if (!resident.household_id) return
    if (!residentsByHousehold.has(resident.household_id)) residentsByHousehold.set(resident.household_id, [])
    residentsByHousehold.get(resident.household_id).push(resident)
  })

  const watchResidentIds = new Set((spatialReadback.watchResidentIds || []).filter(Boolean))
  const watchedDistrictIds = new Set(spatialReadback.watchDistrictIds || [])
  const aftermathDistrictIds = new Set(spatialReadback.aftermathDistrictIds || [])
  const stabilityByDistrict = new Map((stability.districts || []).map((row) => [row.district_id, row.signal]))
  const districtSignals = districtSignalMap(spatialReadback.districtSignals || [])
  const districtServiceContext = serviceContextByDistrict({ districts, institutions, locations: world.locations || [] })

  const householdRows = households.map((household) => {
    const districtId = household.district_id
    const district = districtsById.get(districtId) || {}
    const members = residentsByHousehold.get(household.household_id) || []
    const watchedResidents = members.filter((resident) => watchResidentIds.has(resident.person_id))
    const districtFlags = districtSpatialFlags({
      districtId,
      watchedDistrictIds,
      aftermathDistrictIds,
      stabilityByDistrict,
    })
    const serviceContext = householdServiceInstitutionContext({
      household,
      memberResidents: members,
      institutionsById,
      districtServiceContext: districtServiceContext[districtId] || {},
    })
    const districtSignal = districtSignals.get(districtId) || {}

    return {
      household_id: household.household_id,
      district_id: districtId,
      district_name: districtNames.get(districtId) || districtId,
      district_anchor: district.name || districtId,
      home_location_id: household.home_location_id,
      inWatchedArea: districtFlags.inWatchedArea,
      aftermathTouchesDistrict: districtFlags.aftermathTouchesDistrict,
      districtSignal: districtFlags.districtSignal,
      districtPressure: toNumber(districtSignal.pressure, toNumber(district.pressure_index)),
      watchedResidentCount: watchedResidents.length,
      watchedResidentIds: watchedResidents.map((resident) => resident.person_id),
      serviceContext,
      memberCount: members.length,
    }
  })

  const householdById = new Map(householdRows.map((row) => [row.household_id, row]))
  const selectedResident = (persons || []).find((resident) => resident.person_id === selectedResidentId)
  const selectedHouseholdId = selectedResident?.household_id
  const selectedResidentContext = residentSpatialReadback?.selectedResidentContext || null
  const selectedHouseholdContext = selectedHouseholdId ? householdById.get(selectedHouseholdId) || null : null

  const coherence = (selectedResidentContext && selectedHouseholdContext) ? {
    resident_id: selectedResidentContext.resident_id,
    household_id: selectedHouseholdContext.household_id,
    residentDistrictMatchesHousehold: selectedResidentContext.district_id === selectedHouseholdContext.district_id,
    sameDistrictLabel: selectedResidentContext.district_name === selectedHouseholdContext.district_name
      ? selectedResidentContext.district_name
      : `${selectedResidentContext.district_name} / ${selectedHouseholdContext.district_name}`,
    watchedAlignment: selectedResidentContext.inWatchedArea === selectedHouseholdContext.inWatchedArea,
    aftermathAlignment: selectedResidentContext.aftermathTouchesDistrict === selectedHouseholdContext.aftermathTouchesDistrict,
  } : null

  return {
    householdContextById: householdById,
    selectedHouseholdContext,
    coherence,
    watchSummary: {
      householdsInWatchedAreas: householdRows.filter((row) => row.inWatchedArea).length,
      householdsTouchedByAftermath: householdRows.filter((row) => row.aftermathTouchesDistrict).length,
      householdsWithWatchedResidents: householdRows.filter((row) => row.watchedResidentCount > 0).length,
      watchNext: (watchlist.watch_next || []).slice(0, 2),
    },
  }
}

export const buildInstitutionSpatialReadback = ({
  world = {},
  spatialReadback = {},
  residentSpatialReadback = {},
  householdSpatialReadback = {},
  selectedResidentId = '',
}) => {
  const districts = world.districts || []
  const institutions = world.institutions || []
  const persons = world.persons || []
  const households = world.households || []
  const locations = world.locations || []

  const districtNames = districtNameMap(districts)
  const watchDistrictIds = new Set(spatialReadback.watchDistrictIds || [])
  const aftermathDistrictIds = new Set(spatialReadback.aftermathDistrictIds || [])
  const districtSignals = districtSignalMap(spatialReadback.districtSignals || [])
  const districtServiceContext = serviceContextByDistrict({ districts, institutions, locations })

  const selectedResident = persons.find((resident) => resident.person_id === selectedResidentId) || null
  const selectedHousehold = selectedResident
    ? households.find((household) => household.household_id === selectedResident.household_id) || null
    : null

  const selectedInstitutionIds = new Set([
    selectedResident?.employer_id,
    selectedResident?.transit_service_id,
    selectedResident?.service_provider_id,
    selectedHousehold?.landlord_id,
  ].filter(Boolean))

  const residentDependents = persons.reduce((memo, resident) => {
    ;[resident.employer_id, resident.transit_service_id, resident.service_provider_id]
      .filter(Boolean)
      .forEach((institutionId) => {
        memo[institutionId] = (memo[institutionId] || 0) + 1
      })
    return memo
  }, {})

  const householdDependents = households.reduce((memo, household) => {
    if (household.landlord_id) memo[household.landlord_id] = (memo[household.landlord_id] || 0) + 1
    return memo
  }, {})

  const rows = institutions.map((institution) => {
    const districtId = institution.district_id
    const districtService = districtServiceContext[districtId] || {}
    const districtSignal = districtSignals.get(districtId) || {}
    const ecosystemKinds = (districtService.localKinds || []).slice(0, 3).map((row) => row.kind)
    const nearbyDistricts = (districtService.nearbyDistricts || []).slice(0, 2).map((row) => row.name)
    const residentLinked = residentDependents[institution.institution_id] || 0
    const householdLinked = householdDependents[institution.institution_id] || 0

    return {
      institution_id: institution.institution_id,
      name: institution.name,
      institution_type: institution.institution_type,
      district_id: districtId,
      district_name: districtNames.get(districtId) || districtId,
      district_anchor: districtNames.get(districtId) || districtId,
      inWatchedArea: watchDistrictIds.has(districtId),
      aftermathTouchesDistrict: aftermathDistrictIds.has(districtId),
      districtSignal: districtSignal.signal || 'mixed',
      districtPressure: toNumber(districtSignal.pressure),
      access_score: toNumber(institution.access_score),
      pressure_index: toNumber(institution.pressure_index),
      selectedInstitution: selectedInstitutionIds.has(institution.institution_id),
      linkedResidentCount: residentLinked,
      linkedHouseholdCount: householdLinked,
      relevanceSummary: {
        operational: toNumber(institution.access_score) >= 0.55 ? 'operationally reachable' : 'operationally constrained',
        pressure: toNumber(institution.pressure_index) >= 0.6 ? 'high pressure' : 'moderate pressure',
      },
      ecosystem: {
        localKinds: ecosystemKinds,
        nearbyDistricts,
        districtInstitutionCount: districtService.institutionCount || 0,
      },
    }
  })

  const rowById = new Map(rows.map((row) => [row.institution_id, row]))
  const selectedInstitutionContext = [...selectedInstitutionIds]
    .map((institutionId) => rowById.get(institutionId))
    .filter(Boolean)

  const residentContext = residentSpatialReadback?.selectedResidentContext || null
  const householdContext = householdSpatialReadback?.selectedHouseholdContext || null
  const coherence = (residentContext && householdContext) ? {
    institutionCount: selectedInstitutionContext.length,
    residentDistrictInstitutionAlignment: selectedInstitutionContext.filter((row) => row.district_id === residentContext.district_id).length,
    householdDistrictInstitutionAlignment: selectedInstitutionContext.filter((row) => row.district_id === householdContext.district_id).length,
    watchedInstitutionCount: selectedInstitutionContext.filter((row) => row.inWatchedArea).length,
    aftermathInstitutionCount: selectedInstitutionContext.filter((row) => row.aftermathTouchesDistrict).length,
  } : null

  return {
    institutionContextById: rowById,
    selectedInstitutionContext,
    coherence,
    summary: {
      watchedInstitutions: rows.filter((row) => row.inWatchedArea).length,
      aftermathTouchedInstitutions: rows.filter((row) => row.aftermathTouchesDistrict).length,
    },
  }
}

const yesNo = (value) => (value ? 'yes' : 'no')

export const buildOperatorFocusReadback = ({
  world = {},
  spatialReadback = {},
  residentSpatialReadback = {},
  householdSpatialReadback = {},
  institutionSpatialReadback = {},
  selectedDistrictId = '',
  selectedResidentId = '',
}) => {
  const districtsById = new Map((world.districts || []).map((district) => [district.district_id, district]))
  const residentsById = new Map((world.persons || []).map((resident) => [resident.person_id, resident]))
  const reportingArtifacts = world.reporting_state?.artifacts || world.scenario_state?.reporting_views || {}
  const operatorBrief = reportingArtifacts.operator_brief || {}
  const scenarioHandoff = reportingArtifacts.scenario_handoff || {}

  const districtContext = spatialReadback?.selectedDistrictContext || null
  const residentContext = residentSpatialReadback?.selectedResidentContext || null
  const householdContext = householdSpatialReadback?.selectedHouseholdContext || null
  const institutionContext = institutionSpatialReadback?.selectedInstitutionContext || []

  const districtId = selectedDistrictId || residentContext?.district_id || householdContext?.district_id || ''
  const district = districtsById.get(districtId) || null
  const resident = residentsById.get(selectedResidentId) || null

  const institutionLinks = institutionContext
    .map((row) => ({
      label: `${row.name} (${row.institution_type})`,
      weight: row.linkedResidentCount + row.linkedHouseholdCount,
      watched: row.inWatchedArea,
      aftermath: row.aftermathTouchesDistrict,
      pressure: row.pressure_index,
    }))
    .sort((a, b) => b.weight - a.weight || b.pressure - a.pressure || a.label.localeCompare(b.label))
  const focusPrioritization = operatorBrief.focus_prioritization || scenarioHandoff.focus_prioritization || {}
  const focusConfidence = focusPrioritization.confidence || operatorBrief.focus_confidence || scenarioHandoff.focus_confidence || {}
  const focusEvidence = focusPrioritization.evidence || operatorBrief.focus_evidence || scenarioHandoff.focus_evidence || {}
  const topInstitutionLabel = focusPrioritization.top_institution_link || institutionLinks[0]?.label || null
  const nextCheckWhat = focusPrioritization.next_check || operatorBrief.check_next?.[0] || districtContext?.checkNext?.[0] || null
  const nextCheckWhy = focusPrioritization.next_check_why || operatorBrief.next_check_why || scenarioHandoff?.decision_support?.next_check_why || null

  const quickFacts = [
    districtContext ? `District signal ${districtContext.signal}` : null,
    districtContext ? `District watch ${yesNo(districtContext.watched)}` : null,
    residentContext ? `Resident watch ${yesNo(residentContext.isWatchedResident)}` : null,
    householdContext ? `Household watch-linked ${householdContext.watchedResidentCount || 0}` : null,
    institutionContext.length ? `Institutions linked ${institutionContext.length}` : null,
  ].filter(Boolean)

  return {
    selected: {
      district_id: district?.district_id || districtId || null,
      district_name: district?.name || residentContext?.district_name || householdContext?.district_name || 'Unscoped district',
      resident_id: resident?.person_id || null,
      resident_name: resident?.name || null,
      household_id: householdContext?.household_id || resident?.household_id || null,
      institution_count: institutionContext.length,
    },
    coherence: {
      district_watch: districtContext?.watched || residentContext?.inWatchedArea || householdContext?.inWatchedArea || false,
      district_aftermath: districtContext?.aftermathPresent || residentContext?.aftermathTouchesDistrict || householdContext?.aftermathTouchesDistrict || false,
      district_signal: districtContext?.signal || residentContext?.districtSignal || householdContext?.districtSignal || 'mixed',
      resident_household_alignment: householdSpatialReadback?.coherence?.residentDistrictMatchesHousehold ?? null,
      institution_watch_links: institutionContext.filter((row) => row.inWatchedArea).length,
      institution_aftermath_links: institutionContext.filter((row) => row.aftermathTouchesDistrict).length,
    },
    relevance: {
      districtDrivers: (districtContext?.whyHot || []).slice(0, 2),
      nextChecks: (districtContext?.checkNext || []).slice(0, 2),
      residentKinds: (residentContext?.serviceContext?.relevantKinds || []).slice(0, 3),
      householdKinds: (householdContext?.serviceContext?.relevantKinds || []).slice(0, 3),
      institutionLinks: institutionLinks.slice(0, 3),
      quickFacts,
    },
    priorities: {
      districtDriver: focusPrioritization.current_district_driver || districtContext?.whyHot?.[0] || fallbackFocusCopy.district,
      districtId: focusPrioritization.current_district_id || district?.district_id || null,
      residentServiceRelevance: focusPrioritization.resident_household_service_relevance
        || residentContext?.serviceContext?.relevantKinds?.[0]
        || householdContext?.serviceContext?.relevantKinds?.[0]
        || fallbackFocusCopy.resident,
      residentId: focusPrioritization.resident_id || resident?.person_id || null,
      topInstitutionLink: topInstitutionLabel || fallbackFocusCopy.institution,
      topSystem: focusPrioritization.top_system || null,
      nextCheck: {
        what: nextCheckWhat || fallbackFocusCopy.nextCheck,
        why: nextCheckWhy || fallbackFocusCopy.nextCheckWhy,
      },
      confidence: focusConfidence,
      evidence: focusEvidence,
    },
    explainability: buildFocusExplainability({
      priorities: {
        districtDriver: focusPrioritization.current_district_driver || districtContext?.whyHot?.[0] || fallbackFocusCopy.district,
        residentServiceRelevance: focusPrioritization.resident_household_service_relevance
          || residentContext?.serviceContext?.relevantKinds?.[0]
          || householdContext?.serviceContext?.relevantKinds?.[0]
          || fallbackFocusCopy.resident,
        topInstitutionLink: topInstitutionLabel || fallbackFocusCopy.institution,
        topSystem: focusPrioritization.top_system || null,
        nextCheck: {
          what: nextCheckWhat || fallbackFocusCopy.nextCheck,
          why: nextCheckWhy || fallbackFocusCopy.nextCheckWhy,
        },
        evidence: focusEvidence,
      },
      relevance: {
        districtDrivers: (districtContext?.whyHot || []).slice(0, 2),
        residentKinds: (residentContext?.serviceContext?.relevantKinds || []).slice(0, 3),
        householdKinds: (householdContext?.serviceContext?.relevantKinds || []).slice(0, 3),
      },
    }),
  }
}
