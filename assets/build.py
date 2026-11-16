"""Generates the animated README SVGs in light and dark variants.

Run: python3 assets/build.py  (writes assets/*-light.svg and assets/*-dark.svg)
Edit the content here, never the generated SVGs.
"""
import math
import random
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).parent
T = 16  # seconds per animation loop

THEMES = {
    "dark": dict(bg="#0d1117", panel="#161b22", border="#30363d", text="#e6edf3", muted="#8b949e",
                 accent="#58a6ff", green="#3fb950", yellow="#d29922", orange="#e8743b", red="#f85149", purple="#bc8cff",
                 map_sea="#0a0e15", map_land="#151b25", map_line="#2b3442", glass="#10151d", wind="#ffffff"),
    "light": dict(bg="#ffffff", panel="#f6f8fa", border="#d0d7de", text="#1f2328", muted="#59636e",
                  accent="#0969da", green="#1a7f37", yellow="#9a6700", orange="#c2521f", red="#cf222e", purple="#8250df",
                  map_sea="#dde4ec", map_land="#f4f5f7", map_line="#b6c0cc", glass="#ffffff", wind="#334155"),
}
MAGMA = ["#3b0f70", "#641a80", "#8c2981", "#b73779", "#de4968", "#f7705c", "#fe9f6d", "#fecf92", "#fcfdbf"]
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
CW = 8.43  # width of one 14px monospace char


def pct(t):
    return f"{t / T * 100:.2f}%"


class Anim:
    """Collects per-element keyframes so every element shares one loop of T seconds."""

    def __init__(self):
        self.css, self.n = [], 0

    def _add(self, frames, timing=""):
        name = f"k{self.n}"
        self.n += 1
        self.css.append(f"@keyframes {name}{{{frames}}}.{name}{{animation:{name} {T}s {timing} infinite}}")
        return name

    def appear(self, t):
        """Hidden until t, then visible until the loop fades out."""
        return self._add(f"0%,{pct(t)}{{opacity:0}}{pct(t + .25)},100%{{opacity:1}}")

    def type(self, t, chars):
        """Cover rect that shrinks toward its right edge one char at a time, revealing typed text."""
        dur = chars * 0.05
        return self._add(f"0%,{pct(t)}{{transform:scaleX(1);animation-timing-function:steps({chars})}}"
                         f"{pct(t + dur)},100%{{transform:scaleX(0)}}"), t + dur

    def move(self, t, dur, dx, dy, period=None):
        """Packet travelling (dx,dy) starting at t; repeats every `period` seconds within the loop."""
        steps, cur = [], t
        while cur + dur <= T - 1:
            steps.append(f"{pct(cur)}{{transform:translate(0,0);opacity:1}}"
                         f"{pct(cur + dur)}{{transform:translate({dx}px,{dy}px);opacity:1}}"
                         f"{pct(cur + dur + .01)}{{opacity:0}}")
            if not period:
                break
            cur += period
        return self._add(f"0%,{pct(t - .01)}{{opacity:0}}" + "".join(steps) + "100%{opacity:0}", "linear")

    def grow(self, t, dur=.6):
        """scaleY from 0 for bars (needs .bar: transform-box fill-box, origin bottom)."""
        return self._add(f"0%,{pct(t)}{{transform:scaleY(0)}}{pct(t + dur)},100%{{transform:scaleY(1)}}", "ease-out")

    def style(self, extra=""):
        return (f"<style>text{{font-family:{MONO}}}.sans{{font-family:{SANS}}}"
                f".loop{{animation:loop {T}s infinite}}@keyframes loop{{0%,95%{{opacity:1}}98%,100%{{opacity:0}}}}"
                f".blink{{animation:blink 1s steps(1) infinite}}@keyframes blink{{50%{{opacity:0}}}}"
                f".pulse{{animation:pulse 2.4s ease-in-out infinite;transform-box:fill-box;transform-origin:center}}"
                f"@keyframes pulse{{50%{{transform:scale(1.35);opacity:.55}}}}"
                f".twinkle{{animation:twinkle 3s ease-in-out infinite}}@keyframes twinkle{{50%{{opacity:.35}}}}"
                f".spin{{animation:spin 6s linear infinite;transform-box:fill-box;transform-origin:center}}"
                f"@keyframes spin{{to{{transform:rotate(360deg)}}}}"
                f".bar{{transform-box:fill-box;transform-origin:bottom}}.cover{{transform-box:fill-box;transform-origin:right}}"
                + "".join(self.css) + extra +
                # Reduced motion: show the finished frame, no movement.
                "@media (prefers-reduced-motion:reduce){*{animation:none!important}.cover,.pkt,.wind,.ride{display:none}}</style>")


def svg(w, h, label, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
            f'aria-label="{escape(label)}"><title>{escape(label)}</title>{body}</svg>')


def window(x, y, w, h, title, c):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{c["panel"]}" stroke="{c["border"]}"/>'
            f'<path d="M{x} {y + 34}h{w}" stroke="{c["border"]}"/>'
            + "".join(f'<circle cx="{x + 20 + i * 18}" cy="{y + 17}" r="5.5" fill="{col}"/>'
                      for i, col in enumerate(("#ff5f57", "#febc2e", "#28c840")))
            + f'<text x="{x + w / 2}" y="{y + 22}" text-anchor="middle" font-size="12" fill="{c["muted"]}">{title}</text>')


def box(x, y, w, h, title, sub, c, col):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{c["panel"]}" stroke="{col}" stroke-width="1.5"/>'
            f'<text x="{x + w / 2}" y="{y + h / 2 - 3}" text-anchor="middle" font-size="14" font-weight="600" fill="{c["text"]}">{title}</text>'
            f'<text x="{x + w / 2}" y="{y + h / 2 + 16}" text-anchor="middle" font-size="11" fill="{c["muted"]}">{sub}</text>')


def wire(x1, y1, x2, y2, c):
    return f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{c["border"]}" stroke-width="1.5" stroke-dasharray="4 5"/>'


def packets(a, x1, y1, x2, y2, col, start, n=3):
    return "".join(f'<circle class="pkt {a.move(start + i * .5, 1.1, x2 - x1, y2 - y1, period=3)}" '
                   f'cx="{x1}" cy="{y1}" r="4" fill="{col}"/>' for i in range(n))


def card(c):
    return f'<rect width="880" height="{{h}}" rx="12" fill="{c["panel"]}" stroke="{c["border"]}"/>'


# ---------------------------------------------------------------- hero
def hero(c):
    a, out = Anim(), []
    out.append(window(0, 0, 560, 380, "sebastian@antofagasta: ~", c))
    prompt = f'<tspan fill="{c["green"]}">~/sebastian</tspan><tspan fill="{c["muted"]}"> $ </tspan>'
    award = lambda h, place, col, name: (f'<tspan fill="{c["yellow"]}">{h}</tspan><tspan fill="{col}"> {place}</tspan>'
                                         f'<tspan fill="{c["text"]}"> · {name}</tspan>')
    lines = [
        ("cmd", "whoami"),
        ("out", f'<tspan fill="{c["text"]}">Software Engineer</tspan><tspan fill="{c["muted"]}"> · co-founder @ </tspan>'
                f'<tspan fill="{c["orange"]}">Kuntur AI</tspan>'),
        ("cmd", "cat focus.txt"),
        ("out", f'<tspan fill="{c["text"]}">intelligent products for mining</tspan><tspan fill="{c["accent"]}"> → </tspan>'
                f'<tspan fill="{c["purple"]}">built for who uses them</tspan>'),
        ("cmd", "git log --awards --oneline"),
        ("out", award("e3c19f0", "1st", c["green"], "NASA Space Apps 2026 (Fireguard)")),
        ("out", award("b74d2a1", "1st", c["green"], "Hackadisc 2026 (Insecap)")),
        ("out", award("9f02c6e", "3rd", c["orange"], "Hackamine 2026 (BHP · Case 3)")),
        ("out", award("a1f9c2e", "1st", c["green"], "Space Apps 2025 · 2nd Hackadisc 2025")),
    ]
    t, y, px = 0.6, 70, 20 + 14 * CW  # prompt "~/sebastian $ " is 14 chars
    for i, (kind, txt) in enumerate(lines):
        if kind == "cmd":
            start = t + .4
            out.append(f'<text class="{a.appear(start - .3)}" x="20" y="{y}" font-size="14">{prompt}'
                       f'<tspan fill="{c["text"]}">{txt}</tspan></text>')
            k, t = a.type(start, len(txt))
            out.append(f'<rect class="cover {k}" x="{px - 2:.1f}" y="{y - 15}" width="{len(txt) * CW + 6:.1f}" height="20" fill="{c["panel"]}"/>')
        else:
            t += .35
            out.append(f'<text class="{a.appear(t)}" x="20" y="{y}" font-size="14">{txt}</text>')
        y += 26
        if kind == "out" and i + 1 < len(lines) and lines[i + 1][0] == "cmd":
            y += 10
    out.append(f'<text class="{a.appear(t + .4)}" x="20" y="{y + 10}" font-size="14">{prompt}'
               f'<tspan class="blink" fill="{c["accent"]}">▍</tspan></text>')

    # right column: what I've shipped
    out.append(window(580, 0, 300, 380, "shipped.md", c))
    shipped = [("Kuntur AI", "mining accreditation · agentic AI", c["orange"]),
               ("Fireguard", "26 years of fire data · CL + AR", c["red"]),
               ("Belt vision", "uncrushables before the SAG", c["yellow"]),
               ("Insecap KPIs", "sales + 4 ML models", c["accent"]),
               ("Air quality", "NASA TEMPO + OpenAQ", c["green"])]
    for i, (name, sub, col) in enumerate(shipped):
        yy, k = 50 + i * 64, a.appear(1.2 + i * 1.1)
        out.append(f'<g class="{k}"><rect x="598" y="{yy}" width="264" height="54" rx="8" fill="{c["bg"]}" stroke="{c["border"]}"/>'
                   f'<rect x="598" y="{yy}" width="4" height="54" rx="2" fill="{col}"/>'
                   f'<text x="616" y="{yy + 23}" font-size="13" font-weight="600" fill="{c["text"]}">{name}</text>'
                   f'<text x="616" y="{yy + 42}" font-size="11" fill="{c["muted"]}">{sub}</text>'
                   f'<text x="846" y="{yy + 23}" font-size="13" text-anchor="end" fill="{c["green"]}">✓</text></g>')
    return svg(880, 380, "Terminal session: Sebastián Cortez Silva, software engineer and co-founder of Kuntur AI, "
               "building intelligent products for mining. Awards: 1st at NASA Space Apps 2026, 1st at Hackadisc 2026, "
               "3rd at Hackamine 2026, 1st at NASA Space Apps 2025 and 2nd at Hackadisc 2025. Beside it, a list of "
               "shipped work: Kuntur AI, Fireguard, belt vision, Insecap KPIs and an air quality platform.",
               a.style() + f'<g class="loop">{"".join(out)}</g>')


# ---------------------------------------------------------------- Kuntur AI
def kuntur(c):
    a, o, k = Anim(), [], c["orange"]
    o.append(card(c).format(h=280))
    o.append(f'<text x="40" y="44" font-size="12" fill="{c["muted"]}">contractor uploads once</text>')
    docs = [("contract.pdf", c["accent"]), ("insurance.pdf", c["green"]), ("worker-cert.jpg", c["yellow"]), ("license.pdf", c["purple"])]
    for i, (name, col) in enumerate(docs):
        y = 62 + i * 46
        o.append(f'<g class="{a.appear(.4 + i * .5)}"><rect x="40" y="{y}" width="190" height="36" rx="7" fill="{c["bg"]}" stroke="{c["border"]}"/>'
                 f'<path d="M54 {y + 9}h10l5 5v14h-15z" fill="none" stroke="{col}" stroke-width="1.5"/>'
                 f'<text x="80" y="{y + 23}" font-size="12" fill="{c["text"]}">{name}</text></g>')
    o.append(wire(230, 140, 320, 140, c) + wire(520, 140, 590, 140, c))
    o.append(box(320, 100, 200, 80, "Kuntur agent", "extract · check · alert", c, k))
    o.append(packets(a, 230, 140, 320, 140, k, 2.6) + packets(a, 520, 140, 590, 140, k, 3.4))
    # checklist
    o.append(f'<rect x="590" y="30" width="260" height="222" rx="10" fill="{c["bg"]}" stroke="{c["border"]}"/>'
             f'<text x="606" y="54" font-size="12" fill="{c["text"]}">contract checklist</text>')
    items = [("Company data", "✓", c["green"], ""), ("Insurance in force", "✓", c["green"], ""),
             ("Worker cert", "!", c["yellow"], "expires in 12 days"), ("Conformity", "◐", c["purple"], "a person approves")]
    for i, (name, mark, col, note) in enumerate(items):
        y = 76 + i * 38
        o.append(f'<g class="{a.appear(4.5 + i * .8)}"><circle cx="614" cy="{y}" r="8" fill="{col}" opacity=".18"/>'
                 f'<text x="614" y="{y + 4}" text-anchor="middle" font-size="11" fill="{col}">{mark}</text>'
                 f'<text x="630" y="{y + 4}" font-size="12" fill="{c["text"]}">{name}</text>'
                 f'<text x="836" y="{y + 4}" font-size="10" text-anchor="end" fill="{col}">{note}</text></g>')
    o.append(f'<g class="{a.appear(8.2)}"><rect x="606" y="214" width="228" height="26" rx="13" fill="{k}" opacity=".15"/>'
             f'<text x="720" y="231" text-anchor="middle" font-size="11" fill="{k}">work folder · ZIP + index ✓</text></g>')
    o.append(f'<text x="40" y="262" font-size="11" fill="{c["muted"]}">no conformity is approved without a person</text>')
    return svg(880, 280, "Diagram: a mining contractor uploads its documents once; the Kuntur agent extracts the data, "
               "checks it against each contract's checklist and warns before documents expire, a person approves "
               "conformity, and a work folder is generated as a ZIP with an index.", a.style() + "".join(o))


# ---------------------------------------------------------------- Fireguard (map UI)
def fireguard(c):
    a, o, rnd = Anim(), [], random.Random(7)
    W, H = 880, 460
    glass = f'fill="{c["glass"]}" fill-opacity=".9" stroke="{c["border"]}"'
    o.append(f'<clipPath id="m"><rect width="{W}" height="{H}" rx="12"/></clipPath><g clip-path="url(#m)">')
    o.append(f'<rect width="{W}" height="{H}" fill="{c["map_sea"]}"/>')

    # coastline (west) and Andes border (east), jagged like a real map
    coast = [(380 + rnd.uniform(-14, 14) + (y - 230) * .05, y) for y in range(-10, H + 20, 18)]
    border = [(560 + rnd.uniform(-18, 18), y) for y in range(-10, H + 20, 22)]
    land = "M" + " L".join(f"{x:.0f} {y}" for x, y in coast) + f" L{W} {H + 20} L{W} -10Z"
    o.append(f'<path d="{land}" fill="{c["map_land"]}" stroke="{c["map_line"]}" stroke-width="1.2"/>')
    o.append('<path d="M' + " L".join(f"{x:.0f} {y}" for x, y in border) + f'" fill="none" stroke="{c["map_line"]}" stroke-dasharray="5 4"/>')

    # hotspot grid (FIRMS cells), denser around Valparaíso / central Chile
    S, TW = 26, ' class="twinkle"'
    for gx in range(int(390 // S), int(810 // S)):
        for gy in range(3, 15):
            x, y = gx * S, gy * S
            coast_x = 380 + (y - 230) * .05
            if x < coast_x + 6:
                continue
            dist = ((x - 440) ** 2 + (y - 250) ** 2) ** .5
            p = max(.08, 1 - dist / 260) * (1 if x < 560 else .55)
            if rnd.random() > p:
                continue
            v = min(len(MAGMA) - 1, int(p ** 1.8 * len(MAGMA) * rnd.uniform(.5, 1.25)))
            tw = f' class="twinkle" style="animation-delay:{rnd.uniform(0, 3):.2f}s"' if rnd.random() < .35 else ""
            o.append(f'<rect{tw} x="{x}" y="{y}" width="{S}" height="{S}" fill="{MAGMA[v]}" fill-opacity=".72"/>')

    # region outline
    o.append(f'<path d="M402 196L440 182L470 196L488 230L478 270L452 296L418 302L400 270L396 230Z" fill="none" '
             f'stroke="{c["orange"]}" stroke-width="2.2" stroke-linejoin="round"/>')
    for x, y, name in ((404, 252, "VALPARAÍSO"), (470, 318, "SANTIAGO"), (600, 262, "MENDOZA"), (420, 380, "SAN FERNANDO")):
        o.append(f'<text class="sans" x="{x}" y="{y}" font-size="10" letter-spacing="1" fill="{c["text"]}" stroke="{c["map_land"]}" stroke-width="3" paint-order="stroke">{name}</text>')

    # wind particles (Windy-style streaks)
    o.append('<g class="wind">')
    for i in range(70):
        x, y = rnd.uniform(270, 840), rnd.uniform(70, 390)
        L, d, dur = rnd.uniform(10, 22), rnd.uniform(0, 4), rnd.uniform(2.6, 4.2)
        o.append(f'<path class="w" style="animation-duration:{dur:.2f}s;animation-delay:-{d:.2f}s" '
                 f'd="M{x:.0f} {y:.0f}l{L:.0f} {-L * .3:.0f}" stroke="{c["wind"]}" stroke-width="1.3" stroke-linecap="round"/>')
    o.append('</g>')

    # top bar
    o.append(f'<rect x="16" y="16" width="250" height="46" rx="10" {glass}/>'
             f'<circle cx="40" cy="39" r="12" fill="{c["orange"]}" opacity=".9"/>'
             f'<path d="M40 31c4 5 5 8 2 12c-1-2-3-3-4-2c-2 2 0 5 2 6c-5 0-7-4-5-8c1-3 4-4 5-8z" fill="#fff"/>'
             f'<text x="60" y="36" font-size="14" font-weight="700" fill="{c["text"]}">Fireguard</text>'
             f'<text class="sans" x="60" y="53" font-size="10" fill="{c["muted"]}">Harmonized fire calendar · CL + AR</text>')
    tabs = ["Firefighter", "Early warning", "Land manager", "Science"]
    o.append(f'<rect x="446" y="16" width="418" height="46" rx="10" {glass}/>')
    tx = 458
    for i, name in enumerate(tabs):
        w = len(name) * 6.6 + 22
        if i == 2:
            o.append(f'<rect x="{tx - 4}" y="23" width="{w}" height="32" rx="8" fill="{c["green"]}" fill-opacity=".12" stroke="{c["green"]}"/>')
        o.append(f'<text class="sans" x="{tx + w / 2 - 4}" y="44" text-anchor="middle" font-size="12" '
                 f'font-weight="{600 if i == 2 else 400}" fill="{c["text"] if i == 2 else c["muted"]}">{name}</text>')
        tx += w + 6

    # left panel: burn calendar
    o.append(f'<rect x="16" y="74" width="250" height="300" rx="10" {glass}/>'
             f'<text class="sans" x="32" y="98" font-size="9" letter-spacing="1" fill="{c["green"]}">LAND MANAGER · CHILE</text>'
             f'<text class="sans" x="32" y="120" font-size="17" font-weight="600" fill="{c["text"]}">Valparaíso</text>'
             f'<text class="sans" x="32" y="148" font-size="12" font-weight="600" fill="{c["text"]}">Burn calendar</text>')
    for m, ch in enumerate("JFMAMJJASOND"):
        o.append(f'<text class="sans" x="{66 + m * 15.5}" y="166" text-anchor="middle" font-size="8" fill="{c["muted"]}">{ch}</text>')
    for r in range(11):
        year = 2025 - r * 2
        o.append(f'<text class="sans" x="32" y="{180 + r * 15}" font-size="8" fill="{c["muted"]}">{year}</text>')
        for m in range(12):
            summer = m in (0, 1, 2, 11)
            v = min(8, int(rnd.uniform(0, 3.5) + (rnd.uniform(1.5, 5.5) if summer else 0)))
            hot = (r, m) == (1, 1)
            o.append(f'<rect{TW if hot else ""} x="{59 + m * 15.5}" y="{172 + r * 15}" width="14" height="13" '
                     f'rx="1.5" fill="{MAGMA[8 if hot else v]}"/>')
    o.append(f'<defs><linearGradient id="g"><stop offset="0" stop-color="{MAGMA[0]}"/><stop offset=".5" stop-color="{MAGMA[4]}"/>'
             f'<stop offset="1" stop-color="{MAGMA[8]}"/></linearGradient></defs>'
             f'<rect x="60" y="346" width="150" height="6" rx="3" fill="url(#g)"/>'
             f'<text class="sans" x="52" y="352" text-anchor="end" font-size="8" fill="{c["muted"]}">0</text>'
             f'<text class="sans" x="216" y="352" font-size="8" fill="{c["muted"]}">813</text>')

    # right layer toolbar
    o.append(f'<rect x="814" y="74" width="50" height="196" rx="10" {glass}/>')
    for i, (name, on) in enumerate((("3D", False), ("Heat", False), ("Wind", True), ("Zones", False))):
        y = 84 + i * 46
        o.append(f'<rect x="822" y="{y}" width="34" height="38" rx="7" fill="{c["orange"] if on else "none"}" fill-opacity=".14" '
                 f'stroke="{c["orange"] if on else "none"}"/>'
                 f'<circle cx="839" cy="{y + 14}" r="5" fill="none" stroke="{c["orange"] if on else c["muted"]}" stroke-width="1.4"/>'
                 f'<text class="sans" x="839" y="{y + 32}" text-anchor="middle" font-size="8" fill="{c["text"] if on else c["muted"]}">{name}</text>')

    # bottom timeline with playhead
    o.append(f'<rect x="16" y="386" width="848" height="60" rx="10" {glass}/>'
             f'<circle cx="50" cy="416" r="17" fill="{c["orange"]}"/><path d="M45 407l13 9l-13 9z" fill="#fff"/>')
    for i in range(26):
        h = 8 + rnd.uniform(0, 22) + (6 if i in (16, 19, 23) else 0)
        col = c["orange"] if i == 23 else c["muted"]
        o.append(f'<rect class="bar {a.grow(.3 + i * .08, .4)}" x="{84 + i * 29}" y="{432 - h:.0f}" width="24" height="{h:.0f}" '
                 f'rx="2" fill="{col}" fill-opacity="{1 if i == 23 else .35}"/>')
    for i, lab in ((4, "'05"), (9, "'10"), (14, "'15"), (19, "'20"), (24, "'25")):
        o.append(f'<text class="sans" x="{96 + i * 29}" y="443" text-anchor="middle" font-size="8" fill="{c["muted"]}">{lab}</text>')
    o.append(f'<path class="head" d="M84 396v40" stroke="{c["orange"]}" stroke-width="2"/></g>')

    extra = (".w{animation:wind 3s linear infinite}@keyframes wind{0%{transform:translate(0,0);opacity:0}"
             "25%{opacity:.55}75%{opacity:.4}100%{transform:translate(70px,-22px);opacity:0}}"
             ".head{animation:head 16s linear infinite}@keyframes head{to{transform:translateX(750px)}}")
    return svg(W, H, "Fireguard map interface: hotspot cells over central Chile and Argentina coloured from purple to "
               "yellow, Valparaíso outlined in orange, wind particles drifting across the map, a burn calendar panel "
               "with 26 years by month, a layer toolbar, and a timeline of yearly hotspots with a moving playhead.",
               a.style(extra) + "".join(o))


# ---------------------------------------------------------------- Hackamine: belt vision
def belt(c):
    a, o, rnd = Anim(), [], random.Random(3)
    o.append(card(c).format(h=300))
    # camera + field of view
    o.append(f'<path d="M300 66L250 168H350Z" fill="{c["accent"]}" opacity=".10"/>'
             f'<rect x="284" y="44" width="32" height="22" rx="4" fill="{c["bg"]}" stroke="{c["accent"]}" stroke-width="1.5"/>'
             f'<circle cx="300" cy="55" r="6" fill="none" stroke="{c["accent"]}" stroke-width="1.5"/>'
             f'<circle class="blink" cx="311" cy="49" r="2" fill="{c["red"]}"/>'
             f'<text x="300" y="34" text-anchor="middle" font-size="11" fill="{c["muted"]}">camera · vision model</text>')
    # belt
    o.append(f'<rect x="30" y="170" width="640" height="22" rx="11" fill="{c["bg"]}" stroke="{c["border"]}" stroke-width="1.5"/>'
             f'<path class="tread" d="M42 181H658" stroke="{c["border"]}" stroke-width="2" stroke-dasharray="10 14"/>')
    o.append("".join(f'<circle class="spin" cx="{x}" cy="206" r="9" fill="none" stroke="{c["border"]}" stroke-width="2" stroke-dasharray="6 4"/>'
                     for x in range(60, 660, 75)))
    # rocks ride the belt; one steel piece gets detected under the camera
    BT, X0, X1 = 8, -60, 700  # seconds per pass, start and end x
    speed = (X1 - X0) / BT
    def rock(cx, r):
        pts = " ".join(f"{cx + r * rnd.uniform(.75, 1.1) * math.cos(k * .785):.0f},"
                       f"{168 - r + r * rnd.uniform(.75, 1.05) * math.sin(k * .785):.0f}" for k in range(8))
        return f'<polygon points="{pts}" fill="{c["muted"]}" fill-opacity=".55" stroke="{c["muted"]}"/>'
    objs = [rock(0, 10), rock(70, 14), rock(120, 8), rock(190, 12), rock(330, 9), rock(400, 15), rock(460, 7)]
    steel = (f'<rect x="250" y="148" width="40" height="18" rx="2" fill="{c["text"]}" fill-opacity=".75"/>'
             f'<path d="M254 152h32" stroke="{c["bg"]}" stroke-width="1.5" opacity=".6"/>')
    # time the steel's centre (x=270 in group) reaches the camera at x=300
    t_hit = (300 - (X0 + 270)) / speed
    det = (f'<g class="det"><rect x="244" y="140" width="52" height="32" rx="3" fill="none" stroke="{c["red"]}" stroke-width="2"/>'
           f'<rect x="244" y="124" width="64" height="15" rx="2" fill="{c["red"]}"/>'
           f'<text x="248" y="135" font-size="10" fill="#fff">STEEL .97</text></g>')
    # a second copy one pass behind makes the loop seamless; the clip hides the belt ends
    load = "".join(objs) + steel
    o.append(f'<clipPath id="b"><rect x="30" y="100" width="640" height="100"/></clipPath><g clip-path="url(#b)">'
             f'<g class="ride"><g transform="translate({X0} 0)">{load}{det}'
             f'<g transform="translate({X0 - X1} 0)">{load}</g></g></g></g>')
    # SAG mill
    o.append(f'<circle cx="760" cy="168" r="58" fill="{c["bg"]}" stroke="{c["border"]}" stroke-width="2"/>'
             f'<g class="spin" style="animation-duration:9s"><circle cx="760" cy="168" r="44" fill="none" stroke="{c["muted"]}" '
             f'stroke-width="3" stroke-dasharray="14 10"/></g>'
             f'<text x="760" y="172" text-anchor="middle" font-size="13" font-weight="600" fill="{c["text"]}">SAG</text>'
             f'<text x="760" y="248" text-anchor="middle" font-size="11" fill="{c["muted"]}">SAG mill</text>')
    # alert + P80 readouts
    o.append(f'<g class="alert"><rect x="520" y="40" width="230" height="44" rx="8" fill="{c["red"]}" fill-opacity=".12" stroke="{c["red"]}"/>'
             f'<text x="534" y="59" font-size="12" font-weight="600" fill="{c["red"]}">⚠ uncrushable on belt</text>'
             f'<text x="534" y="75" font-size="10" fill="{c["muted"]}">alert ≥ 4 s before the equipment</text></g>')
    o.append(f'<rect x="30" y="40" width="170" height="70" rx="8" fill="{c["bg"]}" stroke="{c["border"]}"/>'
             f'<text x="44" y="60" font-size="11" fill="{c["muted"]}">granulometry · P80</text>'
             f'<path class="p80" d="M44 96l16-6l14 4l16-10l14 3l16-8l14 5l16-6" fill="none" stroke="{c["green"]}" stroke-width="2"/>')
    o.append(f'<text x="30" y="276" font-size="12" fill="{c["text"]}">77.5 / 90 on the official evaluator '
             f'<tspan fill="{c["muted"]}">(kit baseline 21.8)</tspan></text>'
             f'<text x="850" y="276" text-anchor="end" font-size="12" fill="{c["text"]}">pieces reaching the equipment: '
             f'<tspan fill="{c["red"]}">7</tspan> → <tspan fill="{c["green"]}">1</tspan></text>')
    a_hit, a_end = t_hit / BT * 100, (t_hit + 1.6) / BT * 100
    extra = (f".ride{{animation:ride {BT}s linear infinite}}@keyframes ride{{to{{transform:translateX({X1 - X0}px)}}}}"
             f".det,.alert{{animation:det {BT}s linear infinite}}"
             f"@keyframes det{{0%,{a_hit:.1f}%{{opacity:0}}{a_hit + 1:.1f}%,{min(a_end + 30, 96):.1f}%{{opacity:1}}{min(a_end + 32, 98):.1f}%,100%{{opacity:0}}}}"
             f".tread{{animation:tread .8s linear infinite}}@keyframes tread{{to{{stroke-dashoffset:-24}}}}"
             f".p80{{stroke-dasharray:140;animation:p80 {BT}s ease-out infinite}}@keyframes p80{{0%{{stroke-dashoffset:140}}40%,100%{{stroke-dashoffset:0}}}}")
    return svg(880, 300, "Diagram: rocks and a steel piece ride a conveyor belt toward a SAG mill; a camera with a vision "
               "model measures granulometry (P80) and flags the steel piece, raising an alert at least 4 seconds before "
               "it reaches the equipment. Result: 77.5 of 90 on the official evaluator, and pieces reaching the "
               "equipment drop from 7 to 1 in simulation.", a.style(extra) + "".join(o))


# ---------------------------------------------------------------- Hackadisc 2026: Insecap KPIs
def hackadisc(c):
    a, o = Anim(), []
    o.append(card(c).format(h=300))
    o.append(f'<text x="40" y="44" font-size="12" fill="{c["muted"]}">data + offline models</text>')
    rows = [("sales.csv", c["accent"]), ("quotes.csv", c["accent"]), ("model · late payment", c["purple"]),
            ("model · client risk", c["purple"]), ("+ 2 more models", c["purple"])]
    for i, (name, col) in enumerate(rows):
        y = 60 + i * 42
        o.append(f'<g class="{a.appear(.4 + i * .5)}"><rect x="40" y="{y}" width="200" height="32" rx="7" fill="{c["bg"]}" stroke="{c["border"]}"/>'
                 f'<circle cx="56" cy="{y + 16}" r="4" fill="{col}"/>'
                 f'<text x="68" y="{y + 20}" font-size="12" fill="{c["text"]}">{name}</text></g>')
    o.append(wire(240, 150, 330, 150, c) + wire(530, 150, 590, 150, c))
    o.append(box(330, 110, 200, 80, "KPI API", "FastAPI · SQLite · pandas", c, c["green"]))
    o.append(packets(a, 240, 150, 330, 150, c["purple"], 2.8) + packets(a, 530, 150, 590, 150, c["green"], 3.6))
    # dashboard
    o.append(f'<rect x="590" y="30" width="265" height="240" rx="10" fill="{c["bg"]}" stroke="{c["border"]}"/>'
             f'<rect x="602" y="42" width="84" height="22" rx="6" fill="{c["green"]}" fill-opacity=".15"/>'
             f'<text x="644" y="57" text-anchor="middle" font-size="10" fill="{c["green"]}">management</text>'
             f'<text x="730" y="57" text-anchor="middle" font-size="10" fill="{c["muted"]}">sales exec</text>'
             f'<path d="M606 168h120" stroke="{c["border"]}"/>')
    for i, h in enumerate((40, 58, 46, 70, 64, 84)):
        o.append(f'<rect class="bar {a.grow(4.5 + i * .3)}" x="{610 + i * 19}" y="{168 - h}" width="13" height="{h}" rx="2" '
                 f'fill="{c["accent"]}"/>')
    o.append(f'<text x="606" y="186" font-size="9" fill="{c["muted"]}">sales by month</text>'
             f'<text x="744" y="84" font-size="10" fill="{c["text"]}">collections risk</text>')
    for i, (name, col) in enumerate((("client A", c["green"]), ("client B", c["yellow"]), ("client C", c["red"]),
                                     ("client D", c["green"]), ("client E", c["yellow"]))):
        y = 102 + i * 17
        o.append(f'<g class="{a.appear(6.2 + i * .35)}"><circle cx="750" cy="{y - 3}" r="4" fill="{col}"/>'
                 f'<text x="760" y="{y}" font-size="10" fill="{c["text"]}">{name}</text></g>')
    o.append(f'<g class="{a.appear(8.4)}"><rect x="606" y="206" width="234" height="48" rx="8" fill="{c["red"]}" fill-opacity=".08" stroke="{c["red"]}"/>'
             f'<text x="618" y="225" font-size="11" fill="{c["red"]}">client C · likely to pay late</text>'
             f'<text x="618" y="243" font-size="10" fill="{c["muted"]}">call before the invoice is due</text></g>')
    o.append(f'<text x="40" y="282" font-size="11" fill="{c["muted"]}">sample data</text>')
    return svg(880, 300, "Diagram: sales, quotes and the outputs of offline machine learning models feed a KPI API, "
               "which powers a commercial dashboard with management and sales-executive views, monthly sales bars and a "
               "collections risk traffic light that flags clients likely to pay late.", a.style() + "".join(o))


if __name__ == "__main__":
    for name, fn in (("hero", hero), ("work-kuntur", kuntur), ("work-fireguard", fireguard),
                     ("work-hackamine", belt), ("work-hackadisc", hackadisc)):
        for theme, c in THEMES.items():
            (OUT / f"{name}-{theme}.svg").write_text(fn(c), encoding="utf-8")
            print("wrote", f"{name}-{theme}.svg")
