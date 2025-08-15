# Language Benchmarks (Dockerized)


---

## Web API Benchmark (throughput & latency)

Spins up minimal HTTP servers (.NET JIT, .NET AOT, Node, Go, Rust) and uses **bombardier** for load.

### Run
```bash
chmod +x scripts/run_webapi.sh
./scripts/run_webapi.sh
```

### Output
- Raw JSON: `results/raw/*.json`
- Charts: `results/charts/webapi_rps.png`, `webapi_latency_mean.png`, `webapi_latency_p99.png`
