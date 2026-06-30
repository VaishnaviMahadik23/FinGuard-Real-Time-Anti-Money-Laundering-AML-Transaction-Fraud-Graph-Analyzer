/**
 * useTransactionStream — connects to the backend WebSocket and
 * pipes events into the Zustand store.
 */
import { useEffect, useRef } from 'react'
import { useStore } from '@/utils/store'

const WS_URL = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000'

export function useTransactionStream() {
  const addTransaction = useStore((s) => s.addTransaction)
  const setConnected = useStore((s) => s.setConnected)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>()

  const connect = () => {
    const ws = new WebSocket(`${WS_URL}/ws/transactions`)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      console.info('[WS] Connected to FinGuard stream')
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.event === 'transaction') {
          addTransaction(msg.data)
        }
      } catch {
        // ignore malformed messages
      }
    }

    ws.onclose = () => {
      setConnected(false)
      console.warn('[WS] Disconnected — reconnecting in 3s')
      reconnectTimer.current = setTimeout(connect, 3000)
    }

    ws.onerror = () => {
      ws.close()
    }
  }

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [])
}
