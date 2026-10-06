/**
 * animations/config.js
 * Central config — tweak durations, eases and stagger here to restyle the whole site.
 */
export const ANIM = {
  // Durations (seconds)
  fast:   0.3,
  normal: 0.5,
  slow:   0.8,
  hero:   1.0,

  // Eases
  ease:       'power3.out',
  easeIn:     'power3.in',
  easeInOut:  'power3.inOut',
  hero_ease:  'expo.out',
  spring:     'elastic.out(1, 0.5)',

  // Stagger
  stagger:     0.08,
  staggerFast: 0.05,

  // Scroll
  scrubSmooth: 1.2,

  // Cursor
  cursorEase: 0.12,   // quickTo lag (lower = tighter follow)
}
