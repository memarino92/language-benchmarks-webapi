import json, glob, os
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter

RAW = "results/raw"
OUT = "results/charts"
os.makedirs(OUT, exist_ok=True)

# Set a modern, readable style
sns.set_theme(style="whitegrid", context="talk")

# Fixed colors per runtime for recognizability
PALETTE = {
  "dotnet-aot": "#512BD4",  # .NET brand purple
  "dotnet-jit": "#8A2BE2",  # violet variant to differ from AOT
  "go": "#00ADD8",          # Go cyan
  "node": "#3C873A",        # Node green
  "rust": "#DEA584",        # Rust orange
}

def bar_colors(keys):
  cyc = sns.color_palette("tab10")
  return [PALETTE.get(k, cyc[i % len(cyc)]) for i, k in enumerate(keys)]

def annotate_bars(ax, bars, fmt=lambda v: f"{v:.0f}"):
  for b in bars:
    h = b.get_height()
    ax.annotate(fmt(h), (b.get_x()+b.get_width()/2, h),
                xytext=(0, 4), textcoords="offset points",
                ha="center", va="bottom", fontsize=9)

def pluck_metrics(data):
  # Try common bombardier JSON fields; fallback to searching.
  rps = None
  mean = None
  p99 = None
  # Known structure (newer bombardier):
  # { "result": { "rps": { "mean": 123.4 }, "latency": { "mean": 1.2, "p99": 3.4 } } }
  try:
    r = data.get("result", {})
    rps = r.get("rps", {}).get("mean", rps)
    lat = r.get("latency", {})
    mean = lat.get("mean", mean)
    # p99 can be directly on latency or inside latency.percentiles["99"]
    if isinstance(lat.get("p99", None), (int, float)):
      p99 = float(lat["p99"])
    else:
      pcts = lat.get("percentiles", {})
      # keys in JSON are strings, but be defensive
      if isinstance(pcts.get("99", None), (int, float)):
        p99 = float(pcts["99"])
      elif isinstance(pcts.get(99, None), (int, float)):
        p99 = float(pcts[99])
  except Exception:
    pass
  # Fallback recursive search
  def walk(o, path=""):
    nonlocal rps, mean, p99
    if isinstance(o, dict):
      for k, v in o.items():
        lk = k.lower()
        new_path = f"{path}.{lk}" if path else lk
        if rps is None and "rps" in lk and isinstance(v, (int, float)):
          rps = float(v)
        if isinstance(v, (int, float)):
          # mean if key mentions mean/avg and appears under a latency-like path
          if mean is None and ("mean" in lk or "avg" in lk) and ("lat" in new_path):
            mean = float(v)
          # p99 if key is p99 or 99 and path mentions latency or percentiles
          if p99 is None and (("p99" in lk) or lk in ("99",)) and ("lat" in new_path or "percentile" in new_path):
            p99 = float(v)
        else:
          walk(v, new_path)
    elif isinstance(o, list):
      for item in o:
        walk(item, path)
  walk(data)
  return rps or 0.0, mean or 0.0, p99 or 0.0

labels, rpss, means, p99s = [], [], [], []
for fp in sorted(glob.glob(os.path.join(RAW, "*.json"))):
  with open(fp, "r", encoding="utf-8") as f:
    data = json.load(f)
  rps, mean, p99 = pluck_metrics(data)
  labels.append(os.path.splitext(os.path.basename(fp))[0])
  rpss.append(rps)
  means.append(mean)
  p99s.append(p99)

def make_bar(lbls, values, ylabel, title, outname, yfmt=None):
  fig, ax = plt.subplots(figsize=(9, 4.8))
  colors = bar_colors(lbls)
  bars = ax.bar(lbls, values, color=colors, edgecolor="black", linewidth=0.5)
  ax.set_ylabel(ylabel)
  ax.set_title(title)
  ax.grid(axis="y", linestyle="--", alpha=0.35)
  if yfmt:
    ax.yaxis.set_major_formatter(FuncFormatter(yfmt))
    annotate_bars(ax, bars, fmt=lambda v: yfmt(v, 0))
  else:
    annotate_bars(ax, bars)
  fig.tight_layout()
  fig.savefig(os.path.join(OUT, outname), bbox_inches="tight")
  plt.close(fig)

# Nicely formatted numbers
def fmt_int(x, _):
  try:
    return f"{int(round(x)):,}"
  except Exception:
    return f"{x}"

# RPS (descending)
pairs = sorted(zip(labels, rpss), key=lambda x: x[1], reverse=True)
lbls, vals = [p[0] for p in pairs], [p[1] for p in pairs]
make_bar(lbls, vals, "Requests/sec (higher is better)", "Web API Throughput", "webapi_rps.png", yfmt=fmt_int)


# Mean Latency (ms, ascending)
pairs = sorted(zip(labels, means), key=lambda x: x[1])
lbls, vals = [p[0] for p in pairs], [p[1] for p in pairs]
make_bar(lbls, vals, "Mean latency (ms, lower is better)", "Web API Latency - Mean", "webapi_latency_mean.png", yfmt=fmt_int)

# p99 Latency (ms, ascending)
pairs = sorted(zip(labels, p99s), key=lambda x: x[1])
lbls, vals = [p[0] for p in pairs], [p[1] for p in pairs]
make_bar(lbls, vals, "p99 latency (ms, lower is better)", "Web API Latency - p99", "webapi_latency_p99.png", yfmt=fmt_int)

print("Charts saved in", OUT)
