import { motion } from 'motion/react'
import { Brain, Search as SearchIcon, FileText, CheckCircle } from 'lucide-react'

interface LoadingStateProps {
  stage?: 'thinking' | 'searching' | 'analyzing' | 'synthesizing' | 'idle'
  progress?: number
}

const stages = {
  thinking: {
    icon: Brain,
    text: 'El agente está pensando...',
    subtext: 'Analizando tu pregunta y planificando la investigación',
  },
  searching: {
    icon: SearchIcon,
    text: 'Buscando en internet...',
    subtext: 'Consultando múltiples fuentes de información',
  },
  analyzing: {
    icon: FileText,
    text: 'Analizando la información...',
    subtext: 'Extrayendo puntos clave y verificando datos',
  },
  synthesizing: {
    icon: CheckCircle,
    text: 'Sintetizando resultados...',
    subtext: 'Generando el reporte final con hallazgos',
  },
}

export function LoadingState({ stage = 'thinking', progress = 0 }: LoadingStateProps) {
  const activeStage = stage === 'idle' ? 'thinking' : stage
  const currentStage = stages[activeStage]
  const Icon = currentStage.icon

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="w-full"
    >
      <div className="glass rounded-2xl p-8">
        <div className="flex flex-col items-center justify-center space-y-6">
          {/* Animated Icon */}
          <div className="relative">
            <motion.div
              className="absolute inset-0 rounded-full bg-[hsl(var(--primary))]/20"
              animate={{
                scale: [1, 1.5, 1],
                opacity: [0.5, 0, 0.5],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            />
            <motion.div
              className="relative z-10 w-20 h-20 rounded-full bg-gradient-to-br from-[hsl(var(--primary))] to-cyan-500 flex items-center justify-center"
              animate={{
                rotate: [0, 360],
              }}
              transition={{
                duration: 8,
                repeat: Infinity,
                ease: 'linear',
              }}
            >
              <Icon className="w-10 h-10 text-white" />
            </motion.div>
          </div>

          {/* Progress Text */}
          <div className="text-center space-y-2">
            <motion.h3
              key={stage}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-xl font-semibold text-[hsl(var(--foreground))]"
            >
              {currentStage.text}
            </motion.h3>
            <motion.p
              key={`${stage}-sub`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="text-[hsl(var(--muted-foreground))]"
            >
              {currentStage.subtext}
            </motion.p>
          </div>

          {/* Progress Bar */}
          <div className="w-full max-w-md">
            <div className="h-2 bg-[hsl(var(--muted))] rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-[hsl(var(--primary))] to-cyan-500 rounded-full"
                initial={{ width: '0%' }}
                animate={{ width: `${progress}%` }}
                transition={{
                  duration: 0.5,
                  ease: 'easeOut',
                }}
              />
            </div>
          </div>

          {/* Stage Indicators */}
          <div className="flex items-center gap-3">
            {Object.keys(stages).map((s, index) => (
              <motion.div
                key={s}
                className={`w-3 h-3 rounded-full ${
                  Object.keys(stages).indexOf(stage) >= index
                    ? 'bg-[hsl(var(--primary))]'
                    : 'bg-[hsl(var(--muted))]'
                }`}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: index * 0.1 }}
              />
            ))}
          </div>
        </div>

        {/* Animated Background Pattern */}
        <div className="absolute inset-0 overflow-hidden rounded-2xl pointer-events-none">
          {[...Array(3)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-64 h-64 rounded-full bg-[hsl(var(--primary))]/5"
              style={{
                left: `${20 + i * 30}%`,
                top: `${10 + i * 20}%`,
              }}
              animate={{
                x: [0, 50, 0],
                y: [0, 30, 0],
                scale: [1, 1.2, 1],
              }}
              transition={{
                duration: 5 + i,
                repeat: Infinity,
                ease: 'easeInOut',
                delay: i * 0.5,
              }}
            />
          ))}
        </div>
      </div>
    </motion.div>
  )
}

// Simple skeleton for results
export function ResultsSkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1 }}
          className="glass rounded-xl p-6"
        >
          <div className="space-y-3">
            <div className="h-4 bg-[hsl(var(--muted))] rounded animate-pulse w-3/4" />
            <div className="h-3 bg-[hsl(var(--muted))] rounded animate-pulse w-full" />
            <div className="h-3 bg-[hsl(var(--muted))] rounded animate-pulse w-5/6" />
          </div>
        </motion.div>
      ))}
    </div>
  )
}
