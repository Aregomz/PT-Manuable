export interface QuoteOption {
  rate_id: number
  carrier_id: number
  carrier_name: string
  price_mxn: string
  min_delivery_days: number | null
  max_delivery_days: number | null
}

export interface QuoteResult {
  id: number
  email: string
  origin_postal_code: string
  origin_place_name: string | null
  destination_postal_code: string
  destination_place_name: string | null
  weight_kg: string
  distance_km: string
  zone: number
  options: QuoteOption[]
}

export async function requestQuote(input: {
  email: string
  origin_postal_code: string
  destination_postal_code: string
  weight_kg: string
}): Promise<QuoteResult> {
  const response = await fetch('/api/quotes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail ?? 'No pudimos completar la cotización. Intenta nuevamente.')
  }
  return body as QuoteResult
}

