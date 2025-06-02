#!/usr/bin/env python3
"""
Helper to fetch a single Ed Code section
Usage: python fetch_edcode_section.py <section> <law_code> <description>
"""

import sys
import json
from datetime import datetime, timezone

if len(sys.argv) < 4:
    print("Usage: python fetch_edcode_section.py <section> <law_code> <description>")
    sys.exit(1)

section = sys.argv[1]
law_code = sys.argv[2]
description = " ".join(sys.argv[3:])

# Generate URL based on law code
if law_code == "EDC":
    url = f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=EDC"
elif law_code == "VC":
    url = f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=VEH"
elif law_code == "GC":
    url = f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=GOV"
elif law_code == "PEN":
    url = f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=PEN"
else:
    print(f"Unknown law code: {law_code}")
    sys.exit(1)

# Create the fetch request
request = {
    "url": url,
    "prompt": f"Extract the complete text of {law_code} section {section} regarding {description}. Include all subdivisions, requirements, and the effective date.",
    "section": section,
    "law_code": law_code,
    "description": description
}

print(f"Fetch request for {law_code} {section}:")
print(json.dumps(request, indent=2))
print()
print("Use this with WebFetch to retrieve the section.")
