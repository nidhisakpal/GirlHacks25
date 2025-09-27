import React from 'react'
import { CalendarDays, Database } from 'lucide-react'

const lastIndexed = import.meta.env.VITE_LAST_INDEXED ?? 'Today'

const Footer: React.FC = () => {
  return (
    <footer className="mt-16 border-t border-gray-200 bg-white/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-6 py-6 text-sm text-gray-500 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <Database className="h-4 w-4" />
          <span>Indexed NJIT resources refreshed: {lastIndexed}</span>
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-400">
          <span className="inline-flex items-center gap-1"><CalendarDays className="h-3.5 w-3.5" /> GirlHacks 2025</span>
          <span>Gaia Mentorship prototype - Built with FastAPI + React</span>
        </div>
      </div>
    </footer>
  )
}

export default Footer

