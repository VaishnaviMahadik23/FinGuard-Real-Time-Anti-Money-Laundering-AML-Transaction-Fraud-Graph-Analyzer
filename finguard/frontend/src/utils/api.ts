/**
 * Typed API client — wraps fetch calls to the FastAPI backend.
 */

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const V1 = `${BASE}/api/v1`

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${V1}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? 'API error')
  }
  return res.json()
}

// Transactions
export const api = {
  submitTransaction: (body: {
    from_account_id: string
    to_account_id: string
    amount: number
    currency?: string
    tx_type?: string
  }) => request('/transactions/', { method: 'POST', body: JSON.stringify(body) }),

  getTransactions: (params?: { limit?: number; risk_level?: string; flagged_only?: boolean }) => {
    const qs = new URLSearchParams(params as Record<string, string>).toString()
    return request(`/transactions/?${qs}`)
  },

  getFlaggedTransactions: () => request('/transactions/flagged'),

  freezeTransaction: (txId: string) =>
    request(`/transactions/${txId}/freeze`, { method: 'POST' }),

  // Graph
  getGraph: () => request('/graph/'),

  // Alerts
  getAlerts: (resolved?: boolean) =>
    request(`/alerts/?${resolved !== undefined ? `resolved=${resolved}` : ''}`),

  resolveAlert: (alertId: string) =>
    request(`/alerts/${alertId}/resolve`, { method: 'POST' }),

  // Analytics
  getDashboardStats: () => request('/analytics/dashboard'),

  // Accounts
  freezeAccount: (accountId: string) =>
    request(`/accounts/${accountId}/freeze`, { method: 'POST' }),
}
