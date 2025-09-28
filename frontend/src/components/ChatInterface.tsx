import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useAuth0 } from '@auth0/auth0-react'
import { AlertCircle, Bot, ExternalLink, Loader2, Send, Sparkles, User } from 'lucide-react'
import clsx from 'clsx'

import {
  ApiChatMessage,
  ApiCitation,
  ApiChatResponse,
  createTokenFetcher,
  fetchChatHistory,
  fetchPersonas,
  GoddessPersona,
  sendChatMessage,
  TokenFetcher,
} from '../services/api'

interface ChatMessage extends ApiChatMessage {
  id: string
  citations: ApiCitation[]
}

const goddessThemes: Record<string, { avatar: string; accent: string; bubble: string; badge: string }> = {
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
  gaia: {
    avatar: 'bg-goddess-gaia/90',
    accent: 'text-goddess-gaia',
    bubble: 'border-goddess-gaia/40',
    badge: 'bg-goddess-gaia/10 text-goddess-gaia',
  },
}

const getTheme = (goddess?: string) => goddessThemes[goddess ?? 'athena'] ?? goddessThemes.athena

const ChatInterface: React.FC = () => {
  const { isAuthenticated, getAccessTokenSilently } = useAuth0()

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [personas, setPersonas] = useState<Record<string, GoddessPersona>>({})
  const [currentGoddess, setCurrentGoddess] = useState<string>('athena')
  const [inputText, setInputText] = useState('')
  const [isHydrating, setIsHydrating] = useState(true)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const tokenFetcherRef = useRef<TokenFetcher | null>(null)
  const endOfMessagesRef = useRef<HTMLDivElement | null>(null)

  const timeFormatter = useMemo(
    () => new Intl.DateTimeFormat('en-US', { hour: 'numeric', minute: 'numeric' }),
    [],
  )

  useEffect(() => {
    fetchPersonas()
      .then(setPersonas)
      .catch((err) => {
        console.error('Failed to load personas', err)
        setError('Could not load goddess personas. Responses will default to Athena.')
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
        const normalised = history.map((message, idx) => ({
          ...message,
          id: `${message.timestamp}-${idx}`,
          citations: message.citations ?? [],
        }))
        setMessages(normalised)
        const latestAssistant = [...normalised].reverse().find((msg) => msg.role === 'assistant')
        if (latestAssistant?.goddess) {
          setCurrentGoddess(latestAssistant.goddess)
        }
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
  }, [messages, isSending])

  const handleSend = async () => {
    const trimmed = inputText.trim()
    if (!trimmed || isSending) return
    if (!isAuthenticated) return

    setError(null)
    const now = new Date().toISOString()
    const userMessage: ChatMessage = {
      id: `user-${now}`,
      role: 'user',
      content: trimmed,
      timestamp: now,
      citations: [],
    }

    setMessages((prev) => [...prev, userMessage])
    setInputText('')
    setIsSending(true)

    try {
      if (!tokenFetcherRef.current) {
        tokenFetcherRef.current = createTokenFetcher(getAccessTokenSilently)
      }

      const response: ApiChatResponse = await sendChatMessage(trimmed, tokenFetcherRef.current)
      const assistantMessage: ChatMessage = {
        id: `assistant-${response.timestamp}`,
        role: 'assistant',
        content: response.message,
        goddess: response.goddess,
        intent: response.intent,
        timestamp: response.timestamp ?? new Date().toISOString(),
        citations: response.citations ?? [],
      }

      setMessages((prev) => [...prev, assistantMessage])
      if (assistantMessage.goddess) {
        setCurrentGoddess(assistantMessage.goddess)
      }
    } catch (err) {
      console.error('Error sending chat message', err)
      setError('Gaia is taking a quick pause. Try again in a moment.')
      const fallbackMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'I ran into a technical issue reaching my scrolls. Let\'s retry shortly.',
        timestamp: new Date().toISOString(),
        citations: [],
      }
      setMessages((prev) => [...prev, fallbackMessage])
    } finally {
      setIsSending(false)
    }
  }

  const handleKeyPress = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      void handleSend()
    }
  }

  const persona = personas[currentGoddess]
  const theme = getTheme(currentGoddess)

  return (
    <section className="flex flex-col gap-6">
      <header className="rounded-2xl border border-indigo-100 bg-white/70 p-6 shadow-sm backdrop-blur">
        <div className="flex items-start gap-4">
          <div className={clsx('flex h-14 w-14 items-center justify-center rounded-full text-white', theme.avatar)}>
            <Sparkles className="h-7 w-7" />
          </div>
          <div className="flex flex-col gap-1">
            <p className="text-sm uppercase tracking-wide text-indigo-400">Gaia Mentorship</p>
            <h2 className="text-2xl font-semibold text-gray-900">
              {persona?.display_name ?? 'Athena'} is listening
            </h2>
            <p className="max-w-2xl text-sm text-gray-600">
              {persona?.tagline ?? 'Share what you need�Gaia matches you with the right goddess guide for grounded, NJIT-specific help.'}
            </p>
          </div>
        </div>
      </header>

      <div className="flex min-h-[520px] flex-col rounded-3xl border border-gray-200 bg-white/80 shadow-sm backdrop-blur">
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className={clsx('flex h-10 w-10 items-center justify-center rounded-full text-white', theme.avatar)}>
              <Bot className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-900">{persona?.display_name ?? 'Athena'}</p>
              <p className={clsx('text-xs', theme.accent)}>{persona?.tagline ?? 'Strategic wisdom for NJIT students.'}</p>
            </div>
          </div>
          {isSending && (
            <div className="flex items-center gap-2 rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-600">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Composing a grounded reply...
            </div>
          )}
        </div>

        {error && (
          <div className="flex items-center gap-2 border-b border-red-100 bg-red-50 px-6 py-3 text-sm text-red-700">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
          </div>
        )}

        <div className="flex-1 space-y-4 overflow-y-auto px-6 py-6">
          {isHydrating && (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-gray-500">
              <Loader2 className="h-8 w-8 animate-spin" />
              <p>Summoning previous guidance...</p>
            </div>
          )}

          {!isHydrating && messages.length === 0 && (
            <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-indigo-200 bg-indigo-50/40 p-10 text-center">
              <Bot className="h-10 w-10 text-indigo-300" />
              <p className="text-base font-medium text-gray-700">Start the conversation</p>
              <p className="max-w-md text-sm text-gray-500">
                Ask about classes, career moves, campus events, or well-being. Gaia will retrieve real NJIT resources and cite them for you.
              </p>
            </div>
          )}

          {messages.map((message) => {
            const isAssistant = message.role === 'assistant'
            const activeTheme = getTheme(message.goddess ?? currentGoddess)

            return (
              <article
                key={message.id}
                className={clsx('rounded-2xl border bg-white/90 p-4 shadow-sm backdrop-blur', {
                  'border-gray-200': !isAssistant,
                  [activeTheme.bubble]: isAssistant,
                  'ml-auto max-w-[78%]': !isAssistant,
                  'mr-auto max-w-[85%]': isAssistant,
                })}
              >
                <div className="flex items-start gap-3">
                  <div
                    className={clsx('flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full text-white',
                      isAssistant ? activeTheme.avatar : 'bg-gray-400')}
                  >
                    {isAssistant ? <Bot className="h-5 w-5" /> : <User className="h-5 w-5" />}
                  </div>
                  <div className="flex-1 space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-semibold text-gray-900">
                        {isAssistant ? personas[message.goddess ?? currentGoddess]?.display_name ?? 'Gaia' : 'You'}
                      </span>
                      <span className="text-xs text-gray-400">
                        {timeFormatter.format(new Date(message.timestamp))}
                      </span>
                      {isAssistant && message.intent && (
                        <span className={clsx('rounded-full px-2 py-0.5 text-xs font-medium', activeTheme.badge)}>
                          {message.intent}
                        </span>
                      )}
                    </div>
                    <p className="whitespace-pre-wrap text-sm leading-relaxed text-gray-800">
                      {message.content}
                    </p>

                    {isAssistant && message.citations?.length > 0 && (
                      <div className="space-y-1">
                        <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">Sources</p>
                        <div className="flex flex-wrap gap-2">
                          {message.citations.map((citation) => (
                            <a
                              key={`${message.id}-${citation.id}`}
                              href={citation.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className={clsx('inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-medium text-gray-700 transition-colors hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700')}
                            >
                              <ExternalLink className="h-3.5 w-3.5" />
                              {citation.title}
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

          <div ref={endOfMessagesRef} />
        </div>

        <div className="border-t border-gray-100 bg-gray-50/80 px-6 py-4">
          <div className="flex gap-3">
            <textarea
              value={inputText}
              onChange={(event) => setInputText(event.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask Gaia for academics, events, or well-being support..."
              className="min-h-[72px] flex-1 resize-none rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 shadow-inner focus:border-goddess-athena focus:outline-none focus:ring-2 focus:ring-goddess-athena/40"
              disabled={isSending}
            />
            <button
              type="button"
              onClick={() => void handleSend()}
              disabled={!inputText.trim() || isSending}
              className={clsx(
                'flex h-[72px] w-16 items-center justify-center rounded-xl text-white transition',
                isSending ? 'bg-gray-300' : theme.avatar,
                !isSending && 'hover:opacity-90',
              )}
            >
              {isSending ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
            </button>
          </div>
          <p className="mt-2 text-xs text-gray-400">
            Responses cite real NJIT links - no fabricated events.
          </p>
        </div>
      </div>
    </section>
  )
}

export default ChatInterface

