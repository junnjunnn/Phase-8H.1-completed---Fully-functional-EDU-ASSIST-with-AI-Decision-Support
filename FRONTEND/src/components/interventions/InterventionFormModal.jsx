import { useEffect, useMemo, useRef, useState } from 'react'
import { createIntervention, updateIntervention } from '../../services/interventionService'
import { getApiErrorMessage } from '../../services/api'
import { getUsers } from '../../services/userService'

const STATUS_OPTIONS = [
  { value: 'planned', label: 'Planned' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
]

const PRIORITY_OPTIONS = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
]

function normalizeListResponse(data) {
  const items = data?.results || data || []
  return {
    items,
    count: typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0,
  }
}

export function InterventionFormModal({
  isOpen,
  onClose,
  currentValue,
  studentName,
  latestPrediction,
  latestPredictionFactors,
  enrollmentId,
  onSaved,
}) {
  const [form, setForm] = useState({
    title: '',
    intervention_type: 'Academic Monitoring',
    assigned_personnel: '',
    recommendation: '',
    start_date: '',
    end_date: '',
    priority: 'medium',
    status: 'planned',
    notes: '',
  })
  const [staff, setStaff] = useState([])
  const [loadingStaff, setLoadingStaff] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!isOpen) {
      return
    }

    async function loadStaff() {
      setLoadingStaff(true)
      try {
        const usersData = await getUsers()
        const normalized = normalizeListResponse(usersData)
        setStaff(normalized.items)
      } catch (err) {
        setError(getApiErrorMessage(err))
      } finally {
        setLoadingStaff(false)
      }
    }

    loadStaff()
  }, [isOpen])

  // Avoid unnecessary setState loops by only applying when the next form differs
  const _lastAppliedForm = useRef(null)
  useEffect(() => {
    if (!isOpen) return

    const nextForm = currentValue
      ? {
          title: currentValue.title || currentValue.recommendation || '',
          intervention_type: currentValue.intervention_type || 'Academic Monitoring',
          assigned_personnel: currentValue.assigned_personnel || '',
          recommendation: currentValue.recommendation || '',
          start_date: currentValue.start_date || '',
          end_date: currentValue.end_date || '',
          priority: currentValue.priority || 'medium',
          status: currentValue.status || 'planned',
          notes: currentValue.notes || '',
        }
      : {
          title: '',
          intervention_type: 'Academic Monitoring',
          assigned_personnel: '',
          recommendation: latestPrediction?.explanation || '',
          start_date: '',
          end_date: '',
          priority: 'medium',
          status: 'planned',
          notes: '',
        }

    const last = _lastAppliedForm.current
    const changed = JSON.stringify(last) !== JSON.stringify(nextForm)
    if (changed) {
      setForm(nextForm)
      _lastAppliedForm.current = nextForm
    }
  }, [currentValue, isOpen, latestPrediction])

  const recommendedActions = useMemo(() => {
    if (!latestPrediction?.risk_level) {
      return ['Monitor the student closely and review supporting academic and attendance records.']
    }

    if (latestPrediction.risk_level === 'High') {
      return ['Immediate parent conference', 'Academic remediation', 'Counseling referral', 'Attendance monitoring']
    }

    if (latestPrediction.risk_level === 'Moderate') {
      return ['Weekly monitoring', 'Teacher consultation', 'Targeted tutoring']
    }

    return ['Continue monitoring', 'Positive reinforcement']
  }, [latestPrediction])

  async function handleSubmit(event) {
    event.preventDefault()
    setSaving(true)
    setError('')

    try {
      const payload = {
        enrollment: enrollmentId,
        risk_type: latestPrediction?.risk_level || 'Academic Risk',
        intervention_type: form.intervention_type,
        recommendation: form.recommendation || form.title || 'Intervention planned',
        assigned_personnel: form.assigned_personnel ? Number(form.assigned_personnel) : null,
        status: form.status,
        priority: form.priority,
        notes: form.notes,
        start_date: form.start_date,
        end_date: form.end_date,
      }

      if (currentValue?.id) {
        await updateIntervention(currentValue.id, payload)
      } else {
        await createIntervention(payload)
      }

      onSaved?.()
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  if (!isOpen) {
    return null
  }

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="intervention-form-title">
      <div className="modal-card">
        <div className="section-header">
          <div>
            <p className="eyebrow">Intervention workflow</p>
            <h2 id="intervention-form-title">{currentValue?.id ? 'Update intervention' : 'Create intervention'}</h2>
          </div>
          <button type="button" className="action-button action-button--secondary" onClick={onClose}>
            Close
          </button>
        </div>

        <div className="record-summary-grid">
          <article className="detail-card">
            <p className="stat-label">Student</p>
            <p className="stat-value">{studentName}</p>
          </article>
          <article className="detail-card">
            <p className="stat-label">Prediction</p>
            <p className="stat-value">{latestPrediction?.risk_level || 'Not available'}</p>
          </article>
          <article className="detail-card">
            <p className="stat-label">Probability</p>
            <p className="stat-value">{latestPrediction?.probability != null ? `${Math.round(latestPrediction.probability * 100)}%` : '—'}</p>
          </article>
        </div>

        <div className="detail-card">
          <p className="eyebrow">AI decision support</p>
          <ul className="support-list">
            {recommendedActions.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>

        <form className="form-grid intervention-form-grid" onSubmit={handleSubmit}>
          <label>
            <span>Intervention title</span>
            <input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} required />
          </label>

          <label>
            <span>Intervention type</span>
            <select value={form.intervention_type} onChange={(event) => setForm({ ...form, intervention_type: event.target.value })}>
              <option value="Academic Monitoring">Academic Monitoring</option>
              <option value="Tutoring">Tutoring</option>
              <option value="Counseling">Counseling</option>
              <option value="Parent/Guardian Conference">Parent/Guardian Conference</option>
              <option value="Attendance Monitoring">Attendance Monitoring</option>
              <option value="Mentoring">Mentoring</option>
              <option value="Guidance Referral">Guidance Referral</option>
              <option value="Behavioral Monitoring">Behavioral Monitoring</option>
            </select>
          </label>

          <label>
            <span>Assigned teacher/counselor</span>
            <select value={form.assigned_personnel} onChange={(event) => setForm({ ...form, assigned_personnel: event.target.value })}>
              <option value="">Unassigned</option>
              {loadingStaff ? <option value="">Loading staff...</option> : null}
              {staff.map((person) => (
                <option key={person.id} value={person.id}>{person.username}</option>
              ))}
            </select>
          </label>

          <label>
            <span>Priority</span>
            <select value={form.priority} onChange={(event) => setForm({ ...form, priority: event.target.value })}>
              {PRIORITY_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>

          <label>
            <span>Status</span>
            <select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}>
              {STATUS_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>

          <label>
            <span>Start date</span>
            <input type="date" value={form.start_date} onChange={(event) => setForm({ ...form, start_date: event.target.value })} />
          </label>

          <label>
            <span>Target completion date</span>
            <input type="date" value={form.end_date} onChange={(event) => setForm({ ...form, end_date: event.target.value })} />
          </label>

          <label className="form-grid-full">
            <span>Recommendation</span>
            <textarea rows="3" value={form.recommendation} onChange={(event) => setForm({ ...form, recommendation: event.target.value })} />
          </label>

          <label className="form-grid-full">
            <span>Notes</span>
            <textarea rows="3" value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} />
          </label>

          <div className="form-grid-full">
            <div className="detail-card">
              <p className="eyebrow">Latest AI explanation</p>
              <p>{latestPrediction?.explanation || 'No explanation was stored for this prediction.'}</p>
              {latestPredictionFactors?.length ? (
                <ul className="support-list">
                  {latestPredictionFactors.slice(0, 4).map((factor) => (
                    <li key={factor.id}>{factor.feature_name}: {factor.feature_value}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          </div>

          {error ? <div className="status-banner status-banner--warning form-grid-full">{error}</div> : null}

          <div className="grade-encoding-actions form-grid-full">
            <button type="submit" className="action-button" disabled={saving}>
              {saving ? 'Saving...' : currentValue?.id ? 'Update intervention' : 'Create intervention'}
            </button>
            <button type="button" className="action-button action-button--secondary" onClick={onClose}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
