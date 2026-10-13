const baseUrl = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

export async function api(path, { method = 'GET', data, token } = {}) {
  const response = await fetch(`${baseUrl}/api${path}`, {
    method,
    headers: {
      ...(data !== undefined ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...(data !== undefined ? { body: JSON.stringify(data) } : {}),
  })
  if (response.status === 204) return null
  let result
  try { result = await response.json() } catch { result = null }
  if (!response.ok) throw new Error(result?.erro || `Falha na requisição (${response.status})`)
  return result
}
