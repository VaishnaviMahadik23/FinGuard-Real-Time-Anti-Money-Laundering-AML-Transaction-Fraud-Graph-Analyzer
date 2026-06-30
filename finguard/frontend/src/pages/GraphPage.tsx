/**
 * GraphPage — D3-powered account linkage graph.
 * Renders nodes (accounts) and edges (transaction flows) on a Canvas element.
 * Suspicious / loop paths glow red.
 */
import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { useStore } from '@/utils/store'
import styles from './GraphPage.module.css'

type Mode = 'all' | 'suspicious' | 'loops'

interface Node {
  id: string
  x?: number
  y?: number
  fx?: number | null
  fy?: number | null
  riskScore: number
  txCount: number
  flagged: boolean
  entityType: string
}

interface Edge {
  source: string | Node
  target: string | Node
  suspicious: boolean
  loop: boolean
  count: number
}

export default function GraphPage() {
  const { transactions } = useStore()
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [mode, setMode] = useState<Mode>('all')
  const [info, setInfo] = useState('')
  const simRef = useRef<d3.Simulation<Node, Edge> | null>(null)

  useEffect(() => {
    if (!canvasRef.current || transactions.length === 0) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')!
    const W = canvas.offsetWidth
    const H = canvas.height
    canvas.width = W

    // Build graph from transaction store
    const nodeMap = new Map<string, Node>()
    const edgeMap = new Map<string, Edge>()

    transactions.forEach((tx) => {
      if (!nodeMap.has(tx.from_account_id)) {
        nodeMap.set(tx.from_account_id, {
          id: tx.from_account_id, riskScore: 0, txCount: 0, flagged: false, entityType: 'individual',
        })
      }
      if (!nodeMap.has(tx.to_account_id)) {
        nodeMap.set(tx.to_account_id, {
          id: tx.to_account_id, riskScore: 0, txCount: 0, flagged: false, entityType: 'individual',
        })
      }
      const src = nodeMap.get(tx.from_account_id)!
      src.txCount++
      src.riskScore = Math.max(src.riskScore, tx.risk_score)
      src.flagged = src.flagged || tx.is_flagged

      const key = `${tx.from_account_id}->${tx.to_account_id}`
      const existing = edgeMap.get(key)
      if (existing) {
        existing.count++
        existing.suspicious = existing.suspicious || tx.risk_score > 0.5
        existing.loop = existing.loop || tx.is_loop
      } else {
        edgeMap.set(key, {
          source: tx.from_account_id,
          target: tx.to_account_id,
          suspicious: tx.risk_score > 0.5,
          loop: tx.is_loop,
          count: 1,
        })
      }
    })

    const nodes = Array.from(nodeMap.values())
    const links = Array.from(edgeMap.values())

    setInfo(`${nodes.length} nodes · ${links.length} edges`)

    // D3 force simulation
    if (simRef.current) simRef.current.stop()
    const sim = d3.forceSimulation<Node>(nodes)
      .force('link', d3.forceLink<Node, Edge>(links).id((d) => d.id).distance(80).strength(0.4))
      .force('charge', d3.forceManyBody().strength(-120))
      .force('center', d3.forceCenter(W / 2, H / 2))
      .force('collision', d3.forceCollide(20))
      .on('tick', () => draw(ctx, W, H, nodes, links, mode))

    simRef.current = sim

    return () => { sim.stop() }
  }, [transactions, mode])

  return (
    <div className={styles.page}>
      <div className={styles.toolbar}>
        <span className={styles.title}>Account Linkage Graph</span>
        {(['all', 'suspicious', 'loops'] as Mode[]).map((m) => (
          <button
            key={m}
            className={`${styles.btn} ${mode === m ? styles.active : ''}`}
            onClick={() => setMode(m)}
          >
            {m === 'all' ? 'All' : m === 'suspicious' ? 'Suspicious' : '🔴 Loops'}
          </button>
        ))}
        <span className={styles.info}>{info}</span>
      </div>
      <canvas ref={canvasRef} className={styles.canvas} height={520} />
      <div className={styles.legend}>
        {[
          { color: '#3b82f6', label: 'Normal account' },
          { color: '#f59e0b', label: 'Medium risk' },
          { color: '#ef4444', label: 'High risk / flagged' },
          { color: '#8b5cf6', label: 'Shell / offshore' },
        ].map((l) => (
          <div key={l.label} className={styles.legendItem}>
            <div className={styles.legendDot} style={{ background: l.color }} />
            {l.label}
          </div>
        ))}
        <div className={styles.legendItem}>
          <div style={{ width: 24, height: 2, background: '#ef4444', borderRadius: 1 }} />
          Suspicious flow
        </div>
      </div>
    </div>
  )
}

function nodeColor(n: Node): string {
  if (n.flagged) return '#ef4444'
  if (n.entityType === 'shell') return '#8b5cf6'
  if (n.riskScore > 0.5) return '#f59e0b'
  return '#3b82f6'
}

function draw(
  ctx: CanvasRenderingContext2D,
  W: number, H: number,
  nodes: Node[], links: Edge[],
  mode: Mode,
) {
  ctx.clearRect(0, 0, W, H)

  const visibleLinks = mode === 'all' ? links : mode === 'suspicious' ? links.filter(l => l.suspicious) : links.filter(l => l.loop)

  // Draw edges
  visibleLinks.forEach((l) => {
    const src = l.source as Node
    const dst = l.target as Node
    if (!src.x || !dst.x) return
    ctx.beginPath()
    ctx.moveTo(src.x, src.y!)
    ctx.lineTo(dst.x, dst.y!)
    if (l.loop) {
      ctx.strokeStyle = 'rgba(239,68,68,0.85)'
      ctx.lineWidth = 2
      ctx.shadowColor = '#ef4444'
      ctx.shadowBlur = 6
    } else if (l.suspicious) {
      ctx.strokeStyle = 'rgba(245,158,11,0.6)'
      ctx.lineWidth = 1.5
      ctx.shadowBlur = 0
    } else {
      ctx.strokeStyle = 'rgba(100,116,139,0.25)'
      ctx.lineWidth = 0.8
      ctx.shadowBlur = 0
    }
    ctx.stroke()
    ctx.shadowBlur = 0
  })

  // Draw nodes
  nodes.forEach((n) => {
    if (!n.x) return
    const r = 9 + Math.min(n.txCount, 5)
    const color = nodeColor(n)
    ctx.beginPath()
    ctx.arc(n.x, n.y!, r, 0, Math.PI * 2)
    ctx.fillStyle = color
    ctx.fill()
    ctx.strokeStyle = 'rgba(255,255,255,0.12)'
    ctx.lineWidth = 1.5
    ctx.stroke()

    if (n.txCount > 2) {
      ctx.font = '9px Inter, sans-serif'
      ctx.fillStyle = '#94a3b8'
      ctx.textAlign = 'center'
      ctx.fillText(n.id.slice(0, 7), n.x, n.y! + r + 10)
    }
  })
}
