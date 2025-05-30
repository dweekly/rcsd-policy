#!/usr/bin/env python3
"""
Structured compliance checking with detailed legal citations and sample policies
"""

import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic
import json

# Load environment variables
load_dotenv()

def parse_policy_to_xml(file_path):
    """Convert a policy text file to structured XML format"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract metadata from our specific header format
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
    main_text_match = re.search(r'={50,}\n\n(.+?)(?=\n={50,}\nREFERENCES)', content, re.DOTALL)
    if not main_text_match:
        main_text_match = re.search(r'={50,}\n\n(.+?)$', content, re.DOTALL)
    main_text = main_text_match.group(1).strip() if main_text_match else content
    
    # Extract references
    refs_section = re.search(r'REFERENCES\n={50,}\n(.+?)$', content, re.DOTALL)
    refs_text = refs_section.group(1) if refs_section else ""
    
    # Build structured XML
    xml = f"""<policy>
    <metadata>
        <code>{code}</code>
        <type>{doc_type}</type>
        <title>{title}</title>
        <adopted>{adopted or 'Unknown'}</adopted>
        <last_reviewed>{reviewed or adopted or 'Unknown'}</last_reviewed>
    </metadata>
    <content>
        <main_text>{main_text}</main_text>
        <references>{refs_text}</references>
    </content>
</policy>"""
    
    return xml, code, title, reviewed

def check_compliance_structured(policy_xml, policy_code, policy_title, last_reviewed):
    """Check policy compliance and return structured results"""
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
    
    prompt = f"""You are reviewing a California school district policy for compliance with current Education Code and federal requirements.

Policy: {policy_code} - {policy_title}
Last Updated: {last_reviewed} ({age_years:.1f} years ago)

Analyze this policy and provide a structured compliance report in XML format. For each compliance issue:

1. Identify MATERIAL issues (non-compliance with mandatory legal requirements) with confidence levels
2. Cite the specific Education Code section, federal statute, or regulation that requires the missing element
3. Quote the exact statutory language when possible
4. Find and cite similar language from CSBA sample policies or other California school districts
5. Provide specific required language based on the statute
6. Note the effective date of requirements to determine if the policy predates them

Use this XML structure for your response:

<compliance_report>
    <compliance_issues>
        <issue priority="MATERIAL|MINOR" confidence="[0-100]">
            <title>[Issue Title]</title>
            <description>[Detailed description]</description>
            
            <legal_basis>
                <california_code>
                    <citation>[Ed Code Section]</citation>
                    <text>[Exact statutory text]</text>
                    <effective_date>[YYYY-MM-DD if known]</effective_date>
                </california_code>
                
                <federal_code>
                    <citation>[USC or CFR citation]</citation>
                    <text>[Exact statutory/regulatory text]</text>
                </federal_code>
            </legal_basis>
            
            <required_language>
                <source type="STATUTE|REGULATION">[Citation]</source>
                <text>[Specific language that must be included]</text>
            </required_language>
            
            <sample_policies>
                <policy district="[District Name or CSBA]" code="[Policy Code]" date="[YYYY-MM]">
                    <text>[Sample compliant language]</text>
                </policy>
            </sample_policies>
        </issue>
    </compliance_issues>
    
    <recommended_actions>
        <action priority="[1-N]">
            <description>[What to do]</description>
            <location>[Where in policy to add/change]</location>
        </action>
    </recommended_actions>
</compliance_report>

Focus on California-specific requirements including:
- Universal meals (Ed Code 49501.5)
- Free drinking water (Ed Code 38086)
- Wellness policy requirements (Ed Code 49431.5)
- Current nutrition standards
- Competitive food restrictions
- Anti-discrimination and meal shaming prohibitions

<policy_document>
{policy_xml}
</policy_document>"""

    print(f"\nChecking Policy {policy_code} - {policy_title}")
    print(f"Last reviewed: {last_reviewed} ({age_years:.1f} years ago)")
    
    try:
        response = client.messages.create(
            model=model,
            max_tokens=4000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    except Exception as e:
        return f"Error calling Claude API: {str(e)}"

def parse_compliance_report(xml_response):
    """Parse the XML compliance report into structured data"""
    try:
        # Extract XML content if wrapped in other text
        xml_match = re.search(r'<compliance_report>.*</compliance_report>', xml_response, re.DOTALL)
        if xml_match:
            xml_content = xml_match.group(0)
        else:
            xml_content = xml_response
        
        root = ET.fromstring(xml_content)
        
        report = {
            'issues': [],
            'actions': []
        }
        
        # Parse issues
        for issue in root.findall('.//issue'):
            issue_data = {
                'priority': issue.get('priority'),
                'confidence': issue.get('confidence'),
                'title': issue.find('title').text if issue.find('title') is not None else '',
                'description': issue.find('description').text if issue.find('description') is not None else '',
                'legal_basis': {
                    'california': [],
                    'federal': []
                },
                'required_language': [],
                'sample_policies': []
            }
            
            # Parse legal basis
            for ca_code in issue.findall('.//california_code'):
                issue_data['legal_basis']['california'].append({
                    'citation': ca_code.find('citation').text if ca_code.find('citation') is not None else '',
                    'text': ca_code.find('text').text if ca_code.find('text') is not None else '',
                    'effective_date': ca_code.find('effective_date').text if ca_code.find('effective_date') is not None else ''
                })
            
            for fed_code in issue.findall('.//federal_code'):
                issue_data['legal_basis']['federal'].append({
                    'citation': fed_code.find('citation').text if fed_code.find('citation') is not None else '',
                    'text': fed_code.find('text').text if fed_code.find('text') is not None else ''
                })
            
            # Parse required language
            for req_lang in issue.findall('.//required_language'):
                issue_data['required_language'].append({
                    'source': req_lang.find('source').text if req_lang.find('source') is not None else '',
                    'text': req_lang.find('text').text if req_lang.find('text') is not None else ''
                })
            
            # Parse sample policies
            for sample in issue.findall('.//sample_policies/policy'):
                issue_data['sample_policies'].append({
                    'district': sample.get('district'),
                    'code': sample.get('code'),
                    'date': sample.get('date'),
                    'text': sample.find('text').text if sample.find('text') is not None else ''
                })
            
            report['issues'].append(issue_data)
        
        # Parse recommended actions
        for action in root.findall('.//recommended_actions/action'):
            report['actions'].append({
                'priority': action.get('priority'),
                'description': action.find('description').text if action.find('description') is not None else '',
                'location': action.find('location').text if action.find('location') is not None else ''
            })
        
        return report
        
    except Exception as e:
        return {'error': f"Failed to parse XML: {str(e)}", 'raw': xml_response}

def generate_update_report(policy_code, policy_title, report_data):
    """Generate a human-readable update report with specific recommendations"""
    output = f"\n{'='*80}\n"
    output += f"COMPLIANCE UPDATE REPORT: Policy {policy_code} - {policy_title}\n"
    output += f"{'='*80}\n\n"
    
    # Material Issues
    material_issues = [i for i in report_data.get('issues', []) if i.get('priority') == 'MATERIAL']
    if material_issues:
        output += f"MATERIAL COMPLIANCE ISSUES ({len(material_issues)} found):\n"
        output += "-" * 40 + "\n\n"
        
        for idx, issue in enumerate(material_issues, 1):
            output += f"{idx}. {issue['title']} (Confidence: {issue['confidence']}%)\n\n"
            output += f"   Description: {issue['description']}\n\n"
            
            # Legal citations
            output += "   Legal Requirements:\n"
            for ca_code in issue['legal_basis']['california']:
                output += f"   - CA {ca_code['citation']}: \"{ca_code['text']}\"\n"
                if ca_code['effective_date']:
                    output += f"     (Effective: {ca_code['effective_date']})\n"
            
            for fed_code in issue['legal_basis']['federal']:
                output += f"   - Federal {fed_code['citation']}: \"{fed_code['text']}\"\n"
            
            output += "\n"
            
            # Required language
            if issue['required_language']:
                output += "   Required Language:\n"
                for req in issue['required_language']:
                    output += f"   Per {req['source']}:\n"
                    output += f"   \"{req['text']}\"\n\n"
            
            # Sample policies
            if issue['sample_policies']:
                output += "   Sample Policy Language:\n"
                for sample in issue['sample_policies']:
                    output += f"   From {sample['district']} ({sample['code']}, {sample['date']}):\n"
                    output += f"   \"{sample['text']}\"\n\n"
            
            output += "\n"
    
    # Recommended Actions
    if report_data.get('actions'):
        output += "\nRECOMMENDED ACTIONS (in priority order):\n"
        output += "-" * 40 + "\n\n"
        
        for action in sorted(report_data['actions'], key=lambda x: x.get('priority', '999')):
            output += f"{action['priority']}. {action['description']}\n"
            output += f"   Location: {action['location']}\n\n"
    
    return output

def main():
    # Test on policy 3550
    test_file = "extracted_policies_all/policies/3550.txt"
    
    if not os.path.exists(test_file):
        print(f"Test file not found: {test_file}")
        return
    
    print(f"Testing structured compliance check on: {test_file}")
    
    # Parse policy to XML
    policy_xml, code, title, last_reviewed = parse_policy_to_xml(test_file)
    
    # Check compliance with structured output
    xml_response = check_compliance_structured(policy_xml, code, title, last_reviewed)
    
    # Parse the structured response
    report_data = parse_compliance_report(xml_response)
    
    # Generate human-readable report
    update_report = generate_update_report(code, title, report_data)
    print(update_report)
    
    # Save structured data for programmatic use
    with open(f'compliance_report_{code}.json', 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\nStructured report saved to: compliance_report_{code}.json")

if __name__ == "__main__":
    main()