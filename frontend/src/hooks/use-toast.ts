"use client"

import { useState, useEffect } from "react"

export type ToastVariant = "default" | "success" | "destructive"

export interface ToastData {
  id: string
  title?: string
  description?: string
  variant?: ToastVariant
  duration?: number
}

type ToastInput = Omit<ToastData, "id">

// Module-level state shared across all hook instances
const _toasts: ToastData[] = []
const _listeners = new Set<(toasts: ToastData[]) => void>()
const _timers = new Map<string, ReturnType<typeof setTimeout>>()

function _emit() {
  _listeners.forEach((l) => l([..._toasts]))
}

export function dismiss(id: string) {
  const idx = _toasts.findIndex((t) => t.id === id)
  if (idx !== -1) {
    _toasts.splice(idx, 1)
    _emit()
  }
  const timer = _timers.get(id)
  if (timer) {
    clearTimeout(timer)
    _timers.delete(id)
  }
}

export function toast(input: ToastInput) {
  const id = Math.random().toString(36).slice(2, 10)
  const duration = input.duration ?? 4000
  _toasts.push({ id, variant: "default", ...input })
  _emit()
  _timers.set(id, setTimeout(() => dismiss(id), duration))
  return id
}

export function useToast() {
  const [toasts, setToasts] = useState<ToastData[]>([..._toasts])

  useEffect(() => {
    _listeners.add(setToasts)
    return () => { _listeners.delete(setToasts) }
  }, [])

  return { toasts, dismiss }
}
