# Python Todo List App with MCP Integration

A FastAPI-based todo list application that exposes operations as MCP (Model Context Protocol) tools over HTTP and can be deployed to Azure App Service.

## Features

- ✅ **CRUD Operations**: Create, read, update, delete todos
- 🎯 **Priority Management**: Set priority levels (low, medium, high)
- ✅ **Mark Complete/Incomplete**: Toggle completion status
- 🌐 **Web Interface**: Clean, responsive UI with copy-to-clipboard functionality
- 🔧 **MCP Tools**: HTTP-accessible tools for external integrations
- 📋 **MCP URL Display**: Dynamic MCP server URL with one-click copy functionality
- ☁️ **Azure Ready**: Optimized for Azure App Service deployment

## MCP Tools Available

The application exposes the following MCP tools over HTTP:

- `create_todo(title, description, priority)` - Create a new todo item
- `list_todos(filter_completed)` - Get all todos with optional filtering
- `update_todo(id, title, description, priority, completed)` - Update existing todo
- `delete_todo(id)` - Delete a todo item
- `mark_todo_complete(id, completed)` - Mark todo as complete/incomplete

## Local Development

### Prerequisites

- Python 3.11+
- Virtual environment (venv)

### Setup

1. **Clone and setup environment**:
   ```bash
   git clone https://github.com/Azure-Samples/app-service-python-todo-mcp
   cd app-service-python-todo-mcp
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

4. **Access the application**:
   - Web Interface: http://localhost:8000
   - Health Check: http://localhost:8000/health
   - MCP Endpoint: http://localhost:8000/mcp/stream
   - MCP Tools: http://localhost:8000/mcp/tools/*

## Azure Deployment

### Prerequisites

- Azure CLI installed and logged in
- Azure Developer CLI (azd) installed

### Deploy with AZD

1. **Initialize AZD**:
   ```bash
   azd init
   ```

2. **Deploy to Azure**:
   ```bash
   azd up
   ```

### Infrastructure

The deployment creates:

- **App Service Plan**: P0V3 (Premium V3, Linux)
- **App Service**: Python 3.11 runtime with Uvicorn ASGI server

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Browser   │────│   FastAPI App    │────│   SQLite DB     │
│   (Todo UI)     │    │   (CRUD API)     │    │   (Data Store)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌──────────────────┐
                       │   MCP Server     │
                       │   (HTTP Stream)  │
                       └──────────────────┘
                                │
                       ┌──────────────────┐
                       │  External Tools  │
                       │  & Integrations  │
                       └──────────────────┘
```

## API Endpoints

### REST API
- `GET /api/todos` - List all todos
- `POST /api/todos` - Create new todo
- `GET /api/todos/{id}` - Get specific todo
- `PUT /api/todos/{id}` - Update todo
- `DELETE /api/todos/{id}` - Delete todo
- `PATCH /api/todos/{id}/complete` - Toggle completion

### MCP Integration
- `GET /mcp/stream` - MCP server endpoint (HTTP streaming)
- `POST /mcp/stream` - MCP protocol endpoint (JSON-RPC 2.0)
- `GET/POST /mcp/tools/create_todo` - Direct tool access
- `GET/POST /mcp/tools/list_todos` - Direct tool access
- `POST /mcp/tools/update_todo` - Direct tool access
- `POST /mcp/tools/delete_todo` - Direct tool access
- `POST /mcp/tools/mark_todo_complete` - Direct tool access

## MCP Configuration

The application automatically displays the MCP server URL in the web interface with environment-aware detection:

- **Local Development**: `http://localhost:8000/mcp/stream`
- **Azure App Service**: `https://your-app-name.azurewebsites.net/mcp/stream`

### VS Code MCP Integration

To use this app as an MCP server in VS Code, add the following to your `.vscode/mcp.json`:

```json
{
  "servers": {
    "todo-mcp-server": {
      "url": "http://localhost:8000/mcp/stream",
      "type": "http"
    }
  },
  "inputs": []
}
```

For the deployed Azure version, replace the URL with your App Service URL.

## License

This project is licensed under the MIT License.
