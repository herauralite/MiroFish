const titleCase = (value = '') => value
  .replaceAll('_', ' ')
  .trim()

const asScore = (value) => {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return null
  return numeric.toFixed(2)
}

export const fallbackFocusCopy = {
  district: 'No dominant district driver yet.',
  resident: 'No resident/household tie yet.',
  institution: 'No institution/service link yet.',
  nextCheck: 'Continue watchlist monitoring.',
  nextCheckWhy: 'Immediate follow-up rationale is still forming.',
}

export const operatorSurfaceRoles = {
  chip: 'map-side immediate action',
  digest: 'scenario-level readback snapshot',
  handoff: 'handoff/resumption context',
  inspector: 'selected-resident/local coherence',
}

export const formatFocusConfidenceLine = (confidence = {}) => {
  const level = confidence.focus_confidence_level || 'weak'
  const score = asScore(confidence.focus_confidence_score) || '0.00'
  return `${level} (${score})`
}

export const formatFocusStabilityLine = (confidence = {}) => titleCase(confidence.focus_stability || 'tentative')

export const formatNextCheckSupportLine = (confidence = {}) => titleCase(confidence.next_check_support || 'weakly_supported')

export const formatFocusSignalSet = (confidence = {}) => ({
  confidence: formatFocusConfidenceLine(confidence),
  stability: formatFocusStabilityLine(confidence),
  nextCheck: formatNextCheckSupportLine(confidence),
})

export const formatFocusStateLine = ({ signal = 'mixed', watch = false, aftermath = false } = {}) =>
  `signal ${signal} · watch ${watch ? 'yes' : 'no'} · aftermath ${aftermath ? 'yes' : 'no'}`

export const formatEvidenceScoreLine = (evidenceNode = {}) => {
  const score = asScore(evidenceNode.watch_score)
  if (!score || !evidenceNode.source) return 'limited'
  return score
}

export const formatNextCheckEvidenceLine = (evidence = {}) => evidence?.next_check?.source || 'limited'

const trimLine = (value = '', max = 120) => {
  const text = String(value || '').replace(/\s+/g, ' ').trim()
  if (!text) return '—'
  if (text.length <= max) return text
  return `${text.slice(0, Math.max(0, max - 1)).trimEnd()}…`
}

export const formatCompactFocusLine = (value, max = 84) => trimLine(value, max)
export const formatCompactWhyLine = (value, max = 100) => trimLine(value, max)

export const formatEvidenceBundleLine = (evidence = {}) => {
  const district = formatEvidenceScoreLine(evidence?.district_driver || {})
  const resident = formatEvidenceScoreLine(evidence?.resident_household_relevance || {})
  const institution = formatEvidenceScoreLine(evidence?.institution_link || {})
  const next = formatNextCheckEvidenceLine(evidence)
  return `D ${district} · R ${resident} · I ${institution} · N ${trimLine(next, 36)}`
}

export const buildFocusExplainability = ({ priorities = {}, relevance = {} } = {}) => {
  const districtWhy = priorities?.evidence?.district_driver?.source || (relevance?.districtDrivers || [])[0] || null
  const residentWhy = priorities?.evidence?.resident_household_relevance?.source
    || (relevance?.residentKinds || [])[0]
    || (relevance?.householdKinds || [])[0]
    || null
  const institutionWhy = priorities?.evidence?.institution_link?.source || priorities?.topSystem || null
  const nextCheckWhy = priorities?.nextCheck?.why || priorities?.evidence?.next_check?.rationale || null

  return {
    district: {
      what: priorities?.districtDriver || fallbackFocusCopy.district,
      why: districtWhy || 'Current highest district pressure signal.',
    },
    resident: {
      what: priorities?.residentServiceRelevance || fallbackFocusCopy.resident,
      why: residentWhy || 'Most relevant resident/household service tie.',
    },
    institution: {
      what: priorities?.topInstitutionLink || fallbackFocusCopy.institution,
      why: institutionWhy || 'Top linked service system for this pressure path.',
    },
    nextCheck: {
      what: priorities?.nextCheck?.what || fallbackFocusCopy.nextCheck,
      why: nextCheckWhy || fallbackFocusCopy.nextCheckWhy,
    },
  }
}
