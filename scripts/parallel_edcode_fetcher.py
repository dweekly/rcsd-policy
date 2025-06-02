#!/usr/bin/env python3
"""
Massively parallel Ed Code fetcher using aiohttp
Fetches hundreds of sections concurrently
"""

import asyncio
import aiohttp
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import re
from concurrent.futures import ThreadPoolExecutor
import sys


class ParallelEdCodeFetcher:
    def __init__(self, max_concurrent=20):
        self.max_concurrent = max_concurrent
        self.session = None
        self.results = []
        self.errors = []
        self.cache_dir = Path("data/cache/edcode")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    async def fetch_section(self, session, section_info):
        """Fetch a single Ed Code section"""
        section = section_info["section"]
        law_code = section_info["law_code"]
        url = section_info["url"]
        
        # Check if already cached
        safe_section = section.replace(".", "_")
        output_file = self.cache_dir / f"{law_code.lower()}_{safe_section}_full.json"
        
        if output_file.exists():
            return {"status": "cached", "section": section, "law_code": law_code}
        
        try:
            async with session.get(url, timeout=30) as response:
                if response.status != 200:
                    return {
                        "status": "error",
                        "section": section,
                        "law_code": law_code,
                        "error": f"HTTP {response.status}"
                    }
                
                html = await response.text()
                
                # Parse the HTML to extract the code section
                soup = BeautifulSoup(html, 'html.parser')
                
                # Look for the section content
                content = self.extract_section_content(soup, section, law_code)
                
                if content:
                    # Save to file
                    self.save_section(section, law_code, content["text"], content["title"], url)
                    
                    return {
                        "status": "success",
                        "section": section,
                        "law_code": law_code,
                        "title": content["title"]
                    }
                else:
                    return {
                        "status": "parse_error",
                        "section": section,
                        "law_code": law_code,
                        "error": "Could not extract content"
                    }
                    
        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "section": section,
                "law_code": law_code,
                "error": "Request timed out"
            }
        except Exception as e:
            return {
                "status": "error",
                "section": section,
                "law_code": law_code,
                "error": str(e)
            }
    
    def extract_section_content(self, soup, section, law_code):
        """Extract section content from HTML"""
        
        # Try different patterns to find the content
        patterns = [
            # Pattern 1: Look for div with class containing 'content'
            lambda: soup.find('div', {'class': re.compile('content', re.I)}),
            # Pattern 2: Look for main content area
            lambda: soup.find('main'),
            # Pattern 3: Look for article tag
            lambda: soup.find('article'),
            # Pattern 4: Look for div with id containing 'content'
            lambda: soup.find('div', {'id': re.compile('content', re.I)}),
        ]
        
        content_div = None
        for pattern in patterns:
            content_div = pattern()
            if content_div:
                break
        
        if not content_div:
            # Try to find by section number
            text = soup.get_text()
            if f"{section}." in text or f"Section {section}" in text:
                # Extract around the section number
                lines = text.split('\n')
                relevant_lines = []
                capturing = False
                
                for line in lines:
                    if f"{section}." in line or f"Section {section}" in line:
                        capturing = True
                    if capturing:
                        relevant_lines.append(line.strip())
                        if len(relevant_lines) > 100:  # Limit to prevent huge extracts
                            break
                
                if relevant_lines:
                    return {
                        "title": f"{law_code} Section {section}",
                        "text": '\n'.join(relevant_lines)
                    }
        
        if content_div:
            # Extract text and try to clean it
            text = content_div.get_text(separator='\n', strip=True)
            
            # Try to extract title
            title_match = re.search(rf'{section}\.\s*\[([^\]]+)\]', text)
            if title_match:
                title = title_match.group(1)
            else:
                title = f"{law_code} Section {section}"
            
            return {
                "title": title,
                "text": text
            }
        
        return None
    
    def save_section(self, section, law_code, content, title, url):
        """Save section to JSON file"""
        safe_section = section.replace(".", "_")
        output_file = self.cache_dir / f"{law_code.lower()}_{safe_section}_full.json"
        
        data = {
            "section": section,
            "content": content,
            "title": title,
            "law_code": law_code,
            "url": url,
            "fetched": datetime.now(timezone.utc).isoformat(),
            "verified_by": "Automated parallel fetcher"
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    async def fetch_batch(self, section_infos):
        """Fetch a batch of sections concurrently"""
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def fetch_with_semaphore(session, section_info):
            async with semaphore:
                return await self.fetch_section(session, section_info)
        
        # Create session with custom headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            tasks = [
                fetch_with_semaphore(session, section_info)
                for section_info in section_infos
            ]
            
            # Process with progress indicator
            results = []
            for i, task in enumerate(asyncio.as_completed(tasks)):
                result = await task
                results.append(result)
                
                # Progress indicator
                if (i + 1) % 10 == 0:
                    print(f"Progress: {i + 1}/{len(tasks)} sections processed...")
            
            return results
    
    def run_batch(self, section_infos):
        """Run async batch fetch"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.fetch_batch(section_infos))
        finally:
            loop.close()


def load_sections_to_fetch():
    """Load all sections that need fetching from manifests"""
    manifest_dir = Path("data/cache/edcode_manifests")
    all_sections = []
    
    if not manifest_dir.exists():
        print("No manifests found. Run parallel_fetch_edcodes.py first")
        return []
    
    # Load all manifests
    for manifest_file in sorted(manifest_dir.glob("batch_*.json")):
        with open(manifest_file) as f:
            manifest = json.load(f)
            
        for cmd in manifest["commands"]:
            # Check if already cached
            safe_section = cmd["section"].replace(".", "_")
            cache_file = Path(f"data/cache/edcode/{cmd['law_code'].lower()}_{safe_section}_full.json")
            
            if not cache_file.exists():
                all_sections.append({
                    "section": cmd["section"],
                    "law_code": cmd["law_code"],
                    "url": cmd["url"],
                    "count": cmd.get("count", 1),
                    "description": cmd.get("description", "")
                })
    
    return all_sections


def main():
    """Main function"""
    
    print("=" * 80)
    print("MASSIVELY PARALLEL ED CODE FETCHER")
    print("=" * 80)
    
    # Load sections to fetch
    sections = load_sections_to_fetch()
    
    if not sections:
        print("No sections to fetch!")
        return
    
    print(f"\nTotal sections to fetch: {len(sections)}")
    
    # Sort by priority (citation count)
    sections.sort(key=lambda x: x["count"], reverse=True)
    
    # Show top sections
    print("\nTop 10 sections by citation count:")
    for s in sections[:10]:
        print(f"  {s['law_code']} {s['section']}: {s['count']} citations")
    
    # Ask for confirmation
    batch_size = min(50, len(sections))  # Process in batches of 50
    if len(sys.argv) > 1:
        batch_size = int(sys.argv[1])
    
    print(f"\nReady to fetch {batch_size} sections in parallel")
    print("This will make multiple concurrent HTTP requests")
    
    response = input("\nProceed? (y/n): ")
    if response.lower() != 'y':
        print("Aborted")
        return
    
    # Create fetcher
    fetcher = ParallelEdCodeFetcher(max_concurrent=20)
    
    # Process first batch
    batch = sections[:batch_size]
    
    print(f"\nFetching batch of {len(batch)} sections...")
    start_time = time.time()
    
    results = fetcher.run_batch(batch)
    
    # Summarize results
    status_counts = {}
    for r in results:
        status = r["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    
    elapsed = time.time() - start_time
    
    print(f"\n\nCompleted in {elapsed:.1f} seconds")
    print(f"Average: {elapsed/len(batch):.2f} seconds per section")
    
    print("\nResults:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    
    # Show errors if any
    errors = [r for r in results if r["status"] in ["error", "parse_error", "timeout"]]
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors[:10]:
            print(f"  {e['law_code']} {e['section']}: {e.get('error', 'Unknown error')}")
    
    # Calculate remaining
    remaining = len(sections) - batch_size
    if remaining > 0:
        print(f"\n{remaining} sections remaining")
        print(f"Run again with: python scripts/parallel_edcode_fetcher.py {min(100, remaining)}")


if __name__ == "__main__":
    main()