import { motion } from 'motion/react'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'

interface StatusBadgeProps {
  status: 'online' | 'offline' | 'checking'
  llmAvailable?: boolean
  searchAvailable?: boolean
}

export function StatusBadge({ status, llmAvailable, searchAvailable }: StatusBadgeProps) {
  const getStatusConfig = () => {
    switch (status) {
      case 'online':
        return {
          icon: CheckCircle,
          text: 'Online',
          variant: 'success' as const,
        }
      case 'offline':
        return {
          icon: XCircle,
          text: 'Offline',
          variant: 'destructive' as const,
        }
      case 'checking':
        return {
          icon: Loader2,
          text: 'Verificando...',
          variant: 'secondary' as const,
        }
    }
  }

  const config = getStatusConfig()
  const Icon = config.icon

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex flex-wrap items-center gap-2"
    >
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className={`w-3 h-3 ${status === 'checking' ? 'animate-spin' : ''}`} />
        {config.text}
      </Badge>

      {status === 'online' && (
        <>
          <Badge variant={llmAvailable ? 'success' : 'warning'}>
            🤖 LLM: {llmAvailable ? 'OK' : '⚠️'}
          </Badge>
          <Badge variant={searchAvailable ? 'success' : 'warning'}>
            🔍 Search: {searchAvailable ? 'OK' : '⚠️'}
          </Badge>
        </>
      )}
    </motion.div>
  )
}
