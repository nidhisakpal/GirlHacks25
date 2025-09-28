import React, { useState } from 'react'
import { useAuth0 } from '@auth0/auth0-react'
import { ArrowRight } from 'lucide-react'
import type { GoddessPersona } from '../services/api'
import athenaImg from '../Images/Logos/Athena_Logo.png'
import aphroditeImg from '../Images/Logos/Aphrodite_Logo.png'
import gaiaImg from '../Images/Logos/Gaia_Logo.png'
import artemisImg from '../Images/Logos/Artemis_Logo.png'
import tycheImg from '../Images/Logos/Tyche_Logo.png'

const iconMap: Record<string, { src: string; alt: string; size?: 'md' | 'lg' | 'xl' }> = {
  gaia: { src: gaiaImg, alt: 'Gaia', size: 'xl' },
  athena: { src: athenaImg, alt: 'Athena', size: 'md' },
  aphrodite: { src: aphroditeImg, alt: 'Aphrodite', size: 'md' },
  artemis: { src: artemisImg, alt: 'Artemis', size: 'md' },
  tyche: { src: tycheImg, alt: 'Tyche', size: 'md' },
}

const customPersonas: GoddessPersona[] = [
  {
    id: 'athena',
    display_name: 'Athena',
    tagline: 'Academic strategist',
    persona: '',
    description: 'Your wise guide for academic success, study strategies, and research support.',
  },
  {
    id: 'aphrodite',
    display_name: 'Aphrodite',
    tagline: 'Community and care',
    persona: '',
    description: 'Your compassionate mentor for mental wellness, relationships, and self-care.',
  },
  {
    id: 'gaia',
    display_name: 'Gaia',
    tagline: 'Well-being guide',
    persona: '',
    description: 'Your nurturing mother figure who connects you with the right specialist for any need.',
  },
  {
    id: 'artemis',
    display_name: 'Artemis',
    tagline: 'Career trailblazer',
    persona: '',
    description: 'Your career champion for internships, job searches, and professional development.',
  },
  {
    id: 'tyche',
    display_name: 'Tyche',
    tagline: 'Opportunity scout',
    persona: '',
    description: 'Your financial advisor for scholarships, grants, and funding opportunities.',
  },
]

// Tooltip component
interface TooltipProps {
  content: string
  children: React.ReactNode
  isVisible: boolean
}

const Tooltip: React.FC<TooltipProps> = ({ content, children, isVisible }) => (
  <div className="relative">
    {children}
    {isVisible && (
      <div className="absolute top-full left-1/2 z-50 mt-2 -translate-x-1/2 transform">
        <div className="rounded-lg bg-[#f5f5dc] px-2 py-1.5 text-xs text-gray-800 shadow-lg border border-gray-200">
          <div className="max-w-sm w-48 text-center leading-relaxed">{content}</div>
          {/* Arrow */}
          <div className="absolute left-1/2 bottom-full -translate-x-1/2 transform">
            <div className="border-l-4 border-r-4 border-b-4 border-transparent border-b-[#f5f5dc]"></div>
          </div>
        </div>
      </div>
    )}
  </div>
)

const GoddessSelection: React.FC = () => {
  const { loginWithRedirect, isAuthenticated } = useAuth0()
  const personas = customPersonas
  const [hoveredGoddess, setHoveredGoddess] = useState<string | null>(null)

  return (
    <section className="mx-auto flex max-w-5xl flex-col gap-5">
      <header className="p-5 text-center">
        <h1
          className="text-5xl font-bold"
          style={{ color: '#e5d39e', fontFamily: '"Cinzel", serif' }}
        >
          DISCOVER YOUR <br /> INNER GODDESS
        </h1>
        <p className="text-lg font-light" style={{ fontFamily: '"Inter", sans-serif', color: '#e5d39e'}}>
          Guidance & mentorship for campus women
        </p>
        <div className="mt-4 flex justify-center">
          <button
            onClick={() => loginWithRedirect()}
            className="flex items-center gap-2 rounded-full px-6 py-3 text-sm font-semibold text-[#1f1a2d] shadow-lg shadow-indigo-300 transition hover:shadow-xl"
            style={{ backgroundColor: '#bda55c', fontFamily: '"Inter", sans-serif'}}
          >
            {isAuthenticated ? 'Head to your chat' : 'Log in with Auth0'}
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </header>

      <div className="flex flex-nowrap items-start justify-center gap-8">
        {personas.map(persona => {
          const icon = iconMap[persona.id]

          const sizeClass = icon?.size === 'xl'
            ? 'h-32 w-32'
            : icon?.size === 'lg'
              ? 'h-28 w-28'
              : 'h-24 w-24'

          return (
            <Tooltip 
              key={persona.id}
              content={persona.description || persona.tagline}
              isVisible={hoveredGoddess === persona.id}
            >
              <div
                className="flex w-32 flex-col items-center gap-3 text-center transition-transform duration-200 hover:scale-105 cursor-pointer"
                onMouseEnter={() => setHoveredGoddess(persona.id)}
                onMouseLeave={() => setHoveredGoddess(null)}
              >
                <div className="flex h-32 w-32 items-center justify-center">
                  {icon ? (
                    <img src={icon.src} alt={icon.alt} className={`rounded-full object-cover ${sizeClass}`} />
                  ) : (
                    <SparkleIcon />
                  )}
                </div>
                <span className="text-sm font-semibold uppercase tracking-[0.2em] text-[#f7ba2a]">
                  {persona.display_name}
                </span>
              </div>
            </Tooltip>
          )
        })}
      </div>
    </section>
  )
}

const SparkleIcon = () => (
  <svg className="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
)

export default GoddessSelection
