interface BrandProps {
  inverse?: boolean
}

export function Brand({ inverse = false }: BrandProps) {
  return (
    <div className={`brand${inverse ? ' brand--inverse' : ''}`} aria-label="Manuable">
      <span className="brand__mark" aria-hidden="true">
        m
      </span>
      <span className="brand__name">manuable</span>
    </div>
  )
}
