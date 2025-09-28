import React from 'react'
import { useAuth0 } from '@auth0/auth0-react'
import { LogOut, User } from 'lucide-react'
import logoImage from '../Images/Logos/Main_Logo.png'

interface HomepageProps {
  children: React.ReactNode
}

const Homepage: React.FC<HomepageProps> = ({ children }) => {
  const { logout, user, isAuthenticated } = useAuth0()

  return (
    <section className="flex w-full flex-col px-2 sm:px-0">
      <div className="flex flex-col items-center gap-1 text-center">
        <img src={logoImage} alt="Gaia Logo" className="h-[150px] w-auto" />
      </div>

      <div className="flex flex-wrap items-center justify-between">
        {isAuthenticated && (
          <div className="hidden items-center rounded-full bg-white/10 px-3 py-1 text-sm text-slate-100 sm:flex">
            <User className="h-3.5 w-3.5" />
            <span>{user?.name ?? user?.email ?? 'NJIT student'}</span>
          </div>
        )}

        {isAuthenticated && (
          <button
            onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
            className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-sm font-medium text-slate-100 transition hover:bg-white/20 hover:text-white"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        )}
      </div>

      <div>{children}</div>
    </section>
  )
}

export default Homepage
