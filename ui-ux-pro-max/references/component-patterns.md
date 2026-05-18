# Component Pattern Templates

## Button

```
Component: Button
Variants: primary | secondary | ghost | destructive | link
Sizes: sm (32px height) | md (40px height) | lg (48px height)

[Primary — Default]
  background: #000000
  color: #FFFFFF
  border: none
  border-radius: 6px
  padding: 10px 18px (md) | 6px 12px (sm) | 14px 24px (lg)
  font: 14px/1 weight 500 letter-spacing 0

[Primary — Hover]
  background: #1a1a1a
  transition: background 150ms ease-in-out

[Primary — Active]
  background: #333333
  transform: translateY(1px)

[Primary — Disabled]
  background: #E5E7EB
  color: #9CA3AF
  cursor: not-allowed
  pointer-events: none

[Primary — Loading]
  background: #000000 (unchanged)
  color: transparent
  position: relative
  spinner: 16px white centered absolute

[Focus — all variants]
  outline: 3px solid #005FCC
  outline-offset: 2px

[Secondary — Default]
  background: transparent
  border: 1.5px solid #D1D5DB
  color: #111827

[Secondary — Hover]
  border-color: #9CA3AF
  background: #F9FAFB

[Ghost — Default]
  background: transparent
  border: none
  color: #374151

[Ghost — Hover]
  background: #F3F4F6

[Destructive — Default]
  background: #DC2626
  color: #FFFFFF

[Destructive — Hover]
  background: #B91C1C

Accessibility:
  role: button (or <button> element — never <div>)
  aria-disabled="true" when disabled (not HTML disabled alone)
  aria-busy="true" + aria-label="Loading" when loading
  Keyboard: Enter and Space activate

Mobile:
  Minimum tap target: 44px height (increase padding on sm variant)
  Full-width option at < 480px: add w-full class or width: 100%
```

---

## Form Input

```
Component: Text Input
States: default | focus | filled | error | disabled

[Default]
  height: 40px
  background: #FFFFFF
  border: 1.5px solid #D1D5DB
  border-radius: 6px
  padding: 0 12px
  font: 14px/1.5 weight 400 color #111827
  placeholder color: #9CA3AF

[Focus]
  border: 2px solid #000000
  outline: none (use border change as focus indicator)
  background: #FFFFFF

[Filled]
  border: 1.5px solid #D1D5DB
  background: #FFFFFF

[Error]
  border: 2px solid #DC2626
  background: #FFF5F5

[Disabled]
  background: #F9FAFB
  border: 1.5px solid #E5E7EB
  color: #9CA3AF
  cursor: not-allowed

Label:
  font: 13px weight 500 color #374151
  margin-bottom: 6px
  position: above input always (never placeholder as label)

Error message:
  font: 13px weight 400 color #DC2626
  margin-top: 4px
  display: flex align-items: center gap: 4px
  icon: 14px error icon before text

Helper text:
  font: 13px weight 400 color #6B7280
  margin-top: 4px

Accessibility:
  <label> with for= always required
  aria-describedby pointing to error/helper text ID
  aria-invalid="true" on error state
  role: textbox (implicit on <input type="text">)

Mobile:
  height: 44px (iOS tap target)
  font-size: 16px minimum (prevents iOS auto-zoom)
```

---

## Modal / Dialog

```
Component: Modal
Sizes: sm (400px) | md (560px) | lg (720px) | fullscreen (mobile default)

Overlay:
  background: rgba(0, 0, 0, 0.5)
  position: fixed inset 0
  z-index: 50
  backdrop-filter: blur(2px) — optional, check performance

Dialog container:
  background: #FFFFFF
  border-radius: 12px
  padding: 24px
  max-width: [size variant]
  width: calc(100% - 48px)
  max-height: calc(100vh - 96px)
  overflow-y: auto
  position: fixed
  top: 50% left: 50%
  transform: translate(-50%, -50%)
  z-index: 51
  box-shadow: 0 20px 60px rgba(0,0,0,0.15)

Header:
  display: flex justify-content: space-between align-items: flex-start
  margin-bottom: 16px
  Title: 18px weight 600 color #111827
  Close button: 32x32px ghost icon button top-right

Body:
  font: 14px/1.6 color #374151

Footer:
  display: flex justify-content: flex-end gap: 8px
  margin-top: 24px
  padding-top: 16px
  border-top: 1px solid #E5E7EB

Enter animation:
  overlay: opacity 0→1 150ms ease-out
  dialog: opacity 0→1 + scale(0.95)→scale(1) 200ms ease-out

Exit animation:
  overlay: opacity 1→0 100ms ease-in
  dialog: opacity 1→0 + scale(1)→scale(0.97) 150ms ease-in

Accessibility:
  role="dialog"
  aria-modal="true"
  aria-labelledby pointing to title ID
  Focus trap: first focusable element on open, restore trigger on close
  Escape key closes
  Click overlay closes (unless form with unsaved changes)

Mobile (< 640px):
  Position: bottom sheet — fixed bottom 0, width 100%, border-radius 16px 16px 0 0
  max-height: 90vh
  drag handle: 4px × 32px rounded bar, centered, 8px from top
  Enter: translateY(100%)→translateY(0) 300ms spring
```

---

## Navigation (Top Nav / Header)

```
Component: Top Navigation
Height: 56px desktop | 52px mobile

Container:
  position: sticky top: 0
  z-index: 40
  background: #FFFFFF
  border-bottom: 1px solid transparent
  transition: border-color 200ms ease
  [on scroll > 20px]: border-color #E5E7EB + box-shadow: 0 1px 8px rgba(0,0,0,0.06)

Inner layout:
  max-width: 1280px
  margin: 0 auto
  padding: 0 24px
  height: 100%
  display: flex align-items: center justify-content: space-between

Logo:
  height: 28px auto-width
  link to /

Nav links (desktop):
  display: flex gap: 4px
  font: 14px weight 500 color #374151
  padding: 6px 12px
  border-radius: 6px
  [hover]: background #F3F4F6 color #111827
  [active/current]: color #000000 background #F3F4F6
  transition: 150ms ease

CTA area:
  display: flex align-items: center gap: 8px

Mobile (< 768px):
  Hide nav links
  Show hamburger button (24px icon, 40px tap target)
  Mobile menu: full-width overlay, position fixed inset 0 top 52px
  background: #FFFFFF
  Nav links: stack vertically, full-width, 48px height each, 16px horizontal padding

Accessibility:
  <nav> element with aria-label="Main navigation"
  Current page link: aria-current="page"
  Mobile menu button: aria-expanded, aria-controls pointing to menu ID
  Mobile menu: role="navigation"
```

---

## Card

```
Component: Card
Variants: default | interactive (clickable) | selected | skeleton

[Default]
  background: #FFFFFF
  border: 1px solid #E5E7EB
  border-radius: 8px
  padding: 20px
  box-shadow: 0 1px 3px rgba(0,0,0,0.06)

[Interactive — Default]
  cursor: pointer
  transition: box-shadow 150ms ease, border-color 150ms ease, transform 150ms ease

[Interactive — Hover]
  box-shadow: 0 4px 12px rgba(0,0,0,0.10)
  border-color: #D1D5DB
  transform: translateY(-1px)

[Interactive — Active]
  transform: translateY(0)
  box-shadow: 0 1px 3px rgba(0,0,0,0.06)

[Selected]
  border: 2px solid #000000
  background: #FAFAFA

[Skeleton]
  All content replaced with animated gradient placeholder blocks
  Gradient: background: linear-gradient(90deg, #F3F4F6 25%, #E5E7EB 50%, #F3F4F6 75%)
  background-size: 200% 100%
  animation: shimmer 1.5s infinite
  border-radius: 4px on each placeholder

Accessibility (interactive cards):
  role="button" or <a> (if navigates) or <button> (if action)
  tabindex="0"
  aria-label describing the card's action or destination
  Keyboard: Enter/Space activates
  Focus ring: 3px solid #005FCC offset 2px

Mobile:
  Remove hover transform (no hover on touch)
  Increase tap area — ensure padding ≥ 16px
```

---

## Table

```
Component: Data Table

Container:
  overflow-x: auto (horizontal scroll on mobile)
  border: 1px solid #E5E7EB
  border-radius: 8px

Table:
  width: 100%
  border-collapse: collapse
  font: 14px/1.5 color #374151

Header row:
  background: #F9FAFB
  border-bottom: 1px solid #E5E7EB
  th: padding 10px 16px, font 12px weight 600 color #6B7280 text-transform uppercase letter-spacing 0.05em
  Sortable th: cursor pointer, display flex align-items center gap 4px
  Sort icon: 16px, color #9CA3AF (unsorted), #000000 (active)

Body row:
  border-bottom: 1px solid #F3F4F6
  [hover]: background #F9FAFB
  td: padding 12px 16px

  [last row]: border-bottom: none

Striped variant:
  even rows: background #F9FAFB

Empty state:
  Single row, full colspan
  height: 200px
  text centered: 14px color #9CA3AF
  icon above text: 24px

Loading state:
  Replace rows with 5 skeleton rows
  Skeleton cells: 60–80% width, height 16px, shimmer animation

Pagination:
  display flex justify-content space-between align-items center
  padding 12px 16px
  border-top: 1px solid #E5E7EB
  Left: "Showing X–Y of Z results" — 13px color #6B7280
  Right: Previous / Next buttons + page numbers

Accessibility:
  <table> with role="grid" if interactive
  <caption> (visually hidden if design requires)
  <th scope="col"> for column headers
  <th scope="row"> for row headers
  aria-sort="ascending|descending|none" on sortable headers
  Keyboard: Tab moves between interactive cells, Enter activates
```

---

## Dropdown / Select

```
Component: Dropdown Menu
Trigger: any button component

Menu container:
  position: absolute
  z-index: 30
  background: #FFFFFF
  border: 1px solid #E5E7EB
  border-radius: 8px
  box-shadow: 0 8px 24px rgba(0,0,0,0.10)
  padding: 4px
  min-width: 180px
  max-height: 320px
  overflow-y: auto

Menu item:
  padding: 8px 12px
  border-radius: 6px
  font: 14px weight 400 color #374151
  cursor: pointer
  display: flex align-items: center gap: 8px

  [hover]: background #F3F4F6 color #111827
  [active/selected]: background #F3F4F6 color #000000 font-weight 500
  [destructive]: color #DC2626
  [destructive hover]: background #FEF2F2

  Icon slot: 16px, left-aligned
  Checkmark: 16px, right-aligned (for selected state in multi-select)

Divider:
  height: 1px background #E5E7EB margin: 4px 0

Section label:
  padding: 6px 12px 2px
  font: 11px weight 600 color #9CA3AF text-transform uppercase letter-spacing 0.06em

Open animation:
  opacity 0→1 + translateY(-4px)→translateY(0) 150ms ease-out

Close animation:
  opacity 1→0 100ms ease-in

Positioning:
  Default: below trigger, left-aligned
  Auto-flip: if bottom overflow → position above
  Auto-flip: if right overflow → right-align

Accessibility:
  role="menu" on container
  role="menuitem" on each item
  role="menuitemcheckbox" for checkable items
  aria-haspopup="menu" on trigger
  aria-expanded on trigger
  Keyboard: Arrow keys navigate, Enter/Space select, Escape closes
  Focus: first item on open, return to trigger on close
```

---

## Toast / Notification

```
Component: Toast
Variants: success | error | warning | info

Container (stack):
  position: fixed
  bottom: 24px right: 24px (desktop)
  bottom: 16px left: 16px right: 16px (mobile)
  z-index: 60
  display: flex flex-direction: column-reverse gap: 8px
  pointer-events: none (children override to auto)

Toast item:
  display: flex align-items: flex-start gap: 12px
  padding: 12px 16px
  border-radius: 8px
  min-width: 320px (desktop)
  max-width: 420px
  pointer-events: auto
  box-shadow: 0 8px 24px rgba(0,0,0,0.12)

  [success]: background #F0FDF4 border-left: 4px solid #22C55E icon color #22C55E
  [error]:   background #FFF5F5 border-left: 4px solid #EF4444 icon color #EF4444
  [warning]: background #FFFBEB border-left: 4px solid #F59E0B icon color #F59E0B
  [info]:    background #EFF6FF border-left: 4px solid #3B82F6 icon color #3B82F6

  Icon: 20px, flex-shrink: 0, margin-top: 1px
  Title: 14px weight 600 color #111827
  Message: 13px weight 400 color #6B7280 margin-top: 2px
  Close button: 20px ghost icon, margin-left: auto flex-shrink: 0

Auto-dismiss: 5000ms (error: no auto-dismiss)
Progress bar: 2px height at bottom, animates width 100%→0 over duration

Enter animation: translateX(calc(100% + 24px))→translateX(0) 300ms spring(1, 80, 20, 0)
Exit animation: opacity 1→0 + translateX(60px) 200ms ease-in

Accessibility:
  role="status" for success/info/warning (polite)
  role="alert" for error (assertive)
  aria-live matching the role
  aria-atomic="true"
  Close button: aria-label="Dismiss notification"

Mobile:
  Full width (left: 16px right: 16px)
  Swipe right to dismiss (touch event on item)
```
