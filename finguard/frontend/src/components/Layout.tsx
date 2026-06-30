import { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { useStore } from '@/utils/store'
import styles from './Layout.module.css'

const NAV = [
  { to: '/',             icon: '📊', label: 'Dashboard' },
  { to: '/graph',        icon: '🕸️',  label: 'Graph Explorer' },
  { to: '/transactions', icon: '📋', label: 'Transactions', badge: true },
  { to: '/ai',           icon: '🤖', label: 'AI Analyst' },
]

export default function Layout({ children }: { children: ReactNode }) {
  const { isConnected, flaggedCount } = useStore()

  return (
    <div className={styles.shell}>
      {/* ── Header ── */}
      <header className={styles.header}>
        <div className={styles.logo}>
          <span className={styles.logoIcon}>🛡️</span>
          FinGuard AML
          <span className={styles.version}>v2.4.1</span>
        </div>
        <div className={styles.statusBar}>
          <span className={styles.statusPill} data-online={isConnected}>
            <span className={styles.dot} />
            {isConnected ? 'LIVE' : 'OFFLINE'}
          </span>
          <span className={styles.clock}>{new Date().toLocaleTimeString()}</span>
        </div>
      </header>

      <div className={styles.body}>
        {/* ── Sidebar ── */}
        <nav className={styles.sidebar}>
          <div className={styles.navGroup}>
            <div className={styles.navLabel}>Monitor</div>
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  [styles.navItem, isActive ? styles.active : ''].join(' ')
                }
              >
                <span>{item.icon}</span>
                {item.label}
                {item.badge && flaggedCount > 0 && (
                  <span className={styles.badge}>{flaggedCount}</span>
                )}
              </NavLink>
            ))}
          </div>
        </nav>

        {/* ── Main content ── */}
        <main className={styles.main}>{children}</main>
      </div>
    </div>
  )
}
