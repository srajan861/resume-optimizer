import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { LayoutDashboard, Clock, LogOut, ChevronRight } from 'lucide-react'

const NAV = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Analyze', end: true },
  { to: '/dashboard/history', icon: Clock, label: 'History', end: false },
]

export default function DashboardLayout() {
  const { user, signOut } = useAuth()
  const nav = useNavigate()

  const handleSignOut = async () => {
    await signOut()
    nav('/')
  }

  const initials = user?.email?.slice(0, 2).toUpperCase() || 'U'

  return (
    <div className="min-h-screen bg-ink-900 flex">
      {/* Sidebar */}
      <aside className="w-64 border-r border-ink-800 flex flex-col py-6 px-4 shrink-0">
        {/* Logo */}
        <div className="px-2 mb-10">
          <span className="font-display text-xl font-bold text-acid">
            Resume<span className="text-white">IQ</span>
          </span>
        </div>

        {/* Nav links */}
        <nav className="flex-1 space-y-1">
          {NAV.map(({ to, icon: Icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-body transition-all group ${
                  isActive
                    ? 'bg-acid/10 text-acid border border-acid/20'
                    : 'text-ink-400 hover:text-ink-200 hover:bg-ink-800'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon size={16} />
                  <span className="flex-1">{label}</span>
                  {isActive && <ChevronRight size={14} className="opacity-60" />}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* User */}
        <div className="border-t border-ink-800 pt-4 mt-4">
          <div className="flex items-center gap-3 px-2 mb-3">
            <div className="w-8 h-8 rounded-full bg-acid/20 border border-acid/30 flex items-center justify-center">
              <span className="text-acid text-xs font-display font-bold">{initials}</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-ink-200 text-xs font-medium truncate">{user?.email}</p>
              <p className="text-ink-500 text-xs">Free plan</p>
            </div>
          </div>
          <button
            onClick={handleSignOut}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-ink-500 hover:text-coral hover:bg-coral/5 text-sm transition-all"
          >
            <LogOut size={15} />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
