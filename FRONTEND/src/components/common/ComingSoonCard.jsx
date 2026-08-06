import { ArrowRightIcon, SparklesIcon } from '@heroicons/react/24/outline'
import { useNavigate } from 'react-router-dom'

export function ComingSoonCard({ title, description, features = [], badge = 'Coming Soon' }) {
  const navigate = useNavigate()

  return (
    <div className="coming-soon-card" role="status">
      <div className="coming-soon-illustration" aria-hidden="true">
        <SparklesIcon className="icon icon--xl" />
      </div>
      <div className="coming-soon-copy">
        <span className="coming-soon-badge">{badge}</span>
        <h3>{title}</h3>
        <p>{description}</p>
        {features.length ? (
          <ul>
            {features.map((feature) => (
              <li key={feature}>{feature}</li>
            ))}
          </ul>
        ) : null}
      </div>
      <button type="button" className="btn btn-primary" onClick={() => navigate('/dashboard')}>
        Return to Dashboard <ArrowRightIcon className="icon icon--small" />
      </button>
    </div>
  )
}
