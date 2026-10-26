import { useMemo, useState } from 'react'

import { uploadDataFile } from './dataApi'
import type { ImportKind, ImportResult, ImportStatus } from './dataApi'

interface ImportPanelProps {
  onImported: () => void
}

const FILTERS: Array<{ value: 'all' | ImportStatus; label: string }> = [
  { value: 'all', label: 'Todas' },
  { value: 'loaded', label: 'Cargadas' },
  { value: 'corrected', label: 'Corregidas' },
  { value: 'rejected', label: 'Rechazadas' },
  { value: 'duplicate', label: 'Duplicadas' },
]

function getFilterCount(result: ImportResult, filter: 'all' | ImportStatus): number {
  const counts: Record<'all' | ImportStatus, number> = {
    all: result.total_rows,
    loaded: result.loaded_rows,
    corrected: result.corrected_rows,
    rejected: result.rejected_rows,
    duplicate: result.duplicate_rows,
  }
  return counts[filter]
}

export function ImportPanel({ onImported }: ImportPanelProps) {
  const [carriersFile, setCarriersFile] = useState<File | null>(null)
  const [ratesFile, setRatesFile] = useState<File | null>(null)
  const [historicalQuotesFile, setHistoricalQuotesFile] = useState<File | null>(null)
  const [loadingKind, setLoadingKind] = useState<ImportKind | null>(null)
  const [result, setResult] = useState<ImportResult | null>(null)
  const [filter, setFilter] = useState<'all' | ImportStatus>('all')
  const [error, setError] = useState('')

  const visibleRows = useMemo(
    () => result?.rows.filter((row) => filter === 'all' || row.status === filter) ?? [],
    [filter, result],
  )

  async function handleImport(kind: ImportKind, file: File | null) {
    if (!file) return
    setError('')
    setLoadingKind(kind)
    try {
      setResult(await uploadDataFile(kind, file))
      setFilter('all')
      onImported()
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'No fue posible procesar el archivo.',
      )
    } finally {
      setLoadingKind(null)
    }
  }

  return (
    <div className="import-layout">
      <section className="upload-panel">
        <div className="upload-panel__heading">
          <div>
            <h2>Importar archivos CSV</h2>
            <p>Cada archivo puede cargarse de forma independiente.</p>
          </div>
          <span className="upload-panel__badge">CSV</span>
        </div>

        <div className="upload-list">
          <FileImportCard
            description="Actualiza el catálogo maestro de servicios disponibles."
            file={carriersFile}
            inputLabel="Archivo de paqueterías"
            loading={loadingKind === 'carriers'}
            title="Catálogo de paqueterías"
            onFileChange={setCarriersFile}
            onImport={() => handleImport('carriers', carriersFile)}
          />
          <FileImportCard
            description="Valida zonas, pesos, precios, fechas y tiempos de entrega."
            file={ratesFile}
            inputLabel="Archivo de tarifas"
            loading={loadingKind === 'rates'}
            title="Tarifas por zona y peso"
            onFileChange={setRatesFile}
            onImport={() => handleImport('rates', ratesFile)}
          />
          <FileImportCard
            description="Registra cotizaciones realizadas fuera del cotizador y conserva su precio."
            file={historicalQuotesFile}
            inputLabel="Archivo de cotizaciones históricas"
            loading={loadingKind === 'historical-quotes'}
            title="Cotizaciones históricas"
            onFileChange={setHistoricalQuotesFile}
            onImport={() => handleImport('historical-quotes', historicalQuotesFile)}
          />
        </div>
        {error && (
          <div className="import-error" role="alert">
            {error}
          </div>
        )}
      </section>

      {result && (
        <section className="import-report" aria-label="Resultado de importación">
          {result.already_imported && (
            <div className="duplicate-file-notice" role="status">
              <strong>Este archivo ya fue importado anteriormente.</strong>
              <span>
                No se realizaron cambios. Importación original:{' '}
                {formatImportDate(result.created_at)}.
              </span>
            </div>
          )}
          <div className="import-report__header">
            <div>
              <p className="section-label">RESULTADO DE IMPORTACIÓN</p>
              <h2>{result.filename}</h2>
            </div>
            <div className="import-summary" role="status">
              <strong>{result.total_rows} filas</strong>
              <span>{result.loaded_rows} cargadas</span>
              <span>{result.corrected_rows} corregidas</span>
              <span>{result.rejected_rows} rechazadas</span>
              <span>{result.duplicate_rows} duplicadas</span>
            </div>
          </div>

          <div className="report-filters" aria-label="Filtrar resultado">
            {FILTERS.map((item) => {
              const count = getFilterCount(result, item.value)
              return (
                <button
                  className={filter === item.value ? 'is-active' : ''}
                  key={item.value}
                  type="button"
                  onClick={() => setFilter(item.value)}
                >
                  <span>{item.label}</span>
                  {count > 0 && <span className="report-filter-count">{count}</span>}
                </button>
              )
            })}
          </div>

          <div className="data-table-wrap">
            <table className="data-table import-rows-table">
              <thead>
                <tr>
                  <th>Fila</th>
                  <th>Estado</th>
                  <th>Datos recibidos</th>
                  <th>Cambios o motivo</th>
                </tr>
              </thead>
              <tbody>
                {visibleRows.map((row) => (
                  <tr key={row.row_number}>
                    <td>{row.row_number}</td>
                    <td>
                      <StatusBadge status={row.status} />
                    </td>
                    <td className="raw-data-cell">{formatRecord(row.raw_data)}</td>
                    <td>{(row.reason ?? row.changes.join(' ')) || 'Sin cambios.'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  )
}

interface FileImportCardProps {
  title: string
  description: string
  inputLabel: string
  file: File | null
  loading: boolean
  onFileChange: (file: File | null) => void
  onImport: () => void
}

function FileImportCard(props: FileImportCardProps) {
  return (
    <article className="file-import-card">
      <div>
        <h3>{props.title}</h3>
        <p>{props.description}</p>
      </div>
      <label className="file-picker">
        <span>{props.file?.name ?? 'Seleccionar archivo CSV'}</span>
        <input
          accept=".csv,text/csv"
          aria-label={props.inputLabel}
          type="file"
          onChange={(event) => props.onFileChange(event.target.files?.[0] ?? null)}
        />
      </label>
      <button
        className="compact-primary-button"
        disabled={!props.file || props.loading}
        type="button"
        onClick={props.onImport}
      >
        {props.loading ? 'Procesando…' : 'Cargar archivo'}
      </button>
    </article>
  )
}

function StatusBadge({ status }: { status: ImportStatus }) {
  const labels: Record<ImportStatus, string> = {
    loaded: 'Cargada',
    corrected: 'Corregida',
    rejected: 'Rechazada',
    duplicate: 'Duplicada',
  }
  return <span className={`status-badge status-badge--${status}`}>{labels[status]}</span>
}

function formatRecord(record: Record<string, unknown>): string {
  return Object.entries(record)
    .map(([key, value]) => `${key}: ${String(value || '—')}`)
    .join(' · ')
}

function formatImportDate(value: string): string {
  return new Intl.DateTimeFormat('es-MX', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}
