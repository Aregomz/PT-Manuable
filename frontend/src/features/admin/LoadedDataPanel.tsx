import { FormEvent, useEffect, useState } from 'react'

import { getLoadedData, updateCarrier, updateRate } from './dataApi'
import type { Carrier, LoadedData, Rate } from './dataApi'

interface LoadedDataPanelProps {
  version: number
}

type DataTab = 'carriers' | 'rates'
type EditTarget =
  | { kind: 'carrier'; value: Carrier }
  | { kind: 'rate'; value: Rate }

export function LoadedDataPanel({ version }: LoadedDataPanelProps) {
  const [data, setData] = useState<LoadedData | null>(null)
  const [activeTab, setActiveTab] = useState<DataTab>('carriers')
  const [error, setError] = useState('')
  const [editTarget, setEditTarget] = useState<EditTarget | null>(null)

  useEffect(() => {
    let active = true
    getLoadedData()
      .then((response) => {
        if (active) {
          setError('')
          setData(response)
        }
      })
      .catch((requestError) => {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : 'No fue posible consultar los datos.',
          )
        }
      })
    return () => {
      active = false
    }
  }, [version])

  if (error) {
    return (
      <div className="workspace-message is-error" role="alert">
        {error}
      </div>
    )
  }
  if (!data) return <div className="workspace-message">Consultando datos cargados…</div>

  function handleSaved(updated: Carrier | Rate, kind: EditTarget['kind']) {
    setData((current) => {
      if (!current) return current
      return kind === 'carrier'
        ? {
            ...current,
            carriers: current.carriers.map((carrier) =>
              carrier.id === updated.id ? (updated as Carrier) : carrier,
            ),
            rates: current.rates.map((rate) =>
              rate.carrier_name === (editTarget?.value as Carrier).name
                ? {
                    ...rate,
                    carrier_name: (updated as Carrier).name,
                    carrier_is_active: (updated as Carrier).is_active,
                  }
                : rate,
            ),
          }
        : {
            ...current,
            rates: current.rates.map((rate) =>
              rate.id === updated.id ? (updated as Rate) : rate,
            ),
          }
    })
    setEditTarget(null)
  }

  return (
    <section className="loaded-data-panel">
      <div className="loaded-data-panel__header">
        <div>
          <h2>Información disponible</h2>
          <p>Registros almacenados en PostgreSQL; el estado indica cuáles pueden cotizarse.</p>
        </div>
        <div className="loaded-counts">
          <span>
            <strong>{data.carriers.length}</strong> paqueterías
          </span>
          <span>
            <strong>{data.rates.length}</strong> tarifas
          </span>
        </div>
      </div>

      <div className="data-subtabs">
        <button
          className={activeTab === 'carriers' ? 'is-active' : ''}
          type="button"
          onClick={() => setActiveTab('carriers')}
        >
          Paqueterías
        </button>
        <button
          className={activeTab === 'rates' ? 'is-active' : ''}
          type="button"
          onClick={() => setActiveTab('rates')}
        >
          Tarifas
        </button>
      </div>

      <div className="data-table-wrap loaded-table-wrap">
        {activeTab === 'carriers' ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Paquetería</th>
                <th>Servicio</th>
                <th>Peso cobrable</th>
                <th>Estado</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.carriers.map((carrier) => (
                <tr key={carrier.id}>
                  <td>{carrier.code}</td>
                  <td>{carrier.name}</td>
                  <td>{carrier.service_type}</td>
                  <td>
                    {carrier.volumetric_divisor && carrier.volumetric_effective_from
                      ? `Volumétrico / ${formatNumber(carrier.volumetric_divisor)} desde ${carrier.volumetric_effective_from}`
                      : 'Peso real'}
                  </td>
                  <td>
                    <span
                      className={`availability ${carrier.is_active ? 'is-active' : 'is-inactive'}`}
                    >
                      {carrier.is_active ? 'Activa' : 'Inactiva'}
                    </span>
                  </td>
                  <td>
                    <button
                      className="table-action"
                      type="button"
                      onClick={() => setEditTarget({ kind: 'carrier', value: carrier })}
                    >
                      Editar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <table className="data-table rates-table">
            <thead>
              <tr>
                <th>Paquetería</th>
                <th>Zona</th>
                <th>Peso</th>
                <th>Precio</th>
                <th>Entrega</th>
                <th>Vigencia</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.rates.map((rate) => (
                <tr key={rate.id}>
                  <td>
                    {rate.carrier_name}
                    {!rate.carrier_is_active && <small>Inactiva</small>}
                  </td>
                  <td>Zona {rate.zone}</td>
                  <td>
                    {formatNumber(rate.min_weight_kg)}–{formatNumber(rate.max_weight_kg)} kg
                  </td>
                  <td>
                    ${Number(rate.price_mxn).toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                  </td>
                  <td>{formatDelivery(rate.min_delivery_days, rate.max_delivery_days)}</td>
                  <td>{rate.effective_from ?? 'Sin vigencia'}</td>
                  <td>
                    <button
                      className="table-action"
                      type="button"
                      onClick={() => setEditTarget({ kind: 'rate', value: rate })}
                    >
                      Editar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {editTarget && (
        <CatalogEditModal
          target={editTarget}
          onClose={() => setEditTarget(null)}
          onSaved={handleSaved}
        />
      )}
    </section>
  )
}

function CatalogEditModal({
  target,
  onClose,
  onSaved,
}: {
  target: EditTarget
  onClose: () => void
  onSaved: (updated: Carrier | Rate, kind: EditTarget['kind']) => void
}) {
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [carrierForm, setCarrierForm] = useState(() =>
    target.kind === 'carrier'
      ? {
          name: target.value.name,
          service_type: target.value.service_type,
          is_active: target.value.is_active,
          volumetric_divisor: target.value.volumetric_divisor ?? '',
          volumetric_effective_from: target.value.volumetric_effective_from ?? '',
        }
      : null,
  )
  const [rateForm, setRateForm] = useState(() =>
    target.kind === 'rate'
      ? {
          zone: String(target.value.zone),
          min_weight_kg: target.value.min_weight_kg,
          max_weight_kg: target.value.max_weight_kg,
          price_mxn: target.value.price_mxn,
          min_delivery_days: target.value.min_delivery_days?.toString() ?? '',
          max_delivery_days: target.value.max_delivery_days?.toString() ?? '',
          effective_from: target.value.effective_from ?? '',
        }
      : null,
  )

  useEffect(() => {
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [onClose])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setSaveError('')
    try {
      if (target.kind === 'carrier' && carrierForm) {
        onSaved(
          await updateCarrier(target.value.id, {
            ...carrierForm,
            volumetric_divisor: carrierForm.volumetric_divisor || null,
            volumetric_effective_from: carrierForm.volumetric_effective_from || null,
          }),
          'carrier',
        )
      } else if (target.kind === 'rate' && rateForm) {
        onSaved(
          await updateRate(target.value.id, {
            zone: Number(rateForm.zone),
            min_weight_kg: rateForm.min_weight_kg,
            max_weight_kg: rateForm.max_weight_kg,
            price_mxn: rateForm.price_mxn,
            min_delivery_days: rateForm.min_delivery_days
              ? Number(rateForm.min_delivery_days)
              : null,
            max_delivery_days: rateForm.max_delivery_days
              ? Number(rateForm.max_delivery_days)
              : null,
            effective_from: rateForm.effective_from || null,
          }),
          'rate',
        )
      }
    } catch (requestError) {
      setSaveError(
        requestError instanceof Error ? requestError.message : 'No fue posible guardar los cambios.',
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="catalog-edit-backdrop">
      <section
        aria-labelledby="catalog-edit-title"
        aria-modal="true"
        className="catalog-edit-modal"
        role="dialog"
      >
        <button aria-label="Cerrar edición" className="quote-modal__close" type="button" onClick={onClose}>
          <span aria-hidden="true">×</span>
        </button>
        <div className="catalog-edit-modal__header">
          <span>EDICIÓN MANUAL</span>
          <h3 id="catalog-edit-title">
            {target.kind === 'carrier' ? `Editar ${target.value.name}` : `Editar tarifa de ${target.value.carrier_name}`}
          </h3>
          <p>Guarda un ajuste puntual sin volver a importar el archivo CSV.</p>
        </div>

        <form className="catalog-edit-form" onSubmit={handleSubmit}>
          {carrierForm ? (
            <>
              <label>
                <span>Nombre</span>
                <input
                  maxLength={100}
                  required
                  value={carrierForm.name}
                  onChange={(event) => setCarrierForm({ ...carrierForm, name: event.target.value })}
                />
              </label>
              <label>
                <span>Tipo de servicio</span>
                <input
                  maxLength={50}
                  required
                  value={carrierForm.service_type}
                  onChange={(event) =>
                    setCarrierForm({ ...carrierForm, service_type: event.target.value })
                  }
                />
              </label>
              <label className="catalog-status-field">
                <input
                  checked={carrierForm.is_active}
                  type="checkbox"
                  onChange={(event) =>
                    setCarrierForm({ ...carrierForm, is_active: event.target.checked })
                  }
                />
                <span>Paquetería activa y disponible para cotizar</span>
              </label>
              <div className="catalog-edit-form__grid">
                <label>
                  <span>Divisor volumétrico</span>
                  <input
                    min="0.01"
                    placeholder="Sin cálculo volumétrico"
                    step="0.01"
                    type="number"
                    value={carrierForm.volumetric_divisor}
                    onChange={(event) =>
                      setCarrierForm({ ...carrierForm, volumetric_divisor: event.target.value })
                    }
                  />
                </label>
                <label>
                  <span>Aplicar desde</span>
                  <input
                    type="date"
                    value={carrierForm.volumetric_effective_from}
                    onChange={(event) =>
                      setCarrierForm({
                        ...carrierForm,
                        volumetric_effective_from: event.target.value,
                      })
                    }
                  />
                </label>
              </div>
            </>
          ) : rateForm ? (
            <div className="catalog-edit-form__grid">
              <label>
                <span>Zona</span>
                <select
                  value={rateForm.zone}
                  onChange={(event) => setRateForm({ ...rateForm, zone: event.target.value })}
                >
                  {[1, 2, 3, 4].map((zone) => <option key={zone} value={zone}>Zona {zone}</option>)}
                </select>
              </label>
              <label>
                <span>Precio MXN</span>
                <input
                  min="0.01"
                  required
                  step="0.01"
                  type="number"
                  value={rateForm.price_mxn}
                  onChange={(event) => setRateForm({ ...rateForm, price_mxn: event.target.value })}
                />
              </label>
              <label>
                <span>Peso mínimo (kg)</span>
                <input
                  min="0"
                  required
                  step="0.001"
                  type="number"
                  value={rateForm.min_weight_kg}
                  onChange={(event) => setRateForm({ ...rateForm, min_weight_kg: event.target.value })}
                />
              </label>
              <label>
                <span>Peso máximo (kg)</span>
                <input
                  min="0.001"
                  required
                  step="0.001"
                  type="number"
                  value={rateForm.max_weight_kg}
                  onChange={(event) => setRateForm({ ...rateForm, max_weight_kg: event.target.value })}
                />
              </label>
              <label>
                <span>Entrega mínima (días)</span>
                <input
                  min="1"
                  type="number"
                  value={rateForm.min_delivery_days}
                  onChange={(event) => setRateForm({ ...rateForm, min_delivery_days: event.target.value })}
                />
              </label>
              <label>
                <span>Entrega máxima (días)</span>
                <input
                  min="1"
                  type="number"
                  value={rateForm.max_delivery_days}
                  onChange={(event) => setRateForm({ ...rateForm, max_delivery_days: event.target.value })}
                />
              </label>
              <label className="catalog-edit-form__wide">
                <span>Vigente desde</span>
                <input
                  type="date"
                  value={rateForm.effective_from}
                  onChange={(event) => setRateForm({ ...rateForm, effective_from: event.target.value })}
                />
              </label>
            </div>
          ) : null}

          {saveError && <div className="quote-request-error" role="alert">{saveError}</div>}
          <div className="catalog-edit-form__actions">
            <button className="secondary-button" type="button" onClick={onClose}>Cancelar</button>
            <button className="primary-button" disabled={saving} type="submit">
              {saving ? 'Guardando…' : 'Guardar cambios'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}

function formatNumber(value: string): string {
  return Number(value).toLocaleString('es-MX', { maximumFractionDigits: 3 })
}

function formatDelivery(minimum: number | null, maximum: number | null): string {
  if (minimum === null || maximum === null) return 'Por confirmar'
  if (minimum === maximum) return `${minimum} ${minimum === 1 ? 'día' : 'días'}`
  return `${minimum}–${maximum} días`
}
