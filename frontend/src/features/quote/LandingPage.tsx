import { useState } from 'react'
import { Link } from 'react-router-dom'

import { QuoteWizard } from './QuoteWizard'

export function LandingPage() {
  const [isQuoteOpen, setIsQuoteOpen] = useState(true)

  return (
    <main className="landing-page">
      <header className="landing-header">
        <Link className="landing-header__admin" to="/admin/login">
          Acceso Comercial
        </Link>
      </header>

      <section className="landing-placeholder">
        <h1>Landing Page</h1>
        <button className="landing-quote-button" type="button" onClick={() => setIsQuoteOpen(true)}>
          Cotizar ahora <span aria-hidden="true">→</span>
        </button>
      </section>

      {isQuoteOpen && <QuoteWizard onClose={() => setIsQuoteOpen(false)} />}
    </main>
  )
}
