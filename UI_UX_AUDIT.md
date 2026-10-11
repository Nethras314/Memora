# MEMORA — UI/UX Transformation Audit

## 1. Initial assessment

MEMORA is an AI-assisted cognitive and daily-life companion for elderly dementia patients, with
secondary surfaces for caregivers (daily glance + mood logging) and clinicians (longitudinal
analytics, clinical notes, doctor access grants). The React 18 + Vite + Tailwind frontend is
deployed at https://memora-neon-eight.vercel.app/.

The application's core functionality (games, memories, routines, reminders, analytics) is real and
wired to a FastAPI + Supabase backend. The visual layer, however, carried several "AI-generated
dashboard" tells: a purple `#4943a5` identity with purple-to-blue gradients, Plus Jakarta Sans
everywhere, card-heavy nested layouts, gray-on-cream secondary text, and inconsistent component
styling. The most serious usability defect was the **fixed 288px sidebar** (`w-72` + `ml-72`),
which rendered the app effectively unusable on mobile/tablet widths.

## 2. Routes and user journeys inspected

All 11 pages and 8 shared components were read in full before editing:

- **Pages:** TodayDashboard, MemoriesPage, RoutinePage, RemindersPage, ActivitiesPage,
  ExercisePage, SleepPage, CaregiverDashboard, DoctorDashboard, AuthPage, AdminPage.
- **Components:** Sidebar, PinModal, VoiceAssistantModal, StatusBadge, TrendChart,
  DomainBreakdown, MoodLog, PrintableReport.
- **Shell/config:** App.jsx, AuthContext, services/api.js, services/supabase.js, i18n.js,
  index.css, tailwind.config.js, index.html.

User journeys reviewed: login/signup → role landing, patient selection → language switch, memory
add/edit/delete (PIN-gated), routine toggle/add/reset, reminder create/enable/delete, sequence
memory game + GK + attention games, breathing exercise, sleep/calm mode, caregiver glance + mood
log, doctor cohort → patient detail → clinical note → CSV/PDF export, admin user management.

## 3. Most important problems identified

| # | Problem | Severity |
|---|---|---|
| 1 | Fixed 288px sidebar breaks the app below desktop widths (no mobile navigation) | P0 |
| 2 | Purple-to-blue gradients + purple `#4943a5` identity = generic AI/SaaS look | P0 |
| 3 | `outline-none` on inputs/selects with no visible focus replacement (keyboard barrier) | P0 |
| 4 | `alert()` popups for delete/reset failures (alarming, blocking) | P1 |
| 5 | Inconsistent button/card/input styling duplicated across every page | P1 |
| 6 | Gray-on-cream secondary text, small touch targets, missing icon-button labels | P1 |
| 7 | No `prefers-reduced-motion` handling | P1 |
| 8 | Modals lacked `role="dialog"` / `aria-modal` / Escape-close | P1 |
| 9 | Plus Jakarta Sans everywhere (overused), default `font-serif` headings (inconsistent) | P2 |
| 10 | No empty-state direction in several data views (plain "No data" text) | P2 |

## 4. Design direction and rationale

**Register:** Product (instrument), not brand — operators (caregivers/clinicians) and elderly
patients both need consistency and speed.

**Direction — "Warm Garden":** warm cream surfaces, a grounded terracotta/clay primary, and a
saffron highlight accent. Chosen deliberately against the two obvious clichés (purple SaaS and
teal health). Terracotta/clay is warm, human, and culturally resonant; cream + clay read as calm
and reassuring for an elderly, memory-care audience while remaining distinctive.

**Typography:** Fraunces (warm display serif) for headings, Figtree (high-x-height humanist sans)
for body/UI — replacing Plus Jakarta Sans and the default serif.

## 5. Final design-system decisions

- **Primary (clay/terracotta):** `#b04a28` (dark `#8a3a1e`, tint `#faeae0`/`#f4d6c4`).
- **Neutrals (warm):** ink `#2a211b`, muted `#6e6055`, faint `#8f8378`, cream `#faf5ec`,
  paper `#fffdf9`, line `#e8ddcf`, line-soft `#f0e8dc`.
- **Supporting:** saffron `#d99a2b`, peach `#f7e3c8`, sage `#4a6b57`.
- **Semantic:** success `#3f6b52`, warning `#b45309`, danger `#b3402a` (each with a `-bg` tint).
- **Type scale:** display `font-serif` (Fraunces), body `font-sans` (Figtree).
- **Radii:** `xl2` 1rem, `xl3` 1.25rem (cards/buttons), rounded for softness.
- **Elevation:** `shadow-soft` and `shadow-lift` tokens.
- **Component classes** (`.btn`, `.btn-primary`, `.card`, `.input`, `.label`, `.chip`,
  `.icon-btn`, `.eyebrow`) defined in `index.css` for reuse.

## 6. Implemented improvements

### P0 — critical
- **Responsive navigation (fixed the broken mobile layout).** Rewrote `App.jsx` to use
  `lg:pl-72` instead of a hard `ml-72`, added a mobile hamburger + slide-over drawer with a
  backdrop, and a close affordance; `Sidebar.jsx` is now `-translate-x-full` → `translate-x-0`
  on mobile and static on `lg+`. Primary actions remain reachable at 360px.
- **Removed the purple-gradient hero** (`TodayDashboard`) and the auth gradient; replaced with a
  solid warm primary / cream.
- **Visible focus.** Removed `outline-none` from inputs/selects so the global `:focus-visible`
  ring applies; added a base focus-visible style in `index.css`.

### P1 — major experience
- **Killed `alert()` popups.** `MemoriesPage` and `RoutinePage` now surface delete/reset failures
  through inline error banners instead of blocking `alert()`; `VoiceAssistantModal` uses inline
  reply text.
- **Consistent design tokens + component classes.** Defined the full palette/font/radius/shadow
  tokens and reusable `.btn`/`.card`/`.input`/`.label`/`.chip`/`.icon-btn` classes.
- **Bulk color migration** across 17 page/component files from the old purple/blue palette to the
  warm palette (all `indigo-*` tints now map to warm clay tints).
- **Reduced motion.** Added a `prefers-reduced-motion: reduce` override in `index.css`.
- **Modal accessibility.** `PinModal` and `VoiceAssistantModal` now declare `role="dialog"`,
  `aria-modal="true"`, `aria-label`, labelled close buttons, and close on `Escape`.

### P2 — visual refinement
- **Typography pairing** (Fraunces + Figtree) wired via `index.html` and Tailwind `fontFamily`.
- **Warmer, higher-contrast neutrals** replacing the gray-on-cream secondary text.
- **Semantic status colors** with text + icon + dot (never color alone) via `StatusBadge`.
- Updated favicon, `theme-color`, and meta description.

## 7. Important files and components modified

- `frontend/tailwind.config.js` — design tokens (colors, fonts, radius, shadow).
- `frontend/src/index.css` — CSS variables, base layer (focus, reduced-motion), component classes.
- `frontend/index.html` — fonts, favicon, theme-color, meta.
- `frontend/src/App.jsx` — responsive shell + mobile drawer navigation.
- `frontend/src/components/Sidebar.jsx` — responsive, accessible nav.
- `frontend/src/components/PinModal.jsx`, `VoiceAssistantModal.jsx` — dialog semantics + Escape.
- All 11 pages + remaining components — bulk palette migration and targeted fixes
  (gradients, `outline-none`, `alert()`, inline error banners).

## 8. Tests executed and actual results

- **Production build:** `npm run build` → **PASS** (2402 modules, built in ~59s). Only warning is
  a pre-existing 731 KB chunk (recharts + lucide + supabase), not introduced by these changes.
- **Frontend lint/typecheck/unit tests:** none configured in `package.json` (scripts are
  `dev`/`build`/`preview` only). No frontend test suite to run.
- **Backend tests:** not run in this pass (no backend changes made).

## 9. Before/after screenshots

Not captured. No Playwright/browser-automation tooling is available in this environment to render
the local dev server, so I could not produce verified before/after screenshots. The build output
was inspected via the compiled bundle instead. This is a documented limitation, not an executed
claim.

## 10. Remaining issues, limitations, and recommended next steps

- **Skill installation:** Impeccable (`pbakaus/impeccable`) and UI UX Pro Max
  (`nextlevelbuilder/ui-ux-pro-max-skill`) are Claude Code/Cursor skills installed via
  `npx impeccable install` / `uipro init`. They are **not installed** in this Command Code
  environment (no `.claude/`/`.cursor/` target, and installing them requires running their CLIs,
  which I did not do without authorization). I applied their documented anti-pattern guidance via
  the bundled `design` skill instead.
- **Focus trap:** full focus-trapping (not just Escape-close) is not yet implemented in the
  modals; page-level modals (Memories/Routine/Reminders) still lack `role="dialog"`.
- **Icon-button labels:** many icon-only buttons across pages still lack `aria-label`.
- **Empty/error/loading states:** several data views still use plain text; a shared
  `EmptyState`/`Spinner` component would consolidate them.
- **Bundle size:** 731 KB JS chunk (recharts + supabase) should be code-split via
  `dynamic import()`.
- **No dark-mode/font-scaling toggle** and no PWA/offline support in the web app (offline is a
  separate backend/mobile workstream).
