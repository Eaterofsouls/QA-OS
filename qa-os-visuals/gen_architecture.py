"""
QA Operating System — architecture SVG generator (v2, geometry-corrected).
Every component, status, and relationship drawn here is taken directly from
the Project Knowledge Base (source-verified). Nothing is invented.
"""
import math

W, H = 1700, 1720

BG = "#FFFFFF"
BG_ELEV = "#FFFFFF"
INK = "#000000"
INK_MUTED = "#6B6B6B"
LINE = "#D8D8D8"
C_IMPLEMENTED = "#000000"   # real, verified -- full black
C_VISION = "#000000"        # repurposed: the AI-boundary accent (inverted panel)
C_PARTIAL = "#4A4A4A"       # real logic, not wired -- dark gray
C_PLANNED = "#8A8A8A"       # specified, not exercised -- mid gray

FONT_DISPLAY = "Fraunces, Georgia, 'Times New Roman', serif"
FONT_SANS = "'General Sans', Inter, -apple-system, 'Segoe UI', sans-serif"
FONT_MONO = "'IBM Plex Mono', 'Courier New', monospace"

svg = []


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def box(x, y, w, h, title, sub=None, tag=None, tag_color=INK_MUTED, dashed=False,
        fill=BG_ELEV, stroke=INK, stroke_w=2.0, title_size=15.5, sub_size=11.0,
        title_font="sans", items=None, center_items=False, inverted=False):
    text_ink = "#FFFFFF" if inverted else INK
    text_muted = "#B7B7B7" if inverted else INK_MUTED
    dash = 'stroke-dasharray="5 5"' if dashed else ""
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="0" '
               f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_w}" {dash}/>')
    tx = x + w / 2
    cursor_y = y + 25
    if tag:
        tw_est = len(tag) * 6.7
        dot_x = tx - tw_est / 2 - 10
        svg.append(f'<rect x="{dot_x-3:.1f}" y="{cursor_y - 7}" width="6" height="6" fill="{tag_color}"/>')
        svg.append(f'<text x="{tx:.1f}" y="{cursor_y}" text-anchor="middle" class="mono" '
                   f'font-size="9.6" fill="{tag_color}">{esc(tag)}</text>')
        cursor_y += 22
    ffam = {"sans": "sans", "display": "display", "mono": "mono"}[title_font]
    svg.append(f'<text x="{tx:.1f}" y="{cursor_y}" text-anchor="middle" class="{ffam}" '
               f'font-size="{title_size}" fill="{text_ink}">{esc(title)}</text>')
    cursor_y += 21
    if sub:
        for line in (sub if isinstance(sub, list) else [sub]):
            svg.append(f'<text x="{tx:.1f}" y="{cursor_y}" text-anchor="middle" class="sans" '
                       f'font-size="{sub_size}" fill="{text_muted}">{esc(line)}</text>')
            cursor_y += 15.2
    if items:
        cursor_y += 6
        for it in items:
            if center_items:
                svg.append(f'<text x="{tx:.1f}" y="{cursor_y}" text-anchor="middle" class="mono" '
                           f'font-size="10.2" fill="{text_muted}">{esc(it)}</text>')
            else:
                bx_ = x + 22
                svg.append(f'<circle cx="{bx_}" cy="{cursor_y - 3.5}" r="1.7" fill="{text_muted}"/>')
                svg.append(f'<text x="{bx_ + 10}" y="{cursor_y}" class="mono" font-size="10.2" '
                           f'fill="{text_muted}">{esc(it)}</text>')
            cursor_y += 16.5
    return (x, y, w, h)


def arrow(x1, y1, x2, y2, dashed=False, color=INK_MUTED, w=1.6, label=None,
          lx=None, ly=None, curve=None):
    dash = 'stroke-dasharray="1 5.5"' if dashed else ""
    if curve:
        d = f'M{x1} {y1} C {curve[0]} {curve[1]}, {curve[2]} {curve[3]}, {x2} {y2}'
        svg.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" {dash}/>')
        ang = math.atan2(y2 - curve[3], x2 - curve[2])
    else:
        svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
                   f'stroke-width="{w}" {dash}/>')
        ang = math.atan2(y2 - y1, x2 - x1)
    ah = 6.5
    p1 = (x2 - ah * math.cos(ang - 0.4), y2 - ah * math.sin(ang - 0.4))
    p2 = (x2 - ah * math.cos(ang + 0.4), y2 - ah * math.sin(ang + 0.4))
    svg.append(f'<path d="M{p1[0]:.1f} {p1[1]:.1f} L{x2} {y2} L{p2[0]:.1f} {p2[1]:.1f} Z" fill="{color}"/>')
    if label:
        px = lx if lx is not None else (x1 + x2) / 2
        py = ly if ly is not None else (y1 + y2) / 2 - 8
        tw = len(label) * 5.5 + 14
        svg.append(f'<rect x="{px - tw/2:.1f}" y="{py-12}" width="{tw:.1f}" height="17" rx="0" fill="{BG}"/>')
        svg.append(f'<text x="{px:.1f}" y="{py}" text-anchor="middle" class="mono" font-size="9.4" '
                   f'fill="{color}">{esc(label)}</text>')


def polyline(points, dashed=False, color=INK_MUTED, w=1.6, arrow_end=True):
    d = "M" + " L".join(f"{x} {y}" for x, y in points)
    dash = 'stroke-dasharray="1 5.5"' if dashed else ""
    svg.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" {dash}/>')
    if arrow_end:
        (x1, y1), (x2, y2) = points[-2], points[-1]
        ang = math.atan2(y2 - y1, x2 - x1)
        ah = 6.5
        p1 = (x2 - ah * math.cos(ang - 0.4), y2 - ah * math.sin(ang - 0.4))
        p2 = (x2 - ah * math.cos(ang + 0.4), y2 - ah * math.sin(ang + 0.4))
        svg.append(f'<path d="M{p1[0]:.1f} {p1[1]:.1f} L{x2} {y2} L{p2[0]:.1f} {p2[1]:.1f} Z" fill="{color}"/>')


# ================= canvas =================
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
           f'role="img" aria-labelledby="ar-title ar-desc">')
svg.append('<title id="ar-title">QA Operating System — architecture of the verified working slice</title>')
svg.append('<desc id="ar-desc">A Next.js frontend calls a FastAPI service, which dispatches to three '
           'reasoning modules. Two call an LLM through a single validated gateway inside a bounded AI '
           'region, with an isolated cost ledger and an external, never-live-called LLM provider. The '
           'third module is a human decision with no model call. A retrieval engine feeds prior outcomes '
           'back into the first module. All three modules read and write a swappable storage interface '
           'with three backends. A connector layer to Jira, GitHub, Slack, and Playwright is designed but '
           'not wired into the live pipeline.</desc>')
svg.append('<style>')
svg.append(f'  .display {{ font-family: {FONT_DISPLAY}; }}')
svg.append(f'  .sans {{ font-family: {FONT_SANS}; }}')
svg.append(f'  .mono {{ font-family: {FONT_MONO}; letter-spacing: 0.06em; }}')
svg.append('</style>')
svg.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{BG}"/>')

# ---- header ----
svg.append(f'<text x="90" y="66" class="mono" font-size="12" fill="{INK_MUTED}">QA OPERATING SYSTEM &#8212; SYSTEM ARCHITECTURE</text>')
svg.append(f'<text x="88" y="112" class="display" font-size="32" fill="{INK}">How the verified slice is actually built</text>')
svg.append(f'<text x="90" y="140" class="sans" font-size="14" fill="{INK_MUTED}">Solid = real, exercised call. Dashed = specified, not wired, or not exercised. Full detail in the source Knowledge Base.</text>')
svg.append(f'<line x1="90" y1="160" x2="{W-90}" y2="160" stroke="{LINE}" stroke-width="1"/>')

# ================= Row 1: Frontend =================
fx, fy, fw, fh = 540, 190, 620, 84
box(fx, fy, fw, fh, "Command Center (Next.js)", sub="apps/web — typed client mirrors every backend response model",
    tag="CLIENT", tag_color=INK_MUTED)

# ================= Row 2: API =================
ax, ay, aw, ah_ = 350, 322, 1000, 132
box(ax, ay, aw, ah_, "FastAPI — services/api", tag="API LAYER", tag_color=INK_MUTED,
    items=["POST /assess \u00b7\u00b7\u00b7\u00b7 POST /generate-tests",
           "GET /tests \u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7 POST /tests/{id}/review",
           "GET /cost \u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7\u00b7 GET /graph"],
    center_items=True, sub="six typed, dependency-injected routes \u2014 real HTTP status codes on failure")

arrow(fx + fw/2, fy + fh, ax + aw/2, ay, label="real fetch() \u2014 no mock JSON")

# ================= Row 3: Modules =================
mw, mh, gap = 380, 168, 50
total = mw*3 + gap*2
mx0 = (W - total)/2
my = 512

m1 = box(mx0, my, mw, mh, "Risk Assessor", tag="AI \u00b7 MODULE 1", tag_color=C_VISION,
         sub=["scores a requirement 0\u20131, with a rationale", "reads similar past requirements first"])
m2 = box(mx0+mw+gap, my, mw, mh, "Test Generator", tag="AI \u00b7 MODULE 2", tag_color=C_VISION,
         sub=["drafts test cases, status = \u201cdraft\u201d", "reads the stored risk assessment first"])
m3 = box(mx0+2*(mw+gap), my, mw, mh, "Review Gate", tag="HUMAN \u00b7 MODULE 3", tag_color=C_IMPLEMENTED,
         sub=["approve / reject \u2014 no model call", "a person\u2019s decision is the only input"])

for i, mbox in enumerate((m1, m2, m3)):
    mcx = mbox[0] + mbox[2]/2
    fx_ = ax + aw*[0.18, 0.5, 0.82][i]
    arrow(fx_, ay+ah_, mcx, my, color=INK_MUTED)

# ================= Retrieval / similarity (left column, peer to module row) =================
rx, ry, rw, rh = 30, my, 165, mh
box(rx, ry, rw, rh, "Similarity Engine", tag="RETRIEVAL", tag_color=INK_MUTED,
    sub=["TF-IDF cosine, stdlib only \u2014", "no embeddings, no vector DB", "0.2 threshold \u2014 precision first"],
    sub_size=10.2)
# no inline label here -- module 1's own subtitle already states the relationship
# ("reads similar past requirements first"); a label on this very short arrow would
# only collide with both boxes' text.
arrow(rx+rw, ry+rh*0.42, mx0-4, my+rh*0.42, color=INK_MUTED)

# ================= AI boundary (below modules 1 & 2) — a real "hard cut":
# solid black panel, inverted, exactly the register-change device the
# Kononenko system uses for the single moment that matters most.
bx = mx0
bw = (mx0+mw+gap) + mw - mx0
by, bh = 760, 190
svg.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="{INK}"/>')
svg.append(f'<rect x="{bx+18}" y="{by+16}" width="7" height="7" fill="#FFFFFF"/>')
svg.append(f'<text x="{bx+34}" y="{by+27}" class="mono" font-size="11" fill="#FFFFFF">AI BOUNDARY \u2014 THE ONLY PATH TO AN LLM</text>')

ebw = (bw-70)/2
ebx, eby, ebh = bx+25, by+45, bh-70
box(ebx, eby, ebw, ebh, "Extraction Backbone",
    sub=["validates the reply against a", "Pydantic schema, or raises an error", "isolates cost-log failures from it"],
    sub_size=10.4, fill=INK, stroke="#FFFFFF", stroke_w=1.2, inverted=True)
lgx = ebx+ebw+20
box(lgx, eby, ebw, ebh, "LLM Gateway Client",
    sub=["real httpx calls \u2014 one class is", "the only permitted path out", "raises a typed error on failure"],
    sub_size=10.4, fill=INK, stroke="#FFFFFF", stroke_w=1.2, inverted=True)

for mbox in (m1, m2):
    mcx = mbox[0]+mbox[2]/2
    arrow(mcx, my+mh, mcx, by, color=C_VISION, label="structured prompt")

boundary_center_x = bx + bw/2  # gap between the two sub-boxes; used as the shared storage corridor

# ================= External provider + cost ledger (side by side, below boundary) =================
row_y = by + bh + 30
row_h = 130
cl_x, cl_w = bx, ebw
ext_x, ext_w = lgx, ebw

box(cl_x, row_y, cl_w, row_h, "Cost Ledger", tag="AUDIT \u00b7 ISOLATED", tag_color=INK_MUTED,
    sub=["SQLite \u2014 every real call logged", "a logging failure can't break the response"], sub_size=10.4)
box(ext_x, row_y, ext_w, row_h, "LLM Provider", tag="EXTERNAL", tag_color=C_PLANNED, dashed=True, fill=BG,
    sub=["OpenAI-compatible endpoint", "never called with a live key here"], sub_size=10.4)

arrow(ebx+ebw*0.5, by+bh, cl_x+cl_w*0.5, row_y, dashed=True, color=INK_MUTED,
      label="usage logged (isolated)")
arrow(lgx+ebw*0.5, by+bh, ext_x+ext_w*0.5, row_y, dashed=True, color=C_PLANNED,
      label="never exercised live")

# ================= Storage abstraction =================
sy = row_y + row_h + 60
sw = 1520
sx = (W - sw)/2
sh = 250
box(sx, sy, sw, sh, "KGClientInterface", tag="STORAGE ABSTRACTION \u2014 SWAPPABLE BY ENV VAR",
    tag_color=INK_MUTED, title_size=17)

bw3 = (sw - 60 - 60) / 3
by3 = sy + 78
bh3 = sh - 78 - 25
box(sx+30, by3, bw3, bh3, "KGClientStub", tag="DEFAULT", tag_color=INK_MUTED,
    sub=["in-memory dict", "Sprint-0 grade"])
box(sx+30+bw3+30, by3, bw3, bh3, "KGClientSQLite", tag="VERIFIED PERSISTED", tag_color=C_IMPLEMENTED,
    stroke=C_IMPLEMENTED, stroke_w=2.2,
    sub=["env: KG_SQLITE_PATH", "survives a process restart \u2014", "proven by a two-process test"], sub_size=10.2)
box(sx+30+2*(bw3+30), by3, bw3, bh3, "Neo4j KGClient", tag="SPECIFIED", tag_color=C_PLANNED, dashed=True,
    sub=["real driver exists", "never run against a live Neo4j", "in this repository"], sub_size=10.2)

# module 1 & module 2 -> storage: merge into one corridor through the gap
# between the two AI-boundary sub-boxes and the two row-2 sub-boxes.
corridor_x = boundary_center_x
merge_y = my + mh + 40
polyline([(m1[0]+m1[2]/2, my+mh), (corridor_x, merge_y)], color=INK_MUTED, arrow_end=False)
polyline([(m2[0]+m2[2]/2, my+mh), (corridor_x, merge_y)], color=INK_MUTED, arrow_end=False)
polyline([(corridor_x, merge_y), (corridor_x, sy)], color=INK_MUTED)
corridor_mid_y = (row_y+row_h+sy)/2
svg.append(f'<rect x="{corridor_x-150}" y="{corridor_mid_y-11}" width="300" height="20" rx="0" fill="{BG}"/>')
svg.append(f'<text x="{corridor_x}" y="{corridor_mid_y+4}" text-anchor="middle" class="mono" font-size="9.6" fill="{INK_MUTED}">persist assessment / tests \u2014 tenant-scoped</text>')

# module 3 -> storage: clear column, nothing else occupies its x-range
m3cx = m3[0] + m3[2]/2
arrow(m3cx, my+mh, m3cx, sy, color=INK_MUTED, label="persist review decision")

# retrieval -> storage: long clear corridor down the far-left margin
polyline([(rx+rw*0.3, ry+rh), (rx+rw*0.3, sy-40), (sx+40, sy)], dashed=False, color=INK_MUTED)
svg.append(f'<rect x="{rx-10}" y="{sy-58}" width="225" height="18" rx="0" fill="{BG}"/>')
svg.append(f'<text x="{rx+100}" y="{sy-45}" text-anchor="middle" class="mono" font-size="9.4" fill="{INK_MUTED}">reads stored requirement text</text>')

# ================= Connector layer (peripheral, not wired) =================
cy2 = sy + sh + 50
ch2 = 100
cw2 = sw
cx2 = sx
svg.append(f'<rect x="{cx2}" y="{cy2}" width="{cw2}" height="{ch2}" rx="0" fill="none" stroke="{LINE}" stroke-width="1.6" stroke-dasharray="5 5"/>')
svg.append(f'<circle cx="{cx2+22}" cy="{cy2+24}" r="3.2" fill="{C_PLANNED}"/>')
svg.append(f'<text x="{cx2+34}" y="{cy2+29}" class="mono" font-size="11" fill="{C_PLANNED}">INTEGRATION LAYER \u2014 DESIGNED, NOT WIRED INTO THE PIPELINE</text>')

pills = [("Jira adapter", "real, unwired", C_IMPLEMENTED, False),
         ("GitHub adapter", "stub", C_PLANNED, True),
         ("Slack adapter", "stub", C_PLANNED, True),
         ("Playwright adapter", "stub", C_PLANNED, True)]
pw = (cw2 - 40 - 3*20) / 4
px = cx2 + 20
py = cy2 + 46
for name, status, col, dashed_pill in pills:
    dash = 'stroke-dasharray="4 4"' if dashed_pill else ""
    svg.append(f'<rect x="{px}" y="{py}" width="{pw}" height="42" rx="0" fill="{BG_ELEV}" stroke="{col}" stroke-width="1.6" {dash}/>')
    svg.append(f'<text x="{px+pw/2}" y="{py+18}" text-anchor="middle" class="sans" font-size="11.5" fill="{INK}">{esc(name)}</text>')
    svg.append(f'<text x="{px+pw/2}" y="{py+33}" text-anchor="middle" class="mono" font-size="9.3" fill="{col}">{esc(status.upper())}</text>')
    px += pw + 20

# connector -> API: short, clean sweep up the right margin only, clamped inside the canvas
margin_x = min(cx2+cw2+40, W-40)
polyline([(cx2+cw2-30, cy2), (margin_x, cy2-140), (margin_x, ay+ah_/2), (ax+aw, ay+ah_/2)],
         dashed=True, color=C_PLANNED)
lbl = "connector protocol exists \u2014 no live route calls it"
lbl_w = len(lbl)*5.7 + 20
svg.append(f'<rect x="{margin_x-lbl_w+6}" y="{cy2-232}" width="{lbl_w}" height="18" rx="0" fill="{BG}"/>')
svg.append(f'<text x="{margin_x+6}" y="{cy2-219}" text-anchor="end" class="mono" font-size="9.4" fill="{C_PLANNED}">{lbl}</text>')

# ================= Legend + footer =================
ly0 = cy2 + ch2 + 46
svg.append(f'<line x1="90" y1="{ly0-20}" x2="{W-90}" y2="{ly0-20}" stroke="{LINE}" stroke-width="1"/>')

leg_items = [
    ("line", INK_MUTED, False, "real, exercised call"),
    ("line", INK_MUTED, True, "specified, not wired / not exercised"),
    ("dot", C_IMPLEMENTED, False, "real, verified — thicker border"),
    ("dot", C_PLANNED, False, "specified, not yet exercised"),
]
lx = 90
for kind, col, dashed_l, text in leg_items:
    if kind == "line":
        dash = 'stroke-dasharray="1 5"' if dashed_l else ""
        svg.append(f'<line x1="{lx}" y1="{ly0}" x2="{lx+30}" y2="{ly0}" stroke="{col}" stroke-width="2" {dash}/>')
        lx += 40
    else:
        svg.append(f'<rect x="{lx}" y="{ly0-4}" width="8" height="8" fill="{col}"/>')
        lx += 20
    svg.append(f'<text x="{lx}" y="{ly0+4}" class="mono" font-size="10.2" fill="{INK_MUTED}">{esc(text)}</text>')
    lx += len(text)*6.05 + 34

svg.append(f'<text x="90" y="{ly0+40}" class="sans" font-size="13" fill="{INK_MUTED}">The one filled black panel marks the AI boundary \u2014 the only place a model is ever called. Everything else is deterministic code or a human decision.</text>')

svg.append('</svg>')

open("/home/claude/svg_kononenko/qa-os-architecture.svg", "w").write("\n".join(svg))
print("written", len(svg), "elements; canvas", W, H)
