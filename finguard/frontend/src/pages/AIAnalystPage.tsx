/**
 * AIAnalystPage — Chat interface powered by Claude API.
 * Passes live transaction context to the model for intelligent AML analysis.
 */
import { useState, useRef, useEffect } from 'react'
import { useStore } from '@/utils/store'
import styles from './AIAnalystPage.module.css'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const QUICK_PROMPTS = [
  'Summarize the highest risk transactions detected in this session.',
  'Explain what structural loop patterns have been detected and which accounts are involved.',
  'Which accounts show velocity anomalies that could indicate smurfing or layering?',
  'Generate a SAR (Suspicious Activity Report) summary for the top flagged transaction cluster.',
  'What is the Isolation Forest anomaly score distribution across the current transaction batch?',
]

const API_KEY = import.meta.env.VITE_ANTHROPIC_API_KEY ?? ''

export default function AIAnalystPage() {
  const { transactions, flaggedCount, suspiciousChains, totalVolume } = useStore()
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content:
        '🛡️ **FinGuard AI Online.** Real-time AML monitoring active. I have access to live transaction data from this session. Ask me about detected patterns, specific transactions, or request a compliance report.',
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const chatRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight
    }
  }, [messages])

  const buildSystemPrompt = () => {
    const topFlagged = transactions
      .filter((t) => t.is_flagged)
      .slice(0, 5)
      .map(
        (t) =>
          `${t.tx_id}: ${t.from_account_id} → ${t.to_account_id}, $${t.amount.toLocaleString()}, ` +
          `risk=${(t.risk_score * 100).toFixed(0)}%, pattern=${t.pattern ?? 'anomaly'}`
      )
      .join('\n  ')

    return `You are FinGuard, an expert AML (Anti-Money Laundering) AI compliance analyst embedded in a real-time transaction monitoring system. You combine expertise in financial crime typologies with precise data analysis.

LIVE SYSTEM CONTEXT:
- Session transactions: ${transactions.length}
- Flagged: ${flaggedCount} (${transactions.length ? ((flaggedCount / transactions.length) * 100).toFixed(1) : 0}%)
- Suspicious chain loops: ${suspiciousChains}
- Total monitored volume: $${totalVolume.toLocaleString(undefined, { maximumFractionDigits: 0 })}
- High-risk transactions: ${transactions.filter((t) => t.risk_level === 'high').length}
- Shell company transactions: ${transactions.filter((t) => t.pattern === 'layering').length}
- Structuring alerts: ${transactions.filter((t) => t.pattern === 'smurfing').length}

TOP FLAGGED TRANSACTIONS:
  ${topFlagged || 'None yet in this session'}

DETECTION MODELS ACTIVE:
- Isolation Forest: contamination=0.08, n_estimators=200
- Autoencoder Neural Network: input_dim=16, bottleneck=16, threshold=0.42
- Graph Loop Detector: BFS, max_depth=5

Use precise AML terminology. Cite specific transaction IDs when relevant. Be actionable and concise.`
  }

  const send = async (text?: string) => {
    const userMsg = (text ?? input).trim()
    if (!userMsg || loading) return
    setInput('')
    const newMessages: Message[] = [...messages, { role: 'user', content: userMsg }]
    setMessages(newMessages)
    setLoading(true)

    try {
      const resp = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'claude-sonnet-4-6',
          max_tokens: 1000,
          system: buildSystemPrompt(),
          messages: newMessages.map((m) => ({ role: m.role, content: m.content })),
        }),
      })
      const data = await resp.json()
      const reply = data.content?.[0]?.text ?? 'Unable to retrieve analysis.'
      setMessages((prev) => [...prev, { role: 'assistant', content: reply }])
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Analysis unavailable — check API key configuration.' },
      ])
    }
    setLoading(false)
  }

  return (
    <div className={styles.page}>
      <div className={styles.chatPanel}>
        <div className={styles.chatHeader}>
          <span className={styles.chatTitle}>🤖 AI Compliance Analyst</span>
          <span className={styles.modelBadge}>claude-sonnet-4-6</span>
        </div>

        <div className={styles.chatBody} ref={chatRef}>
          {messages.map((m, i) => (
            <div key={i} className={`${styles.msg} ${m.role === 'user' ? styles.userMsg : styles.aiMsg}`}>
              <div className={styles.msgRole}>{m.role === 'user' ? '👤 Analyst' : '🤖 FinGuard AI'}</div>
              <div className={styles.msgContent}>{m.content}</div>
            </div>
          ))}
          {loading && (
            <div className={styles.msg}>
              <div className={styles.msgRole}>🤖 FinGuard AI</div>
              <div className={styles.msgContent}>
                <span className={styles.dot1}>●</span>
                <span className={styles.dot2}>●</span>
                <span className={styles.dot3}>●</span>
              </div>
            </div>
          )}
        </div>

        <div className={styles.inputRow}>
          <input
            className={styles.input}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send()}
            placeholder="Ask about transaction patterns, risk assessment, AML typologies..."
            disabled={loading}
          />
          <button className={styles.sendBtn} onClick={() => send()} disabled={loading || !input.trim()}>
            Analyze →
          </button>
        </div>
      </div>

      <div className={styles.sidebar}>
        <div className={styles.sideCard}>
          <div className={styles.sideTitle}>⚡ Quick Analysis</div>
          {QUICK_PROMPTS.map((p) => (
            <button key={p} className={styles.quickBtn} onClick={() => send(p)}>
              {p}
            </button>
          ))}
        </div>
        <div className={styles.sideCard}>
          <div className={styles.sideTitle}>📊 Session Stats</div>
          <div className={styles.stat}><span>Total transactions</span><span>{transactions.length}</span></div>
          <div className={styles.stat}><span>Flagged</span><span style={{ color: 'var(--red)' }}>{flaggedCount}</span></div>
          <div className={styles.stat}><span>Loop chains</span><span style={{ color: 'var(--purple)' }}>{suspiciousChains}</span></div>
          <div className={styles.stat}><span>IF model</span><span style={{ color: 'var(--green)' }}>Active</span></div>
          <div className={styles.stat}><span>AE model</span><span style={{ color: 'var(--green)' }}>Active</span></div>
        </div>
      </div>
    </div>
  )
}
