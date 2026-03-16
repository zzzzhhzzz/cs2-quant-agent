"""Obsidian archiver module for saving reports to local filesystem."""

import os
from datetime import datetime
from pathlib import Path


def save_to_obsidian(content: str, output_dir: str = None) -> str:
    """
    Save analysis report to local filesystem.

    Args:
        content: Markdown content to save
        output_dir: Output directory path (default: ./output)

    Returns:
        Path to the saved file
    """
    if output_dir is None:
        # Default to output directory relative to project root
        project_root = Path(__file__).parent.parent.parent
        output_dir = project_root / "output"

    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"cs2_analysis_{timestamp}.md"
    filepath = output_path / filename

    # Write content to file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return str(filepath)
