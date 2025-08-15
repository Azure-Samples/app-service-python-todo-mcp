"""
Todo MCP Server with FastAPI - Azure Ready
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Any, Dict, Optional
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic Models
class Tool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]

class Resource(BaseModel):
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None

class Todo(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = ""
    completed: bool = False
    priority: str = "medium"
    created_at: Optional[str] = None

# Simple in-memory storage for todos
todos_storage: Dict[int, Todo] = {}
next_id = 1

def get_current_time() -> str:
    return datetime.now().isoformat()

# MCP Server Class
class MCPServer:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.resources: Dict[str, Resource] = {}
        self.initialize_tools()
        self.initialize_resources()
    
    def initialize_tools(self):
        """Initialize available MCP tools"""
        # Create todo tool
        create_todo_tool = Tool(
            name="create_todo",
            description="Create a new todo item",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the todo"
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Priority level"
                    }
                },
                "required": ["title"]
            }
        )
        self.tools["create_todo"] = create_todo_tool
        
        # List todos tool
        list_todos_tool = Tool(
            name="list_todos",
            description="Get all todo items",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter_completed": {
                        "type": "boolean",
                        "description": "Filter by completion status"
                    }
                }
            }
        )
        self.tools["list_todos"] = list_todos_tool
        
        # Update todo tool
        update_todo_tool = Tool(
            name="update_todo",
            description="Update an existing todo item",
            inputSchema={
                "type": "object",
                "properties": {
                    "todo_id": {
                        "type": "integer",
                        "description": "Todo ID to update"
                    },
                    "title": {
                        "type": "string",
                        "description": "New title"
                    },
                    "description": {
                        "type": "string",
                        "description": "New description"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Priority level"
                    },
                    "completed": {
                        "type": "boolean",
                        "description": "Completion status"
                    }
                },
                "required": ["todo_id"]
            }
        )
        self.tools["update_todo"] = update_todo_tool
        
        # Delete todo tool
        delete_todo_tool = Tool(
            name="delete_todo",
            description="Delete a todo item",
            inputSchema={
                "type": "object",
                "properties": {
                    "todo_id": {
                        "type": "integer",
                        "description": "Todo ID to delete"
                    }
                },
                "required": ["todo_id"]
            }
        )
        self.tools["delete_todo"] = delete_todo_tool
        
        # Mark complete tool
        mark_complete_tool = Tool(
            name="mark_todo_complete",
            description="Mark a todo as complete",
            inputSchema={
                "type": "object",
                "properties": {
                    "todo_id": {
                        "type": "integer",
                        "description": "Todo ID to mark"
                    },
                    "completed": {
                        "type": "boolean",
                        "description": "Completion status",
                        "default": True
                    }
                },
                "required": ["todo_id"]
            }
        )
        self.tools["mark_todo_complete"] = mark_complete_tool
    
    def initialize_resources(self):
        """Initialize available resources"""
        # Sample resource
        sample_resource = Resource(
            uri="mcp://server/todos",
            name="Todo List",
            description="Current todo list data",
            mimeType="application/json"
        )
        self.resources["todos"] = sample_resource
    
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "listChanged": True
                },
                "resources": {
                    "subscribe": True,
                    "listChanged": True
                }
            },
            "serverInfo": {
                "name": "Todo MCP Server",
                "version": "1.0.0"
            }
        }
    
    async def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request"""
        tools_list = [tool.dict() for tool in self.tools.values()]
        return {"tools": tools_list}
    
    async def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request"""
        global next_id
        
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            raise HTTPException(status_code=400, detail=f"Tool '{tool_name}' not found")
        
        if tool_name == "create_todo":
            title = arguments.get("title")
            if not title:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": "Error: Title is required"
                        }
                    ]
                }
            
            todo = Todo(
                id=next_id,
                title=title,
                description=arguments.get("description", ""),
                priority=arguments.get("priority", "medium"),
                created_at=get_current_time()
            )
            todos_storage[next_id] = todo
            next_id += 1
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Created todo: {todo.dict()}"
                    }
                ]
            }
            
        elif tool_name == "list_todos":
            filter_completed = arguments.get("filter_completed")
            todos = list(todos_storage.values())
            
            if filter_completed is not None:
                todos = [todo for todo in todos if todo.completed == filter_completed]
            
            todos_data = [todo.dict() for todo in todos]
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Found {len(todos_data)} todos: {todos_data}"
                    }
                ]
            }
            
        elif tool_name == "update_todo":
            todo_id = arguments.get("todo_id")
            if todo_id not in todos_storage:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Todo with ID {todo_id} not found"
                        }
                    ]
                }
            
            todo = todos_storage[todo_id]
            if "title" in arguments:
                todo.title = arguments["title"]
            if "description" in arguments:
                todo.description = arguments["description"]
            if "priority" in arguments:
                todo.priority = arguments["priority"]
            if "completed" in arguments:
                todo.completed = arguments["completed"]
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Updated todo: {todo.dict()}"
                    }
                ]
            }
            
        elif tool_name == "delete_todo":
            todo_id = arguments.get("todo_id")
            if todo_id not in todos_storage:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Todo with ID {todo_id} not found"
                        }
                    ]
                }
            
            deleted_todo = todos_storage.pop(todo_id)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Deleted todo: {deleted_todo.dict()}"
                    }
                ]
            }
            
        elif tool_name == "mark_todo_complete":
            todo_id = arguments.get("todo_id")
            if todo_id not in todos_storage:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Todo with ID {todo_id} not found"
                        }
                    ]
                }
            
            todo = todos_storage[todo_id]
            todo.completed = arguments.get("completed", True)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Updated todo completion: {todo.dict()}"
                    }
                ]
            }
        
        return {"content": [{"type": "text", "text": "Tool executed successfully"}]}
    
    async def handle_resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list request"""
        resources_list = [resource.dict() for resource in self.resources.values()]
        return {"resources": resources_list}
    
    async def handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request"""
        uri = params.get("uri")
        
        if uri == "mcp://server/todos":
            todos_data = [todo.dict() for todo in todos_storage.values()]
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": str(todos_data)
                    }
                ]
            }
        
        raise HTTPException(status_code=404, detail=f"Resource '{uri}' not found")

# Initialize MCP server
mcp_server = MCPServer()

# Template configuration
templates = Jinja2Templates(directory="templates")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Todo MCP FastAPI Server")
    yield
    logger.info("Shutting down Todo MCP FastAPI Server")

# Create FastAPI app
app = FastAPI(
    title="Todo MCP Server",
    description="Model Context Protocol server for todo management",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main todo list page"""
    # Determine if running locally or in Azure App Service
    host = request.headers.get("host", "localhost:8000")
    
    # Check if running in Azure App Service
    if "azurewebsites.net" in host:
        mcp_server_url = f"https://{host}/mcp/stream"
    else:
        mcp_server_url = f"http://{host}/mcp/stream"
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "mcp_server_url": mcp_server_url
    })

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "todos_count": len(todos_storage)}

@app.get("/tools")
async def list_tools():
    """REST endpoint to list available tools"""
    return {"tools": [tool.dict() for tool in mcp_server.tools.values()]}

@app.get("/resources")
async def list_resources():
    """REST endpoint to list available resources"""
    return {"resources": [resource.dict() for resource in mcp_server.resources.values()]}

# REST API endpoints for direct usage
@app.get("/api/todos")
async def get_todos(completed: Optional[bool] = None):
    """Get all todos with optional completion filter"""
    todos = list(todos_storage.values())
    
    if completed is not None:
        todos = [todo for todo in todos if todo.completed == completed]
    
    return [todo.dict() for todo in todos]

@app.post("/api/todos")
async def create_todo_api(todo_data: dict):
    """Create a new todo via REST API"""
    global next_id
    try:
        title = todo_data.get("title", "").strip()
        if not title:
            raise HTTPException(status_code=400, detail="Title is required")
        
        description = todo_data.get("description", "")
        priority = todo_data.get("priority", "medium")
        
        if priority not in ["low", "medium", "high"]:
            priority = "medium"
        
        todo = Todo(
            id=next_id,
            title=title,
            description=description,
            priority=priority,
            completed=False,
            created_at=get_current_time()
        )
        
        todos_storage[todo.id] = todo
        next_id += 1
        
        return todo.dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/todos/{todo_id}")
async def update_todo_api(todo_id: int, todo_data: dict):
    """Update a todo via REST API"""
    if todo_id not in todos_storage:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    todo = todos_storage[todo_id]
    
    if "title" in todo_data:
        title = todo_data["title"].strip()
        if not title:
            raise HTTPException(status_code=400, detail="Title is required")
        todo.title = title
    
    if "description" in todo_data:
        todo.description = todo_data["description"]
    
    if "priority" in todo_data:
        priority = todo_data["priority"]
        if priority in ["low", "medium", "high"]:
            todo.priority = priority
    
    if "completed" in todo_data:
        todo.completed = bool(todo_data["completed"])
    
    return todo.dict()

@app.patch("/api/todos/{todo_id}/complete")
async def toggle_todo_complete(todo_id: int, completion_data: dict):
    """Toggle todo completion status"""
    if todo_id not in todos_storage:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    todo = todos_storage[todo_id]
    todo.completed = bool(completion_data.get("completed", not todo.completed))
    
    return todo.dict()

@app.delete("/api/todos/{todo_id}")
async def delete_todo_api(todo_id: int):
    """Delete a todo via REST API"""
    if todo_id not in todos_storage:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    deleted_todo = todos_storage.pop(todo_id)
    return {"message": "Todo deleted successfully", "deleted_todo": deleted_todo.dict()}

# MCP Streamable HTTP Endpoints
@app.get("/mcp/stream")
async def mcp_stream_info():
    """Information about the MCP stream endpoint"""
    return {
        "info": "MCP Streamable HTTP Transport Endpoint",
        "description": "This endpoint accepts POST requests with JSON-RPC 2.0 messages for MCP communication",
        "usage": "Use MCP Inspector or send POST requests with proper JSON-RPC payloads",
        "methods": ["POST"],
        "example_request": {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
    }

@app.post("/mcp/stream")
async def mcp_stream_endpoint(request: Request):
    """Main MCP endpoint with streamable HTTP support"""
    try:
        message = await request.json()
        logger.info(f"Received MCP message: {message}")
        
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")
        
        if method == "initialize":
            result = await mcp_server.handle_initialize(params)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
        elif method == "tools/list":
            result = await mcp_server.handle_tools_list(params)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
        elif method == "tools/call":
            result = await mcp_server.handle_tools_call(params)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
        elif method == "resources/list":
            result = await mcp_server.handle_resources_list(params)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
        elif method == "resources/read":
            result = await mcp_server.handle_resources_read(params)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found"
                }
            }
        
    except Exception as e:
        logger.error(f"MCP stream error: {e}")
        return {
            "jsonrpc": "2.0",
            "id": message.get("id") if 'message' in locals() else None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }

@app.get("/mcp/capabilities")
async def mcp_capabilities():
    """Return MCP server capabilities"""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {"listChanged": True},
            "resources": {"subscribe": True, "listChanged": True}
        },
        "serverInfo": {
            "name": "Todo MCP Server",
            "version": "1.0.0"
        }
    }

@app.options("/mcp/stream")
async def mcp_stream_options():
    """Handle CORS preflight for MCP stream endpoint"""
    return {
        "status": "ok",
        "methods": ["POST", "OPTIONS"],
        "headers": ["Content-Type", "Accept"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
