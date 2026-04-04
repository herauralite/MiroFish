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
