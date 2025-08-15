import json, glob, os
import matplotlib.pyplot as plt

RAW = "results/raw"
OUT = "results/charts"
os.makedirs(OUT, exist_ok=True)

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

# RPS
import matplotlib.pyplot as plt
plt.figure()
plt.bar(labels, rpss)
plt.ylabel("Requests/sec (higher is better)")
plt.title("Web API Throughput")
plt.savefig(os.path.join(OUT, "webapi_rps.png"), bbox_inches="tight")

# Mean Latency
plt.figure()
plt.bar(labels, means)
plt.ylabel("Mean latency (ms, lower is better)")
plt.title("Web API Latency - Mean")
plt.savefig(os.path.join(OUT, "webapi_latency_mean.png"), bbox_inches="tight")

# p99 Latency
plt.figure()
plt.bar(labels, p99s)
plt.ylabel("p99 latency (ms, lower is better)")
plt.title("Web API Latency - p99")
plt.savefig(os.path.join(OUT, "webapi_latency_p99.png"), bbox_inches="tight")

print("Charts saved in", OUT)
