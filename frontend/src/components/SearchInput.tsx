import { useState, useRef, useEffect } from 'react'
import { motion } from 'motion/react'
import { Search, Sparkles, Loader2 } from 'lucide-react'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'

interface SearchInputProps {
  onSearch: (query: string) => void
  isLoading: boolean
  placeholder?: string
  disabled?: boolean
}

export function SearchInput({ 
  onSearch, 
  isLoading, 
  placeholder = '¿Qué quieres investigar hoy? Ejemplo: "¿Cuáles son las mejores prácticas de seguridad para APIs REST?"',
  disabled = false
}: SearchInputProps) {
  const [query, setQuery] = useState('')
  const [isFocused, setIsFocused] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim() && !isLoading && !disabled) {
      onSearch(query.trim())
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }, [query])

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full"
    >
      <form onSubmit={handleSubmit} className="relative">
        {/* Glow Effect Background */}
        <motion.div
          className="absolute -inset-1 rounded-2xl opacity-75 blur-xl"
          animate={{
            background: isFocused
              ? [
                  'linear-gradient(90deg, rgba(139,92,246,0.4) 0%, rgba(6,182,212,0.4) 50%, rgba(139,92,246,0.4) 100%)',
                  'linear-gradient(90deg, rgba(6,182,212,0.4) 0%, rgba(139,92,246,0.4) 50%, rgba(6,182,212,0.4) 100%)',
                  'linear-gradient(90deg, rgba(139,92,246,0.4) 0%, rgba(6,182,212,0.4) 50%, rgba(139,92,246,0.4) 100%)',
                ]
              : 'linear-gradient(90deg, rgba(139,92,246,0.2) 0%, rgba(6,182,212,0.2) 100%)',
          }}
          transition={{ duration: 3, repeat: Infinity }}
        />

        {/* Input Container */}
        <div className="relative glass rounded-2xl p-1">
          <div className="flex items-start gap-3 bg-[hsl(var(--card))] rounded-xl p-4">
            <motion.div
              animate={{ rotate: isLoading ? 360 : 0 }}
              transition={{ duration: 2, repeat: isLoading ? Infinity : 0, ease: 'linear' }}
              className="mt-1"
            >
              {isLoading ? (
                <Loader2 className="w-6 h-6 text-[hsl(var(--primary))]" />
              ) : (
                <Sparkles className="w-6 h-6 text-[hsl(var(--primary))]" />
              )}
            </motion.div>

            <div className="flex-1">
              <Textarea
                ref={textareaRef}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                onKeyDown={handleKeyDown}
                placeholder={placeholder}
                disabled={isLoading}
                className="border-0 p-0 focus-visible:ring-0 focus-visible:ring-offset-0 min-h-[60px] text-base resize-none bg-transparent"
              />
            </div>

            <Button
              type="submit"
              disabled={!query.trim() || isLoading}
              variant="glow"
              size="lg"
              className="shrink-0"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Investigando...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  Investigar
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Helper Text */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="text-center text-sm text-[hsl(var(--muted-foreground))] mt-3"
        >
          Presiona <kbd className="px-1.5 py-0.5 rounded bg-[hsl(var(--muted))] text-xs font-mono">Enter</kbd> para buscar
          o <kbd className="px-1.5 py-0.5 rounded bg-[hsl(var(--muted))] text-xs font-mono">Shift+Enter</kbd> para nueva línea
        </motion.p>
      </form>
    </motion.div>
  )
}
