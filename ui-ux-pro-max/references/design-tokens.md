# Design Tokens Reference

## Token Naming Convention

Tokens follow a 3-tier hierarchy:

```
[category].[group].[variant]

Examples:
  color.surface.primary
  color.text.secondary
  spacing.component.padding-md
  typography.body.size
  radius.card
  shadow.elevation.1
  motion.duration.fast
  motion.easing.enter
```

**Tier 1 — Global (primitives)**
Raw values. Never used directly in components.
```
global.color.gray.100: #F3F4F6
global.color.gray.900: #111827
global.spacing.4: 4px
```

**Tier 2 — Semantic (alias)**
Named by purpose, references a global token. Used in components.
```
color.surface.primary: {global.color.white}
color.text.secondary: {global.color.gray.500}
spacing.layout.section-gap: {global.spacing.64}
```

**Tier 3 — Component (scoped)**
Component-specific overrides. References semantic tokens.
```
button.primary.background: {color.interactive.primary}
button.primary.text: {color.text.on-primary}
```

---

## Color Token System

### Surface Tokens

| Token | Light Value | Dark Value | Usage |
|-------|-------------|------------|-------|
| `color.surface.primary` | #FFFFFF | #0F1117 | Main page background |
| `color.surface.secondary` | #F9FAFB | #161B22 | Sidebar, panels |
| `color.surface.tertiary` | #F3F4F6 | #1C2128 | Inline backgrounds, code blocks |
| `color.surface.overlay` | rgba(0,0,0,0.5) | rgba(0,0,0,0.7) | Modal backdrop |
| `color.surface.inverse` | #111827 | #F9FAFB | Dark surface on light, light surface on dark |

### Text Tokens

| Token | Light Value | Dark Value | Usage |
|-------|-------------|------------|-------|
| `color.text.primary` | #111827 | #F0F6FC | Body text, headings |
| `color.text.secondary` | #6B7280 | #8B949E | Labels, descriptions |
| `color.text.tertiary` | #9CA3AF | #6E7681 | Placeholders, disabled |
| `color.text.on-primary` | #FFFFFF | #FFFFFF | Text on dark/brand backgrounds |
| `color.text.link` | #2563EB | #58A6FF | Hyperlinks |
| `color.text.error` | #DC2626 | #F85149 | Error messages |
| `color.text.success` | #16A34A | #3FB950 | Success messages |

### Border Tokens

| Token | Light Value | Dark Value | Usage |
|-------|-------------|------------|-------|
| `color.border.default` | #E5E7EB | #30363D | Default dividers, card borders |
| `color.border.strong` | #D1D5DB | #484F58 | Input borders on hover |
| `color.border.focus` | #005FCC | #58A6FF | Focus rings |
| `color.border.error` | #DC2626 | #F85149 | Error state borders |

### Interactive Tokens

| Token | Light Value | Dark Value | Usage |
|-------|-------------|------------|-------|
| `color.interactive.primary` | #000000 | #F0F6FC | Primary button background |
| `color.interactive.primary-hover` | #1A1A1A | #E6EDF3 | Primary button hover |
| `color.interactive.secondary-hover` | #F3F4F6 | #21262D | Ghost/secondary hover bg |
| `color.interactive.destructive` | #DC2626 | #F85149 | Destructive actions |
| `color.interactive.destructive-hover` | #B91C1C | #DA3633 | Destructive hover |

### Status Tokens

| Token | Light Value | Usage |
|-------|-------------|-------|
| `color.status.success-bg` | #F0FDF4 | Success toast/banner background |
| `color.status.success-border` | #22C55E | Success accent |
| `color.status.error-bg` | #FFF5F5 | Error toast/banner background |
| `color.status.error-border` | #EF4444 | Error accent |
| `color.status.warning-bg` | #FFFBEB | Warning background |
| `color.status.warning-border` | #F59E0B | Warning accent |
| `color.status.info-bg` | #EFF6FF | Info background |
| `color.status.info-border` | #3B82F6 | Info accent |

---

## Spacing Scale

Base unit: **4px**

| Token | Value | Usage |
|-------|-------|-------|
| `spacing.1` | 4px | Micro gaps — icon to label, tight badge padding |
| `spacing.2` | 8px | Component internal padding small, inline gaps |
| `spacing.3` | 12px | Input vertical padding, small button padding |
| `spacing.4` | 16px | Default component padding, section internal padding |
| `spacing.5` | 20px | Card padding, medium component spacing |
| `spacing.6` | 24px | Section padding, modal padding |
| `spacing.8` | 32px | Between sections on mobile |
| `spacing.10` | 40px | Large section gaps |
| `spacing.12` | 48px | Section padding on desktop |
| `spacing.16` | 64px | Between major page sections |
| `spacing.20` | 80px | Hero top padding |
| `spacing.24` | 96px | Page-level vertical rhythm |

### Semantic Spacing Tokens

```
spacing.component.padding-xs: {spacing.1}     — 4px
spacing.component.padding-sm: {spacing.2}     — 8px
spacing.component.padding-md: {spacing.3}     — 12px 16px (vertical/horizontal)
spacing.component.padding-lg: {spacing.4}     — 16px 24px
spacing.component.gap-xs:     {spacing.1}     — 4px
spacing.component.gap-sm:     {spacing.2}     — 8px
spacing.component.gap-md:     {spacing.4}     — 16px
spacing.layout.column-gap:    {spacing.6}     — 24px
spacing.layout.section-gap:   {spacing.16}    — 64px
spacing.layout.page-padding-mobile: {spacing.4}  — 16px
spacing.layout.page-padding-desktop: {spacing.6} — 24px
```

---

## Typography Scale

Base: **16px** (1rem = 16px). Scale ratio: **1.25 (Major Third)**

| Token | Size | Line Height | Weight | Usage |
|-------|------|-------------|--------|-------|
| `typography.display.size` | 48px | 1.1 | 700 | Hero headlines |
| `typography.h1.size` | 36px | 1.2 | 700 | Page titles |
| `typography.h2.size` | 28px | 1.25 | 600 | Section headings |
| `typography.h3.size` | 22px | 1.3 | 600 | Subsection headings |
| `typography.h4.size` | 18px | 1.4 | 600 | Card titles, labels |
| `typography.body-lg.size` | 16px | 1.6 | 400 | Primary body copy |
| `typography.body.size` | 14px | 1.5 | 400 | UI body text, descriptions |
| `typography.body-sm.size` | 13px | 1.4 | 400 | Secondary labels, captions |
| `typography.caption.size` | 12px | 1.4 | 400 | Timestamps, meta info |
| `typography.overline.size` | 11px | 1.2 | 600 | Table headers, section labels |

### Font Stack Tokens

```
typography.font-family.sans:  "Inter", "system-ui", "-apple-system", sans-serif
typography.font-family.mono:  "JetBrains Mono", "Fira Code", "Consolas", monospace
typography.font-family.serif: "Georgia", "Cambria", serif  — use sparingly
```

### Responsive Typography Rules

- Headings scale down 2 steps at < 768px (h1 → 28px, display → 36px)
- Body text stays at 16px on mobile — NEVER below 16px on iOS (prevents zoom)
- Line-height loosens 0.1 on mobile for readability
- Maximum line length: 70ch desktop, 45ch mobile

---

## Border Radius Scale

| Token | Value | Usage |
|-------|-------|-------|
| `radius.none` | 0px | Tables, code blocks |
| `radius.xs` | 2px | Badges, tags |
| `radius.sm` | 4px | Inputs, small buttons |
| `radius.md` | 6px | Buttons, cards (default) |
| `radius.lg` | 8px | Modals, dropdowns, large cards |
| `radius.xl` | 12px | Sheets, popovers |
| `radius.2xl` | 16px | Bottom sheets, large panels |
| `radius.full` | 9999px | Pills, avatar circles, toggle |

---

## Shadow / Elevation Scale

| Token | Value | Usage |
|-------|-------|-------|
| `shadow.elevation.0` | none | Flat, flush elements |
| `shadow.elevation.1` | `0 1px 3px rgba(0,0,0,0.06)` | Cards at rest |
| `shadow.elevation.2` | `0 4px 12px rgba(0,0,0,0.10)` | Cards on hover, floating inputs |
| `shadow.elevation.3` | `0 8px 24px rgba(0,0,0,0.12)` | Dropdowns, popovers |
| `shadow.elevation.4` | `0 20px 60px rgba(0,0,0,0.15)` | Modals, dialogs |
| `shadow.focus` | `0 0 0 3px rgba(0, 95, 204, 0.4)` | Focus ring — alternative to outline |

**Dark mode adjustment:** reduce shadow opacity by 50%, increase blur by 20%.

---

## Motion Tokens

### Duration

| Token | Value | Usage |
|-------|-------|-------|
| `motion.duration.instant` | 75ms | Micro-interactions (checkbox tick, toggle click) |
| `motion.duration.fast` | 150ms | Hover state changes, color transitions |
| `motion.duration.normal` | 200ms | Element state changes (expand, collapse small) |
| `motion.duration.moderate` | 300ms | Entrances, exits (modals, drawers) |
| `motion.duration.slow` | 500ms | Complex layout transitions, page transitions |

### Easing

| Token | Value | Usage |
|-------|-------|-------|
| `motion.easing.linear` | `linear` | Progress bars, loaders |
| `motion.easing.enter` | `cubic-bezier(0.0, 0.0, 0.2, 1)` | Elements entering the screen (ease-out) |
| `motion.easing.exit` | `cubic-bezier(0.4, 0.0, 1, 1)` | Elements leaving the screen (ease-in) |
| `motion.easing.standard` | `cubic-bezier(0.4, 0.0, 0.2, 1)` | Elements moving on screen (ease-in-out) |
| `motion.easing.spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Playful entrances (slight overshoot) |
| `motion.easing.decelerate` | `cubic-bezier(0.0, 0.0, 0.2, 1)` | Decelerate to rest |

### Reduced Motion

Always include this in components with animation:
```css
@media (prefers-reduced-motion: reduce) {
  /* Remove transform-based animations */
  /* Replace opacity fades with instant show/hide */
  /* Keep functional state changes (color, border for focus) */
}
```

---

## Breakpoints

| Token | Value | Strategy |
|-------|-------|----------|
| `breakpoint.xs` | 480px | Small phones |
| `breakpoint.sm` | 640px | Large phones |
| `breakpoint.md` | 768px | Tablets |
| `breakpoint.lg` | 1024px | Small laptops |
| `breakpoint.xl` | 1280px | Desktop |
| `breakpoint.2xl` | 1536px | Large desktop |

**Mobile-first rule:** write base styles for < 640px, then override upward with `@media (min-width: X)`.

---

## Z-Index Scale

| Token | Value | Usage |
|-------|-------|-------|
| `z.base` | 0 | Default stacking |
| `z.raised` | 10 | Floating elements, sticky table headers |
| `z.dropdown` | 30 | Dropdowns, popovers |
| `z.sticky` | 40 | Sticky nav, toolbars |
| `z.overlay` | 50 | Modal backdrop |
| `z.modal` | 51 | Modal content |
| `z.toast` | 60 | Toast notifications |
| `z.tooltip` | 70 | Tooltips (above toasts) |

---

## Grid System

### 12-Column Grid (Web)

| Breakpoint | Columns | Gutter | Margin |
|------------|---------|--------|--------|
| < 640px | 4 | 16px | 16px |
| 640px–1024px | 8 | 20px | 24px |
| > 1024px | 12 | 24px | 32px |

Container max-width: 1280px, centered.

### Common Layout Patterns

```
Full-width:          span 12 / span 8 / span 4
Two-column equal:    span 6  / span 8 / span 4
Main + sidebar:      span 8 + span 4  / span 8 (stacked) / span 4 (stacked)
Three-column equal:  span 4  / span 4 (stacked above 768) / span 4 (stacked)
Card grid (3-up):    repeat(3, 1fr) / repeat(2, 1fr) / 1fr
```

---

## WCAG 2.1 AA Contrast Reference

| Use Case | Minimum Ratio | Notes |
|----------|---------------|-------|
| Normal text (< 18px) | 4.5:1 | Most body text |
| Large text (≥ 18px or ≥ 14px bold) | 3:1 | Headings |
| UI components and graphic borders | 3:1 | Input borders, button boundaries |
| Decorative elements | No requirement | Pure decoration only |
| Disabled states | No requirement | Must still look disabled visually |
| Focus indicators | 3:1 against adjacent colors | Critical for keyboard navigation |

**Quick reference — #000000 on common backgrounds:**

| Background | Ratio | Pass? |
|------------|-------|-------|
| #FFFFFF | 21:1 | ✅ AA + AAA |
| #F9FAFB | 19.6:1 | ✅ |
| #F3F4F6 | 17.1:1 | ✅ |
| #E5E7EB | 13.5:1 | ✅ |
| #D1D5DB | 9.7:1 | ✅ |
| #9CA3AF | 4.0:1 | ⚠️ Fails for body text, passes for large text |
| #6B7280 | 5.9:1 | ✅ AA |
| #374151 | 10.7:1 | ✅ |
