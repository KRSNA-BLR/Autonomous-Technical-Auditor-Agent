// ========================================
// TypeScript Types for Research Agent
// ========================================

export interface ResearchQuery {
  question: string
  context?: string
  queryType: 'technical' | 'comparison' | 'troubleshooting' | 'best_practices' | 'general'
  priority: 'low' | 'medium' | 'high' | 'critical'
  maxSources: number
}

export interface ResearchResult {
  queryId: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  synthesis: string
  keyFindings: string[]
  sources: Source[]
  confidenceScore: number
  processingTimeMs: number
  timestamp: Date
}

export interface Source {
  title: string
  url: string
  snippet: string
  credibility?: 'high' | 'medium' | 'low' | 'unknown'
}

export interface MemoryEntry {
  id: string
  question: string
  summary: string
  timestamp: Date
}

export interface ThemeMode {
  theme: 'light' | 'dark'
  toggleTheme: () => void
}

export type LoadingState = 'idle' | 'loading' | 'success' | 'error'

export interface AppState {
  currentQuery: string
  result: ResearchResult | null
  loadingState: LoadingState
  error: string | null
  memoryEntries: MemoryEntry[]
}
