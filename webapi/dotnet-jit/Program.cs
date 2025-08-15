using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.Hosting;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();
app.MapGet("/json", () => Results.Json(new { message = "Hello from .NET JIT", value = 42 }));
app.Run();
