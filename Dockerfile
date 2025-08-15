# .NET JIT
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS dotnet_jit_build
WORKDIR /src
COPY webapi/dotnet-jit/ ./
RUN dotnet publish -c Release -o /out
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS dotnet_jit
ENV ASPNETCORE_URLS=http://0.0.0.0:8080
WORKDIR /app
COPY --from=dotnet_jit_build /out ./
EXPOSE 8080
ENTRYPOINT ["dotnet", "dotnet-jit.dll"]

# .NET AOT
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS dotnet_aot_build
WORKDIR /src
COPY webapi/dotnet-aot/ ./
RUN apt-get update && apt-get install -y clang zlib1g-dev \
    && dotnet publish -c Release -o /out
FROM debian:bookworm-slim AS dotnet_aot
WORKDIR /app
COPY --from=dotnet_aot_build /out ./
EXPOSE 8080
ENTRYPOINT ["./dotnet-aot"]

# Node
FROM node:20 AS node
WORKDIR /app
COPY webapi/node/ ./
EXPOSE 8080
ENTRYPOINT ["node", "server.js"]

# Go
FROM golang:1.22 AS go_build
WORKDIR /src
COPY webapi/go/ ./
RUN go build -o /out/server
FROM debian:bookworm-slim AS go
WORKDIR /app
COPY --from=go_build /out/server ./server
EXPOSE 8080
ENTRYPOINT ["./server"]

# Rust
FROM rust:1.80 AS rust_build
WORKDIR /src
COPY webapi/rust/ ./
RUN cargo build --release
FROM debian:bookworm-slim AS rust
WORKDIR /app
COPY --from=rust_build /src/target/release/webapibench ./webapibench
EXPOSE 8080
ENTRYPOINT ["./webapibench"]

# Load generator (bombardier)
FROM alpine/bombardier:latest AS loadgen

# Chart generator
FROM python:3.11-slim AS charts
WORKDIR /charts
COPY results/raw ./results/raw
COPY scripts/generate_webapi_charts.py ./scripts/generate_webapi_charts.py
RUN pip install matplotlib seaborn
ENTRYPOINT ["python3", "./scripts/generate_webapi_charts.py"]
