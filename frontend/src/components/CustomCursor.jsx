import { useEffect } from 'react'

export default function CustomCursor() {
  useEffect(() => {
    const media = window.matchMedia('(pointer: coarse)')
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)')

    if (media.matches || reducedMotion.matches) return

    const root = document.documentElement
    root.style.cursor = 'default'

    return () => {
      root.style.cursor = ''
    }
  }, [])

  return null
}
