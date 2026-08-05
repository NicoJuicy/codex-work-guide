---
name: design-geist
description: Apply Vercel's Geist design system aesthetic. Use when the user asks for Vercel-looking UI, Geist style, clean developer-tool design, or monochrome engineering-forward components.
---

# Vercel / Geist Design System

Apply Vercel's public-facing visual language — the Geist design system — to UIs,
websites, components, and marketing pages.

## When to Use

- Building developer tools, dashboards, landing pages, or documentation sites.
- Requested to make something "look like Vercel" / "Geist aesthetic".
- Need a clean, monochrome, engineering-forward design direction.
- Creating React/Next.js components, HTML/CSS pages, or design specs.

## Core Principles

1. **Less is more.** Clarity over decoration.
2. **Ink is the brand.** The near-black foreground (`#171717`) is the primary identity color, not a blue accent.
3. **Restraint.** No second accent color. No gradients except for hero focal moments. No heavy shadows.
4. **Whitespace is structure.** Generous, deliberate spacing defines hierarchy.
5. **Engineered typography.** Geist Sans + Geist Mono, tight tracking on display text.
6. **Subtle motion.** Spring-based, short, functional transitions.

## Typography

Use **Geist Sans** for UI and body. Use **Geist Mono** for code, data, terminal output, and technical labels.

```css
:root {
  --font-sans: 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'Geist Mono', 'SFMono-Regular', Menlo, monospace;

  --text-xs: 12px;
  --text-sm: 14px;
  --text-base: 16px;
  --text-lg: 18px;
  --text-xl: 24px;
  --text-2xl: 32px;
  --text-3xl: 48px;
  --text-display: 64px;

  --leading-tight: 1.15;
  --leading-base: 1.5;
  --leading-relaxed: 1.625;

  --tracking-tight: -0.04em;
  --tracking-normal: -0.01em;
}
```

- Headlines: `-0.04em` letter-spacing, line-height `1.15`, font-weight `500–600`.
- Body: `-0.01em` letter-spacing, line-height `1.5–1.625`, font-weight `400`.
- Mono labels: uppercase optional, `12–14px`, font-weight `400`.
- Never use a display weight above `600`.

## Color Palette

### Light Theme (Default)

| Token | Value | Usage |
|-------|-------|-------|
| `background-100` | `#ffffff` | Primary background |
| `background-200` | `#fafafa` | Secondary / section background |
| `foreground` | `#171717` | Primary text / ink |
| `gray-100` | `#f5f5f5` | Subtle fills |
| `gray-200` | `#eaeaea` | Hover states |
| `gray-300` | `#dddddd` | Borders / dividers |
| `gray-400` | `#d4d4d4` | Default borders |
| `gray-500` | `#a3a3a3` | Muted text |
| `gray-600` | `#737373` | Secondary text |
| `gray-700` | `#525252` | Strong secondary text |
| `gray-800` | `#404040` | Subtle headings |
| `gray-900` | `#262626` | Emphasis |
| `gray-1000` | `#171717` | Maximum contrast |

### Dark Theme

| Token | Value | Usage |
|-------|-------|-------|
| `background-100` | `#0a0a0a` | Primary background |
| `background-200` | `#171717` | Elevated surfaces |
| `foreground` | `#ededed` | Primary text |
| `gray-100` | `#1a1a1a` | Subtle fills |
| `gray-200` | `#1f1f1f` | Hover states |
| `gray-300` | `#292929` | Borders |
| `gray-400` | `#333333` | Default borders |
| `gray-500` | `#5c5c5c` | Muted text |
| `gray-600` | `#7e7e7e` | Secondary text |
| `gray-700` | `#a0a0a0` | Strong secondary text |
| `gray-800` | `#b7b7b7` | Subtle headings |
| `gray-900` | `#ededed` | Emphasis |
| `gray-1000` | `#ffffff` | Maximum contrast |

### Semantic Accents

Use accents sparingly. The ink/foreground color carries most of the UI.

| Token | Value | Usage |
|-------|-------|-------|
| `blue-700` | `#0070F3` | Info / links / focused accents |
| `green-700` | `#46A758` | Success |
| `red-700` | `#E5484D` | Error |
| `amber-700` | `#FFB224` | Warning |

## Spacing

Base unit is `4px`. Use the scale:

| Token | Value |
|-------|-------|
| `space-1` | 4px |
| `space-2` | 8px |
| `space-3` | 12px |
| `space-4` | 16px |
| `space-5` | 24px |
| `space-6` | 32px |
| `space-7` | 48px |
| `space-8` | 64px |
| `space-9` | 96px |
| `space-10` | 128px |
| `space-11` | 192px |

## Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `radius-sm` | 4px | Inputs, small UI |
| `radius-md` | 6px | Cards, buttons |
| `radius-lg` | 8px | Larger cards |
| `radius-xl` | 10px | Feature cards |
| `radius-full` | 9999px | Pill buttons, tags |
| `radius-marketing` | 100px | Large marketing CTA pills |

## Layout

- Max content width: `1200px` for marketing, `1024px` for dashboards.
- Centered single-column hero where appropriate.
- Use a visible but subtle blueprint grid pattern (10–20% opacity, `8px` or `16px` spacing) for texture.
- Hairline dividers (`1px`, `gray-300` light / `gray-400` dark) separate sections.
- 12-column grid for complex layouts.

## Components

### Buttons

- Primary: solid `foreground` (`#171717` light / `#ededed` dark), white/dark text, `radius-full`, padding `12px 20px`.
- Secondary: transparent with `1px` foreground border, foreground text, `radius-full`.
- Ghost: no border, foreground text, subtle hover fill.

### Cards

- Background: `background-100` or `background-200`.
- Border: `1px solid gray-300` (light) or `gray-400` (dark).
- Radius: `10px` for feature cards, `6px` for UI cards.
- Shadow: none or a very subtle `0 0 0 1px` border. Avoid drop shadows.

### Inputs

- Background: `background-100`.
- Border: `1px solid gray-300` default, `foreground` on focus.
- Radius: `6px`.
- Font: Geist Sans, `14px`.

### Code Blocks

- Background: `background-200` light, `background-200` dark.
- Font: Geist Mono, `14px`.
- Radius: `8px`.
- Use syntax highlighting; prefer `prism-react-renderer` in React.

### Pills / Tags

- Background: `gray-100` / `gray-200`.
- Text: `gray-900` / `foreground`.
- Radius: `9999px`.
- Height: `24–30px`.

## Icons

- Use **Lucide icons** or the official `@geist-ui/icons` set.
- Do NOT use emojis.
- Default size: `16px`, stroke-width `1.5`.

## Motion

- Use spring-based easing for micro-interactions.
- Keep animations short (`150–300ms`).
- Only animate properties that aid comprehension: opacity, transform.
- Example spring config: `damping: 200, stiffness: 2000, mass: 1`.

## Signature Moves

- A single hero headline with `-0.04em` tracking at `48–64px`.
- Mono "eyebrow" label above a display headline.
- Dual CTA: solid black primary + outlined white secondary.
- Subtle blueprint/grid background pattern.
- Section band polarity flip: light body → dark band → light body.
- Code preview cards with Geist Mono.

## Common Mistakes to Avoid

1. Do not add a second bright accent color.
2. Do not use gradients for buttons or borders.
3. Do not use emojis.
4. Do not use heavy drop shadows.
5. Do not use a display font-weight above `600`.
6. Do not crowd the layout — whitespace is structural.

## Quick Tailwind Config Snippet

```js
module.exports = {
  theme: {
    extend: {
      fontFamily: {
        sans: ['Geist', 'system-ui', 'sans-serif'],
        mono: ['Geist Mono', 'SFMono-Regular', 'monospace'],
      },
      colors: {
        background: {
          100: '#ffffff',
          200: '#fafafa',
        },
        foreground: '#171717',
        gray: {
          100: '#f5f5f5',
          200: '#eaeaea',
          300: '#dddddd',
          400: '#d4d4d4',
          500: '#a3a3a3',
          600: '#737373',
          700: '#525252',
          800: '#404040',
          900: '#262626',
          1000: '#171717',
        },
      },
      borderRadius: {
        'marketing': '100px',
      },
      letterSpacing: {
        tighter: '-0.04em',
        tight: '-0.01em',
      },
    },
  },
}
```

## When NOT to Use

- Children's products, playful consumer apps, or heavy editorial content.
- Brands that need warm, expressive, or colorful personalities.
- Situations requiring high information density without whitespace.
