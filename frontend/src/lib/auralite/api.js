import service from '../../api/index'

export const getAuraliteWorld = () => service.get('/api/auralite/world')
export const controlAuraliteRuntime = (payload) => service.post('/api/auralite/runtime/control', payload)
export const tickAuraliteRuntime = (payload) => service.post('/api/auralite/runtime/tick', payload)
export const resetAuraliteWorld = (payload = {}) => service.post('/api/auralite/world/reset', payload)
export const getDistrictDetail = (districtId) => service.get(`/api/auralite/districts/${districtId}`)
export const getResidentDetail = (personId) => service.get(`/api/auralite/residents/${personId}`)
