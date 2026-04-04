import service from '../../api/index'

export const getAuraliteWorld = async () => (await service.get('/api/auralite/world')).data
export const controlAuraliteRuntime = async (payload) => (await service.post('/api/auralite/runtime/control', payload)).data
export const tickAuraliteRuntime = async (payload) => (await service.post('/api/auralite/runtime/tick', payload)).data
export const resetAuraliteWorld = async (payload = {}) => (await service.post('/api/auralite/world/reset', payload)).data
export const saveAuraliteWorld = async (payload = {}) => (await service.post('/api/auralite/world/save', payload)).data
export const loadAuraliteWorld = async (payload) => (await service.post('/api/auralite/world/load', payload)).data
export const getDistrictDetail = async (districtId) => (await service.get(`/api/auralite/districts/${districtId}`)).data
export const getResidentDetail = async (personId) => (await service.get(`/api/auralite/residents/${personId}`)).data
export const getHouseholdDetail = async (householdId) => (await service.get(`/api/auralite/households/${householdId}`)).data
export const applyAuraliteIntervention = async (payload) => (await service.post('/api/auralite/interventions/apply', payload)).data
export const setActiveScenario = async (payload) => (await service.post('/api/auralite/scenario/active', payload)).data
export const compareAuraliteScenarios = async (payload = {}) => (await service.post('/api/auralite/scenario/compare', payload)).data
