"""
Export of CAN message cycle analysis results (CSV / HTML)
"""

import csv
import html
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np

from utils.cycle_analyzer import CycleStats, GroupKey

HEADERS = ["CAN ID", "通道", "方向", "报文数", "平均(ms)", "中位数(ms)", "最小(ms)",
           "最大(ms)", "标准差(ms)", "预期周期(ms)", "平均偏差(%)", "超差次数", "结论"]
MAX_PLOT_POINTS = 2000


def build_rows(stats: Dict[GroupKey, CycleStats], expected: Dict[GroupKey, float],
               tolerance_pct: float) -> List[list]:
    """One row per group; judgement is 'PASS'/'FAIL' or '' without expected cycle"""
    rows = []
    for key in sorted(stats):
        s = stats[key]
        exp = expected.get(key)
        dev = bad = verdict = ""
        if exp and s.intervals.size:
            dev = f"{s.deviation_pct(exp):+.2f}"
            bad = s.out_of_tolerance(exp, tolerance_pct)
            verdict = "FAIL" if bad else "PASS"
        rows.append([f"0x{s.can_id:03X}", s.channel, s.direction, s.count,
                     f"{s.mean:.3f}", f"{s.median:.3f}", f"{s.min:.3f}",
                     f"{s.max:.3f}", f"{s.std:.3f}", f"{exp:g}" if exp else "",
                     dev, bad, verdict])
    return rows


def export_csv(path: str, stats, expected, tolerance_pct: float):
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)
        writer.writerows(build_rows(stats, expected, tolerance_pct))


def _svg_plot(s: CycleStats, expected: Optional[float], tol: float,
              w: int = 760, h: int = 200) -> str:
    if not s.intervals.size:
        return ""
    t, y = s.times, s.intervals
    if len(t) > MAX_PLOT_POINTS:
        idx = np.linspace(0, len(t) - 1, MAX_PLOT_POINTS).astype(int)
        t, y = t[idx], y[idx]
    lo, hi = float(y.min()), float(y.max())
    if expected:
        lo = min(lo, expected * (1 - tol / 100))
        hi = max(hi, expected * (1 + tol / 100))
    if hi == lo:
        hi, lo = hi + 1, lo - 1
    pad = 40
    t0, t1 = float(t[0]), float(t[-1])
    span = (t1 - t0) or 1.0

    def px(v): return pad + (v - t0) / span * (w - pad - 10)
    def py(v): return h - 20 - (v - lo) / (hi - lo) * (h - 30)

    pts = " ".join(f"{px(a):.1f},{py(b):.1f}" for a, b in zip(t, y))
    out = [f'<svg viewBox="0 0 {w} {h}" width="100%" style="max-width:{w}px">',
           f'<rect width="{w}" height="{h}" fill="#fff" stroke="#ccc"/>',
           f'<text x="4" y="14" font-size="11">{hi:.2f}ms</text>',
           f'<text x="4" y="{h - 22}" font-size="11">{lo:.2f}ms</text>',
           f'<text x="{pad}" y="{h - 5}" font-size="11">{t0:.3f}s</text>',
           f'<text x="{w - 60}" y="{h - 5}" font-size="11">{t1:.3f}s</text>']
    if expected:
        for v, color, dash in ((expected, "#2ca02c", ""),
                               (expected * (1 + tol / 100), "#ff7f0e", "4,3"),
                               (expected * (1 - tol / 100), "#ff7f0e", "4,3")):
            out.append(f'<line x1="{pad}" x2="{w - 10}" y1="{py(v):.1f}" y2="{py(v):.1f}" '
                       f'stroke="{color}" stroke-dasharray="{dash}"/>')
    out.append(f'<polyline points="{pts}" fill="none" stroke="#1f77b4" stroke-width="1"/>')
    out.append('</svg>')
    return "".join(out)


def export_html(path: str, stats, expected, tolerance_pct: float, source: str = ""):
    rows = build_rows(stats, expected, tolerance_pct)
    keys = sorted(stats)
    e = html.escape
    parts = ["<!DOCTYPE html><html lang='zh'><head><meta charset='utf-8'>"
             "<title>CAN 报文周期分析报告</title><style>"
             "body{font-family:'Microsoft YaHei',sans-serif;margin:24px}"
             "table{border-collapse:collapse;font-size:13px}"
             "th,td{border:1px solid #ccc;padding:4px 8px;text-align:right}"
             "th{background:#f0f0f0}.FAIL{background:#fdd}.PASS{background:#dfd}"
             "h3{margin-top:28px}</style></head><body>",
             "<h1>CAN 报文周期分析报告</h1>",
             f"<p>生成时间: {datetime.now():%Y-%m-%d %H:%M:%S}<br>"
             f"数据源: {e(source) or '-'}<br>容差: ±{tolerance_pct:g}%<br>"
             "结论: 仅对设置了预期周期的分组判定，存在超差点即为 FAIL</p>",
             "<table><tr>" + "".join(f"<th>{h}</th>" for h in HEADERS) + "</tr>"]
    for row in rows:
        cls = f" class='{row[-1]}'" if row[-1] else ""
        parts.append(f"<tr{cls}>" + "".join(f"<td>{e(str(c))}</td>" for c in row) + "</tr>")
    parts.append("</table><h2>周期曲线</h2>"
                 "<p>蓝线: 实际周期; 绿线: 预期周期; 橙色虚线: 容差范围</p>")
    for key, row in zip(keys, rows):
        s = stats[key]
        parts.append(f"<h3>{row[0]} / 通道{row[1]} / {row[2]}</h3>"
                     + _svg_plot(s, expected.get(key), tolerance_pct))
    parts.append("</body></html>")
    with open(path, 'w', encoding='utf-8') as f:
        f.write("".join(parts))
