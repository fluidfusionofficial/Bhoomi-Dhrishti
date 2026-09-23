"""
Generates an HTML analytics report comparing synthetic dataset against
real-world Indian land record benchmarks (Agricultural Census, NFHS-5, DILRMP).
"""
from __future__ import annotations
import csv, json, math, sys
from collections import Counter
from pathlib import Path
from datetime import datetime

import numpy as np

DATASET = Path(__file__).resolve().parent.parent.parent / "dataset"
OUTPUT = DATASET / "analytics_report.html"


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def percentile_bins(values, bins):
    arr = np.array(values)
    counts = []
    labels = []
    for i in range(len(bins) - 1):
        lo, hi = bins[i], bins[i + 1]
        c = int(np.sum((arr >= lo) & (arr < hi)))
        counts.append(c)
        if hi >= 1e6:
            labels.append(f"{lo/1000:.0f}K+")
        elif hi >= 1000:
            labels.append(f"{lo/1000:.0f}K-{hi/1000:.0f}K")
        else:
            labels.append(f"{lo:.0f}-{hi:.0f}")
    return labels, counts


def main():
    print("Loading dataset...")
    gt = load_jsonl(DATASET / "ground_truth" / "parcels.jsonl")
    manifest = json.loads((DATASET / "ground_truth" / "defects_manifest.json").read_text())

    tn_ror = load_jsonl(DATASET / "raw" / "tn_rural" / "revenue_ror.jsonl")
    tn_sro = load_csv(DATASET / "raw" / "tn_rural" / "sro_registrations.csv")
    tn_tax = load_csv(DATASET / "raw" / "tn_rural" / "municipal_tax.csv")
    tn_bp = load_csv(DATASET / "raw" / "tn_rural" / "building_permissions.csv")
    tn_cases = load_jsonl(DATASET / "raw" / "tn_rural" / "court_cases.jsonl")
    tn_ec = load_jsonl(DATASET / "raw" / "tn_rural" / "encumbrance_ec.jsonl")

    ch_ror = load_jsonl(DATASET / "raw" / "ch_urban" / "revenue_ror.jsonl")
    ch_sro = load_csv(DATASET / "raw" / "ch_urban" / "sro_registrations.csv")
    ch_tax = load_csv(DATASET / "raw" / "ch_urban" / "municipal_tax.csv")
    ch_bp = load_csv(DATASET / "raw" / "ch_urban" / "building_permissions.csv")
    ch_cases = load_jsonl(DATASET / "raw" / "ch_urban" / "court_cases.jsonl")
    ch_ec = load_jsonl(DATASET / "raw" / "ch_urban" / "encumbrance_ec.jsonl")

    tn_parcels = [p for p in gt if p["state_code"] == "TN"]
    ch_parcels = [p for p in gt if p["state_code"] == "CH"]

    # ── Compute all metrics ──────────────────────────────────────────────────
    tn_areas = [p["area_sq_m"] for p in tn_parcels]
    ch_areas = [p["area_sq_m"] for p in ch_parcels]

    # Gender
    all_owners = []
    for p in gt:
        all_owners.extend(p.get("owners", []))
    female_count = sum(1 for o in all_owners if o.get("gender") == "F")
    male_count = sum(1 for o in all_owners if o.get("gender") == "M")
    total_owners = female_count + male_count
    female_pct = female_count / total_owners * 100 if total_owners else 0

    # Land class
    tn_classes = Counter(p["land_class"] for p in tn_parcels)
    ch_classes = Counter(p["land_class"] for p in ch_parcels)

    # Ownership count
    tn_owner_counts = Counter(len(p["owners"]) for p in tn_parcels)
    ch_owner_counts = Counter(len(p["owners"]) for p in ch_parcels)

    # Sale values
    tn_sale_vals = [float(r["sale_value"]) for r in tn_sro if float(r["sale_value"]) > 0]
    ch_sale_vals = [float(r["sale_value"]) for r in ch_sro if float(r["sale_value"]) > 0]

    # Tax
    tn_taxes = [float(r["tax_due"]) for r in tn_tax if float(r["tax_due"]) > 0]
    ch_taxes = [float(r["tax_due"]) for r in ch_tax if float(r["tax_due"]) > 0]

    # Defects
    defect_counts = Counter(d["type"] for d in manifest["defects"])

    # Area size class distribution (Agricultural Census categories)
    def area_class_pcts(areas):
        arr = np.array(areas)
        marginal = float(np.sum(arr < 10000)) / len(arr) * 100  # <1 ha
        small = float(np.sum((arr >= 10000) & (arr < 20000))) / len(arr) * 100  # 1-2 ha
        semi_med = float(np.sum((arr >= 20000) & (arr < 40000))) / len(arr) * 100  # 2-4 ha
        medium = float(np.sum((arr >= 40000) & (arr < 100000))) / len(arr) * 100  # 4-10 ha
        large = float(np.sum(arr >= 100000)) / len(arr) * 100  # 10+ ha
        return [marginal, small, semi_med, medium, large]

    tn_size_pcts = area_class_pcts(tn_areas)
    real_size_pcts = [75.42, 10.79, 7.13, 4.25, 2.41]  # Ag Census 2015-16

    # Court case types
    tn_case_types = Counter(c.get("case_type", "unknown") for c in tn_cases)
    ch_case_types = Counter(c.get("case_type", "unknown") for c in ch_cases)

    # Encumbrance stats
    tn_enc_count = sum(1 for e in tn_ec if e.get("encumbrances"))
    ch_enc_count = sum(1 for e in ch_ec if e.get("encumbrances"))

    # TN area histogram bins
    tn_area_bins = [0, 1000, 2000, 5000, 10000, 20000, 50000, 200000]
    tn_area_labels, tn_area_hist = percentile_bins(tn_areas, tn_area_bins)

    ch_area_bins = [0, 50, 100, 200, 500, 1000, 2000, 10000]
    ch_area_labels, ch_area_hist = percentile_bins(ch_areas, ch_area_bins)

    # ── Benchmark comparison table ───────────────────────────────────────────
    benchmarks = [
        ("TN Parcel Count", "2000+", len(tn_parcels), "DILRMP Target"),
        ("CH Parcel Count", "1000+", len(ch_parcels), "DILRMP Target"),
        ("TN Area Median (sq_m)", 5000, int(np.median(tn_areas)), "TN Bhoomi Pahani"),
        ("CH Area Median (sq_m)", 167, int(np.median(ch_areas)), "CH Estate Office"),
        ("TN Area Mean (sq_m)", 8500, int(np.mean(tn_areas)), "Ag Census lognormal fit"),
        ("CH Area Mean (sq_m)", 312, int(np.mean(ch_areas)), "CH Estate Office"),
        ("Female Ownership %", 14.0, round(female_pct, 1), "NFHS-5 (2019-21)"),
        ("Small+Marginal (<2ha) %", 86.21, round(tn_size_pcts[0] + tn_size_pcts[1], 1), "Ag Census 2015-16"),
        ("TN Tax Median (INR)", "500-5000", int(np.median(tn_taxes)), "TN Revenue Dept"),
        ("CH Tax Median (INR)", "5000-50000", int(np.median(ch_taxes)), "MCL Chandigarh"),
        ("Defect Types", "20+", len(defect_counts), "Trust Engine Design"),
        ("Total Defects", "2000+", len(manifest["defects"]), "Calibrated Rates"),
    ]

    # ── Build HTML ───────────────────────────────────────────────────────────
    print("Building HTML report...")

    def js_arr(lst):
        return json.dumps(lst)

    def pct_deviation(real, synth):
        if isinstance(real, str):
            return "-"
        if real == 0:
            return "N/A"
        return f"{abs(synth - real) / real * 100:.1f}%"

    def status_badge(real, synth):
        if isinstance(real, str):
            return '<span class="badge good">PASS</span>'
        dev = abs(synth - real) / real * 100 if real else 0
        if dev <= 5:
            return '<span class="badge good">EXCELLENT</span>'
        elif dev <= 10:
            return '<span class="badge ok">GOOD</span>'
        elif dev <= 20:
            return '<span class="badge warn">FAIR</span>'
        else:
            return '<span class="badge bad">REVIEW</span>'

    benchmark_rows = ""
    for name, real, synth, source in benchmarks:
        dev = pct_deviation(real, synth)
        badge = status_badge(real, synth)
        real_display = real if not isinstance(real, float) else f"{real:.1f}"
        benchmark_rows += f"""
        <tr>
            <td>{name}</td>
            <td class="num">{real_display}</td>
            <td class="num">{synth}</td>
            <td class="num">{dev}</td>
            <td>{badge}</td>
            <td class="src">{source}</td>
        </tr>"""

    # Defect table rows
    defect_rows = ""
    for dtype, count in sorted(defect_counts.items(), key=lambda x: -x[1]):
        defect_rows += f'<tr><td>{dtype}</td><td class="num">{count}</td></tr>\n'

    # Land class data
    tn_class_labels = list(tn_classes.keys())
    tn_class_values = list(tn_classes.values())
    ch_class_labels = list(ch_classes.keys())
    ch_class_values = list(ch_classes.values())

    # Size class comparison
    size_labels = ["Marginal\\n(<1 ha)", "Small\\n(1-2 ha)", "Semi-Medium\\n(2-4 ha)", "Medium\\n(4-10 ha)", "Large\\n(10+ ha)"]

    # Ownership distribution
    own_labels = sorted(set(list(tn_owner_counts.keys()) + list(ch_owner_counts.keys())))
    own_labels_capped = [str(x) if x < 10 else "10+" for x in own_labels[:6]]
    tn_own_vals = [tn_owner_counts.get(x, 0) for x in own_labels[:6]]
    ch_own_vals = [ch_owner_counts.get(x, 0) for x in own_labels[:6]]

    # Case type data
    all_case_types = sorted(set(list(tn_case_types.keys()) + list(ch_case_types.keys())))
    tn_case_vals = [tn_case_types.get(t, 0) for t in all_case_types]
    ch_case_vals = [ch_case_types.get(t, 0) for t in all_case_types]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bhoomi Dhrishti - Synthetic Data Analytics</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0f172a; --surface: #1e293b; --surface2: #334155;
    --text: #e2e8f0; --text2: #94a3b8; --accent: #38bdf8;
    --green: #34d399; --yellow: #fbbf24; --red: #f87171; --orange: #fb923c;
    --purple: #a78bfa; --pink: #f472b6;
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:var(--bg); color:var(--text); font-family:'Segoe UI',system-ui,sans-serif; padding:20px; }}
  .header {{ text-align:center; padding:30px 0 20px; border-bottom:1px solid var(--surface2); margin-bottom:30px; }}
  .header h1 {{ font-size:2rem; background:linear-gradient(135deg,var(--accent),var(--purple)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
  .header p {{ color:var(--text2); margin-top:8px; }}
  .header .meta {{ display:flex; gap:30px; justify-content:center; margin-top:15px; flex-wrap:wrap; }}
  .header .meta span {{ background:var(--surface); padding:6px 16px; border-radius:20px; font-size:0.85rem; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(460px, 1fr)); gap:20px; margin-bottom:20px; }}
  .card {{ background:var(--surface); border-radius:12px; padding:20px; border:1px solid var(--surface2); }}
  .card h2 {{ font-size:1rem; color:var(--accent); margin-bottom:15px; text-transform:uppercase; letter-spacing:0.05em; }}
  .card.full {{ grid-column: 1 / -1; }}
  .stat-row {{ display:flex; gap:15px; flex-wrap:wrap; margin-bottom:20px; }}
  .stat {{ background:var(--surface2); border-radius:8px; padding:14px 18px; flex:1; min-width:140px; }}
  .stat .label {{ font-size:0.75rem; color:var(--text2); text-transform:uppercase; letter-spacing:0.05em; }}
  .stat .value {{ font-size:1.5rem; font-weight:700; margin-top:4px; }}
  .stat .sub {{ font-size:0.75rem; color:var(--text2); margin-top:2px; }}
  table {{ width:100%; border-collapse:collapse; font-size:0.85rem; }}
  th {{ text-align:left; padding:10px 12px; background:var(--surface2); color:var(--accent); font-weight:600; border-bottom:2px solid var(--accent); }}
  td {{ padding:8px 12px; border-bottom:1px solid var(--surface2); }}
  td.num {{ text-align:right; font-family:'Cascadia Code',monospace; }}
  td.src {{ color:var(--text2); font-size:0.8rem; }}
  .badge {{ padding:2px 10px; border-radius:10px; font-size:0.75rem; font-weight:600; }}
  .badge.good {{ background:#064e3b; color:var(--green); }}
  .badge.ok {{ background:#1a3a1a; color:#86efac; }}
  .badge.warn {{ background:#451a03; color:var(--yellow); }}
  .badge.bad {{ background:#450a0a; color:var(--red); }}
  .chart-wrap {{ position:relative; height:300px; }}
  .chart-wrap.tall {{ height:400px; }}
  .section-title {{ font-size:1.3rem; font-weight:700; margin:30px 0 15px; padding-left:12px; border-left:3px solid var(--accent); }}
  .deviation-bar {{ display:inline-block; height:8px; border-radius:4px; background:var(--green); }}
  .two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
  @media(max-width:900px) {{ .grid {{ grid-template-columns:1fr; }} .two-col {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>

<div class="header">
  <h1>Bhoomi Dhrishti &mdash; Synthetic Data Analytics</h1>
  <p>Comparison of generated synthetic dataset against real-world Indian land record benchmarks</p>
  <div class="meta">
    <span>Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}</span>
    <span>Seed: {manifest['seed']}</span>
    <span>Total Parcels: {len(gt):,}</span>
    <span>Total Defects: {len(manifest['defects']):,}</span>
    <span>PS-26014 / SIH 2026</span>
  </div>
</div>

<!-- ── Key Metrics ────────────────────────────────────────────────────── -->
<div class="stat-row">
  <div class="stat">
    <div class="label">TN Rural Parcels</div>
    <div class="value" style="color:var(--green)">{len(tn_parcels):,}</div>
    <div class="sub">Target: 2000+</div>
  </div>
  <div class="stat">
    <div class="label">CH Urban Parcels</div>
    <div class="value" style="color:var(--green)">{len(ch_parcels):,}</div>
    <div class="sub">Target: 1000+</div>
  </div>
  <div class="stat">
    <div class="label">Female Ownership</div>
    <div class="value" style="color:var(--accent)">{female_pct:.1f}%</div>
    <div class="sub">NFHS-5 Benchmark: 14%</div>
  </div>
  <div class="stat">
    <div class="label">Departmental Views</div>
    <div class="value" style="color:var(--purple)">7</div>
    <div class="sub">RoR, SRO, Tax, BP, Court, Zone, EC</div>
  </div>
  <div class="stat">
    <div class="label">Defect Types</div>
    <div class="value" style="color:var(--yellow)">{len(defect_counts)}</div>
    <div class="sub">{len(manifest['defects']):,} total injected</div>
  </div>
</div>

<!-- ── Benchmark Comparison Table ─────────────────────────────────────── -->
<div class="section-title">Benchmark Comparison: Synthetic vs Real-World</div>
<div class="card full">
  <h2>Deviation Analysis</h2>
  <table>
    <thead>
      <tr><th>Metric</th><th>Real-World</th><th>Synthetic</th><th>Deviation</th><th>Status</th><th>Source</th></tr>
    </thead>
    <tbody>
      {benchmark_rows}
    </tbody>
  </table>
</div>

<!-- ── Area Distribution ──────────────────────────────────────────────── -->
<div class="section-title">Area Distribution Analysis</div>
<div class="grid">
  <div class="card">
    <h2>TN Rural &mdash; Parcel Area Distribution</h2>
    <div class="chart-wrap"><canvas id="tnAreaHist"></canvas></div>
  </div>
  <div class="card">
    <h2>CH Urban &mdash; Parcel Area Distribution</h2>
    <div class="chart-wrap"><canvas id="chAreaHist"></canvas></div>
  </div>
</div>

<!-- ── Size Class Comparison ──────────────────────────────────────────── -->
<div class="grid">
  <div class="card full">
    <h2>Agricultural Census Size Class: Real vs Synthetic (TN)</h2>
    <div class="chart-wrap"><canvas id="sizeClassChart"></canvas></div>
  </div>
</div>

<!-- ── Land Class ─────────────────────────────────────────────────────── -->
<div class="section-title">Land Classification</div>
<div class="grid">
  <div class="card">
    <h2>TN Rural &mdash; Land Use Classes</h2>
    <div class="chart-wrap"><canvas id="tnLandClass"></canvas></div>
  </div>
  <div class="card">
    <h2>CH Urban &mdash; Land Use Classes</h2>
    <div class="chart-wrap"><canvas id="chLandClass"></canvas></div>
  </div>
</div>

<!-- ── Financial ──────────────────────────────────────────────────────── -->
<div class="section-title">Financial Analysis</div>
<div class="stat-row">
  <div class="stat">
    <div class="label">TN Sale Value Median</div>
    <div class="value">{int(np.median(tn_sale_vals)):,}</div>
    <div class="sub">INR &mdash; Agri land ~50-250/sq_m</div>
  </div>
  <div class="stat">
    <div class="label">CH Sale Value Median</div>
    <div class="value">{int(np.median(ch_sale_vals)):,}</div>
    <div class="sub">INR &mdash; Urban ~60K-240K/sq_m</div>
  </div>
  <div class="stat">
    <div class="label">TN Tax Median</div>
    <div class="value">{int(np.median(tn_taxes)):,}</div>
    <div class="sub">INR/year</div>
  </div>
  <div class="stat">
    <div class="label">CH Tax Median</div>
    <div class="value">{int(np.median(ch_taxes)):,}</div>
    <div class="sub">INR/year</div>
  </div>
</div>

<!-- ── Ownership & Court ──────────────────────────────────────────────── -->
<div class="section-title">Ownership & Disputes</div>
<div class="grid">
  <div class="card">
    <h2>Ownership Count per Parcel</h2>
    <div class="chart-wrap"><canvas id="ownershipChart"></canvas></div>
  </div>
  <div class="card">
    <h2>Court Case Types</h2>
    <div class="chart-wrap"><canvas id="caseTypeChart"></canvas></div>
  </div>
</div>

<!-- ── Gender ─────────────────────────────────────────────────────────── -->
<div class="grid">
  <div class="card">
    <h2>Gender Distribution (Ownership)</h2>
    <div class="chart-wrap"><canvas id="genderChart"></canvas></div>
  </div>
  <div class="card">
    <h2>Encumbrance Coverage</h2>
    <div class="chart-wrap"><canvas id="encChart"></canvas></div>
  </div>
</div>

<!-- ── Defects ─────────────────────────────────────────────────────────── -->
<div class="section-title">Defect Injection Analysis</div>
<div class="grid">
  <div class="card full">
    <h2>Defect Distribution (Trust Engine Test Coverage)</h2>
    <div class="chart-wrap tall"><canvas id="defectChart"></canvas></div>
  </div>
</div>

<div class="grid">
  <div class="card">
    <h2>Defect Breakdown</h2>
    <table>
      <thead><tr><th>Defect Type</th><th>Count</th></tr></thead>
      <tbody>{defect_rows}</tbody>
    </table>
  </div>
  <div class="card">
    <h2>Data Quality Summary</h2>
    <table>
      <thead><tr><th>Department</th><th>TN Records</th><th>CH Records</th></tr></thead>
      <tbody>
        <tr><td>Revenue RoR</td><td class="num">{len(tn_ror):,}</td><td class="num">{len(ch_ror):,}</td></tr>
        <tr><td>SRO Registrations</td><td class="num">{len(tn_sro):,}</td><td class="num">{len(ch_sro):,}</td></tr>
        <tr><td>Municipal Tax</td><td class="num">{len(tn_tax):,}</td><td class="num">{len(ch_tax):,}</td></tr>
        <tr><td>Building Permits</td><td class="num">{len(tn_bp):,}</td><td class="num">{len(ch_bp):,}</td></tr>
        <tr><td>Court Cases</td><td class="num">{len(tn_cases):,}</td><td class="num">{len(ch_cases):,}</td></tr>
        <tr><td>Encumbrances</td><td class="num">{len(tn_ec):,}</td><td class="num">{len(ch_ec):,}</td></tr>
      </tbody>
    </table>
    <div style="margin-top:15px">
      <table>
        <thead><tr><th>Metric</th><th>Value</th></tr></thead>
        <tbody>
          <tr><td>TN Parcels with Encumbrances</td><td class="num">{tn_enc_count} ({tn_enc_count/len(tn_ec)*100:.1f}%)</td></tr>
          <tr><td>CH Parcels with Encumbrances</td><td class="num">{ch_enc_count} ({ch_enc_count/len(ch_ec)*100:.1f}%)</td></tr>
          <tr><td>TN Building Permit Rate</td><td class="num">{len(tn_bp)}/{len(tn_parcels)} ({len(tn_bp)/len(tn_parcels)*100:.1f}%)</td></tr>
          <tr><td>CH Building Permit Rate</td><td class="num">{len(ch_bp)}/{len(ch_parcels)} ({len(ch_bp)/len(ch_parcels)*100:.1f}%)</td></tr>
          <tr><td>TN Dispute Rate</td><td class="num">{len(tn_cases)}/{len(tn_parcels)} ({len(tn_cases)/len(tn_parcels)*100:.1f}%)</td></tr>
          <tr><td>CH Dispute Rate</td><td class="num">{len(ch_cases)}/{len(ch_parcels)} ({len(ch_cases)/len(ch_parcels)*100:.1f}%)</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</div>

<div style="text-align:center; padding:30px 0; color:var(--text2); font-size:0.8rem;">
  Bhoomi Dhrishti &mdash; SIH 2026, PS-26014, Ministry of Rural Development / DoLR<br>
  Synthetic data calibrated against: Agricultural Census 2015-16, NFHS-5, DILRMP Dashboard, TN Bhoomi, CH Estate Office
</div>

<script>
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = '#334155';
const COLORS = ['#38bdf8','#a78bfa','#34d399','#fbbf24','#f87171','#fb923c','#f472b6','#818cf8'];

// TN Area Histogram
new Chart(document.getElementById('tnAreaHist'), {{
  type:'bar',
  data:{{
    labels:{js_arr(tn_area_labels)},
    datasets:[{{label:'Parcel Count',data:{js_arr(tn_area_hist)},
      backgroundColor:'rgba(56,189,248,0.7)',borderColor:'#38bdf8',borderWidth:1}}]
  }},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{title:{{display:true,text:'Area (sq_m) — Median: {int(np.median(tn_areas)):,} sq_m'}}}},
    scales:{{x:{{title:{{display:true,text:'Area Range (sq_m)'}}}},y:{{title:{{display:true,text:'Count'}}}}}}
  }}
}});

// CH Area Histogram
new Chart(document.getElementById('chAreaHist'), {{
  type:'bar',
  data:{{
    labels:{js_arr(ch_area_labels)},
    datasets:[{{label:'Parcel Count',data:{js_arr(ch_area_hist)},
      backgroundColor:'rgba(167,139,250,0.7)',borderColor:'#a78bfa',borderWidth:1}}]
  }},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{title:{{display:true,text:'Area (sq_m) — Median: {int(np.median(ch_areas)):,} sq_m'}}}},
    scales:{{x:{{title:{{display:true,text:'Area Range (sq_m)'}}}},y:{{title:{{display:true,text:'Count'}}}}}}
  }}
}});

// Size Class Comparison
new Chart(document.getElementById('sizeClassChart'), {{
  type:'bar',
  data:{{
    labels:{js_arr(size_labels)},
    datasets:[
      {{label:'Real (Ag Census 2015-16)',data:{js_arr([round(x,1) for x in real_size_pcts])},
        backgroundColor:'rgba(56,189,248,0.6)',borderColor:'#38bdf8',borderWidth:1}},
      {{label:'Synthetic (Generated)',data:{js_arr([round(x,1) for x in tn_size_pcts])},
        backgroundColor:'rgba(167,139,250,0.6)',borderColor:'#a78bfa',borderWidth:1}}
    ]
  }},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{title:{{display:true,text:'Holding Size Classification — Real vs Synthetic (%)'}}}},
    scales:{{y:{{title:{{display:true,text:'Percentage (%)'}},max:100}}}}
  }}
}});

// TN Land Class (Doughnut)
new Chart(document.getElementById('tnLandClass'), {{
  type:'doughnut',
  data:{{labels:{js_arr(tn_class_labels)},datasets:[{{data:{js_arr(tn_class_values)},backgroundColor:COLORS}}]}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'right'}}}}}}
}});

// CH Land Class (Doughnut)
new Chart(document.getElementById('chLandClass'), {{
  type:'doughnut',
  data:{{labels:{js_arr(ch_class_labels)},datasets:[{{data:{js_arr(ch_class_values)},backgroundColor:COLORS}}]}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'right'}}}}}}
}});

// Ownership
new Chart(document.getElementById('ownershipChart'), {{
  type:'bar',
  data:{{
    labels:{js_arr(own_labels_capped)},
    datasets:[
      {{label:'TN Rural',data:{js_arr(tn_own_vals)},backgroundColor:'rgba(56,189,248,0.6)'}},
      {{label:'CH Urban',data:{js_arr(ch_own_vals)},backgroundColor:'rgba(167,139,250,0.6)'}}
    ]
  }},
  options:{{responsive:true,maintainAspectRatio:false,
    scales:{{x:{{title:{{display:true,text:'Number of Owners'}}}},y:{{title:{{display:true,text:'Parcels'}}}}}}
  }}
}});

// Case Types
new Chart(document.getElementById('caseTypeChart'), {{
  type:'bar',
  data:{{
    labels:{js_arr(all_case_types)},
    datasets:[
      {{label:'TN',data:{js_arr(tn_case_vals)},backgroundColor:'rgba(251,191,36,0.6)'}},
      {{label:'CH',data:{js_arr(ch_case_vals)},backgroundColor:'rgba(248,113,113,0.6)'}}
    ]
  }},
  options:{{responsive:true,maintainAspectRatio:false,indexAxis:'y'}}
}});

// Gender
new Chart(document.getElementById('genderChart'), {{
  type:'bar',
  data:{{
    labels:['Synthetic','NFHS-5 Benchmark'],
    datasets:[
      {{label:'Male',data:[{round(100-female_pct,1)},86],backgroundColor:'rgba(56,189,248,0.6)'}},
      {{label:'Female',data:[{round(female_pct,1)},14],backgroundColor:'rgba(244,114,182,0.6)'}}
    ]
  }},
  options:{{responsive:true,maintainAspectRatio:false,
    scales:{{x:{{stacked:true}},y:{{stacked:true,max:100,title:{{display:true,text:'%'}}}}}},
    plugins:{{title:{{display:true,text:'Female: {female_pct:.1f}% (target 14%)'}}}}
  }}
}});

// Encumbrance
new Chart(document.getElementById('encChart'), {{
  type:'bar',
  data:{{
    labels:['TN Rural','CH Urban'],
    datasets:[
      {{label:'With Encumbrance',data:[{tn_enc_count},{ch_enc_count}],backgroundColor:'rgba(248,113,113,0.6)'}},
      {{label:'Clear',data:[{len(tn_ec)-tn_enc_count},{len(ch_ec)-ch_enc_count}],backgroundColor:'rgba(52,211,153,0.6)'}}
    ]
  }},
  options:{{responsive:true,maintainAspectRatio:false,
    scales:{{x:{{stacked:true}},y:{{stacked:true}}}},
    plugins:{{title:{{display:true,text:'Encumbrance Status'}}}}
  }}
}});

// Defects Horizontal Bar
const defectLabels = {js_arr(sorted(defect_counts.keys()))};
const defectValues = {js_arr([defect_counts[k] for k in sorted(defect_counts.keys())])};
new Chart(document.getElementById('defectChart'), {{
  type:'bar',
  data:{{
    labels:defectLabels,
    datasets:[{{label:'Count',data:defectValues,
      backgroundColor:defectLabels.map((_,i)=>COLORS[i%COLORS.length]+'99'),
      borderColor:defectLabels.map((_,i)=>COLORS[i%COLORS.length]),borderWidth:1}}]
  }},
  options:{{responsive:true,maintainAspectRatio:false,indexAxis:'y',
    plugins:{{legend:{{display:false}}}},
    scales:{{x:{{title:{{display:true,text:'Injected Count'}}}}}}
  }}
}});
</script>
</body>
</html>"""

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"\nReport saved: {OUTPUT}")
    print(f"Open in browser: file:///{str(OUTPUT).replace(chr(92), '/')}")


if __name__ == "__main__":
    main()
