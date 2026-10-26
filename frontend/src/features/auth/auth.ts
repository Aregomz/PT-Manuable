interface ApiError {
  detail?: string
}

export async function authenticate(username: string, password: string): Promise<boolean> {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!response.ok) {
    const error = (await response.json().catch(() => ({}))) as ApiError
    if (response.status === 401) {
      return false
    }
    throw new Error(error.detail ?? 'No fue posible iniciar sesión. Intenta nuevamente.')
  }
  return true
}

export async function isAuthenticated(): Promise<boolean> {
  const response = await fetch('/api/auth/me', { credentials: 'include' })
  return response.ok
}

export async function logout(): Promise<void> {
  await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
}
