const titleCase = (value = '') => value
  .replaceAll('_', ' ')
  .trim()

const asScore = (value) => {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return null
  return numeric.toFixed(2)
}

export const fallbackFocusCopy = {
  district: 'No dominant district driver surfaced yet.',
  resident: 'No high-relevance resident/household tie surfaced yet.',
  institution: 'No dominant institution/service link surfaced yet.',
  nextCheck: 'Continue watchlist monitoring.',
  nextCheckWhy: 'Best immediate follow-up rationale is still forming.',
}

export const formatFocusConfidenceLine = (confidence = {}) => {
  const level = confidence.focus_confidence_level || 'weak'
  const score = asScore(confidence.focus_confidence_score) || '0.00'
  return `${level} (${score})`
}

export const formatFocusStabilityLine = (confidence = {}) => titleCase(confidence.focus_stability || 'tentative')

export const formatNextCheckSupportLine = (confidence = {}) => titleCase(confidence.next_check_support || 'weakly_supported')

export const formatEvidenceScoreLine = (evidenceNode = {}) => {
  const score = asScore(evidenceNode.watch_score)
  if (!score || !evidenceNode.source) return 'limited'
  return score
}

export const formatNextCheckEvidenceLine = (evidence = {}) => evidence?.next_check?.source || 'limited'

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
      why: districtWhy || 'Highest current district pressure signal.',
    },
    resident: {
      what: priorities?.residentServiceRelevance || fallbackFocusCopy.resident,
      why: residentWhy || 'Most relevant resident/household service tie in current scope.',
    },
    institution: {
      what: priorities?.topInstitutionLink || fallbackFocusCopy.institution,
      why: institutionWhy || 'Top linked service system for current pressure path.',
    },
    nextCheck: {
      what: priorities?.nextCheck?.what || fallbackFocusCopy.nextCheck,
      why: nextCheckWhy || fallbackFocusCopy.nextCheckWhy,
    },
  }
}
