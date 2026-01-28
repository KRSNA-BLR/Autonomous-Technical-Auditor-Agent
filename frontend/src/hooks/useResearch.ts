import { useState, useCallback } from 'react'
import { api, ResearchResponse } from '@/lib/api'

type Language = 'auto' | 'es' | 'en'

interface ResearchOptions {
  language?: Language
  maxSources?: number
}

interface UseResearchReturn {
  result: ResearchResponse | null
  isLoading: boolean
  error: string | null
  stage: 'idle' | 'thinking' | 'searching' | 'analyzing' | 'synthesizing'
  progress: number
  research: (question: string, options?: ResearchOptions) => Promise<void>
  reset: () => void
}

export function useResearch(): UseResearchReturn {
  const [result, setResult] = useState<ResearchResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [stage, setStage] = useState<'idle' | 'thinking' | 'searching' | 'analyzing' | 'synthesizing'>('idle')
  const [progress, setProgress] = useState(0)

  const research = useCallback(async (question: string, options: ResearchOptions = {}) => {
    const { language = 'auto', maxSources = 8 } = options
    
    setIsLoading(true)
    setError(null)
    setResult(null)
    
    // Simulate stages for UX (real progress would come from backend streaming)
    const stages: Array<'thinking' | 'searching' | 'analyzing' | 'synthesizing'> = [
      'thinking', 'searching', 'analyzing', 'synthesizing'
    ]
    
    let currentStageIndex = 0
    setStage(stages[0])
    setProgress(0)
    
    // Progress simulation
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + Math.random() * 8
        if (newProgress >= 100) {
          return 95 // Cap at 95 until complete
        }
        
        // Update stage based on progress
        const stageProgress = Math.floor(newProgress / 25)
        if (stageProgress > currentStageIndex && stageProgress < stages.length) {
          currentStageIndex = stageProgress
          setStage(stages[currentStageIndex])
        }
        
        return newProgress
      })
    }, 300)

    try {
      const response = await api.research({ question, language, max_sources: maxSources })
      setResult(response)
      setProgress(100)
      setStage('synthesizing')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido')
    } finally {
      clearInterval(progressInterval)
      setIsLoading(false)
      setTimeout(() => setStage('idle'), 500)
    }
  }, [])

  const reset = useCallback(() => {
    setResult(null)
    setError(null)
    setStage('idle')
    setProgress(0)
  }, [])

  return {
    result,
    isLoading,
    error,
    stage,
    progress,
    research,
    reset,
  }
}
