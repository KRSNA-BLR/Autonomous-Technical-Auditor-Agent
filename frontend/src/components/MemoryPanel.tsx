import { motion, AnimatePresence } from 'motion/react'
import { Trash2, Clock, MessageSquare, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatTimeAgo } from '@/lib/utils'

interface MemoryEntry {
  question: string
  timestamp: string
}

interface MemoryPanelProps {
  entries: MemoryEntry[]
  onClear: () => void
  onSelectEntry: (question: string) => void
  isClearing: boolean
}

export function MemoryPanel({ 
  entries, 
  onClear, 
  onSelectEntry,
  isClearing 
}: MemoryPanelProps) {
  if (entries.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Card className="border-dashed">
          <CardContent className="py-8 text-center">
            <MessageSquare className="w-12 h-12 mx-auto text-[hsl(var(--muted-foreground))]/50 mb-3" />
            <p className="text-[hsl(var(--muted-foreground))]">
              No hay consultas en memoria
            </p>
            <p className="text-sm text-[hsl(var(--muted-foreground))]/70 mt-1">
              Tus investigaciones aparecerán aquí
            </p>
          </CardContent>
        </Card>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              💾 Memoria del Agente
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClear}
              disabled={isClearing}
              className="text-[hsl(var(--destructive))] hover:text-[hsl(var(--destructive))] hover:bg-[hsl(var(--destructive))]/10"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Limpiar
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          <AnimatePresence>
            {entries.map((entry, index) => (
              <motion.button
                key={`${entry.question}-${index}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ delay: index * 0.05 }}
                onClick={() => onSelectEntry(entry.question)}
                className="w-full group"
              >
                <div className="flex items-center gap-3 p-3 rounded-lg border border-transparent hover:border-[hsl(var(--border))] hover:bg-[hsl(var(--muted))]/30 transition-all text-left">
                  <Clock className="w-4 h-4 text-[hsl(var(--muted-foreground))] shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-[hsl(var(--foreground))] truncate group-hover:text-[hsl(var(--primary))] transition-colors">
                      {entry.question}
                    </p>
                    <p className="text-xs text-[hsl(var(--muted-foreground))]">
                      {formatTimeAgo(new Date(entry.timestamp))}
                    </p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-[hsl(var(--muted-foreground))] opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </motion.button>
            ))}
          </AnimatePresence>
        </CardContent>
      </Card>
    </motion.div>
  )
}
