"""Entry creation module for the Vibe Worldbuilding MCP.

This module handles the creation of detailed world entries with proper formatting,
frontmatter, image generation, and integration with the world context system.
"""

from pathlib import Path
from typing import Any

import mcp.types as types

from ..config import (
    FAL_API_KEY,
    FAL_API_URL,
    FAL_AVAILABLE,
    IMAGE_EXTENSION,
    MARKDOWN_EXTENSION,
    MAX_DESCRIPTION_LINES,
    TAXONOMY_OVERVIEW_SUFFIX,
)
from ..utils.content_parsing import (
    add_frontmatter_to_content,
    extract_description_from_content,
    extract_frontmatter,
)
from .stub_generation import generate_stub_analysis
from .utilities import (
    clean_name,
    create_world_context_prompt,
    extract_taxonomy_context,
    get_existing_entries_with_descriptions,
    get_existing_taxonomies,
)
from ..utils.path_helpers import resolve_world_path

if FAL_AVAILABLE:
    import requests


async def create_world_entry(
    arguments: dict[str, Any] | None,
) -> list[types.TextContent]:
    """Create a detailed entry for a specific world element within a taxonomy.

    Creates an entry file with taxonomy context, generates an image if possible,
    and provides automatic stub analysis for entities mentioned in the content.

    Args:
        arguments: Tool arguments containing world_directory, taxonomy, entry_name, and entry_content

    Returns:
        List containing success message with entry details and optional stub analysis
    """
    # LOGGING: Validate that new code is being executed
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] ===== FUNCTION ENTRY =====")
    print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Arguments: {arguments}")
    
    if not arguments:
        print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] No arguments provided, returning error")
        return [types.TextContent(type="text", text="Error: No arguments provided")]

    world_directory = arguments.get("world_directory", "")
    taxonomy = arguments.get("taxonomy", "")
    entry_name = arguments.get("entry_name", "")
    entry_content = arguments.get("entry_content", "")
    
    print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Parsed arguments:")
    print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG]   world_directory: {world_directory}")
    print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG]   taxonomy: {taxonomy}")
    print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG]   entry_name: {entry_name}")
    print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG]   has_content: {bool(entry_content.strip())}")

    if not all([world_directory, taxonomy, entry_name]):
        print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Missing required arguments, returning error")
        return [
            types.TextContent(
                type="text",
                text="Error: world_directory, taxonomy, and entry_name are required",
            )
        ]

    try:
        print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Resolving world directory path...")
        # CRITICAL FIX: Resolve world directory against base directory
        world_path = resolve_world_path(world_directory)
        print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Resolved world_path: {world_path}")
        
        if not world_path.exists():
            print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] World directory does not exist: {world_path}")
            return [
                types.TextContent(
                    type="text",
                    text=f"Error: World directory {world_path} does not exist",
                )
            ]
        print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] World directory exists, continuing...")

        print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Cleaning names...")
        # Clean names for file system use
        clean_taxonomy = clean_name(taxonomy)
        clean_entry = clean_name(entry_name)
        print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] clean_taxonomy: {clean_taxonomy}, clean_entry: {clean_entry}")

        print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Checking taxonomy exists...")
        # Check if taxonomy exists before proceeding
        taxonomy_overview_file = world_path / "taxonomies" / f"{clean_taxonomy}{TAXONOMY_OVERVIEW_SUFFIX}.md"
        print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] taxonomy_overview_file: {taxonomy_overview_file}")
        print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] file exists: {taxonomy_overview_file.exists()}")
        
        if not taxonomy_overview_file.exists():
            print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Taxonomy does not exist, getting existing taxonomies...")
            existing_taxonomies = get_existing_taxonomies(world_path)
            taxonomy_list = ", ".join(existing_taxonomies) if existing_taxonomies else "None"
            print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] TAXONOMY VALIDATION FAILED - returning error")
            return [
                types.TextContent(
                    type="text",
                    text=f"Error: Taxonomy '{taxonomy}' does not exist. Available taxonomies: {taxonomy_list}\n\nUse the create_taxonomy tool to create this taxonomy first.",
                )
            ]
        
        print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Taxonomy validation passed, continuing...")

        print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Extracting taxonomy context...")
        # Extract taxonomy context if available
        taxonomy_context = extract_taxonomy_context(world_path, clean_taxonomy)
        print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] taxonomy_context length: {len(taxonomy_context) if taxonomy_context else 0}")

        print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Getting world context...")
        # Get world context for generating well-connected entries
        existing_taxonomies = get_existing_taxonomies(world_path)
        print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] existing_taxonomies: {existing_taxonomies}")
        
        existing_entries = get_existing_entries_with_descriptions(world_path)
        print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] existing_entries count: {len(existing_entries) if existing_entries else 0}")

        print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Getting world overview...")
        # Get world overview if available
        world_overview = _get_world_overview(world_path)
        print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] world_overview length: {len(world_overview) if world_overview else 0}")

        print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Creating world context prompt...")
        # Create comprehensive world context for the LLM
        world_context = create_world_context_prompt(
            existing_taxonomies,
            existing_entries,
            taxonomy_context,
            world_overview,
            taxonomy,
        )
        print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] world_context created, length: {len(world_context)}")

        print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Checking if entry_content provided...")
        # Always show context first, then handle entry creation
        if entry_content.strip():
            print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Entry content provided, creating entry file...")
            # Create the entry file
            entry_file = _create_entry_file(
                world_path,
                clean_taxonomy,
                clean_entry,
                entry_name,
                entry_content,
                taxonomy,
                taxonomy_context,
            )
            print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Entry file created: {entry_file}")

            print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Generating optimized entry image...")
            # Generate optimized image prompt and image if FAL API is available
            image_info = await _generate_optimized_entry_image(
                world_path,
                clean_taxonomy,
                clean_entry,
                entry_name,
                entry_content,
            )
            print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Image generation completed: {image_info}")

            print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Generating stub analysis...")
            # Generate auto-stub analysis
            stub_analysis_info = generate_stub_analysis(
                world_path, entry_name, taxonomy, entry_content
            )
            print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Stub analysis completed: {stub_analysis_info}")

            print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Creating response...")
            # Create response with context + creation result
            relative_path = str(entry_file.relative_to(world_path))
            context_info = (
                f"\n\nTaxonomy context included: {taxonomy_context[:100]}..."
                if taxonomy_context
                else "\n\nNo taxonomy overview found for reference."
            )

            response_text = f"# World Context Used for '{entry_name}'\n\n{world_context}\n\n---\n\n## Entry Created Successfully!\n\nSaved to: {relative_path}{context_info}\n\nThe entry includes:\n1. YAML frontmatter with description\n2. Your detailed content\n3. Taxonomy classification footer{image_info}{stub_analysis_info}\n\n**Note**: Review the content above - it should include crosslinks to existing entries based on the context provided."
            
            print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Returning success response, length: {len(response_text)}")
            return [
                types.TextContent(
                    type="text",
                    text=response_text,
                )
            ]
        else:
            print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] No entry content provided, returning context only...")
            # Return world context for entry generation
            response_text = f"# World Context for Creating '{entry_name}' in {taxonomy}\n\n{world_context}\n\n---\n\n**Next Step**: Generate entry content that references existing entries using the linking format provided above, then call this tool again with your `entry_content`."
            
            print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Returning context response, length: {len(response_text)}")
            return [
                types.TextContent(
                    type="text",
                    text=response_text,
                )
            ]

    except Exception as e:
        print(f"[{timestamp}] [CREATE_WORLD_ENTRY DEBUG] Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return [
            types.TextContent(type="text", text=f"Error creating world entry: {str(e)}")
        ]


def _get_world_overview(world_path: Path) -> str:
    """Get world overview content for context."""
    world_overview = ""
    overview_path = world_path / "overview" / "world-overview.md"
    if overview_path.exists():
        try:
            with open(overview_path, "r", encoding="utf-8") as f:
                content = f.read()
                world_overview = content[:500] + ("..." if len(content) > 500 else "")
        except Exception:
            pass
    return world_overview


def _create_entry_file(
    world_path: Path,
    clean_taxonomy: str,
    clean_entry: str,
    entry_name: str,
    entry_content: str,
    taxonomy: str,
    taxonomy_context: str,
) -> Path:
    """Create the entry file with proper formatting and frontmatter."""
    entry_path = world_path / "entries" / clean_taxonomy
    entry_path.mkdir(parents=True, exist_ok=True)

    entry_file = entry_path / f"{clean_entry}{MARKDOWN_EXTENSION}"

    # Extract description for frontmatter
    description = extract_description_from_content(entry_content)

    # Build frontmatter
    frontmatter = {"description": description, "article_type": "full"}
    if taxonomy_context:
        frontmatter["taxonomyContext"] = taxonomy_context

    # Add frontmatter to content
    final_content = add_frontmatter_to_content(entry_content, frontmatter)

    # Add taxonomy footer
    final_content += f"\n\n---\n*Entry in {taxonomy.title()} taxonomy*\n"

    with open(entry_file, "w", encoding="utf-8") as f:
        f.write(final_content)

    return entry_file


async def _generate_optimized_entry_image(
    world_path: Path,
    clean_taxonomy: str,
    clean_entry: str,
    entry_name: str,
    entry_content: str,
) -> str:
    """Generate an optimized image using the new prompt system."""
    # TEMPORARILY DISABLED: Image generation is causing the tool to hang
    # TODO: Debug and re-enable image generation
    return ""
    
    # Original code commented out to prevent hanging:
    # if not (FAL_AVAILABLE and FAL_API_KEY):
    #     return ""
    # 
    # try:
    #     # Create the entry file path for our new image tools
    #     entry_file_path = world_path / "entries" / clean_taxonomy / f"{clean_entry}{MARKDOWN_EXTENSION}"
    #     
    #     # Use the existing generate_image_from_markdown_file function which now checks for
    #     # image_prompt in frontmatter and uses optimized prompts
    #     from ..tools.images import generate_image_from_markdown_file
    #     
    #     result = await generate_image_from_markdown_file({
    #         "filepath": str(entry_file_path),
    #         "style": "fantasy illustration",
    #         "aspect_ratio": "1:1"
    #     })
    #     
    #     if result and result[0].text.startswith("Successfully generated"):
    #         return f"\n4. Generated optimized image: images/{clean_taxonomy}/{clean_entry}{IMAGE_EXTENSION}"
    #     
    # except Exception:
    #     pass  # Silently continue if image generation fails
    # 
    # return ""


# Old _extract_visual_elements function removed - now using optimized image prompt system
