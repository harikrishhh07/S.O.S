/**
 * animations/useCardTilt.js
 *
 * Adds a gentle 3D tilt following the pointer to any element.
 * Automatically reversed and interruptible.
 *
 * Usage:
 *   const tiltRef = useCardTilt()
 *   return <div ref={tiltRef}> ... </div>
 *
 * Options:
 *   maxTilt  — degrees of max rotation (default 6)
 *   scale    — scale on hover (default 1.02)
 */
import { useRef, useCallback } from 'react'
import { gsap } from 'gsap'
import { ANIM } from './config'

export function useCardTilt({ maxTilt = 6, scale = 1.02 } = {}) {
  const ref = useRef(null)

  const onMove = useCallback((e) => {
    const el = ref.current
    if (!el) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

    const rect = el.getBoundingClientRect()
    // Normalise mouse position to -1 … +1 relative to element center
    const nx = ((e.clientX - rect.left) / rect.width  - 0.5) * 2
    const ny = ((e.clientY - rect.top)  / rect.height - 0.5) * 2

    gsap.to(el, {
      rotateY:  nx * maxTilt,
      rotateX: -ny * maxTilt,
      scale,
      duration: 0.4,
      ease:     ANIM.ease,
      overwrite: 'auto',
      transformPerspective: 800,
    })
  }, [maxTilt, scale])

  const onLeave = useCallback(() => {
    const el = ref.current
    if (!el) return
    gsap.to(el, {
      rotateX: 0,
      rotateY: 0,
      scale:   1,
      duration: ANIM.slow,
      ease:     ANIM.spring,
      overwrite: 'auto',
    })
  }, [])

  // Attach via callback ref so it works with dynamic elements
  const setRef = useCallback((node) => {
    if (ref.current) {
      ref.current.removeEventListener('mousemove',  onMove)
      ref.current.removeEventListener('mouseleave', onLeave)
    }
    if (node) {
      node.addEventListener('mousemove',  onMove)
      node.addEventListener('mouseleave', onLeave)
      // Enable hardware layer
      node.style.willChange = 'transform'
      node.style.transformStyle = 'preserve-3d'
    }
    ref.current = node
  }, [onMove, onLeave])

  return setRef
}
