import { useRef, useState } from 'react'
import { ErrorBanner } from '../feedback/ErrorBanner'
import { getApiErrorMessage } from '../../services/api'
import {
  confirmBulkImport,
  downloadBulkImportTemplate,
  previewBulkImport,
} from '../../services/bulkImportService'

const MAX_FILE_SIZE = 2 * 1024 * 1024

function formatRowSummary(summary = {}) {
  return Object.entries(summary)
    .filter(([, value]) => value !== '')
    .map(([key, value]) => `${key.replaceAll('_', ' ')}: ${value}`)
    .join(' · ')
}

export function ExcelImportPanel({
  title,
  templateUrl,
  previewUrl,
  confirmUrl,
  filename,
  instructions,
  onCompleted,
}) {
  const fileInput = useRef(null)
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [completion, setCompletion] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function downloadTemplate() {
    setError('')
    try {
      await downloadBulkImportTemplate(templateUrl, filename)
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  async function showPreview(event) {
    event.preventDefault()
    setError('')
    setCompletion(null)
    setPreview(null)
    if (!file) {
      setError('Choose an .xlsx file to preview.')
      return
    }
    if (file.size > MAX_FILE_SIZE) {
      setError('The selected file exceeds the 2 MB upload limit.')
      return
    }
    setBusy(true)
    try {
      setPreview(await previewBulkImport(previewUrl, file))
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function confirmImport() {
    if (!file || !preview?.import_token || preview.valid_count < 1) return
    const accepted = window.confirm(
      `Import ${preview.valid_count} valid ${title.toLowerCase()} row(s)? Invalid rows will not be saved.`,
    )
    if (!accepted) return
    setBusy(true)
    setError('')
    try {
      const result = await confirmBulkImport(confirmUrl, file, preview.import_token)
      setCompletion(result)
      setPreview(null)
      setFile(null)
      if (fileInput.current) fileInput.current.value = ''
      await onCompleted?.(result)
    } catch (err) {
      setPreview(null)
      setError(getApiErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="panel-card record-panel" aria-label={`${title} Excel import`}>
      <div className="section-header">
        <div>
          <p className="eyebrow">Excel bulk import</p>
          <h2>{title}</h2>
          {instructions ? <p>{instructions}</p> : null}
        </div>
        <button className="action-button action-button--secondary" type="button" onClick={downloadTemplate} disabled={busy}>
          Download template
        </button>
      </div>

      {error ? <ErrorBanner message={error} /> : null}
      {completion ? (
        <div className="success-banner" role="status">
          Imported {completion.imported_count} row(s). Rejected {completion.rejected_count} row(s).
          {completion.rejected_rows?.length ? (
            <ul>
              {completion.rejected_rows.map((row) => (
                <li key={row.row}>Row {row.row}: {row.errors.join(' ')}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}

      <form className="section-actions" onSubmit={showPreview}>
        <label className="form-field">
          <span className="form-field__label">Excel workbook (.xlsx, maximum 2 MB)</span>
          <input
            ref={fileInput}
            type="file"
            accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            onChange={(event) => {
              setFile(event.target.files?.[0] || null)
              setPreview(null)
              setCompletion(null)
              setError('')
            }}
            disabled={busy}
          />
        </label>
        <button className="action-button action-button--primary" type="submit" disabled={busy || !file}>
          {busy ? 'Please wait...' : 'Preview workbook'}
        </button>
      </form>

      {preview ? (
        <div className="import-preview" aria-live="polite">
          <p>
            Preview: {preview.valid_count} valid row(s), {preview.rejected_count} rejected row(s).
          </p>
          <div className="table-card">
            <table className="records-table">
              <thead>
                <tr><th scope="col">Row</th><th scope="col">Record</th><th scope="col">Status and validation</th></tr>
              </thead>
              <tbody>
                {preview.rows.map((row) => (
                  <tr key={row.row}>
                    <td>{row.row}</td>
                    <td>{formatRowSummary(row.summary)}</td>
                    <td>
                      <strong>{row.status === 'valid' ? 'Valid' : 'Invalid'}</strong>
                      {row.errors?.length ? <ul>{row.errors.map((message, index) => <li key={`${row.row}-${index}`}>{message}</li>)}</ul> : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button
            className="action-button action-button--primary"
            type="button"
            onClick={confirmImport}
            disabled={busy || !preview.import_token || preview.valid_count < 1}
          >
            Import {preview.valid_count} valid row(s)
          </button>
        </div>
      ) : null}
    </section>
  )
}
