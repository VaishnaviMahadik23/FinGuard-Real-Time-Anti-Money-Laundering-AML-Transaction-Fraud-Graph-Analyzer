import { useState } from 'react'
import { useStore } from '@/utils/store'
import RiskBadge from '@/components/RiskBadge'
import styles from './TransactionsPage.module.css'

type Filter = 'all' | 'low' | 'medium' | 'high'

function fmt(n: number) {
  return '$' + n.toLocaleString(undefined, { maximumFractionDigits: 0 })
}

export default function TransactionsPage() {
  const { transactions } = useStore()
  const [filter, setFilter] = useState<Filter>('all')
  const [flaggedOnly, setFlaggedOnly] = useState(false)

  const visible = transactions.filter((t) => {
    if (flaggedOnly && !t.is_flagged) return false
    if (filter !== 'all' && t.risk_level !== filter) return false
    return true
  })

  const exportCSV = () => {
    const rows = [
      'tx_id,from,to,amount,type,risk_score,risk_level,is_flagged,is_loop,pattern,timestamp',
      ...visible.map(
        (t) =>
          `${t.tx_id},${t.from_account_id},${t.to_account_id},${t.amount},${t.tx_type},` +
          `${t.risk_score},${t.risk_level},${t.is_flagged},${t.is_loop},${t.pattern ?? ''},${t.timestamp}`
      ),
    ].join('\n')
    const blob = new Blob([rows], { type: 'text/csv' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `finguard_transactions_${Date.now()}.csv`
    a.click()
  }

  return (
    <div className={styles.page}>
      <div className={styles.toolbar}>
        <span className={styles.title}>Live Transaction Feed</span>
        <div className={styles.filters}>
          {(['all', 'high', 'medium', 'low'] as Filter[]).map((f) => (
            <button
              key={f}
              className={`${styles.filterBtn} ${filter === f ? styles.active : ''}`}
              onClick={() => setFilter(f)}
            >
              {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
          <label className={styles.checkbox}>
            <input
              type="checkbox"
              checked={flaggedOnly}
              onChange={(e) => setFlaggedOnly(e.target.checked)}
            />
            Flagged only
          </label>
          <button className={styles.exportBtn} onClick={exportCSV}>⬇ Export CSV</button>
        </div>
        <span className={styles.count}>{visible.length} transactions</span>
      </div>

      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              {['ID', 'From', 'To', 'Amount', 'Type', 'IF Score', 'AE Error', 'Risk', 'Flag', 'Time'].map((h) => (
                <th key={h}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visible.slice(0, 100).map((tx) => (
              <tr key={tx.tx_id} className={tx.is_flagged ? styles.flaggedRow : ''}>
                <td className={styles.mono} style={{ fontSize: 11, color: 'var(--text3)' }}>{tx.tx_id}</td>
                <td className={styles.truncate}>{tx.from_account_id}</td>
                <td className={styles.truncate}>{tx.to_account_id}</td>
                <td style={{ color: tx.amount > 100_000 ? 'var(--amber)' : 'var(--text)', fontWeight: 600 }}>
                  {fmt(tx.amount)}
                </td>
                <td style={{ fontSize: 11, color: 'var(--text3)' }}>{tx.tx_type}</td>
                <td style={{ fontSize: 11, fontWeight: 600, color: tx.isolation_forest_score > 0.65 ? 'var(--red)' : 'var(--text2)' }}>
                  {(tx.isolation_forest_score * 100).toFixed(0)}%
                </td>
                <td style={{ fontSize: 11, color: 'var(--text3)' }}>
                  {tx.autoencoder_error.toFixed(3)}
                </td>
                <td><RiskBadge level={tx.risk_level} score={tx.risk_score} /></td>
                <td>
                  {tx.is_flagged && (
                    <span style={{ fontSize: 10, color: tx.is_loop ? '#8b5cf6' : 'var(--red)', fontWeight: 700 }}>
                      {tx.is_loop ? '🔄 LOOP' : '⚠ FLAG'}
                    </span>
                  )}
                </td>
                <td style={{ fontSize: 10, color: 'var(--text3)', fontVariantNumeric: 'tabular-nums' }}>
                  {new Date(tx.timestamp).toLocaleTimeString('en-US', { hour12: false })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
