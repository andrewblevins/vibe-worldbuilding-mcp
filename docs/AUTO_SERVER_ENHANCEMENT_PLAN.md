# Auto-Server Enhancement Plan for Vibe WorldBuilding MCP

## Overview

This document outlines a plan to enhance the vibe-worldbuilding MCP server to automatically start and manage development/preview servers, eliminating the need for manual terminal commands and providing a seamless user experience.

## Current State

The MCP server currently provides three modes:
- `build` - Generates static files
- `dev` - Prepares development environment but requires manual `npm run dev`
- `preview` - Points to static files but requires manual HTTP server setup

**User Pain Point**: Users must manually start servers in separate terminals, breaking the flow of the worldbuilding experience.

## Proposed Enhancement

### New Tool Parameters

Add optional parameters to `build_static_site`:
```python
{
    "action": "dev|preview|build",
    "auto_serve": true,          # Automatically start server
    "auto_open": true,           # Open browser automatically
    "port": 4321,               # Specify port (with auto-fallback)
    "background": true          # Run server in background
}
```

### Implementation Options

#### Option 1: Enhanced Dev Mode (Recommended)
**Approach**: Spawn and manage the Astro dev server process directly

**Implementation**:
```python
import subprocess
import threading
import webbrowser
import time
from pathlib import Path

class DevServerManager:
    def __init__(self):
        self.processes = {}
    
    def start_dev_server(self, world_directory, port=4321, auto_open=True):
        # 1. Setup symlink (existing logic)
        self.setup_dev_environment(world_directory)
        
        # 2. Start Astro dev server in background
        process = subprocess.Popen(
            ["npm", "run", "dev", "--", "--port", str(port)],
            cwd=self.mcp_server_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 3. Wait for server to be ready
        self.wait_for_server(f"http://localhost:{port}")
        
        # 4. Store process for cleanup
        self.processes[world_directory] = process
        
        # 5. Auto-open browser
        if auto_open:
            webbrowser.open(f"http://localhost:{port}")
        
        return {
            "status": "success",
            "url": f"http://localhost:{port}",
            "pid": process.pid,
            "message": "Development server started! Browser should open automatically."
        }
```

#### Option 2: Built-in Python Server
**Approach**: Implement a lightweight Python HTTP server with live reload

**Benefits**:
- No external dependencies
- Full control over server behavior
- Can implement custom live-reload logic

**Implementation**:
```python
import http.server
import socketserver
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class LiveReloadServer:
    def start_server(self, site_directory, port=8000):
        # Start HTTP server in thread
        server_thread = threading.Thread(
            target=self.run_http_server,
            args=(site_directory, port)
        )
        server_thread.daemon = True
        server_thread.start()
        
        # Start file watcher for live reload
        self.setup_file_watcher(site_directory)
        
        return f"http://localhost:{port}"
```

#### Option 3: Hybrid Approach
**Approach**: Use built-in server for `preview` mode, enhanced process management for `dev` mode

### Process Management Strategy

#### Server Lifecycle Management
```python
class ServerRegistry:
    def __init__(self):
        self.active_servers = {}
    
    def register_server(self, world_id, process, port):
        self.active_servers[world_id] = {
            'process': process,
            'port': port,
            'started_at': time.time()
        }
    
    def cleanup_server(self, world_id):
        if world_id in self.active_servers:
            process = self.active_servers[world_id]['process']
            process.terminate()
            del self.active_servers[world_id]
    
    def cleanup_all(self):
        for world_id in list(self.active_servers.keys()):
            self.cleanup_server(world_id)
```

#### Auto-cleanup Strategies
1. **Session-based**: Clean up when MCP session ends
2. **Timeout-based**: Auto-stop servers after inactivity
3. **Manual**: Provide explicit `stop_server` tool
4. **Port-monitoring**: Detect if user manually stops server

### Enhanced User Experience

#### New Tool: `serve_world`
```python
def serve_world(world_directory, mode="dev", auto_open=True, port=None):
    """
    One-click serve with intelligent defaults
    """
    if mode == "dev":
        return self.start_dev_server(world_directory, port, auto_open)
    elif mode == "preview":
        return self.start_preview_server(world_directory, port, auto_open)
    else:  # build
        self.build_static_site(world_directory)
        return self.start_preview_server(world_directory, port, auto_open)
```

#### Status and Management Tools
```python
def list_active_servers():
    """Show all running world servers"""
    
def stop_server(world_directory):
    """Stop a specific world server"""
    
def stop_all_servers():
    """Clean shutdown of all servers"""
```

## Implementation Plan

### Phase 1: Basic Auto-serve
- [ ] Implement Option 1 (Enhanced Dev Mode)
- [ ] Add `auto_serve` parameter to existing tool
- [ ] Basic process management and cleanup
- [ ] Port conflict detection and auto-fallback

### Phase 2: User Experience Polish
- [ ] Auto-browser opening
- [ ] Better error handling and user feedback
- [ ] Server status reporting
- [ ] Graceful cleanup on MCP shutdown

### Phase 3: Advanced Features
- [ ] Built-in Python server option
- [ ] Live reload for non-Astro workflows
- [ ] Multiple simultaneous world servers
- [ ] Server management dashboard

## Technical Considerations

### Security
- Validate all paths to prevent directory traversal
- Limit server binding to localhost only
- Process isolation and cleanup
- Resource limits (CPU, memory)

### Error Handling
- Port already in use → Auto-increment and retry
- Missing dependencies → Clear error messages
- Process crashes → Automatic cleanup and reporting
- Network issues → Fallback strategies

### Performance
- Lazy server startup (don't start until needed)
- Resource monitoring and limits
- Cleanup inactive servers
- Efficient file watching for live reload

### Cross-platform Compatibility
- Windows process management differences
- macOS/Linux subprocess handling
- Path handling across platforms
- Browser opening cross-platform

## Success Metrics

1. **Seamless Experience**: User runs one command, gets working server and open browser
2. **Zero Manual Steps**: No terminal commands required
3. **Reliable Cleanup**: No orphaned processes or port conflicts
4. **Fast Startup**: Server ready in <3 seconds
5. **Error Recovery**: Clear messages and automatic fallbacks

## Migration Path

1. Keep existing behavior as default for backwards compatibility
2. Add new auto-serve features as opt-in parameters
3. Eventually make auto-serve the default behavior
4. Deprecate manual setup instructions in favor of one-click experience

This enhancement would transform the worldbuilding workflow from "build world, setup server, open browser" to simply "build world" with everything else handled automatically.