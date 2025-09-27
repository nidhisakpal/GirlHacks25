import React from 'react'
import { Loader2 } from 'lucide-react'

const LoadingSpinner: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 via-pink-50 to-indigo-50">
      <div className="text-center">
        <Loader2 className="w-12 h-12 animate-spin text-goddess-athena mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-700 mb-2">Connecting to Gaia</h2>
        <p className="text-gray-500">Preparing your goddess-guided experience...</p>
      </div>
    </div>
  )
}

export default LoadingSpinner
