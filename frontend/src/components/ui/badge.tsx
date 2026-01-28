import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))] focus:ring-offset-2',
  {
    variants: {
      variant: {
        default:
          'border-transparent bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] shadow',
        secondary:
          'border-transparent bg-[hsl(var(--secondary))] text-[hsl(var(--secondary-foreground))]',
        destructive:
          'border-transparent bg-[hsl(var(--destructive))] text-[hsl(var(--destructive-foreground))] shadow',
        outline: 'text-[hsl(var(--foreground))]',
        success:
          'border-transparent bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
        warning:
          'border-transparent bg-amber-500/10 text-amber-500 border-amber-500/20',
        info:
          'border-transparent bg-blue-500/10 text-blue-500 border-blue-500/20',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
