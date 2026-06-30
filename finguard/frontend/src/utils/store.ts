/**
 * Global state — Zustand store.
 * Receives live transactions from the WebSocket hook and
 * exposes derived selectors used across all dashboard pages.
 */
import { create } from 'zustand'

export interface Transaction {
  tx_id: string
  from_account_id: string
  to_account_id: string
  amount: number
  currency: string
  tx_type: string
  risk_score: number
  risk_level: 'low' | 'medium' | 'high'
  is_flagged: boolean
  is_loop: boolean
  pattern: string | null
  isolation_forest_score: number
  autoencoder_error: number
  timestamp: string
}

export interface Alert {
  alert_id: string
  tx_id: string
  severity: 'critical' | 'high' | 'medium'
  alert_type: string
  description: string
  risk_score: number
  created_at: string
  resolved: boolean
}

interface Store {
  transactions: Transaction[]
  alerts: Alert[]
  isConnected: boolean
  flaggedCount: number
  suspiciousChains: number
  totalVolume: number

  addTransaction: (tx: Transaction) => void
  addAlert: (alert: Alert) => void
  setConnected: (v: boolean) => void
}

export const useStore = create<Store>((set, get) => ({
  transactions: [],
  alerts: [],
  isConnected: false,
  flaggedCount: 0,
  suspiciousChains: 0,
  totalVolume: 0,

  addTransaction: (tx) => {
    set((state) => {
      const transactions = [tx, ...state.transactions].slice(0, 500)
      const flaggedCount = transactions.filter((t) => t.is_flagged).length
      const suspiciousChains = transactions.filter((t) => t.is_loop).length
      const totalVolume = transactions.reduce((s, t) => s + t.amount, 0)
      return { transactions, flaggedCount, suspiciousChains, totalVolume }
    })
  },

  addAlert: (alert) => {
    set((state) => ({ alerts: [alert, ...state.alerts].slice(0, 100) }))
  },

  setConnected: (isConnected) => set({ isConnected }),
}))
