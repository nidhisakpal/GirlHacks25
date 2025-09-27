import React from 'react'
import { Clock, Database } from 'lucide-react'

const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t border-gray-200 mt-12">
      <div className="container mx-auto px-4 py-6">
        <div className="flex justify-between items-center text-sm text-gray-500">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <Database className="w-4 h-4" />
              <span>Last indexed: {new Date().toLocaleString()}</span>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <span>© 2024 Gaia Mentorship</span>
            <span>•</span>
            <span>NJIT GirlHacks25</span>
          </div>
        </div>
      </div>
    </footer>
  )
}

export default Footer
