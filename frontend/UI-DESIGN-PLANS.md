# UI design plans: calm & visually appealing

This document outlines **four design directions** for Journal Companion. Each is tuned for a calm, reflective feel. Pick one (or mix elements) and we can implement it.

---

## Current state (baseline)

- **Colors:** Slate grays (50–800), amber for streak, red for errors
- **Font:** System UI (no custom font)
- **Layout:** White nav bar, `slate-50` page background, `max-w-2xl` content, sharp borders
- **Vibe:** Functional and neutral; not yet “calm” or distinctive

---

## Plan A — Soft & Serene

**Vibe:** Quiet, gentle, “morning journal” — soft greens and warm off-whites.

| Element | Change |
|--------|--------|
| **Background** | Warm off-white (`#faf9f7` / “paper”) instead of cold gray; main content on subtle cream cards |
| **Accent** | Muted sage green (`#8b9f82` or Tailwind `stone`/custom) for links, primary buttons, streak highlight |
| **Typography** | Serif for headings (e.g. **Lora** or **Source Serif Pro**), keep sans for body; slightly larger line-height (1.6) |
| **Cards & surfaces** | Soft shadow (`shadow-sm`), border radius 12–16px, very light borders or borderless |
| **Nav** | Same warm off-white as page; nav links in muted green, underline on hover; no heavy border |
| **Buttons** | Rounded-full or rounded-xl; primary = sage fill, secondary = outline in sage |
| **Streak / alerts** | Soft sage or soft gold instead of bright amber |

**Best for:** Users who want the app to feel like a calm, book-like space.

---

## Plan B — Minimal & Breathable

**Vibe:** Clean, spacious, “less is more” — lots of whitespace, one soft accent.

| Element | Change |
|--------|--------|
| **Background** | Pure or near-white (`#fefefe`), or very light gray (`#f8f9fa`) |
| **Accent** | Single calm accent: soft blue (`#6b8cae`) or teal (`#5a7d7d`) for links, CTAs, and key highlights only |
| **Typography** | Clean sans (e.g. **DM Sans** or **Inter**); generous line-height; headings not too bold (font-semibold, not black) |
| **Spacing** | Increase padding (e.g. `p-6` on main, `space-y-8` between sections); wider max-width optional (`max-w-3xl`) |
| **Cards** | Minimal: very light border or subtle shadow only; radius 12px; no heavy borders |
| **Nav** | Light border or shadow; links low-contrast until hover; “Today” or logo slightly emphasized |
| **Buttons** | Outline or very light fill; accent color only on primary (e.g. “Save”, “Log in”) |

**Best for:** Users who prefer a clean, uncluttered, “breathable” interface.

---

## Plan C — Warm & Cozy

**Vibe:** “Notebook by the window” — cream, soft browns, gentle warmth.

| Element | Change |
|--------|--------|
| **Background** | Cream / ivory (`#f5f2eb` or `#faf6f0`); cards a shade lighter or white with warm tint |
| **Accent** | Warm brown / terracotta (`#a67c52`, `#8b6914`) or dusty rose (`#b8958a`) for links and buttons |
| **Typography** | Friendly sans (e.g. **Nunito** or **Work Sans**) or a readable serif; comfortable size (base 16px) |
| **Cards** | Soft, warm shadow; rounded-xl; optional very subtle inner glow or warm border |
| **Nav** | Cream or white; links in warm brown; optional thin bottom border in warm gray |
| **Inputs** | Rounded-lg, light warm-gray border; focus ring in accent (brown/terracotta) |
| **Streak** | Soft gold or warm amber, not bright orange |

**Best for:** Users who want the app to feel warm and inviting, like a personal notebook.

---

## Plan D — Dark Calm (optional mode)

**Vibe:** Low-glare, evening-friendly — deep slate/blue-gray, soft contrast.

| Element | Change |
|--------|--------|
| **Background** | Deep slate (`#1e293b`) or blue-gray (`#1a2332`); cards slightly lighter (`#334155`) |
| **Text** | Off-white (`#f1f5f9`), muted gray for secondary (`#94a3b8`) |
| **Accent** | Soft teal or muted blue (`#67e8f9` at low opacity, or `#7dd3fc`) for links and highlights |
| **Borders** | Very subtle (`border-slate-700`); avoid bright lines |
| **Shadows** | Rare; use subtle elevation or glow instead |
| **Toggle** | Add a theme switch (light/dark) in nav or Profile; persist in `localStorage` |

**Best for:** Evening use or users who prefer dark UIs; can be combined with A, B, or C as a dark variant.

---

## Implementation checklist (any plan)

Once you pick a plan, we can:

1. **Global styles** — Update `index.css` and Tailwind (e.g. `tailwind.config.js` with custom colors and font family).
2. **Layout & nav** — Apply background, nav style, and spacing to `Layout.jsx`.
3. **Login** — Align login page with the same palette and typography.
4. **Today** — Cards, prompt area, mood chips, buttons, streak card.
5. **History / Dashboard / Summary / Profile** — Same tokens (colors, radius, spacing) for consistency.
6. **Components** — Optional: small design tokens file or CSS variables for accent, background, and radius so future changes are easy.

---

## Quick comparison

| Plan | Background | Accent | Typography | Feel |
|------|------------|--------|------------|------|
| **A — Soft & Serene** | Warm off-white | Sage green | Serif headings | Gentle, journal-like |
| **B — Minimal & Breathable** | White / light gray | Soft blue or teal | Clean sans | Spacious, minimal |
| **C — Warm & Cozy** | Cream / ivory | Brown / terracotta | Friendly sans/serif | Warm, notebook |
| **D — Dark Calm** | Deep slate | Soft teal/blue | Same as light | Low-glare, optional |

---

If you tell me which plan (or mix) you prefer, I can outline exact Tailwind classes and CSS changes file-by-file, or implement one plan end-to-end.
