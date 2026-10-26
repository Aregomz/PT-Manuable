export type ImportKind = 'carriers' | 'rates'
export type ImportStatus = 'loaded' | 'corrected' | 'rejected' | 'duplicate'

export interface ImportRow {
  row_number: number
  status: ImportStatus
  raw_data: Record<string, unknown>
  normalized_data: Record<string, unknown> | null
  reason: string | null
  changes: string[]
}

export interface ImportResult {
  id: number
  filename: string
  total_rows: number
  loaded_rows: number
  corrected_rows: number
  rejected_rows: number
  duplicate_rows: number
  created_at: string
  already_imported: boolean
  rows: ImportRow[]
}

export interface Carrier {
  id: number
  code: string
  name: string
  service_type: string
  is_active: boolean
  updated_at: string
}

export interface Rate {
  id: number
  carrier_name: string
  carrier_is_active: boolean
  zone: number
  min_weight_kg: string
  max_weight_kg: string
  price_mxn: string
  min_delivery_days: number | null
  max_delivery_days: number | null
  effective_from: string | null
}

export interface LoadedData {
  carriers: Carrier[]
  rates: Rate[]
}

export interface CarrierUpdate {
  name: string
  service_type: string
  is_active: boolean
}

export interface RateUpdate {
  zone: number
  min_weight_kg: string
  max_weight_kg: string
  price_mxn: string
  min_delivery_days: number | null
  max_delivery_days: number | null
  effective_from: string | null
}

export interface LeadQuote {
  id: number
  origin_postal_code: string
  destination_postal_code: string
  weight_kg: string
  distance_km: string
  zone: number
  option_count: number
  created_at: string
}

export interface CapturedLead {
  id: number
  email: string
  created_at: string
  quotes: LeadQuote[]
}

export interface CapturedLeads {
  leads: CapturedLead[]
}

export async function uploadDataFile(kind: ImportKind, file: File): Promise<ImportResult> {
  const formData = new FormData()
  formData.append(kind === 'carriers' ? 'carriers_file' : 'rates_file', file)

  return requestJson<ImportResult>(`/api/admin/imports/${kind}`, {
    method: 'POST',
    credentials: 'include',
    body: formData,
  })
}

export async function getLoadedData(): Promise<LoadedData> {
  return requestJson<LoadedData>('/api/admin/data', { credentials: 'include' })
}

export async function updateCarrier(id: number, update: CarrierUpdate): Promise<Carrier> {
  return requestJson<Carrier>(`/api/admin/data/carriers/${id}`, {
    method: 'PUT',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(update),
  })
}

export async function updateRate(id: number, update: RateUpdate): Promise<Rate> {
  return requestJson<Rate>(`/api/admin/data/rates/${id}`, {
    method: 'PUT',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(update),
  })
}

export async function getCapturedLeads(): Promise<CapturedLeads> {
  return requestJson<CapturedLeads>('/api/admin/leads', { credentials: 'include' })
}

async function requestJson<T>(url: string, init: RequestInit): Promise<T> {
  const response = await fetch(url, init)
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail ?? 'No fue posible completar la solicitud.')
  }
  return body as T
}
