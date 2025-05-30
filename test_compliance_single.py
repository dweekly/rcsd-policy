#!/usr/bin/env python3
"""
Test compliance checking on a single policy
"""

import os
import re
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()

def parse_policy_to_xml(file_path):
    """Convert a policy text file to structured XML format"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract metadata from our specific header format
    # Format: RCSD Policy/Regulation XXXX
    code_match = re.search(r'RCSD (?:Policy|Regulation|Bylaw)\s+(\d+(?:\.\d+)?)', content)
    code = code_match.group(1) if code_match else "Unknown"
    
    # Determine document type from header
    if "RCSD Policy" in content[:100]:
        doc_type = "Policy"
    elif "RCSD Regulation" in content[:100]:
        doc_type = "Regulation"
    elif "RCSD Bylaw" in content[:100]:
        doc_type = "Bylaw"
    else:
        doc_type = "Unknown"
    
    # Extract title from header section
    title_match = re.search(r'Title:\s*(.+?)(?:\n|$)', content)
    title = title_match.group(1).strip() if title_match else "Unknown Title"
    
    # Extract dates from header
    adopted_match = re.search(r'Original Adopted Date:\s*(\d{1,2}/\d{1,2}/\d{2,4})', content)
    adopted = adopted_match.group(1) if adopted_match else None
    
    reviewed_match = re.search(r'Last Reviewed Date:\s*(\d{1,2}/\d{1,2}/\d{2,4})', content)
    reviewed = reviewed_match.group(1) if reviewed_match else adopted
    
    # Extract main content (between header separator and references)
    # Look for content between the ===== lines
    main_text_match = re.search(r'={50,}\n\n(.+?)(?=\n={50,}\nREFERENCES)', content, re.DOTALL)
    if not main_text_match:
        # Fallback if no REFERENCES section
        main_text_match = re.search(r'={50,}\n\n(.+?)$', content, re.DOTALL)
    main_text = main_text_match.group(1).strip() if main_text_match else content
    
    # Extract references - look in the REFERENCES section
    refs_section = re.search(r'REFERENCES\n={50,}\n(.+?)$', content, re.DOTALL)
    refs_text = refs_section.group(1) if refs_section else content
    
    # Extract state references
    state_refs = []
    state_section = re.search(r'State References:(.*?)(?=Federal References:|Cross References:|Policy References:|Management Resources:|$)', refs_text, re.DOTALL)
    if state_section:
        state_refs = re.findall(r'-\s*(.+?)(?=\n|$)', state_section.group(1))
    
    # Extract federal references
    federal_refs = []
    federal_section = re.search(r'Federal References:(.*?)(?=Cross References:|Policy References:|Management Resources:|$)', refs_text, re.DOTALL)
    if federal_section:
        federal_refs = re.findall(r'-\s*(.+?)(?=\n|$)', federal_section.group(1))
    
    # Extract cross-references
    cross_refs = []
    cross_section = re.search(r'(?:Cross References|Policy References):(.*?)(?=Management Resources:|$)', refs_text, re.DOTALL)
    if cross_section:
        cross_refs = re.findall(r'(?:Policy|Regulation)\s+(\d{4}(?:\.\d+)?)', cross_section.group(1))
    
    # Build XML
    xml = f"""<policy>
    <metadata>
        <code>{code}</code>
        <type>{doc_type}</type>
        <title>{title}</title>
        <adopted>{adopted or 'Unknown'}</adopted>
        <last_reviewed>{reviewed or adopted or 'Unknown'}</last_reviewed>
        <source>{os.path.basename(file_path)}</source>
    </metadata>
    <content>
        <main_text>
{main_text}
        </main_text>
        <legal_references>
            <state_references>
"""
    
    for ref in state_refs[:5]:  # Limit to first 5 to keep it concise
        xml += f"                <reference>{ref.strip()}</reference>\n"
    
    xml += "            </state_references>\n            <federal_references>\n"
    
    for ref in federal_refs[:5]:
        xml += f"                <reference>{ref.strip()}</reference>\n"
    
    xml += "            </federal_references>\n        </legal_references>\n        <cross_references>\n"
    
    for ref in list(set(cross_refs))[:5]:
        xml += f"            <policy_ref>{ref}</policy_ref>\n"
    
    xml += "        </cross_references>\n    </content>\n</policy>"
    
    return xml, code, title, reviewed

def check_compliance(policy_xml, policy_code, policy_title, last_reviewed):
    """Check policy compliance using Claude API"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    model = os.getenv("ANTHROPIC_MODEL", "claude-4-sonnet-20250514")
    
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment")
    
    client = Anthropic(api_key=api_key)
    
    # Calculate age of policy
    if last_reviewed and last_reviewed != 'Unknown':
        try:
            review_date = datetime.strptime(last_reviewed, "%m/%d/%Y")
            age_years = (datetime.now() - review_date).days / 365.25
        except:
            age_years = 0
    else:
        age_years = 0
    
    prompt = f"""You are reviewing a school district policy for compliance with current California Education Code.

Policy: {policy_code} - {policy_title}
Last Updated: {last_reviewed} ({age_years:.1f} years ago)

The policy text is provided below in XML format. Please:
1. Check for MATERIAL non-compliance with current CA Education Code (as of 2025)
2. Only flag issues you are HIGHLY CONFIDENT about (80%+ confidence)
3. Note any typos or minor errors
4. DO NOT suggest stylistic improvements - focus only on legal compliance
5. For each issue found, cite the specific Ed Code section that applies

Format your response as:
MATERIAL ISSUES:
- [Issue description] (Confidence: X%) - Relevant Ed Code: [Section]

MINOR ISSUES:
- [Issue description]

If no issues are found, state "No compliance issues identified."

<policy_document>
{policy_xml}
</policy_document>"""

    print(f"\nContacting Claude API with model: {model}")
    print(f"Checking Policy {policy_code} - {policy_title}")
    print(f"Last reviewed: {last_reviewed} ({age_years:.1f} years ago)")
    
    try:
        response = client.messages.create(
            model=model,
            max_tokens=2000,
            temperature=0,
            messages=[
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
        )
        
        return response.content[0].text
    
    except Exception as e:
        return f"Error calling Claude API: {str(e)}"

def main():
    # Find an older policy to test
    policies_dir = "extracted_policies_all/policies"
    
    # Look for a policy that might be older
    test_file = None
    
    # Try to find policy 3550 which we know exists and might be older
    if os.path.exists(f"{policies_dir}/3550.txt"):
        test_file = f"{policies_dir}/3550.txt"
    else:
        # Just grab the first policy
        for file in sorted(os.listdir(policies_dir)):
            if file.endswith(".txt"):
                test_file = os.path.join(policies_dir, file)
                break
    
    if not test_file:
        print("No policy files found to test")
        return
    
    print(f"Testing compliance check on: {test_file}")
    
    # Parse policy to XML
    policy_xml, code, title, last_reviewed = parse_policy_to_xml(test_file)
    
    print("\nGenerated XML structure:")
    print("=" * 80)
    print(policy_xml[:1000] + "..." if len(policy_xml) > 1000 else policy_xml)
    print("=" * 80)
    
    # Check compliance
    result = check_compliance(policy_xml, code, title, last_reviewed)
    
    print("\nCompliance Check Result:")
    print("=" * 80)
    print(result)
    print("=" * 80)

if __name__ == "__main__":
    main()