import { motion } from 'motion/react'
import { 
  CheckCircle2, 
  Clock, 
  Star, 
  Copy, 
  Check,
  ExternalLink,
  ChevronDown,
  ChevronUp
} from 'lucide-react'
import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { ResearchResponse } from '@/lib/api'

interface ResultsCardProps {
  result: ResearchResponse
  onExportPdf: () => void
}

export function ResultsCard({ result, onExportPdf }: ResultsCardProps) {
  const [copied, setCopied] = useState(false)
  const [showAllSources, setShowAllSources] = useState(false)

  const handleCopy = async () => {
    const text = `
# Resultado de Investigación

## Síntesis
${result.synthesis}

## Hallazgos Clave
${result.key_findings.map((f, i) => `${i + 1}. ${f}`).join('\n')}

## Fuentes
${result.sources.map((s) => `- ${s.title}: ${s.url}`).join('\n')}

---
Confianza: ${Math.round(result.confidence_score * 100)}%
Tiempo de procesamiento: ${result.processing_time_ms}ms
    `.trim()

    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'success'
    if (score >= 0.6) return 'warning'
    return 'destructive'
  }

  const displayedSources = showAllSources ? result.sources : result.sources.slice(0, 3)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full"
      id="research-result"
    >
      <Card className="overflow-hidden">
        {/* Header with gradient */}
        <div className="h-2 bg-gradient-to-r from-[hsl(var(--primary))] via-cyan-500 to-[hsl(var(--primary))]" />
        
        <CardHeader className="pb-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', delay: 0.2 }}
              >
                <CheckCircle2 className="w-6 h-6 text-emerald-500" />
              </motion.div>
              <CardTitle className="text-xl">Resultado de la Investigación</CardTitle>
            </div>
            
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={handleCopy}>
                {copied ? (
                  <>
                    <Check className="w-4 h-4 text-emerald-500" />
                    Copiado
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    Copiar
                  </>
                )}
              </Button>
              <Button variant="default" size="sm" onClick={onExportPdf}>
                📄 Exportar PDF
              </Button>
            </div>
          </div>

          {/* Stats badges */}
          <div className="flex flex-wrap gap-2 mt-3">
            <Badge variant={getConfidenceColor(result.confidence_score)}>
              <Star className="w-3 h-3 mr-1" />
              Confianza: {Math.round(result.confidence_score * 100)}%
            </Badge>
            <Badge variant="secondary">
              <Clock className="w-3 h-3 mr-1" />
              {(result.processing_time_ms / 1000).toFixed(1)}s
            </Badge>
            <Badge variant="info">
              📚 {result.sources.length} fuentes
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Synthesis Section */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="space-y-2"
          >
            <h4 className="font-semibold text-lg flex items-center gap-2">
              📌 Síntesis
            </h4>
            <p className="text-[hsl(var(--muted-foreground))] leading-relaxed">
              {result.synthesis}
            </p>
          </motion.div>

          {/* Key Findings */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="space-y-3"
          >
            <h4 className="font-semibold text-lg flex items-center gap-2">
              🎯 Hallazgos Clave
            </h4>
            <ul className="space-y-2">
              {result.key_findings.map((finding, index) => (
                <motion.li
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 + index * 0.1 }}
                  className="flex items-start gap-3 p-3 rounded-lg bg-[hsl(var(--muted))]/50"
                >
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-[hsl(var(--primary))]/20 text-[hsl(var(--primary))] flex items-center justify-center text-sm font-medium">
                    {index + 1}
                  </span>
                  <span className="text-[hsl(var(--foreground))]">{finding}</span>
                </motion.li>
              ))}
            </ul>
          </motion.div>

          {/* Sources */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="space-y-3"
          >
            <h4 className="font-semibold text-lg flex items-center gap-2">
              📚 Fuentes Consultadas
            </h4>
            <div className="space-y-2">
              {displayedSources.map((source, index) => (
                <motion.a
                  key={index}
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.7 + index * 0.1 }}
                  className="block p-3 rounded-lg border border-[hsl(var(--border))] hover:border-[hsl(var(--primary))]/50 hover:bg-[hsl(var(--muted))]/30 transition-all group"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="space-y-1 flex-1">
                      <p className="font-medium text-[hsl(var(--foreground))] group-hover:text-[hsl(var(--primary))] transition-colors flex items-center gap-2">
                        🔗 {source.title}
                        <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </p>
                      <p className="text-sm text-[hsl(var(--muted-foreground))] line-clamp-2">
                        {source.snippet}
                      </p>
                    </div>
                  </div>
                </motion.a>
              ))}
            </div>

            {result.sources.length > 3 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowAllSources(!showAllSources)}
                className="w-full"
              >
                {showAllSources ? (
                  <>
                    <ChevronUp className="w-4 h-4 mr-2" />
                    Ver menos fuentes
                  </>
                ) : (
                  <>
                    <ChevronDown className="w-4 h-4 mr-2" />
                    Ver todas las fuentes ({result.sources.length})
                  </>
                )}
              </Button>
            )}
          </motion.div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
