# QA OS — qa.buildwithdaksh.com

A deep, honest engineering showcase for QA OS. Built with Next.js 14 (App
Router), TypeScript, Tailwind CSS, and Framer Motion, exported as a fully
static site — no Node.js server required to host it.

Built against `QA_OS_MASTER_BUILD_SPEC.md` (locked design system) and
`QA_OS_SUBDOMAIN_STRATEGIC_BLUEPRINT.md` (content/IA), grounded in the real
module-status data in the `QA_Operating_System` repo's `README.md`.

---

## 1. Configured Repository & Contact Info

`src/lib/site.ts` is configured with:

```ts
githubUrl: "https://github.com/dakshchauhan/qa-operating-system",
contactEmail: "me@buildwithdaksh.com",
```

These feed the footer, the "Talk to me about this direction" button on `/roadmap`, and the "View on GitHub" button on `/run`. Everything else on the site is ready to ship as-is.

If you rebuild after editing, run `npm run build` again before re-uploading
(see §3).

---

## 2. What's in this package

```
qa-os-site/
├── out/                  ← THE DEPLOYABLE SITE. Upload the *contents*
│                            of this folder to Hostinger.
├── src/                  ← full source (Next.js App Router)
│   ├── app/               5 pages: /, /architecture, /implementation,
│   │                      /roadmap, /run
│   ├── components/        Nav, Footer, StatusTag, IntroSequence,
│   │   └── diagrams/       ScrollReveal, RealVisionSeam, PageTransition
│   │                      6 diagrams: LifecycleMap, SystemArchitecture,
│   │                      VerticalSlice, MemoryLayer, ReasoningBoundary,
│   │                      RoadmapDAG
│   └── lib/                modules.ts (single source of truth for the
│                            9-module status ledger), roadmap.ts, site.ts
├── package.json
├── next.config.js        output: "export" — static export config
├── tailwind.config.ts    full design-token system (§4 of the spec)
└── tsconfig.json
```

The `out/` folder is a complete, self-contained static site — every page is
a real `.html` file, all CSS/JS is bundled and hashed, nothing calls back to
a Node server at runtime. That's what makes it deployable on Hostinger's
standard shared hosting, no special Node.js plan required.

---

## 3. Deploying to Hostinger (subdomain)

### Step 1 — create the subdomain
In **hPanel → Domains → Subdomains**, create `qa` as a subdomain of
`buildwithdaksh.com`. Hostinger will provision a folder, usually
`public_html/qa.buildwithdaksh.com` (or `public_html/qa` depending on your
plan) — note the exact path it shows you.

### Step 2 — upload the site
Two ways to get `out/`'s contents into that folder:

**Option A — File Manager (simplest, no extra tools needed)**
1. Zip the *contents* of `out/` (not the `out` folder itself — the `index.html`
   should be at the top level of the zip).
2. In hPanel → **Files → File Manager**, navigate to the subdomain's folder.
3. Upload the zip, then use File Manager's "Extract" on it.
4. Delete the zip after extracting. Confirm `index.html` sits directly in
   that folder (not nested inside an extra `out/` subfolder).

**Option B — FTP (faster for repeat deploys)**
1. Get FTP credentials from hPanel → **Files → FTP Accounts**.
2. Connect with any FTP client (FileZilla, Cyberduck, etc.) to the
   subdomain's folder.
3. Upload everything *inside* `out/` — not the `out` folder itself.

### Step 3 — verify
Visit `https://qa.buildwithdaksh.com/`. All five pages should load; check
`/architecture/`, `/implementation/`, `/roadmap/`, and `/run/` too, since
Hostinger's static file server needs the `trailingSlash: true` export
convention this project already uses (each page is an `index.html` inside
its own folder, e.g. `architecture/index.html` — this is exactly how it's
been exported, so direct links and refreshes on sub-pages both work
correctly without extra server config).

### SSL
Hostinger issues free SSL (Let's Encrypt) automatically for subdomains —
enable it under hPanel → **Security → SSL** if it isn't already active.
The site has no mixed-content risk (fonts load from `https://` CDNs only).

---

## 4. Rebuilding after changes

If you edit any source file and need to regenerate `out/`:

```bash
npm install        # first time only
npm run build       # regenerates out/ from scratch
```

Then re-upload the new contents of `out/`, replacing what's already on
Hostinger (Option A or B above).

---

## 5. Local development

```bash
npm install
npm run dev
# open http://localhost:3000
```

Note: `npm run dev` runs the full Next.js dev server (not the static
export) — this is for editing/previewing only, not what gets deployed.

---

## 6. Design system reference

Everything in `tailwind.config.ts` and `src/app/globals.css` implements the
locked design system from `QA_OS_MASTER_BUILD_SPEC.md`:

- **Colors:** warm ivory (`#F6F2EC`) background, near-black ink
  (`#1B1815`), and exactly four status colors (sage/indigo/rust/gray for
  Implemented/Vision/Partial/Planned) — used *only* on status tags and
  inside diagrams, nowhere else.
- **Type:** Fraunces (display/narrative) + General Sans with Inter
  fallback (body/UI) + IBM Plex Mono (labels/technical), loaded via
  Google Fonts / Fontshare CDN links in `layout.tsx` — no local font
  files to manage, no build-time font fetching required.
- **The status-tag rule:** every capability claim on the site carries a
  `<StatusTag>` (`src/components/StatusTag.tsx`). The 9-module data this
  all derives from lives in one place — `src/lib/modules.ts` — so every
  diagram and every table on the site reads from the same source and
  can't silently drift out of sync with what's actually true.
- **Motion:** a pinned, scroll-linked 3-card intro sequence on the
  homepage, scroll-triggered reveals everywhere else, and a distinct
  "the page takes a breath" treatment at the real→vision seam. Everything
  respects `prefers-reduced-motion` with a complete static fallback.

If you want to change any of these, `tailwind.config.ts` (color/font
tokens) and `src/lib/modules.ts` / `src/lib/roadmap.ts` (content data) are
the places to start — most of the site's visual system flows from those
two files rather than being hardcoded per-component.
