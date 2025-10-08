# metadata_tool_v5.py
# Auto-generated from YAML logic (DKI v5.0 Protocol)

import zipfile
import os
import json
import hashlib
from datetime import datetime

# --- Simulated Tool Functions (Replace with real libraries/tools later) ---
def run_pillow(file): return {"tool": "Pillow", "metadata": {"DateTimeOriginal": "2021:06:01 12:00:00"}}
def run_piexif(file): return {"tool": "piexif", "metadata": {}}
def run_exifread(file): return {"tool": "exifread", "metadata": {}}
def run_hachoir(file): return {"tool": "hachoir", "metadata": {}}
def run_pyheif(file): return {"tool": "pyheif", "metadata": {}}
def run_exiftool(file): return {"tool": "ExifTool", "metadata": {}}
def run_filesystem(file): return {"tool": "filesystem", "metadata": {"Created": os.path.getctime(file)}}
def run_ai_inference(file): return {"tool": "AI_inference", "metadata": {}}

TOOLCHAIN = {
    "jpeg_tiff": [run_pillow, run_piexif, run_exifread, run_hachoir, run_filesystem, run_ai_inference],
    "heic_heif": [run_exiftool, run_pyheif, run_hachoir, run_filesystem, run_ai_inference],
    "raw": [run_exiftool, run_hachoir, run_filesystem, run_ai_inference],
    "video": [run_exiftool, run_hachoir, run_filesystem, run_ai_inference],
}

FILE_CATEGORIES = {
    ".jpg": "jpeg_tiff",
    ".jpeg": "jpeg_tiff",
    ".tiff": "jpeg_tiff",
    ".heic": "heic_heif",
    ".heif": "heic_heif",
    ".dng": "raw",
    ".cr2": "raw",
    ".nef": "raw",
    ".mp4": "video",
    ".mov": "video",
}

def hash_file(path):
    with open(path, "rb") as f:
        data = f.read()
        return hashlib.md5(data).hexdigest(), hashlib.sha256(data).hexdigest()

def process_zip(zip_path, output_dir):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)

    report = []
    for root, _, files in os.walk(output_dir):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            file_path = os.path.join(root, file)
            f_type = FILE_CATEGORIES.get(ext, None)
            if not f_type:
                continue

            md5, sha256 = hash_file(file_path)
            status = "UNRECOVERABLE"
            used_tool = None
            attempted_tools = []
            metadata = {}

            for tool in TOOLCHAIN[f_type]:
                tool_name = tool.__name__.replace("run_", "")
                result = tool(file_path)
                attempted_tools.append(tool_name)
                if result.get("metadata"):
                    metadata = result["metadata"]
                    used_tool = tool_name
                    status = "SUCCESS"
                    break

            if not metadata:
                status = "FALLBACK" if "filesystem" in attempted_tools else "UNRECOVERABLE"

            report.append({
                "filename": file,
                "hash": {"md5": md5, "sha256": sha256},
                "attempted_tools": attempted_tools,
                "used_tool": used_tool,
                "metadata": metadata,
                "final_status": status
            })

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"metadata_report_{timestamp}.json")
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"✅ Report generated: {output_file}")

# Example usage:
# process_zip("path/to/input.zip", "path/to/extracted_dir")
