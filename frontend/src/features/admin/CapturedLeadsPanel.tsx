import { useEffect, useState } from 'react'

import { getCapturedLeads } from './dataApi'
import type { CapturedLead } from './dataApi'

export function CapturedLeadsPanel() {
  const [data, setData] = useState<Awaited<ReturnType<typeof getCapturedLeads>> | null>(null)
  const [activeView, setActiveView] = useState<'dashboard' | 'directory'>('dashboard')
  const [directoryFilter, setDirectoryFilter] = useState<'all' | 'without-options'>('all')
  const [selectedLead, setSelectedLead] = useState<CapturedLead | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    getCapturedLeads()
      .then((response) => {
        if (active) setData(response)
      })
      .catch((requestError) => {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : 'No fue posible consultar los leads.',
          )
        }
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (!selectedLead) return

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') setSelectedLead(null)
    }

    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [selectedLead])

  if (error) return <div className="workspace-message is-error">{error}</div>
  if (!data) return <div className="workspace-message">Consultando leads capturados…</div>

  const { leads, daily_metrics: dailyMetrics } = data
  const quotes = leads.flatMap((lead) => lead.quotes)
  const quoteCount = quotes.length
  const historicalCount = quotes.filter((quote) => quote.source === 'historical').length
  const withoutOptions = quotes.filter((quote) => quote.option_count === 0).length
  const visibleLeads = directoryFilter === 'without-options'
    ? leads.filter((lead) => lead.quotes.some((quote) => quote.option_count === 0))
    : leads

  return (
    <section className="leads-panel">
      <div className="loaded-data-panel__header">
        <div>
          <h2>Leads capturados</h2>
          <p>Un correo representa un lead y puede tener varias cotizaciones.</p>
        </div>
      </div>

      <div className="data-subtabs leads-subtabs">
        <button
          className={activeView === 'dashboard' ? 'is-active' : ''}
          type="button"
          onClick={() => setActiveView('dashboard')}
        >
          Resumen
        </button>
        <button
          className={activeView === 'directory' ? 'is-active' : ''}
          type="button"
          onClick={() => {
            setDirectoryFilter('all')
            setActiveView('directory')
          }}
        >
          Directorio de leads
        </button>
      </div>

      {activeView === 'dashboard' ? (
        <LeadsDashboard
          dailyMetrics={dailyMetrics}
          historicalCount={historicalCount}
          leadCount={leads.length}
          quoteCount={quoteCount}
          withoutOptions={withoutOptions}
          onViewWithoutOptions={() => {
            setDirectoryFilter('without-options')
            setActiveView('directory')
          }}
        />
      ) : leads.length === 0 ? (
          <div className="leads-empty">
            <strong>Aún no hay leads capturados.</strong>
            <span>Cuando una persona cotice desde la landing, aparecerá aquí.</span>
          </div>
      ) : (
        <>
          {directoryFilter === 'without-options' && (
            <div className="leads-filter-notice" role="status">
              <span>
                Mostrando {visibleLeads.length} {visibleLeads.length === 1 ? 'lead' : 'leads'} con
                cotizaciones sin opciones.
              </span>
              <button type="button" onClick={() => setDirectoryFilter('all')}>Mostrar todos</button>
            </div>
          )}
          <div className="data-table-wrap leads-table-wrap">
            <table className="data-table">
            <thead>
              <tr>
                <th>Correo</th>
                <th>Cotizaciones</th>
                <th>Última cotización</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {visibleLeads.map((lead) => (
                <LeadRow
                  key={lead.id}
                  lead={lead}
                  latestQuote={lead.quotes[0]}
                  onView={() => setSelectedLead(lead)}
                />
              ))}
            </tbody>
            </table>
          </div>
        </>
      )}

      {selectedLead && (
        <LeadQuotesModal lead={selectedLead} onClose={() => setSelectedLead(null)} />
      )}
    </section>
  )
}

function LeadsDashboard({
  dailyMetrics,
  historicalCount,
  leadCount,
  quoteCount,
  withoutOptions,
  onViewWithoutOptions,
}: {
  dailyMetrics: Awaited<ReturnType<typeof getCapturedLeads>>['daily_metrics']
  historicalCount: number
  leadCount: number
  quoteCount: number
  withoutOptions: number
  onViewWithoutOptions: () => void
}) {
  const maximumDailyQuotes = Math.max(...dailyMetrics.map((metric) => metric.total_quotes), 1)
  const publicCount = quoteCount - historicalCount
  const successRate = quoteCount === 0 ? 0 : Math.round(((quoteCount - withoutOptions) / quoteCount) * 100)

  return (
    <div className="leads-dashboard">
      <div className="leads-kpis">
        <DashboardMetric label="Leads únicos" value={leadCount} />
        <DashboardMetric label="Cotizaciones" value={quoteCount} />
        <DashboardMetric label="Con opciones" suffix="%" value={successRate} />
        <DashboardMetric
          actionLabel="Ver casos"
          label="Sin opciones"
          onAction={onViewWithoutOptions}
          value={withoutOptions}
          warning={withoutOptions > 0}
        />
      </div>

      <div className="leads-dashboard__grid">
        <section className="dashboard-card dashboard-card--daily">
          <div className="dashboard-card__heading">
            <div>
              <h3>Cotizaciones por día</h3>
              <p>Total generado y casos sin opciones.</p>
            </div>
            <span>Últimas {dailyMetrics.length} fechas</span>
          </div>
          {dailyMetrics.length === 0 ? (
            <div className="dashboard-empty">Aún no hay actividad para mostrar.</div>
          ) : (
            <div className="daily-chart">
              {dailyMetrics.slice(0, 12).reverse().map((metric) => (
                <div className="daily-chart__item" key={metric.date}>
                  <div className="daily-chart__bars">
                    <span
                      className="daily-chart__total"
                      style={{ height: `${Math.max((metric.total_quotes / maximumDailyQuotes) * 100, 8)}%` }}
                    />
                    {metric.without_options > 0 && (
                      <span
                        className="daily-chart__empty"
                        style={{ height: `${(metric.without_options / maximumDailyQuotes) * 100}%` }}
                      />
                    )}
                  </div>
                  <strong>{metric.total_quotes}</strong>
                  <small>{formatDay(metric.date)}</small>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="dashboard-card dashboard-card--source">
          <div className="dashboard-card__heading">
            <div>
              <h3>Origen</h3>
              <p>Cómo se registraron las cotizaciones.</p>
            </div>
          </div>
          <SourceMetric count={historicalCount} label="Cargadas manualmente" total={quoteCount} />
          <SourceMetric count={publicCount} label="Cotizador público" total={quoteCount} />
          <div className="dashboard-note">
            <strong>{historicalCount}</strong>
            <span>cotizaciones manuales con su precio original respetado</span>
          </div>
        </section>
      </div>
    </div>
  )
}

function DashboardMetric({
  label,
  actionLabel,
  onAction,
  suffix = '',
  value,
  warning = false,
}: {
  label: string
  actionLabel?: string
  onAction?: () => void
  suffix?: string
  value: number
  warning?: boolean
}) {
  return (
    <article className={`leads-kpi${warning ? ' leads-kpi--warning' : ''}`}>
      <span>{label}</span>
      <strong>{value}{suffix}</strong>
      {actionLabel && onAction && value > 0 && (
        <button type="button" onClick={onAction}>{actionLabel} →</button>
      )}
    </article>
  )
}

function SourceMetric({ count, label, total }: { count: number; label: string; total: number }) {
  const percentage = total === 0 ? 0 : Math.round((count / total) * 100)
  return (
    <div className="source-metric">
      <div><span>{label}</span><strong>{count}</strong></div>
      <div className="source-metric__track"><span style={{ width: `${percentage}%` }} /></div>
      <small>{percentage}% del total</small>
    </div>
  )
}

function LeadRow({
  lead,
  latestQuote,
  onView,
}: {
  lead: CapturedLead
  latestQuote: CapturedLead['quotes'][number] | undefined
  onView: () => void
}) {
  return (
    <tr>
      <td><strong>{lead.email}</strong></td>
      <td>{lead.quotes.length}</td>
      <td>{latestQuote ? formatDate(latestQuote.quoted_at) : 'Sin cotizaciones'}</td>
      <td>
        <button className="table-action" disabled={!latestQuote} type="button" onClick={onView}>
          Ver cotizaciones
        </button>
      </td>
    </tr>
  )
}

function LeadQuotesModal({ lead, onClose }: { lead: CapturedLead; onClose: () => void }) {
  return (
    <div className="lead-quotes-backdrop">
      <section
        aria-labelledby="lead-quotes-title"
        aria-modal="true"
        className="lead-quotes-modal"
        role="dialog"
      >
        <button
          aria-label="Cerrar historial de cotizaciones"
          className="quote-modal__close"
          type="button"
          onClick={onClose}
        >
          <span aria-hidden="true">×</span>
        </button>
        <div className="lead-quotes-modal__header">
          <span>HISTORIAL DEL LEAD</span>
          <h3 id="lead-quotes-title">Cotizaciones del lead</h3>
          <p className="lead-quotes-modal__email">{lead.email}</p>
          <p>{lead.quotes.length} {lead.quotes.length === 1 ? 'cotización registrada' : 'cotizaciones registradas'}</p>
        </div>
        <div className="quote-history">
          {lead.quotes.map((quote) => (
            <article key={quote.id}>
              <strong>{quote.external_reference} · {quote.origin_postal_code} → {quote.destination_postal_code}</strong>
              <span>{formatNumber(quote.weight_kg)} kg · Zona {quote.zone}</span>
              <span>
                {quote.distance_km ? `${formatNumber(quote.distance_km)} km · ` : ''}
                {quote.source === 'historical' ? 'Capturada por Comercial' : 'Cotizador público'}
              </span>
              {quote.options.map((option) => (
                <span className="quote-history__option" key={`${quote.id}-${option.carrier_name}`}>
                  {option.carrier_name} · ${formatMoney(option.price_mxn)}
                  {option.min_delivery_days !== null
                    ? ` · ${formatDelivery(option.min_delivery_days, option.max_delivery_days)}`
                    : ''}
                </span>
              ))}
              {quote.option_count === 0 && (
                <span className="quote-history__no-option">
                  Sin opciones disponibles · requiere seguimiento
                </span>
              )}
              <small>
                Cotizada {formatDate(quote.quoted_at)} · precio vigente hasta {formatDate(quote.valid_until)}
              </small>
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('es-MX', { dateStyle: 'medium', timeStyle: 'short' }).format(
    new Date(value),
  )
}

function formatNumber(value: string): string {
  return Number(value).toLocaleString('es-MX', { maximumFractionDigits: 3 })
}

function formatMoney(value: string): string {
  return Number(value).toLocaleString('es-MX', { minimumFractionDigits: 2 })
}

function formatDelivery(minimum: number, maximum: number | null): string {
  if (maximum === null || minimum === maximum) return `${minimum} ${minimum === 1 ? 'día' : 'días'}`
  return `${minimum}–${maximum} días`
}

function formatDay(value: string): string {
  return new Intl.DateTimeFormat('es-MX', { day: '2-digit', month: 'short' }).format(
    new Date(`${value}T12:00:00`),
  )
}
