import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { vi } from 'vitest'

import { App } from './App'

describe('App', () => {
  let authenticated = false
  let capturedLeads: Array<Record<string, unknown>> = []

  beforeEach(() => {
    authenticated = false
    capturedLeads = []
    window.history.pushState({}, '', '/')
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input)
        if (url.endsWith('/api/auth/login')) {
          const credentials = JSON.parse(String(init?.body)) as {
            username: string
            password: string
          }
          authenticated =
            credentials.username === 'comercial' && credentials.password === 'comercial123'
          return new Response(
            JSON.stringify(
              authenticated
                ? { username: 'comercial' }
                : { detail: 'El usuario o la contraseña no son correctos.' },
            ),
            { status: authenticated ? 200 : 401, headers: { 'Content-Type': 'application/json' } },
          )
        }
        if (url.endsWith('/api/auth/me')) {
          return new Response(authenticated ? JSON.stringify({ username: 'comercial' }) : '{}', {
            status: authenticated ? 200 : 401,
            headers: { 'Content-Type': 'application/json' },
          })
        }
        if (url.endsWith('/api/admin/data')) {
          return new Response(
            JSON.stringify({
              carriers: [
                {
                  id: 4,
                  code: 'CARR-04',
                  name: 'Redpack',
                  service_type: 'Terrestre',
                  is_active: false,
                  volumetric_divisor: null,
                  volumetric_effective_from: null,
                  updated_at: '2026-10-26T10:00:00Z',
                },
              ],
              rates: [
                {
                  id: 1,
                  carrier_name: 'Redpack',
                  carrier_is_active: false,
                  zone: 1,
                  min_weight_kg: '0',
                  max_weight_kg: '1',
                  price_mxn: '120.00',
                  min_delivery_days: null,
                  max_delivery_days: null,
                  effective_from: null,
                },
              ],
            }),
            { status: 200, headers: { 'Content-Type': 'application/json' } },
          )
        }
        if (url.includes('/api/admin/data/carriers/')) {
          const update = JSON.parse(String(init?.body)) as {
            name: string
            service_type: string
            is_active: boolean
          }
          return new Response(
            JSON.stringify({
              id: 4,
              code: 'CARR-04',
              ...update,
              updated_at: '2026-10-26T10:30:00Z',
            }),
            { status: 200, headers: { 'Content-Type': 'application/json' } },
          )
        }
        if (url.endsWith('/api/admin/leads')) {
          return new Response(JSON.stringify({ leads: capturedLeads, daily_metrics: [] }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        }
        if (url.endsWith('/api/admin/imports/rates')) {
          return new Response(
            JSON.stringify({
              id: 2,
              filename: 'tarifas.csv',
              total_rows: 1,
              loaded_rows: 0,
              corrected_rows: 0,
              rejected_rows: 1,
              duplicate_rows: 0,
              created_at: '2026-10-26T10:00:00Z',
              already_imported: true,
              rows: [
                {
                  row_number: 2,
                  status: 'rejected',
                  raw_data: { paqueteria: 'DHL', precio: '' },
                  normalized_data: null,
                  changes: [],
                  reason: 'La tarifa no tiene precio; se requiere confirmación de Comercial.',
                },
              ],
            }),
            { status: 200, headers: { 'Content-Type': 'application/json' } },
          )
        }
        if (url.endsWith('/api/quotes')) {
          const quote = JSON.parse(String(init?.body)) as { origin_postal_code: string }
          if (quote.origin_postal_code === '00000') {
            return new Response(
              JSON.stringify({ detail: 'No encontramos cobertura para el código postal 00000.' }),
              { status: 422, headers: { 'Content-Type': 'application/json' } },
            )
          }
          return new Response(
            JSON.stringify({
              id: 1,
              external_reference: 'WEB-TEST00000001',
              email: 'cliente@example.com',
              origin_postal_code: '06600',
              origin_place_name: 'Juarez',
              destination_postal_code: '64000',
              destination_place_name: 'Monterrey Centro',
              weight_kg: '2.5',
              length_cm: '20',
              width_cm: '15',
              height_cm: '10',
              volumetric_weight_kg: '0.6',
              distance_km: '728.20',
              zone: 3,
              quoted_at: '2026-10-26T10:00:00Z',
              valid_until: '2026-11-25T10:00:00Z',
              options: [
                {
                  rate_id: 1,
                  carrier_id: 2,
                  carrier_name: 'Estafeta',
                  price_mxn: '309.74',
                  min_delivery_days: 5,
                  max_delivery_days: 7,
                  actual_weight_kg: '2.5',
                  volumetric_weight_kg: '0.6',
                  billable_weight_kg: '2.5',
                },
                {
                  rate_id: 2,
                  carrier_id: 3,
                  carrier_name: 'FedEx',
                  price_mxn: '577.04',
                  min_delivery_days: null,
                  max_delivery_days: null,
                  actual_weight_kg: '2.5',
                  volumetric_weight_kg: '0.6',
                  billable_weight_kg: '2.5',
                },
              ],
            }),
            { status: 201, headers: { 'Content-Type': 'application/json' } },
          )
        }
        return new Response(null, { status: 204 })
      }),
    )
  })

  it('keeps the public landing at the root route', () => {
    render(<App />)

    expect(screen.getByRole('heading', { name: 'Landing Page' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Acceso Comercial' })).toBeInTheDocument()
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Cotiza tu envío en 2 clics' })).toBeInTheDocument()
  })

  it('closes and reopens the quote modal from the landing page', () => {
    render(<App />)

    fireEvent.click(screen.getByRole('button', { name: 'Cerrar cotizador' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Landing Page' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /Cotizar ahora/ }))
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('guides the user through the three quote steps', async () => {
    render(<App />)

    fireEvent.change(screen.getByLabelText(/¿A qué correo enviamos tu cotización\?/), {
      target: { value: 'cliente@example.com' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Continuar' }))

    fireEvent.change(screen.getByLabelText(/^Código postal de origen/), {
      target: { value: '06600' },
    })
    fireEvent.change(screen.getByLabelText(/^Código postal de destino/), {
      target: { value: '64000' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Continuar' }))

    fireEvent.change(screen.getByLabelText(/Peso del paquete/), { target: { value: '2.5' } })
    fireEvent.change(screen.getByLabelText(/^Largo/), { target: { value: '20' } })
    fireEvent.change(screen.getByLabelText(/^Ancho/), { target: { value: '15' } })
    fireEvent.change(screen.getByLabelText(/^Alto/), { target: { value: '10' } })
    fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Cotizar ahora' }))

    expect(
      await screen.findByRole('heading', { name: 'Encontramos 2 opciones' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Estafeta')).toBeInTheDocument()
    expect(screen.getByText('$309.74')).toBeInTheDocument()
    expect(screen.getByText('Entrega estimada: 5–7 días')).toBeInTheDocument()
    expect(screen.queryByText('Tiempo por confirmar')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Continuar al pago/ })).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Enviar cotización por correo' }),
    ).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Enviar cotización por correo' }))
    expect(screen.getByRole('status')).toHaveTextContent(
      'Esta acción enviaría la cotización mediante el proceso actual de Manuable a cliente@example.com.',
    )
  })

  it('redirects protected visitors to the commercial login', async () => {
    window.history.pushState({}, '', '/admin')

    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Bienvenido de nuevo' })).toBeInTheDocument()
  })

  it('allows the commercial credentials through the API', async () => {
    window.history.pushState({}, '', '/admin/login')
    render(<App />)

    fireEvent.change(screen.getByLabelText('Usuario'), { target: { value: 'comercial' } })
    fireEvent.change(screen.getByLabelText('Contraseña'), {
      target: { value: 'comercial123' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Iniciar sesión' }))

    expect(await screen.findByRole('button', { name: 'Cargar datos' })).toBeInTheDocument()
    expect(screen.getByLabelText('Archivo de paqueterías')).toBeInTheDocument()
    expect(screen.getByLabelText('Archivo de tarifas')).toBeInTheDocument()
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/auth/me', { credentials: 'include' }))
  })

  it('shows the data currently stored in PostgreSQL', async () => {
    authenticated = true
    window.history.pushState({}, '', '/admin')
    render(<App />)

    fireEvent.click(await screen.findByRole('button', { name: 'Datos cargados' }))

    expect(await screen.findByText('Redpack')).toBeInTheDocument()
    expect(screen.getByText('Inactiva')).toBeInTheDocument()
    expect(
      screen.getByText((_, element) => element?.textContent?.trim() === '1 tarifas'),
    ).toBeInTheDocument()
  })

  it('edits and activates a carrier without importing another CSV', async () => {
    authenticated = true
    window.history.pushState({}, '', '/admin')
    render(<App />)

    fireEvent.click(await screen.findByRole('button', { name: 'Datos cargados' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Editar' }))

    const activeCheckbox = screen.getByLabelText('Paquetería activa y disponible para cotizar')
    fireEvent.click(activeCheckbox)
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))

    expect(await screen.findByText('Activa')).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith(
      '/api/admin/data/carriers/4',
      expect.objectContaining({ method: 'PUT' }),
    )
  })

  it('imports rates independently and explains rejected rows', async () => {
    authenticated = true
    window.history.pushState({}, '', '/admin')
    render(<App />)

    const input = await screen.findByLabelText('Archivo de tarifas')
    const file = new File(['paqueteria,precio\nDHL,'], 'tarifas.csv', { type: 'text/csv' })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getAllByRole('button', { name: 'Cargar archivo' })[1])

    expect(
      await screen.findByText('La tarifa no tiene precio; se requiere confirmación de Comercial.'),
    ).toBeInTheDocument()
    expect(screen.getByText('Rechazada')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Todas 1' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Rechazadas 1' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cargadas' })).toBeInTheDocument()
    expect(screen.getByText('Este archivo ya fue importado anteriormente.')).toBeInTheDocument()
    expect(screen.getByText(/No se realizaron cambios/)).toBeInTheDocument()
  })

  it('shows the captured leads section with an empty state', async () => {
    authenticated = true
    window.history.pushState({}, '', '/admin')
    render(<App />)

    fireEvent.click(await screen.findByRole('button', { name: 'Leads capturados' }))
    expect(await screen.findByText('Cargadas manualmente')).toBeInTheDocument()
    expect(
      screen.getByText('cotizaciones manuales con su precio original respetado'),
    ).toBeInTheDocument()
    fireEvent.click(await screen.findByRole('button', { name: 'Directorio de leads' }))

    expect(await screen.findByText('Aún no hay leads capturados.')).toBeInTheDocument()
    expect(
      screen.getByText('Cuando una persona cotice desde la landing, aparecerá aquí.'),
    ).toBeInTheDocument()
  })

  it('opens a lead quote history in a modal', async () => {
    capturedLeads = [
      {
        id: 9,
        email: 'cliente@example.com',
        created_at: '2026-10-26T07:00:00Z',
        quotes: [
          {
            id: 12,
            external_reference: 'COT-0012',
            source: 'historical',
            origin_postal_code: '06600',
            destination_postal_code: '64000',
            weight_kg: '1.84',
            distance_km: '725.93',
            zone: 3,
            option_count: 2,
            options: [
              {
                carrier_name: 'DHL',
                price_mxn: '350.00',
                min_delivery_days: null,
                max_delivery_days: null,
                billable_weight_kg: '1.84',
              },
            ],
            quoted_at: '2026-10-26T07:13:00Z',
            valid_until: '2026-11-25T07:13:00Z',
          },
        ],
      },
    ]
    authenticated = true
    window.history.pushState({}, '', '/admin')
    render(<App />)

    fireEvent.click(await screen.findByRole('button', { name: 'Leads capturados' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Directorio de leads' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Ver cotizaciones' }))

    expect(screen.getByRole('dialog')).toHaveTextContent('Cotizaciones del lead')
    expect(screen.getByRole('dialog')).toHaveTextContent('cliente@example.com')
    expect(screen.getByRole('dialog')).toHaveTextContent('06600 → 64000')

    fireEvent.click(screen.getByRole('button', { name: 'Cerrar historial de cotizaciones' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('filters leads that require follow-up from the dashboard', async () => {
    capturedLeads = [
      {
        id: 15,
        email: 'seguimiento@example.com',
        created_at: '2026-10-26T07:00:00Z',
        quotes: [
          {
            id: 20,
            external_reference: 'WEB-SINOPCIONES',
            source: 'public',
            origin_postal_code: '06600',
            destination_postal_code: '00000',
            weight_kg: '2.00',
            distance_km: null,
            zone: 4,
            option_count: 0,
            options: [],
            quoted_at: '2026-10-26T07:13:00Z',
            valid_until: '2026-11-25T07:13:00Z',
          },
        ],
      },
    ]
    authenticated = true
    window.history.pushState({}, '', '/admin')
    render(<App />)

    fireEvent.click(await screen.findByRole('button', { name: 'Leads capturados' }))
    fireEvent.click(await screen.findByRole('button', { name: /Ver casos/ }))

    expect(screen.getByRole('status')).toHaveTextContent(
      'Mostrando 1 lead con cotizaciones sin opciones.',
    )
    expect(screen.getByText('seguimiento@example.com')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Ver cotizaciones' }))
    expect(screen.getByRole('dialog')).toHaveTextContent(
      'Sin opciones disponibles · requiere seguimiento',
    )
  })
})

