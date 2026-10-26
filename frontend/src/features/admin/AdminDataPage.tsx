import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { logout } from '../auth/auth'
import { CapturedLeadsPanel } from './CapturedLeadsPanel'
import { ImportPanel } from './ImportPanel'
import { LoadedDataPanel } from './LoadedDataPanel'

type AdminTab = 'import' | 'data' | 'leads'

export function AdminDataPage() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<AdminTab>('import')
  const [dataVersion, setDataVersion] = useState(0)

  async function handleLogout() {
    await logout().catch(() => undefined)
    navigate('/admin/login', { replace: true })
  }

  return (
    <main className="admin-page">
      <header className="admin-header">
        <button className="secondary-button" type="button" onClick={handleLogout}>
          Cerrar sesión
        </button>
      </header>

      <section className="admin-content">
        <p className="section-label admin-section-label">EQUIPO COMERCIAL</p>

        <nav className="admin-tabs" aria-label="Secciones de carga de datos">
          <button
            className={activeTab === 'import' ? 'is-active' : ''}
            type="button"
            onClick={() => setActiveTab('import')}
          >
            Cargar datos
          </button>
          <button
            className={activeTab === 'data' ? 'is-active' : ''}
            type="button"
            onClick={() => setActiveTab('data')}
          >
            Datos cargados
          </button>
          <button
            className={activeTab === 'leads' ? 'is-active' : ''}
            type="button"
            onClick={() => setActiveTab('leads')}
          >
            Leads capturados
          </button>
        </nav>

        <div className="admin-workspace">
          {activeTab === 'import' ? (
            <ImportPanel onImported={() => setDataVersion((version) => version + 1)} />
          ) : activeTab === 'data' ? (
            <LoadedDataPanel version={dataVersion} />
          ) : (
            <CapturedLeadsPanel />
          )}
        </div>
      </section>
    </main>
  )
}
