#!/usr/bin/env python3
"""
Enhanced compliance checking that examines both policies and their corresponding regulations
"""

import os
import re
import json
from pathlib import Path
from compliance_check_comprehensive import ComplianceChecker

class PolicyRegulationChecker(ComplianceChecker):
    """Extended checker that considers policy/regulation pairs"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.regulation_coverage = {}
    
    def find_matching_regulation(self, policy_code, base_dir='extracted_policies_all'):
        """Find the administrative regulation matching a policy"""
        reg_path = os.path.join(base_dir, 'regulations', f"{policy_code}.txt")
        if os.path.exists(reg_path):
            return reg_path
        return None
    
    def extract_regulation_provisions(self, reg_path, search_terms):
        """Extract key provisions from regulation that might satisfy policy requirements"""
        provisions = []
        
        try:
            with open(reg_path, 'r') as f:
                content = f.read()
            
            # Extract title and last reviewed
            title_match = re.search(r'Title:\s*(.+?)(?:\n|$)', content)
            title = title_match.group(1) if title_match else 'Unknown'
            
            reviewed_match = re.search(r'Last Reviewed Date:\s*(\d{1,2}/\d{1,2}/\d{2,4})', content)
            last_reviewed = reviewed_match.group(1) if reviewed_match else 'Unknown'
            
            provisions.append({
                'type': 'metadata',
                'title': title,
                'last_reviewed': last_reviewed
            })
            
            # Search for each term
            for term in search_terms:
                pattern = re.compile(r'(.{0,100}' + re.escape(term) + r'.{0,200})', re.IGNORECASE | re.DOTALL)
                matches = pattern.findall(content)
                
                for match in matches[:3]:  # Limit to first 3 matches
                    # Clean up the match
                    clean_match = ' '.join(match.split())
                    provisions.append({
                        'type': 'provision',
                        'term': term,
                        'text': clean_match
                    })
            
        except Exception as e:
            print(f"Error reading regulation: {e}")
        
        return provisions
    
    def check_compliance_with_regulation(self, policy_xml, policy_code, policy_title, 
                                       policy_reviewed, related_policies, regulation_provisions):
        """Enhanced compliance check that considers regulation content"""
        
        cache_key = self.get_cache_key(policy_code + "_with_reg", policy_xml, policy_reviewed)
        
        # Check cache
        cached = self.get_cached_response(cache_key)
        if cached:
            return cached
        
        # Build regulation context
        reg_context = ""
        if regulation_provisions:
            reg_meta = next((p for p in regulation_provisions if p['type'] == 'metadata'), None)
            if reg_meta:
                reg_context = f"\n\nIMPORTANT: Administrative Regulation {policy_code} exists"
                reg_context += f"\nTitle: {reg_meta['title']}"
                reg_context += f"\nLast Reviewed: {reg_meta['last_reviewed']}"
                reg_context += "\n\nKey provisions found in the regulation:"
                
                for prov in regulation_provisions:
                    if prov['type'] == 'provision':
                        reg_context += f"\n- {prov['term']}: \"{prov['text'][:200]}...\""
        
        prompt = f"""You are reviewing a California school district policy for compliance.

CRITICAL CONTEXT: School districts typically split requirements between:
- POLICIES: Set board direction and major requirements
- ADMINISTRATIVE REGULATIONS: Provide detailed implementation procedures

Policy: {policy_code} - {policy_title}
Last Updated: {policy_reviewed}
{reg_context}

Related policies: {', '.join(related_policies.keys()) if related_policies else 'None found'}

IMPORTANT INSTRUCTIONS:
1. If an Administrative Regulation exists for this policy code, assume it contains implementation details
2. Only flag as MATERIAL if a legal requirement is missing from BOTH the policy AND its regulation
3. If the regulation appears to cover a requirement, flag it as RESOLVED or MINOR at most
4. Focus on requirements that MUST be in the policy itself (not just the regulation)

<compliance_report>
    <compliance_issues>
        <issue priority="MATERIAL|MINOR|RESOLVED" confidence="[0-100]">
            <title>[Issue Title]</title>
            <description>[Explain why this is an issue considering both documents]</description>
            <regulation_status>[COVERED|PARTIALLY_COVERED|NOT_COVERED|NO_REGULATION]</regulation_status>
            
            <legal_basis>
                <citation>[Code Section]</citation>
                <text>[Legal requirement]</text>
                <requires_in_policy>[true/false - must it be in policy, not just regulation?]</requires_in_policy>
            </legal_basis>
            
            <recommended_action>
                <option>[What to do given regulation coverage]</option>
            </recommended_action>
        </issue>
    </compliance_issues>
</compliance_report>

<policy_document>
{policy_xml}
</policy_document>"""

        print(f"  Calling API with regulation context...")
        self.api_calls_made += 1
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = response.content[0].text
        self.save_cache(cache_key, result)
        
        return result
    
    def process_policy(self, file_path):
        """Process policy with regulation awareness"""
        print(f"\nProcessing: {file_path}")
        
        # Parse policy
        policy_xml, code, title, last_reviewed = self.parse_policy_to_xml(file_path)
        
        # Check for matching regulation
        reg_path = self.find_matching_regulation(code)
        regulation_provisions = []
        
        if reg_path:
            print(f"  Found matching regulation: {reg_path}")
            
            # Extract key search terms based on common compliance areas
            search_terms = [
                'school of origin',
                'immediate', 
                'enrollment',
                'transportation',
                'credit',
                'notice',
                'hearing',
                'timeline',
                'shall provide',
                'shall notify',
                'due process'
            ]
            
            # Add policy-specific terms based on the title
            if 'foster' in title.lower():
                search_terms.extend(['foster youth', 'educational rights', 'liaison'])
            elif 'meal' in title.lower() or 'food' in title.lower():
                search_terms.extend(['free meal', 'universal', 'drinking water'])
            elif 'invest' in title.lower():
                search_terms.extend(['maturity', 'authorized', 'credit quality'])
            
            regulation_provisions = self.extract_regulation_provisions(reg_path, search_terms)
            print(f"  Extracted {len([p for p in regulation_provisions if p['type'] == 'provision'])} key provisions from regulation")
        else:
            print(f"  No matching regulation found")
        
        # Get related policies
        cross_refs = self.extract_cross_references(file_path)
        related = self.find_related_policies(code, cross_refs)
        
        # Check compliance with regulation context
        response = self.check_compliance_with_regulation(
            policy_xml, code, title, last_reviewed, related, regulation_provisions
        )
        
        # Parse and save
        compliance_data = self.parse_compliance_xml(response)
        
        # Count only truly material issues (not resolved by regulation)
        material_count = 0
        for issue in compliance_data.get('issues', []):
            if (issue.get('priority') == 'MATERIAL' and 
                issue.get('regulation_status') != 'COVERED'):
                material_count += 1
        
        policy_data = {
            'code': code,
            'title': title,
            'type': 'Policy' if '/policies/' in file_path else 'Regulation',
            'last_reviewed': last_reviewed,
            'has_regulation': reg_path is not None,
            'file_path': file_path
        }
        
        self.save_results(policy_data, compliance_data)
        
        print(f"  Material issues NOT covered by regulation: {material_count}")
        
        return material_count

def main():
    # Test on the foster youth policy
    checker = PolicyRegulationChecker()
    
    # Process the foster youth policy that we know has a comprehensive regulation
    checker.process_policy('extracted_policies_all/policies/6173.1.txt')
    
    # Also test on one without a regulation
    if os.path.exists('extracted_policies_all/policies/3430.txt'):
        checker.process_policy('extracted_policies_all/policies/3430.txt')

if __name__ == "__main__":
    main()