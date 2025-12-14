import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface Conversation {
  message_id: string
  conversation_id: string
  role: string
  text: string
  similarity: number
  create_time?: number
  update_time?: number
}

export interface SearchResponse {
  query: string
  results: Conversation[]
  total: number
  limit: number
  threshold: number
}

export interface Stats {
  total_messages: number
  messages_with_embeddings: number
  role_distribution: Record<string, number>
}

export interface SearchFilters {
  limit?: number
  threshold?: number
  role?: string
  conversation_id?: string
  metric?: string
}

export async function searchConversations(
  query: string,
  filters?: SearchFilters
): Promise<SearchResponse> {
  const params = new URLSearchParams({
    query,
    ...(filters?.limit && { limit: filters.limit.toString() }),
    ...(filters?.threshold && { threshold: filters.threshold.toString() }),
    ...(filters?.role && { role: filters.role }),
    ...(filters?.conversation_id && { conversation_id: filters.conversation_id }),
    ...(filters?.metric && { metric: filters.metric }),
  })

  const response = await api.get<SearchResponse>(`/api/v1/search?${params}`)
  return response.data
}

export async function getStats(): Promise<Stats> {
  const response = await api.get<Stats>('/api/v1/stats')
  return response.data
}



