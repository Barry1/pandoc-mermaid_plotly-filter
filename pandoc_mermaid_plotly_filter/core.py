import hashlib
import re
from pathlib import Path

import plotly.graph_objects as go

PALETTE = ["#7aa5ff", "#7ac9d0", "#ffbe7a", "#a8c6ff", "#8fb5ff", "#ffb3ba", "#baffc9"]
PROJECT_ROOT = Path.cwd()
DEFAULT_OUTDIR = PROJECT_ROOT / "mermaid-plotly-cache"


def parse_sankey(t):
    flows = []
    for line in t.splitlines():
        s = line.strip()
        if (
            not s
            or "," not in s
            or s.lower().startswith("sankey")
            or s.startswith(("%", "#|"))
        ):
            continue
        parts = [p.strip().strip('"').strip("'") for p in s.split(",")]
        if len(parts) >= 3:
            try:
                flows.append((parts[0], parts[1], float(parts[2])))
            except:
                pass
    return flows


def parse_pie(t):
    out = []
    for line in t.splitlines():
        if "#|" in line:
            continue
        m = re.match(r'\s*"?([^":]+)"?\s*:\s*([0-9.]+)', line)
        if m:
            k = m.group(1).strip().lower()
            if k in ("pie", "title", "showdata"):
                continue
            out.append((m.group(1).strip().strip('"'), float(m.group(2))))
    return out


def build_fig(code, width=1920, height=1080, title=""):
    low = code.lower()
    if "sankey" in low:
        flows = parse_sankey(code) or [("A", "B", 10), ("B", "C", 5)]
        labels = []
        l2i = {}

        def idx(n):
            if n not in l2i:
                l2i[n] = len(labels)
                labels.append(n)
            return l2i[n]

        src = [idx(s) for s, _, _ in flows]
        tgt = [idx(t) for _, t, _ in flows]
        val = [v for _, _, v in flows]
        node_c = [PALETTE[i % len(PALETTE)] for i in range(len(labels))]
        link_c = [
            f"rgba({int(c[1:3], 16)},{int(c[3:5], 16)},{int(c[5:7], 16)},0.45)"
            for c in [node_c[s] for s in src]
        ]
        fig = go.Figure(
            go.Sankey(
                node={
                    "label": labels,
                    "color": node_c,
                    "pad": 25,
                    "thickness": 22,
                    "line": {"color": "white", "width": 2},
                },
                link={"source": src, "target": tgt, "value": val, "color": link_c},
            )
        )
    elif "pie" in low:
        parsed = parse_pie(code)
        labs, vals = (
            zip(*parsed) if parsed else (["Dogs", "Cats", "Birds"], [40, 30, 30])
        )
        fig = go.Figure(
            go.Pie(
                labels=labs,
                values=vals,
                hole=0.35,
                marker_colors=PALETTE,
                textinfo="label+percent",
            )
        )
    else:
        nodes = re.findall(r"(\w+)\s*[\[\{]", code)
        nodes = list(dict.fromkeys(nodes)) or ["A", "B", "C"]
        pos = {n: (i % 4, i // 4) for i, n in enumerate(nodes)}
        fig = go.Figure()
        for line in code.splitlines():
            m = re.match(r"\s*(\w+)\s*--?[-=]*>\s*(\w+)", line)
            if m and m.group(1) in pos and m.group(2) in pos:
                x0, y0 = pos[m.group(1)]
                x1, y1 = pos[m.group(2)]
                fig.add_shape(
                    type="line",
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    y1=y1,
                    line={"color": "#a0aec0", "width": 2},
                )
        fig.add_trace(
            go.Scatter(
                x=[pos[n][0] for n in nodes],
                y=[pos[n][1] for n in nodes],
                mode="markers+text",
                text=nodes,
                marker={"size": 50, "color": PALETTE[0]},
                showlegend=False,
            )
        )
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False, autorange="reversed")
    fig.update_layout(
        title={"text": title, "x": 0.5, "font": {"size": 22}},
        width=width,
        height=height,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
    )
    return fig


def render_to_file(code, width, height, title, outdir=None):
    outdir = Path(outdir) if outdir else DEFAULT_OUTDIR
    if not outdir.is_absolute():
        outdir = PROJECT_ROOT / outdir
    outdir.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256(code.encode()).hexdigest()[:12]
    outfile = outdir / f"mermaid-{h}.png"
    if not outfile.exists():
        fig = build_fig(code, width, height, title)
        fig.write_image(str(outfile), scale=2)
    return outfile
