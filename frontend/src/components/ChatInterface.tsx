import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useAuth0 } from '@auth0/auth0-react'
import {
  AlertCircle,
  Bot,
  ExternalLink,
  Loader2,
  Send,
  User,
} from 'lucide-react'
import clsx from 'clsx'

import {
  ApiChatMessage,
  ApiChatResponse,
  ApiCitation,
  ApiChatHistory,
  createTokenFetcher,
  fetchChatHistory,
  fetchPersonas,
  sendChatMessage,
  TokenFetcher,
  withAuth,
  confirmHandoff,       // <-- NEW
  declineHandoff,       // <-- NEW
} from '../services/api'

import gaiaPortrait from '../Images/Logos/Gaia_Logo.png'
import athenaPortrait from '../Images/Logos/Athena_Logo.png'
import aphroditePortrait from '../Images/Logos/Aphrodite_Logo.png'
import artemisPortrait from '../Images/Logos/Artemis_Logo.png'
import tychePortrait from '../Images/Logos/Tyche_Logo.png'
import gaiaFeature from '../Images/Goddesses/Gaia_noBG.png'
import athenaFeature from '../Images/Goddesses/Athena_noBG.png'
import aphroditeFeature from '../Images/Goddesses/Aphrodite_noBG.png'
import artemisFeature from '../Images/Goddesses/Artemis_noBG.png'
import tycheFeature from '../Images/Goddesses/Tyche_noBG.png'

const goddessTabs = ['gaia', 'athena', 'aphrodite', 'artemis', 'tyche'] as const
type GoddessKey = typeof goddessTabs[number]

interface GoddessPersona {
  key?: GoddessKey
  display_name: string
  tagline?: string
}

interface ChatMessage extends ApiChatMessage {
  id: string
  citations: ApiCitation[]
  intent?: string
  goddess?: GoddessKey
  timestamp: string
  suggested?: GoddessKey
  handoffReason?: string[]
}

// ----- Theming -------------------------------------------------------------

const goddessThemes: Record<
  GoddessKey,
  { avatar: string; accent: string; bubble: string; badge: string }
> = {
  gaia: {
    avatar: 'bg-gradient-to-br from-emerald-500 to-lime-500',
    accent: 'text-emerald-600',
    bubble: 'border-emerald-200',
    badge: 'bg-emerald-50 text-emerald-600',
  },
  athena: {
    avatar: 'bg-goddess-athena/90',
    accent: 'text-goddess-athena',
    bubble: 'border-goddess-athena/40',
    badge: 'bg-goddess-athena/10 text-goddess-athena',
  },
  aphrodite: {
    avatar: 'bg-goddess-aphrodite/90',
    accent: 'text-goddess-aphrodite',
    bubble: 'border-goddess-aphrodite/40',
    badge: 'bg-goddess-aphrodite/10 text-goddess-aphrodite',
  },
  artemis: {
    avatar: 'bg-gradient-to-br from-sky-500 to-cyan-500',
    accent: 'text-sky-600',
    bubble: 'border-sky-200',
    badge: 'bg-sky-50 text-sky-600',
  },
  tyche: {
    avatar: 'bg-gradient-to-br from-amber-500 to-amber-600',
    accent: 'text-amber-600',
    bubble: 'border-amber-200',
    badge: 'bg-amber-50 text-amber-600',
  },
}

const getTheme = (goddess?: GoddessKey) => goddessThemes[goddess ?? 'gaia']

const goddessPortraits: Record<GoddessKey, string> = {
  gaia: gaiaPortrait,
  athena: athenaPortrait,
  aphrodite: aphroditePortrait,
  artemis: artemisPortrait,
  tyche: tychePortrait,
}

const goddessFeatureArt: Record<GoddessKey, string> = {
  gaia: gaiaFeature,
  athena: athenaFeature,
  aphrodite: aphroditeFeature,
  artemis: artemisFeature,
  tyche: tycheFeature,
}

const formatGoddessLabel = (key: GoddessKey) => key.charAt(0).toUpperCase() + key.slice(1)

// ----- Component -----------------------------------------------------------

const ChatInterface: React.FC = () => {
  const { isAuthenticated, getAccessTokenSilently } = useAuth0()

  const [messagesByGoddess, setMessagesByGoddess] = useState<ApiChatHistory>({
    gaia: [],
    athena: [],
    aphrodite: [],
    artemis: [],
    tyche: [],
  })

  const [activeTab, setActiveTab] = useState<GoddessKey>('gaia')
  const [personas, setPersonas] = useState<Partial<Record<GoddessKey, GoddessPersona>>>({})
  const [currentGoddess, setCurrentGoddess] = useState<GoddessKey>('gaia')
  const [inputText, setInputText] = useState('')
  const [isHydrating, setIsHydrating] = useState(true)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pendingRecommendation, setPendingRecommendation] = useState<GoddessKey | null>(null)
  const [pendingTabSwitch, setPendingTabSwitch] = useState<GoddessKey | null>(null)

  const [isHandoffActioning, setIsHandoffActioning] = useState(false)
  const isHandoffPending = !!pendingRecommendation
  const isTabSwitchPending = !!pendingTabSwitch

  const tokenFetcherRef = useRef<TokenFetcher | null>(null)
  const endOfMessagesRef = useRef<HTMLDivElement | null>(null)

  const timeFormatter = useMemo(
    () => new Intl.DateTimeFormat('en-US', { hour: 'numeric', minute: 'numeric' }),
    [],
  )

  useEffect(() => {
    fetchPersonas()
      .then(setPersonas as any)
      .catch(err => {
        console.error('Failed to load personas', err)
        setError('Could not load goddess personas. Responses will default to Gaia.')
      })
  }, [])

  useEffect(() => {
    if (!isAuthenticated) {
      setIsHydrating(false)
      return
    }

    const initialise = async () => {
      setIsHydrating(true)
      try {
        if (!tokenFetcherRef.current) {
          tokenFetcherRef.current = createTokenFetcher(getAccessTokenSilently)
        }
        const history = await fetchChatHistory(tokenFetcherRef.current)
        setMessagesByGoddess(history)
        setActiveTab('gaia')

        const latestAssistant = (
          [...history.gaia, ...history.athena, ...history.aphrodite, ...history.artemis, ...history.tyche] as ApiChatMessage[]
        ).slice().reverse().find(msg => msg.role === 'assistant')

        const latestKey = (latestAssistant?.goddess ?? 'gaia') as GoddessKey
        setCurrentGoddess(latestKey)
      } catch (err) {
        console.error('Failed to load chat history', err)
        setError('Unable to load your earlier conversation. Start fresh with Gaia!')
      } finally {
        setIsHydrating(false)
      }
    }

    void initialise()
  }, [isAuthenticated, getAccessTokenSilently])

  useEffect(() => {
    if (!endOfMessagesRef.current) return
    endOfMessagesRef.current.scrollIntoView({ behavior: 'smooth' })
  }, [messagesByGoddess, activeTab, isSending, pendingRecommendation])

  const handleSend = async (overrideMessage?: string) => {
    const trimmed = (overrideMessage ?? inputText).trim()
    if (!trimmed || isSending) return
    if (!isAuthenticated) return
    if (isHandoffPending || isTabSwitchPending) return

    const sourceTab = activeTab
    setError(null)
    const nowISO = new Date().toISOString()
    const userMessage: ChatMessage = {
      id: `user-${nowISO}`,
      role: 'user',
      content: trimmed,
      goddess: sourceTab,
      timestamp: nowISO,
      citations: [],
    }

    setMessagesByGoddess(prev => ({
      ...prev,
      [sourceTab]: [...prev[sourceTab], userMessage],
    }))
    if (!overrideMessage)     setInputText('')
    setIsSending(true)
    setPendingRecommendation(null)
    setPendingTabSwitch(null)

    try {
      if (!tokenFetcherRef.current) {
        tokenFetcherRef.current = createTokenFetcher(getAccessTokenSilently)
      }

      const response: ApiChatResponse = await sendChatMessage(
      trimmed,
      sourceTab,                    // <-- send current tab
      tokenFetcherRef.current!,
      )


      // Awaiting confirmation -> special assistant bubble with inline UI
      if (response.trace?.stage === 'awaiting_confirmation' && response.trace?.suggested) {
        const suggested = response.trace.suggested as GoddessKey
        setPendingRecommendation(suggested)
        const handoffReason = Array.isArray(response.trace?.['handoff_reason'])
          ? (response.trace['handoff_reason'] as string[])
          : undefined

        const assistantMessage: ChatMessage = {
          id: `assistant-${response.timestamp ?? Date.now()}`,
          role: 'assistant',
          content: response.message || `I can connect you with ${personas[suggested]?.display_name ?? suggested}.`,
          goddess: (response.goddess ?? sourceTab) as GoddessKey,
          intent: response.intent ?? 'handoff_request',
          timestamp: response.timestamp ?? new Date().toISOString(),
          citations: response.citations ?? [],
          suggested,
          handoffReason,
        }
        setMessagesByGoddess(prev => ({
          ...prev,
          [assistantMessage.goddess]: [...prev[assistantMessage.goddess], assistantMessage],
        }))
        return
      }

      // Normal flow
      const assistantMessage: ChatMessage = {
        id: `assistant-${response.timestamp ?? Date.now()}`,
        role: 'assistant',
        content: response.message,
        goddess: (response.goddess ?? 'gaia') as GoddessKey,
        intent: response.intent,
        timestamp: response.timestamp ?? new Date().toISOString(),
        citations: response.citations ?? [],
      }

      setMessagesByGoddess(prev => {
        const destination = assistantMessage.goddess
        const next: ApiChatHistory = { ...prev }

        if (destination !== sourceTab) {
          next[sourceTab] = prev[sourceTab].filter(msg => msg.id !== userMessage.id)
          next[destination] = [
            ...prev[destination],
            { ...userMessage, goddess: destination },
          ]
        } else {
          next[destination] = [...prev[destination]]
        }

        next[destination] = [...next[destination], assistantMessage]
        return next
      })

      // NO AUTO-SWITCHING: Only switch on explicit user confirmation
      // if (response.goddess) {
      //   const key = response.goddess as GoddessKey
      //   setActiveTab(key)
      //   setCurrentGoddess(key)
      // }
    } catch (err) {
      console.error('Error sending chat message', err)
      setError('Gaia is taking a quick pause. Try again in a moment.')
      const fallbackMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        goddess: sourceTab,
        content: "I ran into a technical issue reaching my scrolls. Let's retry shortly.",
        timestamp: new Date().toISOString(),
        citations: [],
      }
      setMessagesByGoddess(prev => ({
        ...prev,
        [sourceTab]: [...prev[sourceTab], fallbackMessage],
      }))
    } finally {
      setIsSending(false)
    }
  }

  // Inline handoff actions
  const handleHandoffAction = async (action: 'confirm' | 'decline') => {
    if (!tokenFetcherRef.current) return
    if (!pendingRecommendation) return
    try {
      setIsHandoffActioning(true)
      const api = action === 'confirm' ? confirmHandoff : declineHandoff
      const response = await api(tokenFetcherRef.current)

      setPendingRecommendation(null)
      setPendingTabSwitch(null)

      const assistantMessage: ChatMessage = {
        id: `assistant-${response.timestamp ?? Date.now()}`,
        role: 'assistant',
        content: response.message,
        goddess: (response.goddess ?? currentGoddess) as GoddessKey,
        intent: response.intent,
        timestamp: response.timestamp ?? new Date().toISOString(),
        citations: response.citations ?? [],
      }
      setMessagesByGoddess(prev => ({
        ...prev,
        [assistantMessage.goddess]: [...prev[assistantMessage.goddess], assistantMessage],
      }))

      if (action === 'confirm' && response.goddess) {
        const key = response.goddess as GoddessKey
        setActiveTab(key)
        setCurrentGoddess(key)
      }
    } catch (err) {
      console.error('Handoff action failed', err)
      setError('Could not complete the handoff. Please try again.')
    } finally {
      setIsHandoffActioning(false)
    }
  }

  // Tab switch confirmation
  const handleTabSwitchAction = (action: 'confirm' | 'decline') => {
    if (action === 'confirm' && pendingTabSwitch) {
      setActiveTab(pendingTabSwitch)
      setCurrentGoddess(pendingTabSwitch)
    }
    setPendingTabSwitch(null)
  }

  const handleReset = async () => {
    if (!tokenFetcherRef.current) return
    try {
      await withAuth({ url: '/api/chat/reset', method: 'POST' }, tokenFetcherRef.current)
      setCurrentGoddess('gaia')
      setActiveTab('gaia')
      setMessagesByGoddess({
        gaia: [],
        athena: [],
        aphrodite: [],
        artemis: [],
        tyche: [],
      })
      setPendingRecommendation(null)
      setPendingTabSwitch(null)
    } catch (error) {
      console.error('Unable to reset goddess selection', error)
    }
  }

  const handleKeyPress = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      void handleSend()
    }
  }

  const persona =
    personas[currentGoddess] ?? {
      display_name: 'Gaia',
      tagline:
        'Share what you need—Gaia matches you with the right goddess guide for grounded, NJIT-specific help.',
    }
  const theme = getTheme(currentGoddess)

  return (
    <section className="flex h-full min-h-0 flex-col gap-6 lg:flex-row lg:items-start">
      <aside className="flex items-center justify-center px-2 sm:px-0 lg:sticky lg:top-16 lg:w-[420px] xl:w-[520px] lg:flex-shrink-0 lg:items-start">
        <img
          src={goddessFeatureArt[currentGoddess]}
          alt={`${persona.display_name} artwork`}
          className="h-auto w-full max-h-[min(78vh,36rem)] object-contain"
        />
      </aside>

      <div className="flex flex-1 min-h-0 flex-col gap-6">
        <header className="rounded-2xl border border-indigo-100 bg-white/70 p-6 shadow-sm backdrop-blur">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4">
              <div
                className={clsx(
                  'relative flex h-20 w-20 flex-shrink-0 items-center justify-center overflow-hidden rounded-2xl border border-indigo-100 bg-white shadow-sm',
                )}
              >
                <img
                  src={goddessPortraits[currentGoddess]}
                  alt={`${persona.display_name} illustration`}
                  className="h-full w-full object-contain"
                />
              </div>
              <div className="flex flex-col gap-1">
                <p className="text-sm uppercase tracking-wide text-[#173b3b]">Gaia Mentorship</p>
                <h2 className="text-2xl font-semibold text-gray-900">
                  {persona.display_name} is listening
                </h2>
                <p className="max-w-2xl text-sm text-gray-600">{persona.tagline}</p>
              </div>
            </div>
            <button
              onClick={() => void handleReset()}
              className="rounded-full border border-gray-300 px-3 py-1 text-xs text-gray-600 hover:border-gray-400 hover:text-gray-900"
            >
              Talk with Gaia again
            </button>
          </div>
        </header>

        {/* CHAT CARD */}
        <div className="flex flex-1 min-h-[520px] flex-col overflow-hidden rounded-3xl border border-gray-200 bg-[#507f6b] shadow-sm backdrop-blur lg:max-h-[70vh] lg:min-h-0">
          {/* Goddess tabs */}
          <div className="flex flex-wrap items-center gap-2 gap-y-2 border-b border-gray-100 px-6 py-3">
            {goddessTabs.map(tab => (
              <button
                key={tab}
                onClick={() => {
                  if (tab !== activeTab) {
                    setPendingTabSwitch(tab)
                  }
                }}
                className={clsx(
                  'rounded-full px-3 py-1 text-xs font-medium transition',
                  tab === activeTab
                    ? 'bg-[#173b3b] text-white hover:opacity-90'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
                )}
              >
                {personas[tab]?.display_name ?? formatGoddessLabel(tab)}
              </button>
            ))}

            {isSending && (
              <div className="flex basis-full justify-end sm:ml-auto sm:basis-auto">
                <div className="inline-flex items-center gap-2 rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-600">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Composing a grounded reply...
                </div>
              </div>
            )}
          </div>

          {/* Error strip */}
          {error && (
            <div className="flex items-center gap-2 border-b border-red-100 bg-red-50 px-6 py-3 text-sm text-red-700">
              <AlertCircle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          )}

          {/* Messages (scroll owner) */}
          <div className="flex-1 min-h-0 space-y-4 overflow-y-auto px-6 py-6">
            {isHydrating && (
              <div className="flex h-full flex-col items-center justify-center gap-3 text-gray-500">
                <Loader2 className="h-8 w-8 animate-spin" />
                <p>Summoning previous guidance...</p>
              </div>
            )}

            {!isHydrating && messagesByGoddess[activeTab].length === 0 && (
              <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-indigo-200 bg-indigo-50/40 p-10 text-center">
                <Bot className="h-10 w-10 text-indigo-300" />
                <p className="text-base font-medium text-gray-700">Start the conversation</p>
                <p className="max-w-md text-sm text-gray-500">
                  Ask about classes, career moves, campus events, or well-being. Gaia will retrieve real NJIT resources and cite them for you.
                </p>
              </div>
            )}

            {messagesByGoddess[activeTab].map(message => {
              const isAssistant = message.role === 'assistant'
              const themedKey = (message.goddess ?? currentGoddess) as GoddessKey
              const activeTheme = getTheme(themedKey)
              const ts = message.timestamp ? new Date(message.timestamp) : new Date()
              const isHandoffCard = isAssistant && message.intent === 'handoff_request'

              return (
                <article
                  key={message.id}
                  className={clsx(
                    'rounded-2xl p-4 shadow-sm backdrop-blur',
                    isAssistant ? 'bg-[#ece5cc]' : 'bg-[#cdb476]',
                    { 'ml-auto max-w-[78%]': !isAssistant, 'mr-auto max-w-[85%]': isAssistant },
                  )}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={clsx(
                        'flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full',
                        isAssistant ? 'overflow-hidden border border-white/60 bg-white p-0.5 shadow-sm' : 'bg-gray-400 text-white',
                      )}
                    >
                      {isAssistant ? (
                        <img
                          src={goddessPortraits[themedKey]}
                          alt={`${personas[themedKey]?.display_name ?? 'Gaia'} avatar`}
                          className="h-full w-full object-contain"
                        />
                      ) : (
                        <User className="h-5 w-5" />
                      )}
                    </div>

                    <div className="flex-1 space-y-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-sm font-semibold text-gray-900">
                          {isAssistant ? personas[themedKey]?.display_name ?? 'Gaia' : 'You'}
                        </span>
                        <span className={clsx('text-xs', isAssistant ? 'text-gray-400' : 'text-[#ece5cc]')}>
                          {timeFormatter.format(ts)}
                        </span>
                        {isAssistant && message.intent && (
                          <span className={clsx('rounded-full px-2 py-0.5 text-xs font-medium', activeTheme.badge, 'bg-[#173b3b] text-white')}>
                            {message.intent}
                          </span>
                        )}
                      </div>

                      {message.content && (
                        <p className="whitespace-pre-wrap text-sm leading-relaxed text-gray-800">
                          {message.content}
                        </p>
                      )}

                      {isHandoffCard && message.suggested && isHandoffPending && (
                        <div className="mt-2 rounded-xl border border-amber-200 bg-amber-50 p-3">
                          <p className="text-sm text-amber-800">
                            {personas[message.suggested]?.display_name ?? message.suggested} can take it from here. Connect you?
                          </p>
                          {message.handoffReason?.length ? (
                            <p className="mt-1 text-xs text-amber-700">Why: {message.handoffReason.join('; ')}</p>
                          ) : null}
                          <div className="mt-2 flex gap-2">
                            <button
                              className={clsx('rounded-full px-3 py-1 text-xs font-semibold text-white', 'bg-amber-600 hover:bg-amber-700 disabled:opacity-60', isHandoffActioning && 'cursor-wait')}
                              disabled={isHandoffActioning}
                              onClick={() => void handleHandoffAction('confirm')}
                            >
                              {isHandoffActioning ? 'Connecting…' : 'Yes, connect me'}
                            </button>
                            <button
                              className="rounded-full border border-amber-400 px-3 py-1 text-xs font-semibold text-amber-700 hover:bg-amber-100 disabled:opacity-60"
                              disabled={isHandoffActioning}
                              onClick={() => void handleHandoffAction('decline')}
                            >
                              Maybe later
                            </button>
                          </div>
                        </div>
                      )}

                      {/* Tab switch confirmation */}
                      {isTabSwitchPending && pendingTabSwitch && (
                        <div className="mt-2 rounded-xl border border-blue-200 bg-blue-50 p-3">
                          <p className="text-sm text-blue-800">
                            Switch to {personas[pendingTabSwitch]?.display_name ?? formatGoddessLabel(pendingTabSwitch)}?
                          </p>
                          <div className="mt-2 flex gap-2">
                            <button
                              className="rounded-full bg-blue-600 px-3 py-1 text-xs font-semibold text-white hover:bg-blue-700"
                              onClick={() => handleTabSwitchAction('confirm')}
                            >
                              Yes, switch
                            </button>
                            <button
                              className="rounded-full border border-blue-400 px-3 py-1 text-xs font-semibold text-blue-700 hover:bg-blue-100"
                              onClick={() => handleTabSwitchAction('decline')}
                            >
                              Stay here
                            </button>
                          </div>
                        </div>
                      )}

                      {isAssistant && message.citations?.length > 0 && (
                        <div className="space-y-1">
                          <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">Sources</p>
                          <div className="flex flex-wrap gap-2">
                            {message.citations.map(citation => (
                              <a
                                key={`${message.id}-${citation.url}`}
                                href={citation.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-medium text-gray-700 transition-colors hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700"
                              >
                                <ExternalLink className="h-3.5 w-3.5" />
                                {citation.title ?? new URL(citation.url).hostname}
                              </a>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </article>
              )
            })}

            <div ref={endOfMessagesRef} className="h-px" />
          </div>

          {/* Footer INSIDE chat card */}
          <div className="border-t border-gray-100 bg-gray-50/80 px-6 py-4 flex-none">
            <div className="flex gap-3">
              <textarea
                value={inputText}
                onChange={event => setInputText(event.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Ask Gaia for academics, events, or well-being support..."
                className="min-h-[72px] flex-1 resize-none rounded-xl border border-[#6b9784] bg-white px-4 py-3 text-sm text-gray-800 shadow-inner focus:border-[#6b9784] focus:outline-none focus:ring-2 focus:ring-[#6b9784]/50"
                disabled={isSending || isHandoffPending || isTabSwitchPending}
              />
              <button
                type="button"
                onClick={() => void handleSend()}
                disabled={!inputText.trim() || isSending || isHandoffPending || isTabSwitchPending}
                className={clsx(
                  'flex h-[72px] w-16 items-center justify-center rounded-xl bg-[#6b9784] text-white transition',
                  isSending ? 'opacity-60' : 'hover:opacity-90',
                )}
              >
                {isSending ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
              </button>
            </div>
            <p className="mt-2 text-xs text-gray-400">Responses cite real NJIT links - no fabricated events.</p>
          </div>
        </div>
      </div>
    </section>
  )
}

export default ChatInterface
