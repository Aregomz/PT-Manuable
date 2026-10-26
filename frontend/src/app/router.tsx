import { Navigate, Route, Routes } from 'react-router-dom'

import { AdminDataPage } from '../features/admin/AdminDataPage'
import { AdminLoginPage } from '../features/auth/AdminLoginPage'
import { ProtectedRoute } from '../features/auth/ProtectedRoute'
import { LandingPage } from '../features/quote/LandingPage'

export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/admin/login" element={<AdminLoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/admin" element={<AdminDataPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
