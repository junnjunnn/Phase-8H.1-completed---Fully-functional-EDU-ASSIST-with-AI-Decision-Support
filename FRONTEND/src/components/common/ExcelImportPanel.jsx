import { useRef, useState } from 'react'
import { ErrorBanner } from '../feedback/ErrorBanner'
import { getApiErrorMessage } from '../../services/api'
import {
  confirmBulkImport,
  downloadBulkImportTemplate,
  previewBulkImport,
} from '../../services/bulkImportService'

const MAX_FILE_SIZE = 2 * 1024 * 1024

function formatRowSummary(row = {}) {
  const summary = row.summary || {
    lrn: row.lrn,
    student: [row.first_name, row.last_name].filter(Boolean).join(' '),
  }
  return Object.entries(summary)
    .filter(([, value]) => value !== '' && value !== null && value !== undefined)
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

  function clearFile() {
    setFile(null)
    setPreview(null)
    setCompletion(null)
    setError('')
    if (fileInput.current) fileInput.current.value = ''
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
      `Import ${preview.valid_count} valid ${title.toLowerCase()} row(s)? Invalid rows will be skipped.`,
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
    <section className="bulk-import-panel" aria-label={`${title} Excel import`} aria-busy={busy}>
      <div className="bulk-import-toolbar">
        <div className="bulk-import-heading">
          <h2>{title}</h2>
          <p>Upload a workbook to preview records before importing.</p>
        </div>
        <div className="bulk-import-actions">
          <button className="action-button action-button--secondary" type="button" onClick={downloadTemplate} disabled={busy}>
            Download template
          </button>
          <label className="action-button action-button--secondary bulk-import-file-picker">
            <span>{file ? 'Change workbook' : 'Choose workbook'}</span>
            <input
              ref={fileInput}
              type="file"
              accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              onClick={(event) => { event.currentTarget.value = '' }}
              onChange={(event) => {
                setFile(event.target.files?.[0] || null)
                setPreview(null)
                setCompletion(null)
                setError('')
              }}
              disabled={busy}
              aria-label={`Choose ${title.toLowerCase()} Excel workbook`}
            />
          </label>
        </div>
      </div>

      {file ? (
        <form className="bulk-import-file-row" onSubmit={showPreview}>
          <p className="bulk-import-filename" title={file.name}>
            <span>Selected workbook</span>
            <strong>{file.name}</strong>
          </p>
          <div className="bulk-import-actions">
            <button className="action-button action-button--primary" type="submit" disabled={busy}>
              {busy ? 'Validating...' : 'Preview workbook'}
            </button>
            <button className="action-button action-button--outline" type="button" onClick={clearFile} disabled={busy}>
              Remove
            </button>
          </div>
        </form>
      ) : null}

      <div className="bulk-import-guidance">
        <p>Download the .xlsx template and open its Instructions and Example worksheets before filling it in.</p>
        <p>Edit only the first worksheet. Keep its column names and order unchanged; the Example worksheet is never imported.</p>
        <p>Upload an .xlsx workbook no larger than 2 MB, preview it, correct any rejected rows, and preview again. Only valid rows are imported.</p>
        {instructions ? <p>{instructions}</p> : null}
      </div>

      {error ? <ErrorBanner message={error} /> : null}
      {completion ? (
        <div className="success-banner bulk-import-success" role="status">
          <p>Imported {completion.imported_count} row(s). Rejected {completion.rejected_count} row(s).</p>
          {completion.rejected_rows?.length ? (
            <details>
              <summary>Review rejected rows</summary>
              <ul>
                {completion.rejected_rows.map((row) => (
                  <li key={row.row}>Row {row.row}: {row.errors.join(' ')}</li>
                ))}
              </ul>
            </details>
          ) : null}
        </div>
      ) : null}

      {preview ? (
        <div className="bulk-import-preview" aria-live="polite">
          <div className="bulk-import-counts">
            <p><strong>{preview.valid_count ?? 0}</strong><span>Valid rows</span></p>
            <p><strong>{preview.rejected_count ?? 0}</strong><span>Need correction</span></p>
          </div>
          <p className="bulk-import-consequence">Only valid rows will be imported; rows with errors will be skipped.</p>
          {preview.rows.length ? (
            <div className="table-card bulk-import-table">
              <table className="records-table">
                <thead>
                  <tr><th scope="col">Row</th><th scope="col">Record</th><th scope="col">Validation</th></tr>
                </thead>
                <tbody>
                  {preview.rows.map((row) => (
                    <tr key={row.row}>
                      <td>{row.row}</td>
                      <td>{formatRowSummary(row)}</td>
                      <td>
                        {row.status === 'valid' ? <strong>Valid</strong> : (
                          <details>
                            <summary>Review {row.errors?.length || 0} issue(s)</summary>
                            {row.errors?.length ? <ul>{row.errors.map((message, index) => <li key={`${row.row}-${index}`}>{message}</li>)}</ul> : null}
                          </details>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <p className="bulk-import-consequence">No data rows were found in this workbook.</p>}
          <button
            className="action-button action-button--primary"
            type="button"
            onClick={confirmImport}
            disabled={busy || !preview.import_token || preview.valid_count < 1}
          >
            {busy ? 'Importing...' : `Import ${preview.valid_count} valid row(s)`}
          </button>
        </div>
      ) : null}
    </section>
  )
}
