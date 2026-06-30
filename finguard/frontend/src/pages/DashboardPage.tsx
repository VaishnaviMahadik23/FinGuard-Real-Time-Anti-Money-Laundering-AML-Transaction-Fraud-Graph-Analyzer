import { useStore } from '@/utils/store'
import RiskBadge from '@/components/RiskBadge'
import styles from './DashboardPage.module.css'

function fmt(n: number) {
  return '$' + n.toLocaleString(undefined, { maximumFractionDigits: 0 })
}

function fmtTime(iso: string) {
  return new Date(iso).toLocaleTimeString('en-US', { hour12: false })
}

export default function DashboardPage() {
  const { transactions, flaggedCount, suspiciousChains, totalVolume } = useStore()

  const avgRisk =
    transactions.length
      ? transactions.slice(0, 50).reduce((s, t) => s + t.risk_score, 0) /
        Math.min(transactions.length, 50)
      : 0

  const recentAlerts = transactions.filter((t) => t.is_flagged).slice(0, 10)
  const topRisk = [...transactions]
    .sort((a, b) => b.risk_score - a.risk_score)
    .slice(0, 6)

  return (
    <div className={styles.page}>
      {/* KPI Row */}
      <div className={styles.kpiRow}>
        {[
          { label: 'Transactions (session)', value: transactions.length, color: 'var(--blue)' },
          { label: 'Flagged', value: flaggedCount, color: 'var(--red)', sub: `${transactions.length ? ((flaggedCount / transactions.length) * 100).toFixed(1) : 0}% of total` },
          { label: 'Avg Risk Score', value: `${(avgRisk * 100).toFixed(1)}%`, color: 'var(--amber)', sub: 'IF + AE ensemble' },
          { label: 'Suspicious Chains', value: suspiciousChains, color: 'var(--red)', sub: 'Graph loops' },
          { label: 'Total Volume', value: fmt(totalVolume), color: 'var(--cyan)', sub: 'USD' },
        ].map((k) => (
          <div key={k.label} className={styles.kpiCard}>
            <div className={styles.kpiLabel}>{k.label}</div>
            <div className={styles.kpiValue} style={{ color: k.color }}>{k.value}</div>
            {k.sub && <div className={styles.kpiSub}>{k.sub}</div>}
          </div>
        ))}
      </div>

      <div className={styles.panels}>
        {/* Alert feed */}
        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            <span>🚨 Live Alerts</span>
          </div>
          <div className={styles.alertFeed}>
            {recentAlerts.length === 0 && (
              <p className={styles.empty}>No flagged transactions yet</p>
            )}
            {recentAlerts.map((tx) => (
              <div key={tx.tx_id} className={styles.alertRow}>
                <span style={{ fontSize: 18 }}>{tx.is_loop ? '🔄' : tx.risk_score > 0.85 ? '🚨' : '⚠️'}</span>
                <div>
                  <div className={styles.alertTitle} style={{ color: tx.risk_score > 0.8 ? 'var(--red)' : 'var(--amber)' }}>
                    {tx.is_loop ? 'Loop chain detected' : 'High-risk transaction'} — {tx.tx_id}
                  </div>
                  <div className={styles.alertDesc}>
                    {tx.from_account_id} → {tx.to_account_id} · {fmt(tx.amount)} · {tx.tx_type}
                  </div>
                  <div className={styles.alertTime}>{fmtTime(tx.timestamp)}</div>
                </div>
                <RiskBadge level={tx.risk_level} score={tx.risk_score} />
              </div>
            ))}
          </div>
        </div>

        {/* Risk score bars */}
        <div className={styles.panel}>
          <div className={styles.panelHeader}>🧠 Top Risk Scores</div>
          <div className={styles.panelBody}>
            {topRisk.map((tx) => (
              <div key={tx.tx_id} className={styles.scoreRow}>
                <div className={styles.scoreLabel}>
                  <span className={styles.mono} style={{ fontSize: 11 }}>{tx.tx_id}</span>
                  <span style={{ color: tx.risk_score > 0.65 ? 'var(--red)' : tx.risk_score > 0.35 ? 'var(--amber)' : 'var(--green)', fontWeight: 700 }}>
                    {(tx.risk_score * 100).toFixed(0)}%
                  </span>
                </div>
                <div className={styles.scoreTrack}>
                  <div
                    className={styles.scoreFill}
                    style={{
                      width: `${tx.risk_score * 100}%`,
                      background: tx.risk_score > 0.65 ? 'var(--red)' : tx.risk_score > 0.35 ? 'var(--amber)' : 'var(--green)',
                    }}
                  />
                </div>
              </div>
            ))}
            {topRisk.length === 0 && <p className={styles.empty}>Awaiting transactions...</p>}
          </div>
        </div>
      </div>
    </div>
  )
}
