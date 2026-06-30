import styles from './RiskBadge.module.css'

interface Props {
  level: 'low' | 'medium' | 'high'
  score?: number
}

export default function RiskBadge({ level, score }: Props) {
  return (
    <span className={`${styles.badge} ${styles[level]}`}>
      {score !== undefined ? `${(score * 100).toFixed(0)}%` : level.toUpperCase()}
    </span>
  )
}
