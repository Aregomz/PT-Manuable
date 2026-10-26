import { FormEvent, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { Brand } from '../../shared/components/Brand'
import { authenticate } from './auth'

interface LoginLocationState {
  from?: string
}

export function AdminLoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      if (!(await authenticate(username, password))) {
        setError('El usuario o la contraseña no son correctos.')
        return
      }

      const state = location.state as LoginLocationState | null
      navigate(state?.from ?? '/admin', { replace: true })
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No fue posible iniciar sesión.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="login-page">
      <section className="login-story" aria-hidden="true">
        <div className="login-story__glow login-story__glow--top" />
        <div className="login-story__glow login-story__glow--bottom" />
      </section>

      <section className="login-panel">
        <div className="login-panel__mobile-brand">
          <Brand />
        </div>

        <div className="login-card">
          <div className="login-card__heading">
            <p className="section-label">EQUIPO COMERCIAL</p>
            <h2>Bienvenido de nuevo</h2>
            <p>Ingresa tus datos para acceder al panel.</p>
          </div>

          <form className="login-form" onSubmit={handleSubmit} noValidate>
            <div className="form-field">
              <label htmlFor="username">Usuario</label>
              <input
                id="username"
                name="username"
                type="text"
                autoComplete="username"
                placeholder="Ingresa tu usuario"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                required
              />
            </div>

            <div className="form-field">
              <label htmlFor="password">Contraseña</label>
              <div className="password-field">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  placeholder="Ingresa tu contraseña"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                />
                <button
                  className="password-field__toggle"
                  type="button"
                  onClick={() => setShowPassword((current) => !current)}
                  aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                >
                  {showPassword ? 'Ocultar' : 'Mostrar'}
                </button>
              </div>
            </div>

            {error && (
              <div className="form-error" role="alert">
                <span aria-hidden="true">!</span>
                {error}
              </div>
            )}

            <button className="primary-button" disabled={submitting} type="submit">
              {submitting ? 'Ingresando…' : 'Iniciar sesión'}
              <span aria-hidden="true">→</span>
            </button>
          </form>

          <p className="login-card__support">
            ¿Tienes problemas para entrar? Contacta al equipo de Desarrollo.
          </p>
        </div>
      </section>
    </main>
  )
}
