import axios, { AxiosRequestConfig } from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
const audience = import.meta.env.VITE_AUTH0_AUDIENCE

export const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface ApiCitation {
  id: string
  title: string
  url: string
  source: string
  snippet: string
  published?: string
}

export interface ApiChatMessage {
  id?: string
  role: 'user' | 'assistant'
  content: string
  goddess?: string
  intent?: string
  citations?: ApiCitation[]
  timestamp: string
  suggested?: string
  handoffReason?: string[]
}

export interface ApiChatHistory {
  gaia: ApiChatMessage[]
  athena: ApiChatMessage[]
  aphrodite: ApiChatMessage[]
  artemis: ApiChatMessage[]
  tyche: ApiChatMessage[]
}

export const fetchChatHistory = async (
  getToken: TokenFetcher,
): Promise<ApiChatHistory> => {
  return withAuth<ApiChatHistory>(
    { url: '/api/chat/history', method: 'GET' },
    getToken,
  )
}

export interface ApiChatResponse {
  message: string
  goddess: string
  intent: string
  citations: ApiCitation[]
  timestamp: string
  trace?: Record<string, unknown>
}

export async function confirmHandoff(tokenFetcher: TokenFetcher): Promise<ApiChatResponse> {
  return withAuth(
    { url: '/api/chat/handoff', method: 'POST', data: { action: 'confirm' } },
    tokenFetcher
  )
}

export async function declineHandoff(tokenFetcher: TokenFetcher): Promise<ApiChatResponse> {
  return withAuth(
    { url: '/api/chat/handoff', method: 'POST', data: { action: 'decline' } },
    tokenFetcher
  )
}

export interface GoddessPersona {
  id: string
  display_name: string
  persona: string
  tagline: string
  description?: string
}

export type TokenFetcher = () => Promise<string>

export const createTokenFetcher = (
  getAccessTokenSilently: (options?: { authorizationParams?: { audience?: string } }) => Promise<string>,
): TokenFetcher => {
  if (!audience) {
    throw new Error('VITE_AUTH0_AUDIENCE is not defined')
  }
  return () => getAccessTokenSilently({ authorizationParams: { audience } })
}

export const withAuth = async <T>(
  config: AxiosRequestConfig,
  getToken: TokenFetcher,
): Promise<T> => {
  const token = await getToken()
  const response = await apiClient.request<T>({
    ...config,
    headers: {
      ...(config.headers || {}),
      Authorization: `Bearer ${token}`,
    },
  })
  return response.data
}

export const sendChatMessage = async (
  message: string,
  goddess: string,
  getToken: TokenFetcher,
): Promise<ApiChatResponse> => {
  return withAuth<ApiChatResponse>({
    url: '/api/chat',
    method: 'POST',
    data: { message, goddess },   // <-- include active tab
  }, getToken)
}


export const fetchPersonas = async (): Promise<Record<string, GoddessPersona>> => {
  const response = await apiClient.get<Record<string, GoddessPersona>>('/api/config/personas')
  return response.data
}



