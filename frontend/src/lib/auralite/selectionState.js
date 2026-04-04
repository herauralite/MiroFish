const asIdMap = (rows = [], idField = 'id') => new Map(rows.map((row) => [row?.[idField], row]).filter(([id]) => !!id))

const firstValidId = (...candidates) => candidates.find((candidate) => typeof candidate === 'string' && candidate.length > 0) || ''

const resolveResidentDistrictId = ({ selectedResident = null, districtById = new Map() }) => {
  if (!selectedResident) return ''
  const scopedDistrictId = firstValidId(
    selectedResident.district_id,
    selectedResident.current_district_id,
    selectedResident.home_district_id,
  )
  return scopedDistrictId && districtById.has(scopedDistrictId) ? scopedDistrictId : ''
}

export const resolveAuraliteSelectionState = ({
  worldState = {},
  districtId = '',
  residentId = '',
}) => {
  const districts = worldState?.districts || []
  const residents = worldState?.persons || []
  const households = worldState?.households || []

  const districtById = asIdMap(districts, 'district_id')
  const residentById = asIdMap(residents, 'person_id')
  const householdById = asIdMap(households, 'household_id')
  const selectedResident = residentById.get(residentId) || null

  const resolvedResidentId = selectedResident?.person_id || ''
  const residentDistrictId = resolveResidentDistrictId({
    selectedResident,
    districtById,
  })

  if (residentDistrictId) {
    return {
      selectedResidentId: resolvedResidentId,
      selectedDistrictId: residentDistrictId,
      selectionSource: 'resident',
    }
  }

  const residentHousehold = selectedResident ? householdById.get(selectedResident.household_id) : null
  const householdDistrictId = residentHousehold?.district_id
  if (householdDistrictId && districtById.has(householdDistrictId)) {
    return {
      selectedResidentId: resolvedResidentId,
      selectedDistrictId: householdDistrictId,
      selectionSource: 'resident_household',
    }
  }

  if (districtId && districtById.has(districtId)) {
    return {
      selectedResidentId: resolvedResidentId,
      selectedDistrictId: districtId,
      selectionSource: 'explicit_district',
    }
  }

  return {
    selectedResidentId: resolvedResidentId,
    selectedDistrictId: districts[0]?.district_id || '',
    selectionSource: 'default_district',
  }
}
