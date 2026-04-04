export const mapRegions = [
  { regionKey: 'region_1', path: 'M29,5 L40,5 L40,27 L29,27 Z', label: { x: 34.5, y: 16 }, tone: '#a6b3c5', zone: 'civic' },
  { regionKey: 'region_2', path: 'M58,5 L80,5 L80,27 L58,27 Z', label: { x: 69, y: 16 }, tone: '#9aa9ba', zone: 'mixed' },
  { regionKey: 'region_3', path: 'M29,35 L52,35 L52,58 L29,58 Z', label: { x: 40.5, y: 46 }, tone: '#b7c0c7', zone: 'commercial' },
  { regionKey: 'region_4', path: 'M58,59 L80,59 L80,90 L58,90 Z', label: { x: 69, y: 74 }, tone: '#8897a4', zone: 'industrial' },
  { regionKey: 'region_5', path: 'M0,5 L23,5 L23,27 L0,27 Z', label: { x: 11, y: 16 }, tone: '#91b077', zone: 'parkland' },
  { regionKey: 'region_6', path: 'M81,5 L100,5 L100,27 L81,27 Z', label: { x: 90.5, y: 16 }, tone: '#6e9b8d', zone: 'waterfront' },
  { regionKey: 'region_7', path: 'M0,35 L23,35 L23,58 L0,58 Z', label: { x: 11, y: 46 }, tone: '#9f8f7d', zone: 'residential' },
  { regionKey: 'region_8', path: 'M0,59 L23,59 L23,90 L0,90 Z', label: { x: 11, y: 74 }, tone: '#8a8478', zone: 'lowrise' },
  { regionKey: 'region_9', path: 'M0,28 L23,28 L23,34 L0,34 Z M0,91 L100,91 L100,100 L0,100 Z', label: { x: 20, y: 95 }, tone: '#7f9370', zone: 'services' },
  { regionKey: 'region_10', path: 'M81,35 L100,35 L100,90 L81,90 Z', label: { x: 90.5, y: 62 }, tone: '#887d6f', zone: 'industrial' },
]

export const arterialRoads = [
  { x: 0, y: 28, width: 100, height: 7 },
  { x: 0, y: 58, width: 100, height: 7 },
  { x: 23, y: 0, width: 6, height: 100 },
  { x: 52, y: 0, width: 6, height: 100 },
  { x: 80, y: 0, width: 6, height: 100 },
]

export const collectorRoads = [
  { x: 2, y: 46, width: 18, height: 2.8 },
  { x: 31, y: 45, width: 18, height: 2.8 },
  { x: 60, y: 44, width: 18, height: 2.8 },
  { x: 84, y: 45, width: 14, height: 2.8 },
  { x: 9.5, y: 66, width: 2.2, height: 22 },
  { x: 37, y: 67, width: 2.2, height: 20 },
  { x: 66, y: 67, width: 2.2, height: 21 },
]

export const sidewalks = [
  { x: 0, y: 27.2, width: 100, height: 0.65 },
  { x: 0, y: 35.05, width: 100, height: 0.65 },
  { x: 0, y: 57.2, width: 100, height: 0.65 },
  { x: 0, y: 65.05, width: 100, height: 0.65 },
  { x: 22.2, y: 0, width: 0.65, height: 100 },
  { x: 29.05, y: 0, width: 0.65, height: 100 },
  { x: 51.2, y: 0, width: 0.65, height: 100 },
  { x: 58.05, y: 0, width: 0.65, height: 100 },
  { x: 79.2, y: 0, width: 0.65, height: 100 },
  { x: 86.05, y: 0, width: 0.65, height: 100 },
]

export const laneStripes = [
  'M0,31.5 L100,31.5',
  'M0,61.5 L100,61.5',
  'M26,0 L26,100',
  'M55,0 L55,100',
  'M83,0 L83,100',
]

export const districtTextureDots = [
  { x: 33, y: 8 }, { x: 35, y: 11 }, { x: 37, y: 14 }, { x: 60, y: 8 }, { x: 75, y: 10 },
  { x: 7, y: 42 }, { x: 15, y: 48 }, { x: 39, y: 40 }, { x: 45, y: 44 }, { x: 90, y: 40 },
  { x: 6, y: 71 }, { x: 12, y: 75 }, { x: 66, y: 73 }, { x: 94, y: 74 }, { x: 70, y: 87 },
]

export const waterFeatures = [
  { x: 83, y: 7, width: 14, height: 10, radius: 3 },
  { x: 66, y: 70, width: 6, height: 3, radius: 0.8 },
  { x: 66, y: 78, width: 6, height: 3, radius: 0.8 },
]

export const greenSpaces = [
  { cx: 4, cy: 7, r: 2.5 },
  { cx: 10, cy: 6, r: 2.2 },
  { cx: 16, cy: 7.5, r: 2.3 },
  { cx: 6, cy: 16, r: 2.2 },
  { cx: 14, cy: 18, r: 2.4 },
  { cx: 20, cy: 86, r: 2.6 },
  { cx: 95, cy: 84, r: 2.3 },
]

export const serviceLandmarks = [
  { id: 'service-civic-1', x: 35.5, y: 16.5, kind: 'civic' },
  { id: 'service-medical-1', x: 70, y: 45.5, kind: 'medical' },
  { id: 'service-transit-1', x: 55, y: 31.5, kind: 'transit' },
  { id: 'service-school-1', x: 12.5, y: 47, kind: 'education' },
  { id: 'service-industrial-1', x: 90, y: 74, kind: 'industry' },
]

export const urbanBlocks = [
  { x: 31, y: 8, width: 5, height: 17, fill: '#6f7f8f', zone: 'office' },
  { x: 37, y: 10, width: 4, height: 15, fill: '#8393a3', zone: 'office' },
  { x: 59.5, y: 8, width: 9, height: 17, fill: '#9f9c98', zone: 'mixed' },
  { x: 70, y: 8, width: 8, height: 17, fill: '#8b97a8', zone: 'mixed' },
  { x: 85, y: 19, width: 5, height: 7, fill: '#7b7b7b', zone: 'utility' },
  { x: 90.5, y: 20, width: 5, height: 6, fill: '#888', zone: 'utility' },
  { x: 2, y: 37, width: 8, height: 14, fill: '#c7a777', zone: 'housing' },
  { x: 11.5, y: 37, width: 9, height: 15, fill: '#b6b6c6', zone: 'housing' },
  { x: 31, y: 38, width: 9, height: 14, fill: '#d8d2cc', zone: 'civic' },
  { x: 41.5, y: 39, width: 8, height: 13, fill: '#c7d3da', zone: 'civic' },
  { x: 59.5, y: 38, width: 8, height: 13, fill: '#efefef', zone: 'services' },
  { x: 69, y: 39, width: 10, height: 12, fill: '#d0d7dc', zone: 'services' },
  { x: 83, y: 38, width: 7, height: 14, fill: '#707878', zone: 'industrial' },
  { x: 4, y: 67, width: 5, height: 11, fill: '#c19070', zone: 'rowhouse' },
  { x: 10.5, y: 67, width: 5, height: 10, fill: '#af6f50', zone: 'rowhouse' },
  { x: 60, y: 67, width: 13, height: 18, fill: '#8888a8', zone: 'warehouse' },
  { x: 84, y: 68, width: 6.5, height: 12, fill: '#c8a880', zone: 'housing' },
  { x: 91.5, y: 69, width: 5.5, height: 11, fill: '#d0b890', zone: 'housing' },
]
