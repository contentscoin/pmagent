from http.server import BaseHTTPRequestHandler
import json
from pmagent.server import TOOL_FUNCTIONS, TOOLS

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "jsonrpc": "2.0",
            "name": "PMAgent MCP Server",
            "version": "0.1.0",
            "description": "프로젝트 관리를 위한 MCP(Model Context Protocol) 서버",
            "tools": TOOLS
        }
        
        self.wfile.write(json.dumps(response).encode())
        
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        request_body = self.rfile.read(content_length)
        
        try:
            data = json.loads(request_body)
            
            if data.get("method") == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "result": {
                        "name": "PMAgent MCP Server",
                        "version": "0.1.0",
                        "tools": TOOLS
                    }
                }
            elif data.get("method") == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "result": {"tools": TOOLS}
                }
            elif data.get("method") == "tools/invoke":
                params = data.get("params", {})
                tool_name = params.get("name")
                tool_params = params.get("parameters", {})
                
                if tool_name in TOOL_FUNCTIONS:
                    try:
                        result = TOOL_FUNCTIONS[tool_name](tool_params)
                        response = {
                            "jsonrpc": "2.0",
                            "id": data.get("id"),
                            "result": result
                        }
                    except Exception as e:
                        response = {
                            "jsonrpc": "2.0",
                            "id": data.get("id"),
                            "error": {"message": str(e)}
                        }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": data.get("id"),
                        "error": {"message": f"Method not found: {tool_name}"}
                    }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "error": {"message": "Method not found"}
                }
        except Exception as e:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"message": f"Error: {str(e)}"}
            }
            
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        self.wfile.write(json.dumps(response).encode()) 