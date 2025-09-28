import { BrowserRouter as Router, Navigate, Route, Routes } from 'react-router-dom'
import { useAuth0 } from '@auth0/auth0-react'
import { apiClient } from './services/api'   // make sure apiClient is exported
import { useEffect } from 'react'


import ChatInterface from './components/ChatInterface'
import GoddessSelection from './components/GoddessSelection'
import LoadingSpinner from './components/LoadingSpinner'
import Homepage from './components/Homepage'
import Footer from './components/Footer'
import BackgroundShapes from './components/BackgroundShapes'

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
      <div className="relative min-h-screen overflow-hidden bg-[#173b3b]">
        <BackgroundShapes />
        <div className="relative z-10">
          <main className="mx-auto w-full max-w-6xl px-6 py-10">
            <Routes>
              <Route
                path="/"
                element={(
                  <Homepage>
                    {isAuthenticated ? <ChatInterface /> : <GoddessSelection />}
                  </Homepage>
                )}
              />
              <Route
                path="/chat"
                element={isAuthenticated ? <ChatInterface /> : <Navigate to="/" replace />}
              />
            </Routes>
          </main>
          <Footer />
        </div>
      </div>
    </Router>
  )
}

export default App
