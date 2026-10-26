import { useEffect, useState } from 'react'

import { getCapturedLeads } from './dataApi'
import type { CapturedLead } from './dataApi'

export function CapturedLeadsPanel() {
  const [leads, setLeads] = useState<CapturedLead[] | null>(null)
  const [selectedLead, setSelectedLead] = useState<CapturedLead | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    getCapturedLeads()
      .then((response) => {
        if (active) setLeads(response.leads)
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
  if (!leads) return <div className="workspace-message">Consultando leads capturados…</div>

  const quoteCount = leads.reduce((total, lead) => total + lead.quotes.length, 0)

  return (
    <section className="leads-panel">
      <div className="loaded-data-panel__header">
        <div>
          <h2>Leads capturados</h2>
          <p>Un correo representa un lead y puede tener varias cotizaciones.</p>
        </div>
        <div className="loaded-counts">
          <span><strong>{leads.length}</strong> leads</span>
          <span><strong>{quoteCount}</strong> cotizaciones</span>
        </div>
      </div>

      {leads.length === 0 ? (
        <div className="leads-empty">
          <strong>Aún no hay leads capturados.</strong>
          <span>Cuando una persona cotice desde la landing, aparecerá aquí.</span>
        </div>
      ) : (
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
              {leads.map((lead) => (
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
      )}

      {selectedLead && (
        <LeadQuotesModal lead={selectedLead} onClose={() => setSelectedLead(null)} />
      )}
    </section>
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
      <td>{latestQuote ? formatDate(latestQuote.created_at) : 'Sin cotizaciones'}</td>
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
              <strong>{quote.origin_postal_code} → {quote.destination_postal_code}</strong>
              <span>{formatNumber(quote.weight_kg)} kg · Zona {quote.zone}</span>
              <span>{formatNumber(quote.distance_km)} km · {quote.option_count} opciones</span>
              <small>{formatDate(quote.created_at)}</small>
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
