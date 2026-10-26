export interface QuoteOption {
  rate_id: number
  carrier_id: number
  carrier_name: string
  price_mxn: string
  min_delivery_days: number | null
  max_delivery_days: number | null
  actual_weight_kg: string
  volumetric_weight_kg: string | null
  billable_weight_kg: string
}

export interface QuoteResult {
  id: number
  external_reference: string
  email: string
  origin_postal_code: string
  origin_place_name: string | null
  destination_postal_code: string
  destination_place_name: string | null
  weight_kg: string
  length_cm: string | null
  width_cm: string | null
  height_cm: string | null
  volumetric_weight_kg: string | null
  distance_km: string
  zone: number
  quoted_at: string
  valid_until: string
  options: QuoteOption[]
}

export async function requestQuote(input: {
  email: string
  origin_postal_code: string
  destination_postal_code: string
  weight_kg: string
  length_cm: string
  width_cm: string
  height_cm: string
}): Promise<QuoteResult> {
  const response = await fetch('/api/quotes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = Array.isArray(body.detail)
      ? body.detail.map((item: { msg?: string }) => item.msg).filter(Boolean).join(' ')
      : body.detail
    throw new Error(detail ?? 'No pudimos completar la cotización. Intenta nuevamente.')
  }
  return body as QuoteResult
}

