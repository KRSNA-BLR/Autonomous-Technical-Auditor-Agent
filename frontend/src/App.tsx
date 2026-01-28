import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { AlertCircle, RefreshCw } from 'lucide-react'

import { Header } from '@/components/Header'
import { SearchInput } from '@/components/SearchInput'
import { LoadingState } from '@/components/LoadingState'
import { ResultsCard } from '@/components/ResultsCard'
import { MemoryPanel } from '@/components/MemoryPanel'
import { StatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

import { useResearch, useMemory, useExportPdf } from '@/hooks'
import { api, AgentStatus } from '@/lib/api'

function App() {
  // Theme state
  const [isDark, setIsDark] = useState(true)
  
  // API status
  const [status, setStatus] = useState<'online' | 'offline' | 'checking'>('checking')
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null)
  
  // Research hook
  const { result, isLoading, error, stage, progress, research, reset } = useResearch()
  
  // Memory hook
  const { entries, isClearing, clearMemory, addEntry, fetchMemory } = useMemory()
  
  // PDF export hook
  const { exportResultToPdf } = useExportPdf()

  // Toggle theme
  const toggleTheme = useCallback(() => {
    setIsDark(prev => {
      const newValue = !prev
      document.documentElement.classList.toggle('dark', newValue)
      return newValue
    })
  }, [])

  // Check API status
  const checkStatus = useCallback(async () => {
    setStatus('checking')
    try {
      const healthCheck = await api.healthCheck()
      if (healthCheck.status === 'healthy') {
        setStatus('online')
        const agentInfo = await api.getStatus()
        setAgentStatus(agentInfo)
      } else {
        setStatus('offline')
      }
    } catch {
      setStatus('offline')
    }
  }, [])

  // Initial load
  useEffect(() => {
    checkStatus()
    fetchMemory()
  }, [checkStatus, fetchMemory])

  // Handle search
  const handleSearch = async (question: string) => {
    if (!question.trim() || isLoading) return
    
    addEntry(question)
    await research(question)
  }

  // Handle select from memory
  const handleSelectEntry = (question: string) => {
    handleSearch(question)
  }

  // Handle new search
  const handleNewSearch = () => {
    reset()
  }

  // Handle export PDF
  const handleExportPdf = () => {
    if (result) {
      exportResultToPdf(result)
    }
  }

  return (
    <div className={`min-h-screen bg-[hsl(var(--background))] transition-colors`}>
      {/* Header */}
      <Header isDark={isDark} onToggleTheme={toggleTheme} />

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Status Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
        >
          <div>
            <h2 className="text-2xl font-bold text-[hsl(var(--foreground))] mb-1">
              🔬 Investigador Autónomo
            </h2>
            <p className="text-[hsl(var(--muted-foreground))]">
              Realiza investigaciones técnicas con inteligencia artificial
            </p>
          </div>
          <StatusBadge 
            status={status}
            llmAvailable={agentStatus?.llm_available}
            searchAvailable={agentStatus?.search_available}
          />
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Column */}
          <div className="lg:col-span-2 space-y-6">
            {/* Search Input */}
            <AnimatePresence mode="wait">
              {!isLoading && !result && (
                <motion.div
                  key="search"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                >
                  <SearchInput 
                    onSearch={handleSearch}
                    isLoading={isLoading}
                    disabled={status === 'offline'}
                  />
                  
                  {status === 'offline' && (
                    <Card className="mt-4 border-[hsl(var(--destructive))]/50 bg-[hsl(var(--destructive))]/10">
                      <CardContent className="py-4 flex items-center gap-3">
                        <AlertCircle className="w-5 h-5 text-[hsl(var(--destructive))]" />
                        <div className="flex-1">
                          <p className="text-sm font-medium text-[hsl(var(--destructive))]">
                            API no disponible
                          </p>
                          <p className="text-xs text-[hsl(var(--muted-foreground))]">
                            Verifica que el backend esté ejecutándose en http://localhost:8000
                          </p>
                        </div>
                        <Button variant="outline" size="sm" onClick={checkStatus}>
                          <RefreshCw className="w-4 h-4 mr-2" />
                          Reintentar
                        </Button>
                      </CardContent>
                    </Card>
                  )}
                </motion.div>
              )}

              {/* Loading State */}
              {isLoading && (
                <motion.div
                  key="loading"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                >
                  <LoadingState stage={stage} progress={progress} />
                </motion.div>
              )}

              {/* Results */}
              {result && !isLoading && (
                <motion.div
                  key="results"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="space-y-4"
                >
                  <ResultsCard 
                    result={result}
                    onExportPdf={handleExportPdf}
                  />
                  
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.5 }}
                    className="flex justify-center"
                  >
                    <Button 
                      variant="glow" 
                      size="lg"
                      onClick={handleNewSearch}
                    >
                      🔍 Nueva Investigación
                    </Button>
                  </motion.div>
                </motion.div>
              )}

              {/* Error State */}
              {error && !isLoading && (
                <motion.div
                  key="error"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <Card className="border-[hsl(var(--destructive))]/50 bg-[hsl(var(--destructive))]/10">
                    <CardContent className="py-6 text-center">
                      <AlertCircle className="w-12 h-12 mx-auto text-[hsl(var(--destructive))] mb-3" />
                      <p className="font-medium text-[hsl(var(--destructive))]">
                        Error en la investigación
                      </p>
                      <p className="text-sm text-[hsl(var(--muted-foreground))] mt-1">
                        {error}
                      </p>
                      <Button 
                        variant="outline" 
                        className="mt-4"
                        onClick={handleNewSearch}
                      >
                        Intentar de nuevo
                      </Button>
                    </CardContent>
                  </Card>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <MemoryPanel
              entries={entries}
              onClear={clearMemory}
              onSelectEntry={handleSelectEntry}
              isClearing={isClearing}
            />

            {/* Tips Card */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <Card className="bg-gradient-to-br from-[hsl(var(--primary))]/5 to-cyan-500/5 border-[hsl(var(--primary))]/20">
                <CardContent className="py-5">
                  <h3 className="font-semibold text-[hsl(var(--foreground))] mb-3 flex items-center gap-2">
                    💡 Tips de Investigación
                  </h3>
                  <ul className="space-y-2 text-sm text-[hsl(var(--muted-foreground))]">
                    <li className="flex items-start gap-2">
                      <span className="text-[hsl(var(--primary))]">•</span>
                      Sé específico en tus preguntas para mejores resultados
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-[hsl(var(--primary))]">•</span>
                      Incluye contexto técnico relevante
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-[hsl(var(--primary))]">•</span>
                      El agente recuerda conversaciones anteriores
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-[hsl(var(--primary))]">•</span>
                      Exporta reportes a PDF para compartir
                    </li>
                  </ul>
                </CardContent>
              </Card>
            </motion.div>

            {/* Tech Stack Card */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <Card>
                <CardContent className="py-5">
                  <h3 className="font-semibold text-[hsl(var(--foreground))] mb-3 flex items-center gap-2">
                    ⚡ Stack Tecnológico
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {['React', 'FastAPI', 'LangChain', 'Groq', 'DuckDuckGo'].map((tech) => (
                      <span
                        key={tech}
                        className="px-2 py-1 text-xs rounded-full bg-[hsl(var(--muted))] text-[hsl(var(--muted-foreground))]"
                      >
                        {tech}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[hsl(var(--border))] py-6 mt-12">
        <div className="container mx-auto px-4 text-center text-sm text-[hsl(var(--muted-foreground))]">
          <p>
            🚀 Desarrollado por{' '}
            <a 
              href="https://www.linkedin.com/in/danilo-viteri-moreno/"
              className="text-[hsl(var(--primary))] hover:underline font-medium"
              target="_blank"
              rel="noopener noreferrer"
            >
              Danilo Viteri
            </a>
            {' '}|{' '}
            <a 
              href="https://github.com/KRSNA-BLR/Autonomous-Technical-Auditor-Agent"
              className="text-[hsl(var(--primary))] hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              GitHub
            </a>
            {' '}|{' '}
            <a 
              href="https://www.linkedin.com/in/danilo-viteri-moreno/"
              className="text-[hsl(var(--primary))] hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              LinkedIn
            </a>
          </p>
        </div>
      </footer>

      {/* Floating background elements */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <motion.div
          className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-[hsl(var(--primary))]/5 blur-3xl"
          animate={{
            x: [0, 50, 0],
            y: [0, -30, 0],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
        <motion.div
          className="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full bg-cyan-500/5 blur-3xl"
          animate={{
            x: [0, -40, 0],
            y: [0, 40, 0],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      </div>
    </div>
  )
}

export default App
