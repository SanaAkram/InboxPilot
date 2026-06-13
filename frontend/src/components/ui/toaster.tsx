"use client"

import { CheckCircle2, XCircle, Info } from "lucide-react"
import { useToast, dismiss } from "@/hooks/use-toast"
import {
  Toast,
  ToastClose,
  ToastDescription,
  ToastProvider,
  ToastTitle,
  ToastViewport,
} from "@/components/ui/toast"

const ICONS = {
  default: <Info className="h-4 w-4 mt-0.5 shrink-0 text-foreground/50" />,
  success: <CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0 text-green-600 dark:text-green-400" />,
  destructive: <XCircle className="h-4 w-4 mt-0.5 shrink-0 text-destructive" />,
}

export function Toaster() {
  const { toasts } = useToast()

  return (
    <ToastProvider swipeDirection="right">
      {toasts.map(({ id, title, description, variant = "default" }) => (
        <Toast
          key={id}
          variant={variant}
          onOpenChange={(open) => { if (!open) dismiss(id) }}
        >
          {ICONS[variant]}
          <div className="flex-1 min-w-0">
            {title && <ToastTitle>{title}</ToastTitle>}
            {description && <ToastDescription>{description}</ToastDescription>}
          </div>
          <ToastClose />
        </Toast>
      ))}
      <ToastViewport />
    </ToastProvider>
  )
}
