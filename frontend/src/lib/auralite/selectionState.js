const asIdMap = (rows = [], idField = 'id') => new Map(rows.map((row) => [row?.[idField], row]).filter(([id]) => !!id))

export const resolveAuraliteSelectionState = ({
  worldState = {},
  districtId = '',
  residentId = '',
}) => {
  const districts = worldState?.districts || []
  const residents = worldState?.persons || []

  const districtById = asIdMap(districts, 'district_id')
  const residentById = asIdMap(residents, 'person_id')
  const selectedResident = residentById.get(residentId) || null

  const resolvedResidentId = selectedResident?.person_id || ''
  const residentDistrictId = selectedResident?.district_id
  if (residentDistrictId && districtById.has(residentDistrictId)) {
    return {
      selectedResidentId: resolvedResidentId,
      selectedDistrictId: residentDistrictId,
      selectionSource: 'resident',
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
