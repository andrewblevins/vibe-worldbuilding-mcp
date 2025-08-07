"""Entry tools router for the Vibe Worldbuilding MCP.

This module provides the main tool handler interface for entry operations,
delegating to the appropriate specialized modules in the entries package.
"""

from typing import Any

import mcp.types as types

from ..entries.consistency import analyze_world_consistency
from ..entries.content_processing import (
    add_entry_frontmatter,
    generate_entry_descriptions,
)
from ..entries.creation import create_world_entry
from ..entries.stub_generation import create_stub_entries

# Tool router for entry operations
ENTRY_HANDLERS = {
    "create_world_entry": create_world_entry,
    "create_stub_entries": create_stub_entries,
    "generate_entry_descriptions": generate_entry_descriptions,
    "add_entry_frontmatter": add_entry_frontmatter,
    "analyze_world_consistency": analyze_world_consistency,
}


async def handle_entry_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent]:
    """Route entry tool calls to appropriate handlers.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        Tool execution result

    Raises:
        ValueError: If tool name is not recognized
    """
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [ENTRY HANDLER DEBUG] ===== ENTRY TOOL HANDLER CALLED =====")
    print(f"[{timestamp}] [ENTRY HANDLER DEBUG] Tool name: {name}")
    print(f"[{timestamp}] [ENTRY HANDLER DEBUG] Arguments: {arguments}")
    
    if name not in ENTRY_HANDLERS:
        print(f"[{timestamp}] [ENTRY HANDLER DEBUG] Unknown entry tool: {name}")
        raise ValueError(f"Unknown entry tool: {name}")

    print(f"[{timestamp}] [ENTRY HANDLER DEBUG] Calling handler for {name}")
    try:
        result = await ENTRY_HANDLERS[name](arguments)
        print(f"[{timestamp}] [ENTRY HANDLER DEBUG] Handler completed successfully")
        return result
    except Exception as e:
        print(f"[{timestamp}] [ENTRY HANDLER DEBUG] Handler failed with exception: {e}")
        import traceback
        traceback.print_exc()
        raise
