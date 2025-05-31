#!/usr/bin/env python3
"""
Policy Research Module for RCSD Policy Compliance Analyzer
Analyzes extracted policies and performs research on compliance requirements
"""

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd


@dataclass
class PolicyResearch:
    """Research findings for a single policy"""

    policy_code: str
    policy_title: str
    ca_ed_code_references: List[str]
    federal_law_references: List[str]
    csba_alignment: str
    key_compliance_areas: List[str]
    potential_issues: List[str]
    recommendations: List[str]
    research_date: str

    def to_dict(self) -> Dict:
        return asdict(self)


class PolicyResearcher:
    """Researches policies for compliance with CA Ed Code and best practices"""

    def __init__(self):
        self.research_results: List[PolicyResearch] = []

        # California Education Code patterns
        self.ed_code_pattern = re.compile(
            r"(?:Education Code|Ed\.?\s*Code|EC)\s*(?:Section\s*)?(\d{3,5}(?:\.\d+)?(?:\s*-\s*\d{3,5}(?:\.\d+)?)?)",
            re.IGNORECASE,
        )

        # Federal law patterns
        self.federal_patterns = {
            "title_ix": re.compile(r"Title\s+IX|Title\s+9", re.IGNORECASE),
            "idea": re.compile(
                r"IDEA|Individuals with Disabilities Education Act", re.IGNORECASE
            ),
            "ferpa": re.compile(
                r"FERPA|Family Educational Rights and Privacy Act", re.IGNORECASE
            ),
            "section_504": re.compile(r"Section\s+504|504\s+Plan", re.IGNORECASE),
            "ada": re.compile(r"ADA|Americans with Disabilities Act", re.IGNORECASE),
            "title_vi": re.compile(r"Title\s+VI|Title\s+6", re.IGNORECASE),
            "title_vii": re.compile(r"Title\s+VII|Title\s+7", re.IGNORECASE),
        }

        # Key compliance areas by policy code range
        self.compliance_areas = {
            "0000-0999": [
                "Board Governance",
                "District Organization",
                "School Accountability",
            ],
            "1000-1999": ["Community Relations", "Parent Involvement", "Complaints"],
            "2000-2999": ["Administration", "Superintendent", "Management Systems"],
            "3000-3999": [
                "Business Operations",
                "Facilities",
                "Safety",
                "Transportation",
            ],
            "4000-4999": ["Personnel", "Employee Relations", "Credentialing"],
            "5000-5999": ["Students", "Attendance", "Discipline", "Rights"],
            "6000-6999": ["Instruction", "Curriculum", "Special Education"],
            "7000-7999": ["Facilities", "Construction", "Maintenance"],
            "9000-9999": ["Board Bylaws", "Board Operations", "Ethics"],
        }

        # Common compliance issues to check
        self.compliance_checks = {
            "outdated_references": self._check_outdated_references,
            "missing_mandates": self._check_missing_mandates,
            "procedural_gaps": self._check_procedural_gaps,
            "timeline_requirements": self._check_timeline_requirements,
            "notification_requirements": self._check_notification_requirements,
        }

    def research_policies(
        self, policies_file: str = "extracted_policies.json"
    ) -> List[PolicyResearch]:
        """Research all extracted policies"""
        with open(policies_file, encoding="utf-8") as f:
            data = json.load(f)

        policies = data.get("policies", [])
        print(f"Researching {len(policies)} policies...")

        for policy in policies:
            research = self._research_single_policy(policy)
            if research:
                self.research_results.append(research)

        return self.research_results

    def _research_single_policy(self, policy: Dict) -> Optional[PolicyResearch]:
        """Research a single policy"""
        code = policy.get("policy_code", "")
        title = policy.get("title", "")
        content = policy.get("content", "")

        if not code or not content:
            return None

        # Extract legal references
        ca_ed_codes = self._extract_ed_code_references(content)
        federal_refs = self._extract_federal_references(content)

        # Determine compliance areas
        compliance_areas = self._get_compliance_areas(code)

        # Check for potential issues
        potential_issues = self._check_compliance_issues(code, content)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            code, content, potential_issues
        )

        # CSBA alignment check
        csba_alignment = self._check_csba_alignment(code, content)

        research = PolicyResearch(
            policy_code=code,
            policy_title=title,
            ca_ed_code_references=ca_ed_codes,
            federal_law_references=federal_refs,
            csba_alignment=csba_alignment,
            key_compliance_areas=compliance_areas,
            potential_issues=potential_issues,
            recommendations=recommendations,
            research_date=datetime.now().isoformat(),
        )

        return research

    def _extract_ed_code_references(self, content: str) -> List[str]:
        """Extract California Education Code references"""
        matches = self.ed_code_pattern.findall(content)
        return list(set(matches))  # Remove duplicates

    def _extract_federal_references(self, content: str) -> List[str]:
        """Extract federal law references"""
        references = []
        for law_name, pattern in self.federal_patterns.items():
            if pattern.search(content):
                references.append(law_name.upper().replace("_", " "))
        return references

    def _get_compliance_areas(self, policy_code: str) -> List[str]:
        """Get compliance areas based on policy code"""
        try:
            code_num = int(policy_code.split(".")[0])
            for range_str, areas in self.compliance_areas.items():
                start, end = map(int, range_str.split("-"))
                if start <= code_num <= end:
                    return areas
        except:
            pass
        return ["General Compliance"]

    def _check_compliance_issues(self, code: str, content: str) -> List[str]:
        """Check for potential compliance issues"""
        issues = []

        for check_name, check_func in self.compliance_checks.items():
            issue = check_func(code, content)
            if issue:
                issues.append(issue)

        return issues

    def _check_outdated_references(self, code: str, content: str) -> Optional[str]:
        """Check for outdated legal references"""
        # Look for years in references
        year_pattern = re.compile(r"\b(19\d{2}|20[0-1]\d)\b")
        years = year_pattern.findall(content)

        outdated_years = [y for y in years if int(y) < 2020]
        if outdated_years:
            return (
                f"Contains potentially outdated references from {min(outdated_years)}"
            )

        return None

    def _check_missing_mandates(self, code: str, content: str) -> Optional[str]:
        """Check for missing mandated elements"""
        # Check specific policy requirements
        if code.startswith("1312") and "uniform complaint" in content.lower():
            if "timeline" not in content.lower():
                return "Uniform complaint policy may be missing required timelines"

        if code.startswith("5141") and "health" in content.lower():
            if "medication" not in content.lower():
                return (
                    "Health policy may be missing medication administration procedures"
                )

        return None

    def _check_procedural_gaps(self, code: str, content: str) -> Optional[str]:
        """Check for procedural gaps"""
        procedure_keywords = ["shall", "must", "will", "procedure", "process"]
        has_procedures = any(
            keyword in content.lower() for keyword in procedure_keywords
        )

        if not has_procedures:
            return "Policy lacks clear procedural language"

        return None

    def _check_timeline_requirements(self, code: str, content: str) -> Optional[str]:
        """Check for timeline requirements"""
        timeline_keywords = ["days", "weeks", "timeline", "deadline", "within"]

        # Policies that typically require timelines
        timeline_required_codes = ["1312", "4117", "4217", "5144", "5145"]

        if any(code.startswith(req) for req in timeline_required_codes):
            if not any(keyword in content.lower() for keyword in timeline_keywords):
                return "Policy may be missing required timelines"

        return None

    def _check_notification_requirements(
        self, code: str, content: str
    ) -> Optional[str]:
        """Check for notification requirements"""
        notification_keywords = ["notify", "notification", "inform", "notice"]

        # Policies that typically require notifications
        notification_required_codes = ["5145", "5116", "6164", "1312"]

        if any(code.startswith(req) for req in notification_required_codes):
            if not any(keyword in content.lower() for keyword in notification_keywords):
                return "Policy may be missing required notification procedures"

        return None

    def _generate_recommendations(
        self, code: str, content: str, issues: List[str]
    ) -> List[str]:
        """Generate recommendations based on findings"""
        recommendations = []

        if issues:
            recommendations.append(
                "Review and update policy to address identified compliance issues"
            )

        # Check for missing legal references
        if not self._extract_ed_code_references(content):
            recommendations.append("Add relevant California Education Code references")

        # Check policy age indicators
        if "adopted" in content.lower():
            date_pattern = re.compile(
                r"adopted.*?(\d{1,2}/\d{1,2}/\d{4})", re.IGNORECASE
            )
            match = date_pattern.search(content)
            if match:
                date_str = match.group(1)
                try:
                    adopted_date = datetime.strptime(date_str, "%m/%d/%Y")
                    if (datetime.now() - adopted_date).days > 1825:  # 5 years
                        recommendations.append(
                            "Policy is over 5 years old - consider comprehensive review"
                        )
                except:
                    pass

        # Specific recommendations by policy area
        if code.startswith("3"):
            recommendations.append(
                "Ensure business procedures align with current fiscal requirements"
            )
        elif code.startswith("5"):
            recommendations.append(
                "Verify student policies comply with current due process requirements"
            )
        elif code.startswith("6"):
            recommendations.append(
                "Check instructional policies against current state standards"
            )

        return recommendations

    def _check_csba_alignment(self, code: str, content: str) -> str:
        """Check alignment with CSBA best practices"""
        csba_indicators = [
            "csba",
            "california school boards association",
            "best practice",
        ]

        if any(indicator in content.lower() for indicator in csba_indicators):
            return "References CSBA guidance"

        # Check for comprehensive policy elements
        elements = {
            "purpose": any(
                word in content.lower() for word in ["purpose", "intent", "goal"]
            ),
            "definitions": "definition" in content.lower()
            or "means" in content.lower(),
            "procedures": "procedure" in content.lower()
            or "process" in content.lower(),
            "responsibilities": "responsib" in content.lower()
            or "shall" in content.lower(),
        }

        score = sum(elements.values())
        if score >= 3:
            return "Well-structured policy with key elements"
        elif score >= 2:
            return "Partially aligned with best practices"
        else:
            return "May benefit from CSBA template review"

    def save_research_results(self, output_file: str = "policy_research.json") -> None:
        """Save research results to JSON"""
        data = {
            "research_date": datetime.now().isoformat(),
            "total_policies_researched": len(self.research_results),
            "research_results": [r.to_dict() for r in self.research_results],
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(
            f"\nSaved research for {len(self.research_results)} policies to {output_file}"
        )

    def export_research_summary(
        self, output_file: str = "research_summary.xlsx"
    ) -> None:
        """Export research summary to Excel"""
        if not self.research_results:
            print("No research results to export")
            return

        # Create summary dataframe
        summary_data = []
        for research in self.research_results:
            summary_data.append(
                {
                    "Policy Code": research.policy_code,
                    "Title": research.policy_title,
                    "CA Ed Code Refs": len(research.ca_ed_code_references),
                    "Federal Law Refs": len(research.federal_law_references),
                    "CSBA Alignment": research.csba_alignment,
                    "Compliance Areas": ", ".join(research.key_compliance_areas),
                    "Issues Found": len(research.potential_issues),
                    "Issue Details": "; ".join(research.potential_issues)
                    if research.potential_issues
                    else "None",
                    "Recommendations": len(research.recommendations),
                }
            )

        df = pd.DataFrame(summary_data)
        df.to_excel(output_file, index=False, engine="openpyxl")

        print(f"Exported research summary to {output_file}")


def main():
    """Test the policy researcher"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Research extracted policies for compliance"
    )
    parser.add_argument(
        "--input",
        default="extracted_policies.json",
        help="Input JSON file with extracted policies",
    )
    parser.add_argument(
        "--output",
        default="policy_research.json",
        help="Output JSON file for research results",
    )
    parser.add_argument(
        "--excel", action="store_true", help="Also export Excel summary"
    )

    args = parser.parse_args()

    researcher = PolicyResearcher()
    researcher.research_policies(args.input)
    researcher.save_research_results(args.output)

    if args.excel:
        researcher.export_research_summary()


if __name__ == "__main__":
    main()
