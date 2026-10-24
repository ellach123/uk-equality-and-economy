"""Generate the README charts as standalone SVG files.

Uses only the Python standard library so it runs without extra installs.

Usage:
    python v2-revisited/scripts/make_charts.py [data_selected_for_tableau.csv] [2021_industry_0.csv]
"""

import csv
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # v2-revisited/
DATA = ROOT.parent / "data"
DEFAULT_CSV = DATA / "data_selected_for_tableau.csv"
DEFAULT_INDUSTRY_CSV = DATA / "2021_industry" / "2021_industry_0.csv"
SECTIONS = "ABCDEFGHIJKLMNOPQR"  # all 18 industry sections in the 2021 census table
OUT_DIR = ROOT / "images"

FONT = "Helvetica, Arial, sans-serif"
INK = "#1f2933"
MUTED = "#6b7785"
GRID = "#e4e7eb"
LONDON = "#d4572a"
OTHER = "#2f6f9f"
TREND = "#1f2933"


def industry_structure(csv_path):
    """Shannon diversity across the 18 industry sections and the manufacturing share, keyed by geography code."""
    out = {}
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            counts = [float(r["Industry_" + s]) for s in SECTIONS]
            total = sum(counts)
            out[r["geography_code"]] = (
                -sum(c / total * math.log(c / total) for c in counts if c),
                100 * float(r["Industry_C"]) / total,
            )
    return out


def load(csv_path, industry_csv_path):
    structure = industry_structure(industry_csv_path)
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            f = lambda k: float(r[k])
            creative = f("2_I_Creative_arts_entertainment")
            rows.append({
                "name": r["geography"],
                "london": r["geography_code"].startswith("E09"),
                "female_mgr": 100 * f("1_O_F_Managers_directors_seniorOfficials") / f("1_Females_Occupation_Total"),
                "male_mgr": 100 * f("1_O_M_Managers_directors_seniorOfficials") / f("1_Males_Occupation_Total"),
                "female_mgr_count": f("1_O_F_Managers_directors_seniorOfficials"),
                "female_share_of_mgrs": 100 * f("1_O_F_Managers_directors_seniorOfficials") / f("1_O_Managers_directors_seniorOfficials"),
                "creative_count": creative,
                "creative_share": 100 * creative / f("2_Industry_Total"),
                "professional_share": 100 * f("2_I_Professional_scientific_technical") / f("2_Industry_Total"),
                "manufacturing_share": structure[r["geography_code"]][1],
                "industry_total": f("2_Industry_Total"),
                "education_count": f("2_I_Education"),
                "education_share": 100 * f("2_I_Education") / f("2_Industry_Total"),
                "simpson": 1 - sum((f("2_Ethnic_group_" + g) / f("2_Ethnic_group_Total")) ** 2
                                   for g in ("Asian", "Black", "Mixed", "White", "Arab", "Other")),
                "industry_diversity": structure[r["geography_code"]][0],
            })
    return rows


def partial(x, y, z):
    """Correlation of x and y after removing the linear effect of z."""
    rxy, rxz, ryz = statistics.correlation(x, y), statistics.correlation(x, z), statistics.correlation(y, z)
    return (rxy - rxz * ryz) / math.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))


def spearman(x, y):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        out = [0] * len(v)
        for pos, i in enumerate(order):
            out[i] = pos
        return out
    return statistics.correlation(rank(x), rank(y))


def nice_ticks(lo, hi, n=5):
    span = hi - lo
    raw = span / n
    mag = 10 ** len(str(int(raw))) / 10 if raw >= 1 else 1
    for step in (0.1, 0.2, 0.25, 0.5, 1, 2, 2.5, 5, 10):
        if step * mag >= raw:
            step *= mag
            break
    start = (lo // step) * step
    ticks = []
    t = start
    while t <= hi + 1e-9:
        if t >= lo - 1e-9:
            ticks.append(round(t, 6))
        t += step
    return ticks


def fmt(v):
    if abs(v) >= 1000:
        return f"{v / 1000:g}k"
    return f"{v:g}"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def panel(x, y, rows, ox, oy, w, h, xlabel, ylabel, title, subtitle, labels=(), xpad=0.04, ypad=0.06):
    """Return SVG elements for one scatter panel with its top-left corner at (ox, oy)."""
    xs = [r[x] for r in rows]
    ys = [r[y] for r in rows]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    x0, x1 = x0 - (x1 - x0) * xpad, x1 + (x1 - x0) * xpad
    y0, y1 = y0 - (y1 - y0) * ypad, y1 + (y1 - y0) * ypad
    left, top, right, bottom = ox + 58, oy + 58, ox + w - 14, oy + h - 46
    sx = lambda v: left + (v - x0) / (x1 - x0) * (right - left)
    sy = lambda v: bottom - (v - y0) / (y1 - y0) * (bottom - top)

    el = [
        f'<text x="{ox}" y="{oy + 18}" font-size="16" font-weight="700" fill="{INK}">{esc(title)}</text>',
        f'<text x="{ox}" y="{oy + 38}" font-size="13" fill="{MUTED}">{esc(subtitle)}</text>',
    ]
    for t in nice_ticks(x0, x1):
        el.append(f'<line x1="{sx(t):.1f}" y1="{top}" x2="{sx(t):.1f}" y2="{bottom}" stroke="{GRID}"/>')
        el.append(f'<text x="{sx(t):.1f}" y="{bottom + 18}" font-size="11" fill="{MUTED}" text-anchor="middle">{fmt(t)}</text>')
    for t in nice_ticks(y0, y1):
        el.append(f'<line x1="{left}" y1="{sy(t):.1f}" x2="{right}" y2="{sy(t):.1f}" stroke="{GRID}"/>')
        el.append(f'<text x="{left - 8}" y="{sy(t) + 4:.1f}" font-size="11" fill="{MUTED}" text-anchor="end">{fmt(t)}</text>')
    el.append(f'<text x="{(left + right) / 2:.1f}" y="{bottom + 38}" font-size="12" fill="{INK}" text-anchor="middle">{esc(xlabel)}</text>')
    el.append(f'<text transform="translate({ox + 14},{(top + bottom) / 2:.1f}) rotate(-90)" font-size="12" fill="{INK}" text-anchor="middle">{esc(ylabel)}</text>')

    # least-squares trend line, clipped to the plot area
    clip = f"clip{ox}"
    el.append(f'<clipPath id="{clip}"><rect x="{left}" y="{top}" width="{right - left}" height="{bottom - top}"/></clipPath>')
    slope, intercept = statistics.linear_regression(xs, ys)
    lx0, lx1 = min(xs), max(xs)
    el.append(f'<line clip-path="url(#{clip})" x1="{sx(lx0):.1f}" y1="{sy(slope * lx0 + intercept):.1f}" x2="{sx(lx1):.1f}" '
              f'y2="{sy(slope * lx1 + intercept):.1f}" stroke="{TREND}" stroke-width="1.5" stroke-dasharray="5 4" opacity="0.7"/>')

    for r in sorted(rows, key=lambda r: r["london"]):
        colour = LONDON if r["london"] else OTHER
        el.append(f'<circle cx="{sx(r[x]):.1f}" cy="{sy(r[y]):.1f}" r="3.6" fill="{colour}" fill-opacity="0.55" stroke="{colour}" stroke-width="0.6"/>')

    by_name = {r["name"]: r for r in rows}
    for name, dx, dy in labels:
        r = by_name[name]
        name = name.removesuffix(", City of")
        px, py = sx(r[x]), sy(r[y])
        anchor = "start" if dx >= 0 else "end"
        el.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="none" stroke="{INK}" stroke-width="1.2"/>')
        el.append(f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{px + dx:.1f}" y2="{py + dy:.1f}" stroke="{MUTED}" stroke-width="0.8"/>')
        el.append(f'<text x="{px + dx + (3 if dx >= 0 else -3):.1f}" y="{py + dy + 4:.1f}" font-size="11.5" fill="{INK}" text-anchor="{anchor}">{esc(name)}</text>')

    r_p = statistics.correlation(xs, ys)
    el.append(f'<rect x="{right - 128}" y="{bottom - 46}" width="122" height="40" rx="4" fill="#ffffff" fill-opacity="0.9" stroke="{GRID}"/>')
    el.append(f'<text x="{right - 118}" y="{bottom - 29}" font-size="12.5" font-weight="700" fill="{INK}">Pearson r = {r_p:.2f}</text>')
    el.append(f'<text x="{right - 118}" y="{bottom - 13}" font-size="11.5" fill="{MUTED}">Spearman ρ = {spearman(xs, ys):.2f}</text>')
    return el


def legend(x, y):
    return [
        f'<circle cx="{x}" cy="{y}" r="4.5" fill="{LONDON}" fill-opacity="0.6" stroke="{LONDON}"/>',
        f'<text x="{x + 10}" y="{y + 4}" font-size="12" fill="{INK}">London boroughs</text>',
        f'<circle cx="{x + 130}" cy="{y}" r="4.5" fill="{OTHER}" fill-opacity="0.6" stroke="{OTHER}"/>',
        f'<text x="{x + 140}" y="{y + 4}" font-size="12" fill="{INK}">Other local authorities</text>',
    ]


def write_svg(path, w, h, elements):
    body = "\n  ".join(elements)
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" font-family="{FONT}">\n'
        f'  <rect width="{w}" height="{h}" fill="#ffffff"/>\n  {body}\n</svg>\n',
        encoding="utf-8",
    )
    print("wrote", path.relative_to(ROOT))


def main():
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    industry_csv_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_INDUSTRY_CSV
    rows = load(csv_path, industry_csv_path)
    OUT_DIR.mkdir(exist_ok=True)

    # 1. headline chart: women's career advancement (2011) vs creative share (2021)
    el = panel(
        "female_mgr", "creative_share", rows, 24, 20, 832, 500,
        "Female managers as % of employed women (2011)",
        "Arts, entertainment & recreation, % of jobs (2021)",
        "Where more women reached management in 2011, creative work took a larger share by 2021",
        f"{len(rows)} local authorities in England & Wales · ONS Census 2011 and 2021",
        labels=[
            ("Kensington and Chelsea", -14, -14),
            ("Westminster", -16, 16),
            ("Hackney", 14, -12),
            ("Isles of Scilly", -14, -18),
            ("Leeds", -60, -60),
            ("Bristol, City of", -70, -24),
            ("Leicester", 14, 14),
            ("Luton", 16, 22),
        ],
    )
    write_svg(OUT_DIR / "gender_vs_creative_share.svg", 880, 560, el + legend(500, 545))

    # 2. revisited: why counts misled and shares did not
    w = 330
    el = []
    el += panel("female_mgr_count", "creative_count", rows, 20, 20, w, 380,
                "Female managers (count, 2011)", "Creative jobs (count, 2021)",
                "A · Original dashboard", "Counts on both axes")
    el += panel("industry_total", "female_mgr_count", rows, 20 + w + 20, 20, w, 380,
                "All jobs in the area (2021)", "Female managers (count, 2011)",
                "B · Counts mostly measure size", "Female managers vs all jobs")
    el += panel("female_mgr", "creative_share", rows, 20 + 2 * (w + 20), 20, w, 380,
                "Female managers, % of women (2011)", "Creative jobs, % of all jobs",
                "C · Revisited", "Rates and shares")
    write_svg(OUT_DIR / "revisited_count_vs_share.svg", 3 * w + 80, 430, el + legend(340, 418))

    # 3. industry diversity index vs creative share and women's advancement
    w = 440
    el = []
    el += panel("industry_diversity", "creative_share", rows, 20, 20, w, 400,
                "Industry diversity, Shannon index (2021)", "Creative jobs, % of all jobs",
                "A · Diverse economies, more creative work", "Across all 18 industry sections", ypad=0.22)
    el += panel("industry_diversity", "female_mgr", rows, 20 + w + 20, 20, w, 400,
                "Industry diversity, Shannon index (2021)", "Female managers, % of women (2011)",
                "B · Diverse economies, more women managers", "Same index against the 2011 measure", ypad=0.22)
    write_svg(OUT_DIR / "industry_diversity.svg", 2 * w + 60, 450, el + legend(300, 438))

    # numbers quoted in the README
    col = lambda k, rs=rows: [r[k] for r in rs]
    fm, mm, share, div = col("female_mgr"), col("male_mgr"), col("creative_share"), col("industry_diversity")
    gap = [f / m for f, m in zip(fm, mm)]
    outside = [r for r in rows if not r["london"]]
    print(f"female mgr vs creative share: r={statistics.correlation(fm, share):.2f} rho={spearman(fm, share):.2f}")
    print(f"male mgr vs creative share:   r={statistics.correlation(mm, share):.2f}")
    print(f"female vs male mgr:           r={statistics.correlation(fm, mm):.2f}")
    print(f"female/male ratio vs share:   r={statistics.correlation(gap, share):.2f}")
    print(f"partial female | male:        {partial(fm, share, mm):.2f}")
    print(f"partial male | female:        {partial(mm, share, fm):.2f}")
    print(f"diversity vs creative share:  r={statistics.correlation(div, share):.2f} rho={spearman(div, share):.2f}")
    print(f"diversity vs female mgr:      r={statistics.correlation(div, fm):.2f} rho={spearman(div, fm):.2f}")
    print(f"female mgr count vs creative count: r={statistics.correlation(col('female_mgr_count'), col('creative_count')):.2f}")
    print(f"female mgr count vs all jobs:       r={statistics.correlation(col('female_mgr_count'), col('industry_total')):.2f}")
    print(f"outside London ({len(outside)}): r={statistics.correlation(col('female_mgr', outside), col('creative_share', outside)):.2f}")
    print(f"women's share of managers vs creative share: r={statistics.correlation(col('female_share_of_mgrs'), share):.2f}")
    print("version 1 relationships, counts vs shares (main-page comparison):")
    for x, y, label in (("simpson", "education", "ethnic diversity vs education"),
                        ("education", "creative", "education vs arts")):
        xc = col(x) if x == "simpson" else col(x + "_count")
        print(f"  {label}: counts r={statistics.correlation(xc, col(y + '_count')):.2f}"
              f", shares r={statistics.correlation(col(x) if x == 'simpson' else col(x + '_share'), col(y + '_share')):.2f}")
    eden = next(r for r in rows if r["name"] == "Eden")
    print(f"  Eden female manager rate: {eden['female_mgr']:.1f}% (average {statistics.mean(fm):.1f}%)")
    print(f"  creative vs all jobs (counts): r={statistics.correlation(col('creative_count'), col('industry_total')):.2f}")
    for k in ("professional_share", "manufacturing_share"):
        print(f"{k} vs creative share: r={statistics.correlation(col(k), share):.2f}"
              f" (outside London r={statistics.correlation(col(k, outside), col('creative_share', outside)):.2f})")


if __name__ == "__main__":
    main()
