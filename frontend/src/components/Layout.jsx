import { useState, useRef, useEffect } from 'react'
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const INSIGHTS_PATHS = ['/history', '/dashboard', '/summary']

function navLinkClass(active) {
  return `font-medium transition-colors border-b-2 py-1 ${active ? 'text-sage-700 border-sage-500' : 'text-sage-600 hover:text-sage-700 border-transparent hover:border-sage-400'}`
}

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [showMenu, setShowMenu] = useState(false)
  const [showInsightsDropdown, setShowInsightsDropdown] = useState(false)
  const menuRef = useRef(null)
  const insightsRef = useRef(null)

  const pathname = location.pathname
  const isInsightsPage = INSIGHTS_PATHS.some((p) => pathname === p || pathname.startsWith(p + '/'))

  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) setShowMenu(false)
      if (insightsRef.current && !insightsRef.current.contains(e.target)) setShowInsightsDropdown(false)
    }
    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [])

  const handleLogout = () => {
    setShowMenu(false)
    logout()
    navigate('/login')
  }

  const displayName = user?.firstName?.trim() ? user.firstName.trim() : user?.email ?? 'Profile'

  return (
    <div className="min-h-screen bg-paper">
      <nav className="bg-paper border-b border-sage-200/80 px-4 py-3 flex items-center justify-between gap-3 shadow-soft">
        <div className="flex flex-1 gap-4 items-center justify-start flex-wrap">
          <Link to="/" className={navLinkClass(pathname === '/')}>
            Write
          </Link>
          <div className="relative" ref={insightsRef}>
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); setShowInsightsDropdown((v) => !v) }}
              className={`${navLinkClass(isInsightsPage)} inline-flex items-center gap-0.5`}
              aria-expanded={showInsightsDropdown}
              aria-haspopup="true"
            >
              Insights
              <span className="text-sage-500 text-xs" aria-hidden>{showInsightsDropdown ? '▲' : '▼'}</span>
            </button>
            {showInsightsDropdown && (
              <div className="absolute left-0 top-full mt-1 py-1 min-w-[140px] bg-white border border-sage-200 rounded-card shadow-card z-50">
                <Link to="/history" onClick={() => setShowInsightsDropdown(false)} className="block px-4 py-2 text-sm text-sage-700 hover:bg-sage-50">
                  History
                </Link>
                <Link to="/dashboard" onClick={() => setShowInsightsDropdown(false)} className="block px-4 py-2 text-sm text-sage-700 hover:bg-sage-50">
                  Dashboard
                </Link>
                <Link to="/summary" onClick={() => setShowInsightsDropdown(false)} className="block px-4 py-2 text-sm text-sage-700 hover:bg-sage-50">
                  Summary
                </Link>
              </div>
            )}
          </div>
        </div>
        <div className="flex flex-1 justify-center items-center shrink-0">
          <Link to="/" className="hover:opacity-90 transition-opacity" aria-label="Antar.AI home">
            <img src="/antar-logo.png" alt="Antar.AI" className="h-8 w-auto" />
          </Link>
        </div>
        <div className="relative flex flex-1 items-center justify-end" ref={menuRef}>
          {user && (
            <>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); setShowMenu((v) => !v) }}
                className="text-sm text-sage-600 hover:text-sage-700 truncate max-w-[180px] font-medium transition-colors border-b-2 border-transparent hover:border-sage-400 py-1"
                aria-expanded={showMenu}
                aria-haspopup="true"
              >
                {displayName}
              </button>
              {showMenu && (
                <div className="absolute right-0 top-full mt-1 py-1 min-w-[140px] bg-white border border-sage-200 rounded-card shadow-card z-50">
                  <Link
                    to="/profile"
                    onClick={() => setShowMenu(false)}
                    className="block px-4 py-2 text-sm text-sage-700 hover:bg-sage-50"
                  >
                    Profile
                  </Link>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="block w-full text-left px-4 py-2 text-sm text-sage-700 hover:bg-sage-50 border-t border-sage-100"
                  >
                    Log out
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </nav>
      {isInsightsPage && (
        <div className="bg-sage-50/50 border-b border-sage-200/80 px-4 py-2 flex flex-wrap gap-4 items-center">
          <Link to="/history" className={navLinkClass(pathname === '/history')}>History</Link>
          <Link to="/dashboard" className={navLinkClass(pathname === '/dashboard')}>Dashboard</Link>
          <Link to="/summary" className={navLinkClass(pathname === '/summary')}>Summary</Link>
        </div>
      )}
      <main className="max-w-2xl mx-auto p-5 md:p-6">
        <Outlet />
      </main>
    </div>
  )
}
