#!/usr/bin/env python3
"""
Fetch Ed Code sections using WebFetch tool to handle dynamic content
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone


def fetch_ed_code_section(section_num: str, cache_dir: Path):
    """Fetch an Ed Code section using WebFetch (must be run in Claude Code)"""
    
    # Check cache first
    cache_file = cache_dir / f"edc_{section_num.replace('.', '_')}_full.json"
    if cache_file.exists():
        with open(cache_file) as f:
            data = json.load(f)
            # Cache for 180 days
            if (datetime.now(timezone.utc) - datetime.fromisoformat(data["fetched"])).days < 180:
                print(f"Using cached version of Ed Code {section_num}")
                return data
    
    print(f"This script must be run within Claude Code to fetch Ed Code {section_num}")
    print(f"Please run: WebFetch the following URL and extract the full text of Education Code Section {section_num}")
    print(f"URL: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section_num}&lawCode=EDC")
    
    # Return placeholder
    return {
        "section": section_num,
        "content": f"[PLACEHOLDER - Run in Claude Code to fetch actual content]",
        "url": f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section_num}&lawCode=EDC",
        "fetched": datetime.now(timezone.utc).isoformat()
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fetch_edcode_with_ai.py <section_number>")
        sys.exit(1)
    
    section = sys.argv[1]
    cache_dir = Path("data/cache/edcode")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    result = fetch_ed_code_section(section, cache_dir)
    print(json.dumps(result, indent=2))