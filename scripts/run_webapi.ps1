# filepath: scripts/run_webapi.ps1
# PowerShell version of run_webapi.sh

$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path 'results/raw' | Out-Null
New-Item -ItemType Directory -Force -Path 'results/charts' | Out-Null

Write-Host '>>> Building images...'
docker build --target dotnet_jit -t webbench-dotnet-jit .
docker build --target dotnet_aot -t webbench-dotnet-aot .
docker build --target node -t webbench-node .
docker build --target go -t webbench-go .
docker build --target rust -t webbench-rust .
docker build --target loadgen -t webbench-loadgen .

if (-not (docker network ls --format '{{.Name}}' | Select-String -SimpleMatch 'webbench-net')) {
    docker network create webbench-net | Out-Null
}

function Start-Container($name, $image) {
    docker rm -f $name 2>$null | Out-Null
    docker run -d --name $name --network webbench-net $image | Out-Null
}

Start-Container 'dotnet-jit' 'webbench-dotnet-jit'
Start-Container 'dotnet-aot' 'webbench-dotnet-aot'
Start-Container 'node'       'webbench-node'
Start-Container 'go'         'webbench-go'
Start-Container 'rust'       'webbench-rust'

Write-Host 'Waiting for servers...'
Start-Sleep -Seconds 3

function Bench($name, $url, $out) {
    Write-Host ">>> $name warmup"
    try {
        docker run --rm --network webbench-net webbench-loadgen -c 256 -d 5s -l $url | Out-Null
    }
    catch {}
    Write-Host ">>> $name benchmark"
    try {
        docker run --rm --network webbench-net webbench-loadgen -c 256 -d 15s -l -o json $url | Select-Object -Last 1 | Out-File -Encoding utf8 $out
    }
    catch {}
    Write-Host "Saved $out"
}

Bench 'dotnet-jit' 'http://dotnet-jit:8080/json' 'results/raw/dotnet-jit.json'
Bench 'dotnet-aot' 'http://dotnet-aot:8080/json' 'results/raw/dotnet-aot.json'
Bench 'node'       'http://node:8080/json'       'results/raw/node.json'
Bench 'go'         'http://go:8080/json'         'results/raw/go.json'
Bench 'rust'       'http://rust:8080/json'       'results/raw/rust.json'

Write-Host 'Stopping servers...'
docker rm -f dotnet-jit dotnet-aot node go rust 2>$null | Out-Null

Write-Host 'Generating charts in Docker...'
docker build --target charts -t webbench-charts .
docker run --rm -v ${PWD}/results:/charts/results webbench-charts

Write-Host 'Done. Charts in results/charts'
