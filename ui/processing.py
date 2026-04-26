"""
UI module: render_processing_screen
Animated gear transition screen between pipeline phases.
"""
import math
import streamlit as st


def _gear(cx, cy, R, n, tooth=0.2, hole=0.35):
    """Generate SVG path for a gear (outer teeth + inner hole, evenodd fill)."""
    ri = R * (1 - tooth)  # root radius
    hr = R * hole          # hole radius
    pts = []
    for i in range(n):
        apt  = 2 * math.pi / n
        base = i * apt - math.pi / 2
        for frac, r in [(0.0, ri), (0.25, R), (0.5, R), (0.75, ri)]:
            a = base + frac * apt
            pts.append(f"{cx + r*math.cos(a):.2f},{cy + r*math.sin(a):.2f}")
    outer = "M " + " L ".join(pts) + " Z"
    hole_d = (f"M {cx+hr:.2f},{cy:.2f} "
              f"A {hr:.2f},{hr:.2f} 0 1 0 {cx-hr:.2f},{cy:.2f} "
              f"A {hr:.2f},{hr:.2f} 0 1 0 {cx+hr:.2f},{cy:.2f} Z")
    return outer + " " + hole_d


def render_processing_screen(phase: str, estimated_seconds: int = 15) -> None:
    """
    Renders an animated processing transition screen.

    Args:
        phase: "setup_to_assessment" or "assessment_to_plan"
        estimated_seconds: drives progress bar animation duration
    """
    cfg = {
        "setup_to_assessment": {
            "label": "ANALYSING",
            "msgs": [
                "Parsing your resume...",
                "Extracting required skills from JD...",
                "Identifying skill requirements...",
                "Mapping your experience...",
                "Preparing assessment questions...",
                "Almost ready...",
            ],
        },
        "assessment_to_plan": {
            "label": "GENERATING",
            "msgs": [
                "Scoring your proficiency...",
                "Calculating skill gaps...",
                "Finding adjacent skill leverage...",
                "Curating learning resources...",
                "Building your week-by-week plan...",
                "Finalising your learning roadmap...",
            ],
        },
    }
    info   = cfg.get(phase, cfg["setup_to_assessment"])
    label  = info["label"]
    msgs   = str(info["msgs"]).replace("'", '"')   # JS-safe JSON array
    dur    = estimated_seconds

    # ── SVG gear paths (Python-generated, no external deps) ──────────────────
    # Layout: large left, medium top-right, small bottom-right
    # All inside a ~300° circular arrow
    g_large  = _gear(62, 82,  34, 8)
    g_medium = _gear(116, 52, 22, 7)
    g_small  = _gear(116, 114, 17, 6)

    # Circular arrow arc: center (80,82), radius 73 — goes from 50° to 310°
    ax, ay, ar = 80, 82, 73

    def arc_pt(deg):
        r = math.radians(deg)
        return ax + ar * math.cos(r), ay + ar * math.sin(r)

    s1x, s1y = arc_pt(55)
    e1x, e1y = arc_pt(305)
    # arrowhead tip at 305°, tangent direction ~ (sin305°, -cos305°)
    t_deg = math.radians(305)
    tx, ty = math.sin(t_deg), -math.cos(t_deg)
    arrow_size = 11
    # arrowhead triangle points
    tip = (e1x, e1y)
    bl  = (e1x - tx*arrow_size + ty*5, e1y - ty*arrow_size - tx*5)
    br  = (e1x - tx*arrow_size - ty*5, e1y - ty*arrow_size + tx*5)
    arrow_pts = f"{tip[0]:.2f},{tip[1]:.2f} {bl[0]:.2f},{bl[1]:.2f} {br[0]:.2f},{br[1]:.2f}"

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:transparent;display:flex;align-items:center;
      justify-content:center;min-height:400px;font-family:-apple-system,
      BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}}

.wrap{{display:flex;flex-direction:column;align-items:center;
       justify-content:center;width:100%;min-height:380px;
       background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);
       border:1px solid #334155;border-radius:20px;padding:48px 24px;
       animation:breathe 3s ease-in-out infinite}}
@keyframes breathe{{0%,100%{{opacity:1}}50%{{opacity:.97}}}}

/* Gear animations */
@keyframes spin-ccw{{to{{transform:rotate(-360deg)}}}}
@keyframes spin-cw {{to{{transform:rotate( 360deg)}}}}
.gear-large {{
  transform-origin:{62}px {82}px;
  animation:spin-ccw 3s linear infinite}}
.gear-medium{{
  transform-origin:{116}px {52}px;
  animation:spin-cw 2s linear infinite}}
.gear-small {{
  transform-origin:{116}px {114}px;
  animation:spin-ccw 1.5s linear infinite}}
.arrow-ring{{
  transform-origin:{ax}px {ay}px;
  animation:spin-cw 4s linear infinite}}

/* Text */
.phase-label{{font-size:12px;font-weight:700;letter-spacing:3px;
              color:#64748b;text-transform:uppercase;margin-top:28px}}
.status-msg {{font-size:18px;font-weight:500;color:#f1f5f9;
              margin-top:14px;min-height:28px;
              transition:opacity .3s ease}}
.status-msg.fade{{opacity:0}}

/* Dots */
.dots{{display:flex;gap:8px;margin-top:16px;align-items:center}}
.dot{{width:8px;height:8px;border-radius:50%;background:#475569;
      animation:pulse-dot 1.2s ease-in-out infinite}}
.dot:nth-child(1){{animation-delay:0s}}
.dot:nth-child(2){{animation-delay:.4s}}
.dot:nth-child(3){{animation-delay:.8s}}
@keyframes pulse-dot{{
  0%,100%{{transform:scale(1);background:#475569}}
  50%{{transform:scale(1.6);background:#94a3b8}}
}}

/* Progress bar */
.bar-track{{width:320px;height:3px;background:#1e3a5f;
            border-radius:2px;margin-top:28px;overflow:hidden}}
.bar-fill {{height:100%;width:0;background:#3b82f6;border-radius:2px;
            animation:prog {dur}s linear forwards}}
@keyframes prog{{from{{width:0%}}to{{width:95%}}}}
</style></head><body>
<div class="wrap">

  <!-- GEAR SVG -->
  <svg width="160" height="164" viewBox="0 0 160 164"
       xmlns="http://www.w3.org/2000/svg">
    <defs>
      <style>path{{fill:#e2e8f0;fill-rule:evenodd}}
        .arc{{fill:none;stroke:#e2e8f0;stroke-width:7;stroke-linecap:round}}
        .arr{{fill:#e2e8f0}}
      </style>
    </defs>

    <!-- Circular rotating arrow -->
    <g class="arrow-ring">
      <path class="arc"
        d="M {s1x:.2f},{s1y:.2f}
           A {ar},{ar} 0 1 1 {e1x:.2f},{e1y:.2f}"/>
      <polygon class="arr" points="{arrow_pts}"/>
    </g>

    <!-- Large gear (CCW, 3s) -->
    <path class="gear-large" d="{g_large}"/>

    <!-- Medium gear (CW, 2s) -->
    <path class="gear-medium" d="{g_medium}"/>

    <!-- Small gear (CCW, 1.5s) -->
    <path class="gear-small" d="{g_small}"/>
  </svg>

  <div class="phase-label">{label}</div>
  <div class="status-msg" id="msg">Initialising...</div>
  <div class="dots">
    <div class="dot"></div>
    <div class="dot"></div>
    <div class="dot"></div>
  </div>
  <div class="bar-track"><div class="bar-fill"></div></div>

</div>
<script>
const msgs = {msgs};
let idx = 0;
const el = document.getElementById('msg');
el.textContent = msgs[0];

setInterval(() => {{
  el.classList.add('fade');
  setTimeout(() => {{
    idx = (idx + 1) % msgs.length;
    el.textContent = msgs[idx];
    el.classList.remove('fade');
  }}, 300);
}}, 2500);
</script></body></html>"""

    st.components.v1.html(html, height=420, scrolling=False)
