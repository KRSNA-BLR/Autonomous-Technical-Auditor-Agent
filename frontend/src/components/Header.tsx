import { motion } from 'motion/react'
import { Moon, Sun, Microscope, Github, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface HeaderProps {
  isDark: boolean
  onToggleTheme: () => void
}

export function Header({ isDark, onToggleTheme }: HeaderProps) {
  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="sticky top-0 z-50 glass border-b border-[hsl(var(--border))]"
    >
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo */}
        <motion.div 
          className="flex items-center gap-3"
          whileHover={{ scale: 1.02 }}
        >
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[hsl(var(--primary))] to-cyan-500 flex items-center justify-center">
              <Microscope className="w-6 h-6 text-white" />
            </div>
            <motion.div
              className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-emerald-500"
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
          </div>
          <div>
            <h1 className="font-bold text-lg text-[hsl(var(--foreground))]">
              Research Agent
            </h1>
            <p className="text-xs text-[hsl(var(--muted-foreground))] flex items-center gap-1">
              <Zap className="w-3 h-3 text-amber-500" />
              Powered by AI
            </p>
          </div>
        </motion.div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleTheme}
            className="rounded-full"
          >
            <motion.div
              initial={false}
              animate={{ rotate: isDark ? 180 : 0 }}
              transition={{ duration: 0.3 }}
            >
              {isDark ? (
                <Sun className="w-5 h-5" />
              ) : (
                <Moon className="w-5 h-5" />
              )}
            </motion.div>
          </Button>

          <Button
            variant="outline"
            size="sm"
            asChild
            className="hidden sm:flex"
          >
            <a
              href="https://github.com/KRSNA-BLR/Autonomous-Technical-Auditor-Agent"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Github className="w-4 h-4 mr-2" />
              GitHub
            </a>
          </Button>
        </div>
      </div>
    </motion.header>
  )
}
