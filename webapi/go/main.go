package main
import (
  "encoding/json"
  "net/http"
)
func main() {
  http.HandleFunc("/json", func(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(map[string]any{"message": "Hello from Go", "value": 42})
  })
  http.ListenAndServe(":8080", nil)
}
