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
