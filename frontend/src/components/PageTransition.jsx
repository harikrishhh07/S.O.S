/**
 * components/PageTransition.jsx
 *
 * Wraps a page with a fast fade+lift entrance on mount.
 * Lightweight — no route-level coordination needed.
 * Uses gsap.context() for proper cleanup.
 */
import { useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { ANIM } from '../animations/config'

export default function PageTransition({ children, className = '' }) {
  const ref = useRef(null)

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

    const ctx = gsap.context(() => {
      gsap.fromTo(
        ref.current,
        { opacity: 0, y: 16 },
        { opacity: 1, y: 0, duration: ANIM.normal, ease: ANIM.ease, clearProps: 'all' }
      )
    }, ref)

    return () => ctx.revert()
  }, [])

  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  )
}
