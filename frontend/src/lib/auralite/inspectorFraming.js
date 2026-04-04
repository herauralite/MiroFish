const trimInspectorLine = (value = '', max = 180) => {
  const text = String(value ?? '').replace(/\s+/g, ' ').trim()
  if (!text) return '—'
  if (text.length <= max) return text
  return `${text.slice(0, Math.max(0, max - 1)).trimEnd()}…`
}

export const inspectorSectionTitles = {
  summary: 'Summary first',
  secondary: 'Secondary context',
  diagnostics: 'Deeper diagnostics',
}

export const inspectorYesNo = (value) => (value ? 'yes' : 'no')

export const formatInspectorLabeledLine = (label, value, max = 180) =>
  `${label}: ${trimInspectorLine(value, max)}`

export const formatCoherenceLaneLine = ({
  anchor = 'unscoped district',
  lane = 'no lane anchor',
  watch = false,
  watchUrgency = null,
  aftermath = false,
  signal = 'mixed',
  context = 'context still forming',
} = {}, max = 180) => {
  const watchLine = `watch ${inspectorYesNo(watch)}${watchUrgency ? ` (${watchUrgency})` : ''}`
  return trimInspectorLine(
    `${anchor} · ${lane} · ${watchLine} · aftermath ${inspectorYesNo(aftermath)} · signal ${signal} · ${context}`,
    max,
  )
}

const trendLabel = (trend) => {
  if (!trend) return '—'
  return `${trend.direction} (now ${trend.current}, Δ ${trend.delta})`
}

export const formatInspectorTrajectoryLine = (signals = {}) => [
  `stress ${trendLabel(signals?.stress_trend)}`,
  `housing ${trendLabel(signals?.housing_stability_trend)}`,
  `employment ${trendLabel(signals?.employment_stability_trend)}`,
  `service ${trendLabel(signals?.service_access_trend)}`,
].join(' · ')

export const summarizeInspectorSystems = (systems = [], limit = 3) => {
  if (!systems?.length) return '—'
  return systems.slice(0, limit).map((entry) => `${entry.system} (${entry.score})`).join(', ')
}

export const formatInspectorRippleLine = ({
  incomingStress = 0,
  edgeCount = null,
  delta = null,
  edges = '—',
} = {}) => {
  const edgePart = edgeCount === null || edgeCount === undefined ? null : `${edgeCount} edges`
  const deltaPart = delta === null || delta === undefined ? null : `Δ ${delta}`
  return [incomingStress, deltaPart, edgePart].filter(Boolean).join(' · ') + ` · ${edges}`
}

export const formatInspectorCausalDeltaLine = ({
  stress = 0,
  housing = 0,
  employment = 0,
  stressLabel = 'stress',
  housingLabel = 'housing',
  employmentLabel = 'employment',
  service = null,
  phase = null,
  driver = null,
} = {}) => {
  const parts = [
    `Δ ${stressLabel} ${stress}`,
    `Δ ${housingLabel} ${housing}`,
    `Δ ${employmentLabel} ${employment}`,
  ]
  if (service !== null && service !== undefined) parts.push(`Δ service ${service}`)
  if (phase !== null && phase !== undefined) parts.push(`phase ${phase}`)
  if (driver) parts.push(`driver ${driver}`)
  return parts.join(' · ')
}

const asNumeric = (value, fallback = 0) => {
  const n = Number(value)
  return Number.isFinite(n) ? n : fallback
}

export const formatInstitutionContextLine = (institution = {}, max = 180) => trimInspectorLine(
  `${institution.institution_type || 'institution'} · ${institution.name || 'unnamed'} · `
  + `access ${asNumeric(institution.access_score).toFixed(2)} · pressure ${asNumeric(institution.pressure_index).toFixed(2)}`,
  max,
)

export const formatInstitutionSpatialLine = (institution = {}, max = 180) => trimInspectorLine(
  `${institution.name || 'Unnamed institution'} (${institution.institution_type || 'institution'}) · `
  + `${institution.district_name || institution.district_id || 'unscoped district'} · `
  + `state ${institution.relevanceSummary?.operational || 'operational status forming'} / ${institution.relevanceSummary?.pressure || 'pressure status forming'} · `
  + `watch ${inspectorYesNo(institution.inWatchedArea)} · aftermath ${inspectorYesNo(institution.aftermathTouchesDistrict)} · `
  + `ecosystem ${(institution.ecosystem?.localKinds || []).slice(0, 3).join(', ') || '—'} · `
  + `links R${institution.linkedResidentCount ?? 0}/H${institution.linkedHouseholdCount ?? 0}`,
  max,
)

export const formatInstitutionCoherenceLine = (coherence = {}, max = 180) => {
  const total = coherence.institutionCount ?? 0
  return trimInspectorLine(
    `resident-district ${coherence.residentDistrictInstitutionAlignment ?? 0}/${total} · `
    + `household-district ${coherence.householdDistrictInstitutionAlignment ?? 0}/${total} · `
    + `watch links ${coherence.watchedInstitutionCount ?? 0} · `
    + `aftermath links ${coherence.aftermathInstitutionCount ?? 0}`,
    max,
  )
}

export const formatDistrictInstitutionCadenceLine = ({
  serviceKinds = '—',
  locationKinds = '—',
  institutionCount = 0,
  averagePressure = 0,
} = {}, max = 180) => trimInspectorLine(
  `services ${serviceKinds} · channels ${locationKinds} · footprint ${institutionCount} · avg pressure ${averagePressure}`,
  max,
)
