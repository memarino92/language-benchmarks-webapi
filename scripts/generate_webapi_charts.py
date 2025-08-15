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
    mean = r.get("latency", {}).get("mean", mean)
    p99 = r.get("latency", {}).get("p99", p99)
  except Exception:
    pass
  # Fallback recursive search
  def walk(o):
    nonlocal rps, mean, p99
    if isinstance(o, dict):
      for k, v in o.items():
        lk = k.lower()
        if rps is None and "rps" in lk and isinstance(v, (int, float)):
          rps = float(v)
        if isinstance(v, (int, float)):
          if mean is None and ("mean" in lk or "avg" in lk) and "lat" in lk:
            mean = float(v)
          if p99 is None and ("p99" in lk or "99" == lk) and "lat" in lk:
            p99 = float(v)
        else:
          walk(v)
    elif isinstance(o, list):
      for item in o:
        walk(item)
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
