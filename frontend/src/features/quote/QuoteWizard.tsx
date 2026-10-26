import { FormEvent, useEffect, useState } from 'react'

import { requestQuote } from './quoteApi'
import type { QuoteOption, QuoteResult } from './quoteApi'

const TOTAL_STEPS = 3

export function QuoteWizard({ onClose }: { onClose: () => void }) {
  const [step, setStep] = useState(1)
  const [email, setEmail] = useState('')
  const [originPostalCode, setOriginPostalCode] = useState('')
  const [destinationPostalCode, setDestinationPostalCode] = useState('')
  const [weight, setWeight] = useState('')
  const [result, setResult] = useState<QuoteResult | null>(null)
  const [selectedRateId, setSelectedRateId] = useState<number | null>(null)
  const [actionNotice, setActionNotice] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const progress = result ? 100 : (step / TOTAL_STEPS) * 100

  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }

    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [onClose])

  function handlePostalCode(value: string, update: (postalCode: string) => void) {
    update(value.replace(/\D/g, '').slice(0, 5))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    if (step < TOTAL_STEPS) {
      setStep((current) => current + 1)
      return
    }
    setSubmitting(true)
    try {
      const quote = await requestQuote({
        email,
        origin_postal_code: originPostalCode,
        destination_postal_code: destinationPostalCode,
        weight_kg: weight,
      })
      setResult(quote)
      setSelectedRateId(quote.options[0]?.rate_id ?? null)
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'No pudimos completar la cotización. Intenta nuevamente.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  function reset() {
    setStep(1)
    setEmail('')
    setOriginPostalCode('')
    setDestinationPostalCode('')
    setWeight('')
    setResult(null)
    setSelectedRateId(null)
    setActionNotice('')
    setError('')
  }

  function showUpcomingAction(action: 'pago' | 'correo') {
    setActionNotice(
      action === 'pago'
        ? 'Esta acción continuaría al proceso de pago actual de Manuable.'
        : `Esta acción enviaría la cotización mediante el proceso actual de Manuable a ${email}.`,
    )
  }

  return (
    <div className="quote-modal-backdrop">
      <section
        aria-describedby="quote-wizard-description"
        aria-labelledby="quote-wizard-title"
        aria-modal="true"
        className={`quote-modal${result ? ' quote-modal--complete' : ''}`}
        role="dialog"
      >
        <button
          aria-label="Cerrar cotizador"
          className="quote-modal__close"
          type="button"
          onClick={onClose}
        >
          <span aria-hidden="true">×</span>
        </button>
        <div className="quote-modal__accent" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>

        <div className="quote-modal__body">
          <p className="section-label">COTIZA EN POCOS PASOS</p>
          <h2 id="quote-wizard-title">Cotiza tu envío en 2 clics</h2>
          <p id="quote-wizard-description">
            Danos los datos esenciales y te mostraremos las opciones disponibles.
          </p>

          <div className="quote-progress" aria-label={`Paso ${step} de ${TOTAL_STEPS}`}>
            <div className="quote-progress__labels">
              <span>{result ? 'Cotización lista' : `Paso ${step} de ${TOTAL_STEPS}`}</span>
              <strong>{Math.round(progress)}%</strong>
            </div>
            <div className="quote-progress__track">
              <span style={{ width: `${progress}%` }} />
            </div>
          </div>

          {result ? (
            <div className="quote-complete quote-step" key="complete">
              <span className="quote-complete__check" aria-hidden="true">✓</span>
              <h3>
                {result.options.length > 0
                  ? `Encontramos ${result.options.length} ${result.options.length === 1 ? 'opción' : 'opciones'}`
                  : 'No encontramos una tarifa disponible'}
              </h3>
              <p>
                {result.origin_place_name ?? result.origin_postal_code} →{' '}
                {result.destination_place_name ?? result.destination_postal_code} ·{' '}
                {formatNumber(result.distance_km)} km · Zona {result.zone}
              </p>
              {result.options.length > 0 ? (
                <div className="quote-options">
                  {result.options.map((option) => (
                    <QuoteOptionCard
                      key={option.rate_id}
                      option={option}
                      selected={selectedRateId === option.rate_id}
                      onSelect={() => {
                        setSelectedRateId(option.rate_id)
                        setActionNotice('')
                      }}
                    />
                  ))}
                </div>
              ) : (
                <div className="quote-no-options" role="status">
                  Por ahora no tenemos una tarifa para este peso y trayecto. Tus datos quedaron
                  guardados para que Comercial pueda dar seguimiento.
                </div>
              )}
              {result.options.length > 0 && (
                <div className="quote-next-actions">
                  <p>Selecciona una opción y continúa con tu envío.</p>
                  <div>
                    <button
                      className="quote-next-step-action"
                      type="button"
                      aria-disabled="true"
                      onClick={() => showUpcomingAction('pago')}
                    >
                      Continuar al pago
                    </button>
                    <button
                      className="quote-email-action"
                      type="button"
                      aria-disabled="true"
                      onClick={() => showUpcomingAction('correo')}
                    >
                      Enviar cotización por correo
                    </button>
                  </div>
                  {actionNotice && <div className="quote-action-notice" role="status">{actionNotice}</div>}
                </div>
              )}
              <button className="quote-secondary-action quote-restart-action" type="button" onClick={reset}>
                Cotizar otro envío
              </button>
            </div>
          ) : (
            <form className="quote-wizard-form" onSubmit={handleSubmit}>
              <div className="quote-step" key={step}>
                {step === 1 && (
                  <label className="quote-field">
                    <span>¿A qué correo enviamos tu cotización?</span>
                    <input
                      autoFocus
                      autoComplete="email"
                      placeholder="tu@correo.com"
                      required
                      type="email"
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                    />
                    <small>Tu correo identifica el historial de tus cotizaciones.</small>
                  </label>
                )}

                {step === 2 && (
                  <div className="quote-route-fields">
                    <label className="quote-field">
                      <span>Código postal de origen</span>
                      <input
                        autoFocus
                        inputMode="numeric"
                        pattern="[0-9]{5}"
                        placeholder="00000"
                        required
                        value={originPostalCode}
                        onChange={(event) => handlePostalCode(event.target.value, setOriginPostalCode)}
                      />
                    </label>
                    <label className="quote-field">
                      <span>Código postal de destino</span>
                      <input
                        inputMode="numeric"
                        pattern="[0-9]{5}"
                        placeholder="00000"
                        required
                        value={destinationPostalCode}
                        onChange={(event) =>
                          handlePostalCode(event.target.value, setDestinationPostalCode)
                        }
                      />
                    </label>
                  </div>
                )}

                {step === 3 && (
                  <>
                    <label className="quote-field">
                      <span>Peso del paquete</span>
                      <div className="quote-weight-input">
                        <input
                          autoFocus
                          min="0.01"
                          placeholder="1.5"
                          required
                          step="0.01"
                          type="number"
                          value={weight}
                          onChange={(event) => setWeight(event.target.value)}
                        />
                        <span>kg</span>
                      </div>
                    </label>
                    <div className="quote-summary">
                      <span>{originPostalCode} → {destinationPostalCode}</span>
                      <span>{email}</span>
                    </div>
                  </>
                )}
              </div>

              <div className="quote-wizard-actions">
                {error && <div className="quote-request-error" role="alert">{error}</div>}
                {step > 1 && (
                  <button
                    className="quote-back-button"
                    type="button"
                    onClick={() => setStep((current) => current - 1)}
                  >
                    Atrás
                  </button>
                )}
                <button className="quote-next-button" disabled={submitting} type="submit">
                  {submitting
                    ? 'Buscando opciones…'
                    : step === TOTAL_STEPS
                      ? 'Cotizar ahora'
                      : 'Continuar'}
                  <span aria-hidden="true">→</span>
                </button>
              </div>
            </form>
          )}
        </div>
      </section>
    </div>
  )
}

function QuoteOptionCard({
  option,
  selected,
  onSelect,
}: {
  option: QuoteOption
  selected: boolean
  onSelect: () => void
}) {
  const delivery = formatDelivery(option.min_delivery_days, option.max_delivery_days)

  return (
    <button
      aria-pressed={selected}
      className={`quote-option-card${selected ? ' quote-option-card--selected' : ''}`}
      type="button"
      onClick={onSelect}
    >
      <div>
        <strong>{option.carrier_name}</strong>
        {delivery && <span>Entrega estimada: {delivery}</span>}
      </div>
      <b>
        ${Number(option.price_mxn).toLocaleString('es-MX', { minimumFractionDigits: 2 })}
      </b>
    </button>
  )
}

function formatDelivery(minimum: number | null, maximum: number | null): string | null {
  if (minimum === null || maximum === null) return null
  if (minimum === maximum) return `${minimum} ${minimum === 1 ? 'día' : 'días'}`
  return `${minimum}–${maximum} días`
}

function formatNumber(value: string): string {
  return Number(value).toLocaleString('es-MX', { maximumFractionDigits: 2 })
}
