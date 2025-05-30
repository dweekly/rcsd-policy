#!/usr/bin/env python3
"""
Test compliance check on a specific policy
"""

import sys
import os
from compliance_check_structured import (
    parse_policy_to_xml,
    check_compliance_structured,
    parse_compliance_report,
    generate_update_report
)

def main():
    if len(sys.argv) > 1:
        policy_file = sys.argv[1]
    else:
        policy_file = "extracted_policies_all/policies/5131.4.txt"
    
    if not os.path.exists(policy_file):
        print(f"Error: File not found: {policy_file}")
        return
    
    print(f"Running compliance check on: {policy_file}")
    
    # Parse policy to XML
    policy_xml, code, title, last_reviewed = parse_policy_to_xml(policy_file)
    
    print(f"\nPolicy {code}: {title}")
    print(f"Last reviewed: {last_reviewed}")
    print("-" * 80)
    
    # Check compliance
    xml_response = check_compliance_structured(policy_xml, code, title, last_reviewed)
    
    # Parse response
    report_data = parse_compliance_report(xml_response)
    
    # Generate human-readable report
    update_report = generate_update_report(code, title, report_data)
    print(update_report)
    
    # Save for review
    import json
    with open(f'test_compliance_{code}.json', 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\nStructured data saved to: test_compliance_{code}.json")

if __name__ == "__main__":
    main()