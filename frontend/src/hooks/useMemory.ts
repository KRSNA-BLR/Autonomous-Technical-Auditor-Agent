import { useState, useCallback, useRef } from 'react'
import { api, MemoryState } from '@/lib/api'

interface MemoryEntry {
  question: string
  timestamp: string
}

interface UseMemoryReturn {
  entries: MemoryEntry[]
  isLoading: boolean
  isClearing: boolean
  error: string | null
  fetchMemory: () => Promise<void>
  clearMemory: () => Promise<void>
  addEntry: (question: string) => void
}

export function useMemory(): UseMemoryReturn {
  const [entries, setEntries] = useState<MemoryEntry[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isClearing, setIsClearing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const hasFetched = useRef(false)

  const fetchMemory = useCallback(async () => {
    if (hasFetched.current) return
    
    setIsLoading(true)
    setError(null)
    
    try {
      const response: MemoryState = await api.getMemory()
      // Transform memory context to entries
      const memoryEntries: MemoryEntry[] = response.entries || []
      setEntries(memoryEntries)
      hasFetched.current = true
    } catch (err) {
      // Memory might not be available initially
      console.log('Memory not available yet')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const clearMemory = useCallback(async () => {
    setIsClearing(true)
    setError(null)
    
    try {
      await api.clearMemory()
      setEntries([])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error limpiando memoria')
    } finally {
      setIsClearing(false)
    }
  }, [])

  const addEntry = useCallback((question: string) => {
    setEntries(prev => [
      { question, timestamp: new Date().toISOString() },
      ...prev.slice(0, 9) // Keep max 10 entries
    ])
  }, [])

  return {
    entries,
    isLoading,
    isClearing,
    error,
    fetchMemory,
    clearMemory,
    addEntry,
  }
}
