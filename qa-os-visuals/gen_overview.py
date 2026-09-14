"""
QA Operating System — overview visual, Kononenko design system.
Pure black/white, zero saturation, no rounded corners, no icons except the
single arrow glyph, hairline rules, generous whitespace, numbered-list
grammar (matching the site's real "office-locations list" convention).
"""
W, H = 1500, 1052

WHITE = "#FFFFFF"
BLACK = "#000000"
HAIR = "#D8D8D8"
MUTED = "#6B6B6B"
FAINT = "#9A9A9A"

F_DISPLAY = "Fraunces, Georgia, 'Times New Roman', serif"
F_CAPTION = "Georgia, 'Times New Roman', serif"
F_SANS = "'General Sans', Inter, -apple-system, 'Segoe UI', sans-serif"
F_MONO = "'IBM Plex Mono', 'Courier New', monospace"

M = 72  # fixed margin, not proportional (Kononenko DNA: fixed-pixel gutter)

steps = [
    ("01", "INPUT",  "Requirement",
     "Someone writes what needs to be true, in plain English \u2014 e.g. \u201cusers must be able to log in via OAuth2, including token refresh and session expiry.\u201d"),
    ("02", "AI",     "Risk is scored",
     "The system checks its memory for similar requirements it has seen before, then scores how risky this one is \u2014 and writes down why."),
    ("03", "AI",     "Tests are drafted",
     "Candidate test cases are generated from the requirement and its risk score. They are marked \u201cdraft.\u201d Nothing here is trusted yet."),
    ("04", "HUMAN",  "A person decides",
     "A QA lead approves or rejects each draft. No model makes this call \u2014 this is the one step with no AI in it at all."),
    ("05", "OUTPUT", "The decision is remembered",
     "Whatever the person decided is written back to memory, so the next similar requirement inherits it instead of starting from zero."),
]

svg = []
def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="ov-title ov-desc">')
svg.append('<title id="ov-title">QA Operating System — how one requirement moves through the working slice</title>')
svg.append('<desc id="ov-desc">Five steps: a requirement is scored for risk by AI, test cases are drafted by AI, a human reviews and decides with no model involved, and the outcome is written back to memory for the next similar requirement.</desc>')
svg.append('<style>')
svg.append(f'  .display {{ font-family: {F_DISPLAY}; letter-spacing: -0.01em; }}')
svg.append(f'  .caption {{ font-family: {F_CAPTION}; font-style: italic; }}')
svg.append(f'  .sans {{ font-family: {F_SANS}; }}')
svg.append(f'  .mono {{ font-family: {F_MONO}; letter-spacing: 0.07em; }}')
svg.append('</style>')
svg.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{WHITE}"/>')

# header
svg.append(f'<text x="{M}" y="70" class="mono" font-size="11" fill="{MUTED}">QA OPERATING SYSTEM \u2014 WORKING SLICE</text>')
svg.append(f'<text x="{M-2}" y="128" class="display" font-size="42" fill="{BLACK}">One requirement, followed end to end</text>')
svg.append(f'<text x="{M}" y="162" class="sans" font-size="15" fill="{MUTED}">The single real, verified path through a much larger planned system \u2014 not a mockup of one.</text>')
svg.append(f'<line x1="{M}" y1="196" x2="{W-M}" y2="196" stroke="{BLACK}" stroke-width="1.5"/>')

row_top = 196
row_h = (5) and 0
rows_y0 = 196
row_height = 128
label_col_w = 150

for i, (n, tag, title, body) in enumerate(steps):
    y0 = rows_y0 + i * row_height
    y1 = y0 + row_height
    # hairline under each row (bottom edge)
    svg.append(f'<line x1="{M}" y1="{y1}" x2="{W-M}" y2="{y1}" stroke="{HAIR}" stroke-width="1"/>')

    ty = y0 + 52
    svg.append(f'<text x="{M}" y="{ty}" class="mono" font-size="16" fill="{MUTED}">{n}</text>')
    svg.append(f'<text x="{M+52}" y="{ty-14}" class="mono" font-size="10" fill="{FAINT}">[{tag}]</text>')
    svg.append(f'<text x="{M+52}" y="{ty+8}" class="sans" font-size="21" fill="{BLACK}">{esc(title)}</text>')

    # wrap body text to two lines within remaining width
    body_x = M + label_col_w + 290
    max_chars = 96
    words = body.split(" ")
    lines, cur = [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if len(trial) > max_chars:
            lines.append(cur)
            cur = w_
        else:
            cur = trial
    if cur:
        lines.append(cur)
    by = y0 + 40
    for line in lines[:3]:
        svg.append(f'<text x="{body_x}" y="{by}" class="sans" font-size="13.5" fill="{MUTED}">{esc(line)}</text>')
        by += 20

    if i == len(steps) - 1:
        svg.append(f'<text x="{W-M}" y="{ty+8}" text-anchor="end" class="sans" font-size="18" fill="{BLACK}">\u2197</text>')

closing_y = rows_y0 + len(steps) * row_height + 56
svg.append(f'<text x="{M}" y="{closing_y}" class="caption" font-size="19" fill="{BLACK}">That is the entire real, working slice.</text>')
svg.append(f'<text x="{M}" y="{closing_y+30}" class="sans" font-size="14" fill="{MUTED}">Everything past step five \u2014 running the tests, triaging failures, deciding if a release is ready \u2014</text>')
svg.append(f'<text x="{M}" y="{closing_y+52}" class="sans" font-size="14" fill="{MUTED}">is the vision this project is honest about not having built yet.</text>')

footer_y = closing_y + 96
svg.append(f'<line x1="{M}" y1="{footer_y-30}" x2="{W-M}" y2="{footer_y-30}" stroke="{BLACK}" stroke-width="1.5"/>')
svg.append(f'<text x="{M}" y="{footer_y}" class="mono" font-size="11" fill="{BLACK}">[IMPLEMENTED]</text>')
svg.append(f'<text x="{M+150}" y="{footer_y}" class="sans" font-size="13" fill="{MUTED}">This loop runs today, over real HTTP \u2014 three of ten planned modules; the rest remain a specified, not-yet-built vision.</text>')

svg.append('</svg>')
open("/home/claude/svg_kononenko/qa-os-overview.svg", "w").write("\n".join(svg))
print("written, rows end at", rows_y0 + len(steps)*row_height, "footer at", footer_y)
