import React from 'react'
import { CalendarDays, Database } from 'lucide-react'

const lastIndexed = import.meta.env.VITE_LAST_INDEXED ?? 'Today'

const Footer: React.FC = () => {
  return (
    <footer className="mt-16" style={{ backgroundColor: '#e5d39e', color: '#173b3b' }}>
      <div className="mx-auto flex max-w-6xl flex-col px-6 py-3 text-sm md:flex-row md:items-center md:justify-between" style={{ color: '#173b3b' }}>
        <div className="flex items-center gap-3">
          <Database className="h-4 w-4" color="#173b3b" />
          <span>Indexed NJIT resources refreshed: {lastIndexed}</span>
        </div>
        <div className="flex items-center gap-4 text-xs" style={{ color: '#173b3b' }}>
          <span className="inline-flex items-center gap-1"><CalendarDays className="h-3.5 w-3.5" color="#173b3b" /> GirlHacks 2025</span>
          <span>Gaia Mentorship prototype - Built with FastAPI + React</span>
        </div>
      </div>
    </footer>
  )
}

export default Footer
