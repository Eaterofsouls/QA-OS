# QA Operating System — Full Package (Updated)

This zip contains everything: the codebase, the portfolio site, and the standalone visuals — all restyled to the Kononenko design system, all honest about what's real versus what's a stub.

## What's inside

```
QA_Operating_System/        The actual codebase + specification library.
                             Start with QA_Operating_System/README.md.
                             Nothing was deleted from this repo — every
                             module, including broken and stub ones, is
                             still here and labeled by what it actually is.
                             Three new deep docs sit at its root:
                               README.md    -- what this is, how to run it,
                                               the full module ledger
                               VISION.md    -- the problem, the ten-module
                                               lifecycle, why it's built
                                               this way
                               GUIDANCE.md  -- engineering principles for
                                               contributors, roadmap order,
                                               and four specific ways to help

qa-os-site/                 The portfolio website's full Next.js source.
                             Restyled to the Kononenko design system: pure
                             black/white, zero saturation, no rounded
                             corners, hairline dividers, one arrow glyph.
                             Explains the vision first, then a simple
                             five-step walkthrough, then an honest
                             module-by-module status, then an explicit
                             "where I need help" collaboration section
                             with four tailored asks.
                             Run it: cd qa-os-site && npm install && npm run dev

qa-os-site-deploy/           The static export of the site above, ready to
                             upload to any static host (Hostinger, Netlify,
                             GitHub Pages, etc.) as-is.

qa-os-visuals/               The two standalone portfolio SVGs (overview +
                             architecture), the HTML file that embeds both
                             as real inline markup, and the Python scripts
                             that generated them. Same Kononenko visual
                             language as the site.
```

## What changed in this update

- The whole site's visual system moved from the earlier cream/olive editorial
  palette to the Kononenko system: pure black and white only, one hairline
  gray, zero saturation anywhere, sharp corners throughout, one icon (↗)
  used sparingly, a static underline for the current nav item instead of a
  hover fade.
- The homepage now leads with the vision, then a plain-language five-step
  explainer anyone can read without architecture vocabulary, then the honest
  module ledger (framed explicitly as an engineering-credibility signal, not
  just a status report), then a new **Collaborate** section naming four
  kinds of contributor and what's specifically being asked of each.
- The repository's own README, plus two new documents (VISION.md,
  GUIDANCE.md), now do the same job for anyone reading the code instead of
  the website. No module was removed from the codebase to make it look more
  finished — Module 4 and the stub connectors are still there, and now
  documented as deliberately left visible rather than hidden.
- The two standalone portfolio SVGs were redrawn from scratch in the new
  visual language, including a genuinely new device for the architecture
  diagram: the "AI boundary" (the only place a model is ever called) is now
  a single, solid black inverted panel — the same hard-cut register-change
  the Kononenko system uses at hero scale, translated into diagram form.
