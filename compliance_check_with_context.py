#!/usr/bin/env python3
"""
Enhanced compliance checking that considers related policies
"""

import os
import re

from anthropic import Anthropic
from dotenv import load_dotenv

from compliance_check_structured import parse_policy_to_xml

load_dotenv()


def find_related_policies(policy_code, base_dir="extracted_policies_all"):
    """Find policies that might contain related requirements"""
    related = {}

    # Common policy relationships
    policy_relationships = {
        # Student behavior policies often split requirements
        "5131.4": [
            "0450",
            "5144",
            "5144.1",
            "5144.2",
            "5131",
            "5131.2",
        ],  # Student disturbances → Safety plans, Discipline
        "5131": [
            "5131.4",
            "5144",
            "5144.1",
            "5144.2",
        ],  # Conduct → Related discipline policies
        # Food service often relates to wellness
        "3550": [
            "5030",
            "3551",
            "3552",
            "3553",
            "3554",
            "3555",
        ],  # Food service → Wellness, other nutrition
        # Safety policies are interconnected
        "0450": [
            "3515",
            "3515.5",
            "3516",
            "5131.4",
            "5141.4",
        ],  # Comprehensive safety → Various safety topics
        "3515.5": [
            "0450",
            "3515",
            "4158",
            "4258",
            "4358",
        ],  # Sex offender → Safety, employee policies
        # Non-discrimination policies overlap
        "0410": ["1312.3", "4119.11", "4219.11", "4319.11", "5145.3", "5145.7"],
        "5145.7": ["0410", "1312.3", "4119.12", "4219.12", "4319.12"],
        # Wellness and physical activity
        "5030": ["3550", "3551", "3552", "3553", "3554", "3555", "6142.7"],
        # Special education related
        "6159": ["6159.1", "6159.2", "6159.3", "6164.4", "6164.5", "6164.6"],
        # Technology policies
        "6163.4": ["4040", "5125", "5125.2"],
        # Translation/communication requirements often in one place
        "5145.6": [
            "6020",
            "1312.3",
            "5145.3",
        ],  # Parent involvement → Translation requirements
        "6020": ["5145.6"],  # Parent involvement
    }

    # Get potential related policies
    related_codes = policy_relationships.get(policy_code, [])

    # Also check for sequential policies (e.g., 5131.1, 5131.2 if checking 5131)
    base_code = policy_code.split(".")[0]
    for i in range(1, 6):
        related_codes.append(f"{base_code}.{i}")

    # Check parent policy if this is a sub-policy
    if "." in policy_code:
        related_codes.append(base_code)

    # Check for each related policy
    for code in set(related_codes):
        for subdir in ["policies", "regulations"]:
            file_path = os.path.join(base_dir, subdir, f"{code}.txt")
            if os.path.exists(file_path):
                try:
                    with open(file_path) as f:
                        content = f.read(
                            5000
                        )  # Just read enough to get title and overview

                    title_match = re.search(r"Title:\s*(.+?)(?:\n|$)", content)
                    title = title_match.group(1) if title_match else "Unknown"

                    related[code] = {
                        "title": title,
                        "type": subdir[:-1].capitalize(),
                        "file_path": file_path,
                    }
                except:
                    pass

    return related


def extract_key_provisions(file_path, search_terms):
    """Extract provisions from a policy that might address specific requirements"""
    try:
        with open(file_path) as f:
            content = f.read()

        relevant_sections = []
        lines = content.split("\n")

        for i, line in enumerate(lines):
            for term in search_terms:
                if term.lower() in line.lower():
                    # Get context (2 lines before and after)
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    context = "\n".join(lines[start:end])
                    relevant_sections.append(
                        {"term": term, "context": context, "line_num": i}
                    )
                    break

        return relevant_sections
    except:
        return []


def check_compliance_with_context(
    policy_xml, code, title, last_reviewed, related_policies
):
    """Enhanced compliance check that considers related policies"""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    model = os.getenv("ANTHROPIC_MODEL", "claude-4-sonnet-20250514")

    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment")

    client = Anthropic(api_key=api_key)

    # Build context about related policies
    related_context = "Related policies in the district:\n"
    for rel_code, rel_info in related_policies.items():
        related_context += f"- {rel_info['type']} {rel_code}: {rel_info['title']}\n"

    prompt = f"""You are reviewing a California school district policy for compliance with current Education Code and federal requirements.

IMPORTANT CONTEXT: School districts often address legal requirements across multiple related policies rather than duplicating language in each policy. Before flagging a requirement as missing, consider whether it would typically be addressed in a related policy.

Policy being reviewed: {code} - {title}
Last Updated: {last_reviewed}

{related_context}

Common policy organization patterns:
- Comprehensive School Safety Plans are typically in Policy 0450, not in individual student conduct policies
- Wellness requirements are typically in Policy 5030, not in food service policies  
- Translation requirements are often centralized in parent involvement or communication policies
- Non-discrimination procedures may be in separate complaint policies (1312.3)
- Employee background checks may be in personnel policies (4000 series)

For each potential compliance issue:
1. First consider whether this requirement would typically be addressed in this specific policy or in a related policy
2. Only flag as MATERIAL if the requirement MUST be in this specific policy by law
3. Flag as MINOR if the requirement could reasonably be in a related policy but a cross-reference would be helpful
4. Include confidence level based on how certain you are this specific policy needs the language

<compliance_report>
    <compliance_issues>
        <issue priority="MATERIAL|MINOR" confidence="[0-100]">
            <title>[Issue Title]</title>
            <description>[Explain why this specific policy needs this language]</description>
            <typical_location>[Where this requirement is typically addressed: "This Policy" or "Usually in Policy XXXX"]</typical_location>
            
            <legal_basis>
                <california_code>
                    <citation>[Ed Code Section]</citation>
                    <text>[Relevant excerpt]</text>
                    <requires_in_specific_policy>[true/false - does law require it in THIS policy?]</requires_in_specific_policy>
                </california_code>
            </legal_basis>
            
            <recommended_action>
                <option type="ADD_LANGUAGE">Add specific language to this policy</option>
                <option type="CROSS_REFERENCE">Add cross-reference to Policy [XXXX]</option>
                <option type="VERIFY_EXISTS">Verify requirement is addressed in Policy [XXXX]</option>
            </recommended_action>
        </issue>
    </compliance_issues>
</compliance_report>

<policy_document>
{policy_xml}
</policy_document>"""

    response = client.messages.create(
        model=model,
        max_tokens=4000,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text


def main():
    import sys

    if len(sys.argv) > 1:
        policy_file = sys.argv[1]
    else:
        policy_file = "extracted_policies_all/policies/5131.4.txt"

    if not os.path.exists(policy_file):
        print(f"Error: File not found: {policy_file}")
        return

    print(f"Running context-aware compliance check on: {policy_file}")

    # Parse policy
    policy_xml, code, title, last_reviewed = parse_policy_to_xml(policy_file)

    # Find related policies
    print(f"\nFinding related policies for {code}...")
    related = find_related_policies(code)

    if related:
        print(f"Found {len(related)} related policies:")
        for rel_code, rel_info in related.items():
            print(f"  - {rel_info['type']} {rel_code}: {rel_info['title']}")

    # Check compliance with context
    print("\nChecking compliance with awareness of related policies...")
    result = check_compliance_with_context(
        policy_xml, code, title, last_reviewed, related
    )

    print("\nCompliance Analysis (Context-Aware):")
    print("=" * 80)
    print(result)
    print("=" * 80)


if __name__ == "__main__":
    main()
