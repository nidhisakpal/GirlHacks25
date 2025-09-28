import React from 'react'
import { useAuth0 } from '@auth0/auth0-react'
import { LogIn, LogOut, User } from 'lucide-react'
import logoImage from '../Images/Logos/Main_Logo.png'

interface HomepageProps {
  children: React.ReactNode
}

const Homepage: React.FC<HomepageProps> = ({ children }) => {
  const { loginWithRedirect, logout, user, isAuthenticated } = useAuth0()

  return (
    <section className="flex w-full flex-col gap-8 px-2 sm:px-0">
      <div className="flex flex-col items-center gap-3 text-center">
        <img src={logoImage} alt="Gaia Logo" className="h-[300px] w-auto" />
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4">
        {isAuthenticated && (
          <div className="hidden items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-sm text-slate-100 sm:flex">
            <User className="h-3.5 w-3.5" />
            <span>{user?.name ?? user?.email ?? 'NJIT student'}</span>
          </div>
        )}

        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <button
              onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
              className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-sm font-medium text-slate-100 transition hover:bg-white/20 hover:text-white">
              <LogOut className="h-4 w-4" />
              Sign out
            </button>
          ) : (
            <button
              onClick={() => loginWithRedirect()}
              className="inline-flex items-center gap-2 rounded-full bg-white/15 px-5 py-2 text-sm font-semibold text-white shadow-md transition hover:bg-white/25"
            >
              <LogIn className="h-4 w-4" />
              Log in with Auth0
            </button>
          )}
        </div>
      </div>

      <div>{children}</div>
    </section>
  )
}

export default Homepage
