import React, { useEffect, useState } from 'react'
import { useAuth0 } from '@auth0/auth0-react'
import { ArrowRight, BookOpen, Briefcase, Heart } from 'lucide-react'
import clsx from 'clsx'

import { fetchPersonas, GoddessPersona } from '../services/api'

const iconMap: Record<string, JSX.Element> = {
  athena: <BookOpen className="h-8 w-8" />,
  aphrodite: <Heart className="h-8 w-8" />,
  hera: <Briefcase className="h-8 w-8" />,
}

const accentClass: Record<string, string> = {
  athena: 'text-goddess-athena',
  aphrodite: 'text-goddess-aphrodite',
  hera: 'text-goddess-hera',
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
    <section className="mx-auto flex max-w-5xl flex-col gap-10">
      <header className="rounded-3xl border border-indigo-100 bg-white/80 p-10 text-center shadow-sm backdrop-blur">
        <p className="text-sm uppercase tracking-[0.3em] text-indigo-400">Gaia at GirlHacks</p>
        <h1 className="mt-4 text-4xl font-semibold text-gray-900">NJIT mentorship in goddess form</h1>
        <p className="mt-4 text-base text-gray-600">
          Gaia listens to what you need, matches you with a Greek goddess persona, and pulls real NJIT resources from Highlander Hub, Handshake, and support centers. No fluff—just grounded guidance.
        </p>
        <div className="mt-8 flex justify-center">
          <button
            onClick={() => loginWithRedirect()}
            className="flex items-center gap-2 rounded-full bg-goddess-athena px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-200 transition hover:shadow-xl"
          >
            {isAuthenticated ? 'Head to your chat' : 'Log in with your NJIT email'}
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </header>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-3">
        {personas.map((persona) => (
          <article
            key={persona.id}
            className="group relative h-full overflow-hidden rounded-3xl border border-transparent bg-white/80 p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-xl"
          >
            <div className="absolute inset-0 rounded-3xl border border-indigo-100 opacity-0 transition group-hover:opacity-100" />
            <div className="relative flex flex-col gap-4">
              <div className={clsx('inline-flex h-16 w-16 items-center justify-center rounded-full bg-indigo-50 text-indigo-500', accentClass[persona.id] ?? 'text-indigo-500')}>
                {iconMap[persona.id] ?? <SparkleIcon />}
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900">{persona.display_name}</h3>
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
