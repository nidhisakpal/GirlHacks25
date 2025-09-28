import { BrowserRouter as Router, Navigate, Route, Routes } from 'react-router-dom'
import { useAuth0 } from '@auth0/auth0-react'
import { apiClient } from './services/api'   // make sure apiClient is exported
import { useEffect } from 'react'


import ChatInterface from './components/ChatInterface'
import GoddessSelection from './components/GoddessSelection'
import LoadingSpinner from './components/LoadingSpinner'
import Header from './components/Header'
import Footer from './components/Footer'

function App() {
  const { isLoading, isAuthenticated, getAccessTokenSilently } = useAuth0()

  useEffect(() => {
    if (!isAuthenticated) return

    const syncUser = async () => {
      const token = await getAccessTokenSilently()
      await apiClient.get('/api/user', {
        headers: { Authorization: `Bearer ${token}` },
      })
    }

    void syncUser()
  }, [isAuthenticated, getAccessTokenSilently])


  if (isLoading) {
    return <LoadingSpinner />
  }

  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-rose-50">
        <Header />
        <main className="mx-auto w-full max-w-6xl px-6 py-10">
          <Routes>
            <Route
              path="/"
              element={isAuthenticated ? <ChatInterface /> : <GoddessSelection />}
            />
            <Route
              path="/chat"
              element={isAuthenticated ? <ChatInterface /> : <Navigate to="/" replace />}
            />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  )
}

export default App
