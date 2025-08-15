#!/bin/bash
set -euo pipefail
mkdir -p results/raw results/charts

echo ">>> Building images..."
docker build --target dotnet_jit -t webbench-dotnet-jit .
docker build --target dotnet_aot -t webbench-dotnet-aot .
docker build --target node -t webbench-node .
docker build --target go -t webbench-go .
docker build --target rust -t webbench-rust .
docker build --target loadgen -t webbench-loadgen .

docker network inspect webbench-net >/dev/null 2>&1 || docker network create webbench-net

start() {
  n=$1; img=$2
  docker rm -f "$n" >/dev/null 2>&1 || true
  docker run -d --name "$n" --network webbench-net "$img" >/dev/null
}
start dotnet-jit webbench-dotnet-jit
start dotnet-aot webbench-dotnet-aot
start node       webbench-node
start go         webbench-go
start rust       webbench-rust

echo "Waiting for servers..."; sleep 3

bench() {
  name=$1; url=$2; out=$3
  echo ">>> $name warmup"
  docker run --rm --network webbench-net webbench-loadgen -c 256 -d 5s -l "$url" >/dev/null || true
  echo ">>> $name benchmark"
  docker run --rm --network webbench-net webbench-loadgen -c 256 -d 15s -l -o json "$url" > "$out" || true
  echo "Saved $out"
}
bench dotnet-jit http://dotnet-jit:8080/json results/raw/dotnet-jit.json
bench dotnet-aot http://dotnet-aot:8080/json results/raw/dotnet-aot.json
bench node       http://node:8080/json       results/raw/node.json
bench go         http://go:8080/json         results/raw/go.json
bench rust       http://rust:8080/json       results/raw/rust.json

echo "Stopping servers..."
docker rm -f dotnet-jit dotnet-aot node go rust >/dev/null 2>&1 || true

python3 scripts/generate_webapi_charts.py

echo "Done. Charts in results/charts"
