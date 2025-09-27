import React from 'react'
import { useAuth0 } from '@auth0/auth0-react'
import { LogIn, User } from 'lucide-react'

const Header: React.FC = () => {
  const { loginWithRedirect, logout, user, isAuthenticated } = useAuth0()

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
            <span className="text-white font-bold text-lg">G</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Gaia</h1>
          <span className="text-sm text-gray-500">Goddess-Guided Mentorship</span>
        </div>
        
        <div className="flex items-center space-x-4">
          {isAuthenticated ? (
            <>
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <User className="w-4 h-4" />
                <span>{user?.name || user?.email}</span>
              </div>
              <button
                onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                Logout
              </button>
            </>
          ) : (
            <button
              onClick={() => loginWithRedirect()}
              className="flex items-center space-x-2 px-4 py-2 bg-goddess-athena text-white rounded-lg hover:bg-indigo-600 transition-colors"
            >
              <LogIn className="w-4 h-4" />
              <span>Login with NJIT</span>
            </button>
          )}
        </div>
      </div>
    </header>
  )
}

export default Header
