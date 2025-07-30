from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "message": "Hello from LumiLens API!",
            "status": "working",
            "timestamp": "2025-07-30"
        }
        
        self.wfile.write(json.dumps(response).encode())
        return
