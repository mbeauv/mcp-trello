#!/usr/bin/env python3
"""Build script to create a .dxt Desktop Extension from the MCP server."""

import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

def build_dxt():
    """Build the .dxt file for Desktop Extension deployment."""
    
    # Paths
    project_root = Path(__file__).parent.parent
    dxt_dir = project_root / "dxt"
    src_dir = project_root / "src" / "mcp_trello"
    manifest_path = dxt_dir / "manifest.json"
    
    # Load version from manifest
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    version = manifest["version"]
    output_file = project_root / f"mbeauv-mcp-trello-{version}.dxt"
    
    print(f"Building Desktop Extension v{version}...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create extension structure
        server_dir = temp_path / "server"
        server_dir.mkdir()
        
        # Copy source files to server directory
        for file in src_dir.glob("*.py"):
            shutil.copy2(file, server_dir)
        
        # Copy manifest
        shutil.copy2(manifest_path, temp_path / "manifest.json")
        
        # Copy icon if it exists
        icon_path = dxt_dir / "icon.png"
        if icon_path.exists():
            shutil.copy2(icon_path, temp_path / "icon.png")
        
        # Install dependencies to lib directory using uv
        lib_dir = temp_path / "lib"
        lib_dir.mkdir()
        
        print("Installing dependencies with uv...")
        subprocess.run([
            "uv", "pip", "install", 
            "--target", str(lib_dir),
            "--no-deps",  # We'll handle deps manually
            "mcp>=1.0.0",
            "py-trello>=0.19.0", 
            "python-dotenv>=1.0.0",
            "httpx>=0.24.0"
        ], check=True)
        
        # Create requirements.txt
        requirements = [
            "mcp>=1.0.0",
            "py-trello>=0.19.0",
            "python-dotenv>=1.0.0", 
            "httpx>=0.24.0"
        ]
        
        with open(temp_path / "requirements.txt", "w") as f:
            f.write("\n".join(requirements))
        
        # Create the .dxt file (zip archive)
        print(f"Creating {output_file}...")
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in temp_path.rglob("*"):
                if file_path.is_file():
                    arc_path = file_path.relative_to(temp_path)
                    zf.write(file_path, arc_path)
        
        print(f"✅ Desktop Extension built: {output_file}")
        print(f"📦 Size: {output_file.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    build_dxt()
