import React, { useEffect, useState } from 'react'
import { useAuth0 } from '@auth0/auth0-react'
import { ArrowRight} from 'lucide-react'
import clsx from 'clsx'
import { fetchPersonas, GoddessPersona } from '../services/api'
import athenaImg from '../Images/Logos/Athena_Logo.png'
import aphroditeImg from '../Images/Logos/Aphrodite_Logo.png'
import gaiaImg from '../Images/Logos/Gaia_Logo.png'
import artemisImg from '../Images/Logos/Artemis_Logo.png'
import tycheImg from '../Images/Logos/Tyche_Logo.png'

const iconMap: Record<string, JSX.Element> = {
  athena: <img src={athenaImg} alt="Athena" className="h-16 w-16 rounded-full object-cover" />,
  aphrodite: <img src={aphroditeImg} alt="Aphrodite" className="h-16 w-16 rounded-full object-cover" />,
  artemis: <img src={artemisImg} alt="Artemis" className="h-16 w-16 rounded-full object-cover" />,
  tyche: <img src={tycheImg} alt="Tyche" className="h-16 w-16 rounded-full object-cover" />,
  gaia: <img src={gaiaImg} alt="Gaia" className="h-16 w-16 rounded-full object-cover" />,
}

const accentClass: Record<string, string> = {
  athena: 'text-goddess-athena',
  aphrodite: 'text-goddess-aphrodite',
  gaia: 'text-goddess-gaia',
}

const GoddessSelection: React.FC = () => {
  const { loginWithRedirect, isAuthenticated } = useAuth0()
  const [personas, setPersonas] = useState<GoddessPersona[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPersonas()
      .then((data) => setPersonas(Object.values(data)))
      .catch((err) => {
        console.error('Failed to load personas', err)
        setError('Unable to load goddess profiles right now. Please try again soon.')
      })
  }, [])

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

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="flex flex-wrap justify-center gap-6">
        {personas.map((persona) => (
          <article
            key={persona.id}
            className="group relative h-full w-[calc(25%-1.5rem)] min-w-[220px] overflow-hidden rounded-3xl border border-white/20 bg-white/10 p-6 shadow-sm backdrop-blur-lg transition hover:-translate-y-1 hover:shadow-xl"
          >
            <div className="absolute inset-0 rounded-3xl border border-indigo-100 opacity-0 transition group-hover:opacity-100" />
            <div className="relative flex flex-col gap-4">
              <div className={clsx('inline-flex h-16 w-16 items-center justify-center rounded-full bg-indigo-50 text-indigo-500', accentClass[persona.id] ?? 'text-indigo-500')}>
                {iconMap[persona.id] ?? <SparkleIcon />}
              </div>
              <div>
                <h3 className="text-xl font-semibold" style={{ color: '#e5d39e' }}>
                  {persona.display_name}
                </h3>
                <p className={clsx('text-sm font-medium', accentClass[persona.id] ?? 'text-indigo-500')}>{persona.tagline}</p>
              </div>
              <p className="text-sm leading-relaxed text-gray-600">
                {persona.persona}
              </p>
            </div>
          </article>
        ))}
      </div>

      <footer className="rounded-3xl border border-gray-200 bg-gray-50/70 p-6 text-sm text-gray-600">
        <p className="font-medium text-gray-800">What happens next?</p>
        <ul className="mt-3 list-disc space-y-1 pl-5">
          <li>Authenticate with your NJIT account via Auth0.</li>
          <li>Tell Gaia what you need—academics, well-being, or career.</li>
          <li>Each reply cites NJIT resources so you can follow through quickly.</li>
        </ul>
      </footer>
    </section>
  )
}

const SparkleIcon = () => (
  <svg className="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
)

export default GoddessSelection
