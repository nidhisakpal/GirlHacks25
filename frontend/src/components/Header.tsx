import React from 'react'
import { useAuth0 } from '@auth0/auth0-react'
import { LogIn, LogOut, User } from 'lucide-react'

const Header: React.FC = () => {
  const { loginWithRedirect, logout, user, isAuthenticated } = useAuth0()

  return (
    <header className="sticky top-0 z-20 border-b border-indigo-100 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-goddess-athena to-goddess-aphrodite text-white shadow-md">
            <span className="text-lg font-bold">G</span>
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-semibold text-gray-900">Gaia Mentorship</span>
            <span className="text-xs uppercase tracking-[0.3em] text-gray-400">NJIT resources, goddess guidance</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {isAuthenticated && (
            <div className="hidden items-center gap-2 rounded-full bg-gray-100 px-3 py-1 text-sm text-gray-600 sm:flex">
              <User className="h-3.5 w-3.5" />
              <span>{user?.name ?? user?.email ?? 'NJIT student'}</span>
            </div>
          )}

          {isAuthenticated ? (
            <button
              onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
              className="inline-flex items-center gap-2 rounded-full border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition hover:border-gray-400 hover:text-gray-900"
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </button>
          ) : (
            <button
              onClick={() => loginWithRedirect()}
              className="inline-flex items-center gap-2 rounded-full bg-goddess-athena px-5 py-2 text-sm font-semibold text-white shadow-md transition hover:bg-indigo-600"
            >
              <LogIn className="h-4 w-4" />
              Log in with Auth0
            </button>
          )}
        </div>
      </div>
    </header>
  )
}

export default Header
