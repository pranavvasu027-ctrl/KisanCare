/**
 * KisanCare Development API Bridge
 * Bypasses Windows Defender Firewall inbound blocks on python.exe by proxying
 * mobile HTTP traffic through the permitted Node.js JavaScript runtime.
 */
import http from 'http';

const TARGET_PORT = parseInt(process.env.BACKEND_PORT || '8002', 10);
const PROXY_PORT = parseInt(process.env.PROXY_PORT || '8000', 10);
const HOST = '0.0.0.0';

const server = http.createServer((req, res) => {
  // Add CORS headers for mobile clients
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', '*');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  const options = {
    hostname: '127.0.0.1',
    port: TARGET_PORT,
    path: req.url,
    method: req.method,
    headers: {
      ...req.headers,
      host: `127.0.0.1:${TARGET_PORT}`,
    },
  };

  const proxyReq = http.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res, { end: true });
  });

  proxyReq.on('error', (err) => {
    console.error(`[Bridge Error] ${req.method} ${req.url} ->`, err.message);
    if (!res.headersSent) {
      res.writeHead(502, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ detail: `Backend bridge error: ${err.message}` }));
    }
  });

  req.pipe(proxyReq, { end: true });
});

server.listen(PROXY_PORT, HOST, () => {
  console.log(`[KisanCare Bridge] Listening on ${HOST}:${PROXY_PORT} -> forwarding to 127.0.0.1:${TARGET_PORT}`);
});
