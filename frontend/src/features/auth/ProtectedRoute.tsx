import { useEffect, useState } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { isAuthenticated } from './auth'

export function ProtectedRoute() {
  const location = useLocation()
  const [authenticated, setAuthenticated] = useState<boolean | null>(null)

  useEffect(() => {
    let active = true
    isAuthenticated()
      .then((valid) => active && setAuthenticated(valid))
      .catch(() => active && setAuthenticated(false))
    return () => {
      active = false
    }
  }, [])

  if (authenticated === null) {
    return <main className="session-loading">Validando sesión…</main>
  }

  if (!authenticated) {
    return <Navigate to="/admin/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}
