const http = require('http');
const server = http.createServer((req, res) => {
  if (req.url === '/json') {
    const payload = JSON.stringify({ message: 'Hello from Node', value: 42 });
    res.statusCode = 200;
    res.setHeader('Content-Type', 'application/json');
    res.end(payload);
  } else {
    res.statusCode = 404;
    res.end('Not found');
  }
});
server.listen(8080, '0.0.0.0');
