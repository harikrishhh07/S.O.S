/**
 * animations/usePageAnimations.js
 *
 * Drop this hook into any page component to get:
 *   - Staggered entrance for .anim-hero-* elements on mount
 *   - ScrollTrigger fade+slide reveals for [data-reveal] elements
 *   - ScrollTrigger batch reveals for [data-reveal-batch] lists
 *
 * Usage:
 *   const containerRef = usePageAnimations()
 *   return <div ref={containerRef}> ... </div>
 */
import { useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { ANIM } from './config'

gsap.registerPlugin(ScrollTrigger)

export function usePageAnimations(options = {}) {
  const {
    hero   = true,   // animate .anim-hero-* on mount
    scroll = true,   // wire up [data-reveal] and [data-reveal-batch]
  } = options

  const containerRef = useRef(null)

  useEffect(() => {
    // Respect reduced motion
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    const ctx = gsap.context(() => {

      // ── Hero entrance ──────────────────────────────────────────────────────
      if (hero && !prefersReduced) {
        const tl = gsap.timeline({ defaults: { ease: ANIM.hero_ease } })

        // Set initial state for all hero elements
        gsap.set('.anim-hero-title',   { y: 40, opacity: 0 })
        gsap.set('.anim-hero-sub',     { y: 30, opacity: 0 })
        gsap.set('.anim-hero-cta',     { y: 20, opacity: 0, scale: 0.95 })
        gsap.set('.anim-hero-item',    { y: 24, opacity: 0 })

        tl.to('.anim-hero-title', { y: 0, opacity: 1, duration: ANIM.hero,   stagger: ANIM.stagger })
          .to('.anim-hero-sub',   { y: 0, opacity: 1, duration: ANIM.slow,   stagger: ANIM.stagger }, '-=0.5')
          .to('.anim-hero-cta',   { y: 0, opacity: 1, duration: ANIM.normal, scale: 1, stagger: ANIM.staggerFast }, '-=0.4')
          .to('.anim-hero-item',  { y: 0, opacity: 1, duration: ANIM.normal, stagger: ANIM.staggerFast }, '-=0.3')
      } else if (hero) {
        // Reduced: just make visible
        gsap.set(['.anim-hero-title', '.anim-hero-sub', '.anim-hero-cta', '.anim-hero-item'], { opacity: 1, y: 0 })
      }

      // ── Scroll reveals ─────────────────────────────────────────────────────
      if (scroll) {
        // Individual elements: [data-reveal] or [data-reveal="up|left|right|scale"]
        containerRef.current?.querySelectorAll('[data-reveal]').forEach(el => {
          const dir = el.dataset.reveal || 'up'
          const from = {
            up:    { y: 40,  opacity: 0 },
            left:  { x: -40, opacity: 0 },
            right: { x: 40,  opacity: 0 },
            scale: { scale: 0.92, opacity: 0 },
            fade:  { opacity: 0 },
          }[dir] || { y: 40, opacity: 0 }

          if (!prefersReduced) {
            gsap.from(el, {
              ...from,
              duration: ANIM.slow,
              ease:     ANIM.ease,
              scrollTrigger: {
                trigger: el,
                start:   'top 88%',
                once:    true,
              },
            })
          }
        })

        // Batch lists: [data-reveal-batch] on a container, children animate as a wave
        containerRef.current?.querySelectorAll('[data-reveal-batch]').forEach(container => {
          const children = Array.from(container.children)
          if (!children.length) return

          if (!prefersReduced) {
            ScrollTrigger.batch(children, {
              start:    'top 90%',
              once:     true,
              onEnter:  batch => gsap.from(batch, {
                y:        30,
                opacity:  0,
                duration: ANIM.normal,
                ease:     ANIM.ease,
                stagger:  ANIM.stagger,
              }),
            })
          }
        })
      }

    }, containerRef)

    return () => ctx.revert()   // cleanup: kills tweens + ScrollTriggers scoped to this context
  }, [hero, scroll])

  return containerRef
}
