use axum::{routing::get, Json, Router};
use serde::Serialize;
use std::net::SocketAddr;
#[derive(Serialize)]
struct Msg { message: &'static str, value: i32 }
async fn json_handler() -> Json<Msg> {
  Json(Msg { message: "Hello from Rust (axum)", value: 42 })
}
#[tokio::main]
async fn main() {
  let app = Router::new().route("/json", get(json_handler));
  let addr = SocketAddr::from(([0, 0, 0, 0], 8080));
  axum::serve(tokio::net::TcpListener::bind(addr).await.unwrap(), app).await.unwrap();
}
