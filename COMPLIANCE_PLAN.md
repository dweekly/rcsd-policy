# RCSD Policy Compliance Checking - Architecture & Plan

## Overview

This document outlines the architecture and implementation plan for Phase 2: automated compliance checking of RCSD policies against California Education Code using Claude API with web search capabilities.

## Goals

1. **Identify Material Non-Compliance**: Flag policies that materially conflict with current CA Education Code
2. **Identify Minor Issues**: Note typos, outdated references, or formatting errors
3. **Prioritize by Risk**: Focus on older policies (>10 years) that are more likely to be outdated
4. **Maintain Legal Accuracy**: Avoid stylistic suggestions since policy language is often legally mandated

## Proposed Architecture

### 1. High-Level Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Extracted Docs  │────▶│ Priority Filter  │────▶│ Document Parser │
│ (Text Files)    │     │ (Age-based)      │     │ (Structured)    │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                           │
                        ┌──────────────────┐               │
                        │ Compliance Report│◀──────────────┤
                        │ (JSON/Markdown)  │               │
                        └──────────────────┘               │
                                                           ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │  Claude API      │◀────│ Prompt Builder  │
                        │  + Web Search    │     │ (Context-aware) │
                        └──────────────────┘     └─────────────────┘
```

### 2. Component Design

#### A. Priority Filter (`compliance_filter.py`)
- Skip policies updated in 2024 or later (assumed compliant)
- Prioritize policies >10 years old
- Create ordered queue based on:
  - Last review date
  - Policy type (regulations may change more than policies)
  - Series (e.g., 4000/5000 series on personnel/students are high priority)

#### B. Document Parser (`policy_parser_structured.py`)
- Convert plain text to structured pseudo-XML format
- Extract key sections:
  ```xml
  <policy>
    <metadata>
      <code>3550</code>
      <type>Policy</type>
      <title>Food Service/Child Nutrition Program</title>
      <adopted>1996-03-26</adopted>
      <last_reviewed>2017-10-24</last_reviewed>
      <source>RCSD Policies 3000.pdf</source>
    </metadata>
    <content>
      <main_text>
        The Board of Trustees recognizes that adequate nourishment is essential...
      </main_text>
      <legal_references>
        <state_references>
          <reference>Education Code 49430-49436</reference>
          <reference>Education Code 49490-49494</reference>
        </state_references>
        <federal_references>
          <reference>42 USC 1751-1769</reference>
        </federal_references>
        <code_of_regulations>
          <reference>7 CFR 210.1-210.31</reference>
        </code_of_regulations>
      </legal_references>
      <cross_references>
        <policy_ref>3551</policy_ref>
        <policy_ref>3553</policy_ref>
      </cross_references>
      <csba_reference>CSBA 10/16</csba_reference>
    </content>
  </policy>
  ```

#### C. Prompt Builder (`compliance_prompter.py`)
- Create focused, context-aware prompts for Claude
- Include relevant metadata (age, type, subject)
- Structure prompt to focus on:
  1. Material compliance issues only
  2. Confidence level required for flagging
  3. Specific Ed Code sections to check
- Example prompt structure:
  ```
  You are reviewing a school district policy for compliance with current California Education Code.
  
  Policy: [Code] - [Title]
  Last Updated: [Date] (X years ago)
  Type: [Policy/Regulation]
  
  The policy text is provided below. Please:
  1. Check for MATERIAL non-compliance with current CA Ed Code (as of 2025)
  2. Only flag issues you are HIGHLY CONFIDENT about
  3. Note any typos or minor errors
  4. DO NOT suggest stylistic improvements - focus only on legal compliance
  
  Use web search to verify current Ed Code requirements if needed.
  
  <policy_document>
  [Structured XML Policy Content]
  </policy_document>
  ```

#### D. API Client (`claude_client.py`)
- Handle Claude API authentication and rate limiting
- Implement retry logic with exponential backoff
- Cost tracking and budgeting
- Response parsing and validation
- Batch processing capabilities

#### E. Report Generator (`compliance_reporter.py`)
- Aggregate findings by severity
- Generate reports in multiple formats:
  - JSON for programmatic access
  - Markdown for human review
  - Excel summary for administrators
- Include:
  - Policy details
  - Issues found with confidence levels
  - Specific Ed Code citations
  - Suggested priority for review

### 3. Data Model

```python
class ComplianceIssue:
    policy_code: str
    issue_type: Literal["MATERIAL", "MINOR"]
    description: str
    confidence: float  # 0.0 to 1.0
    ed_code_reference: Optional[str]
    current_text: str
    notes: Optional[str]

class ComplianceReport:
    policy: PolicyMetadata
    check_date: datetime
    issues: List[ComplianceIssue]
    api_cost: float
    processing_time: float
```

## Implementation Plan

### Phase 1: Infrastructure (Week 1)
1. Set up project structure and configuration
2. Implement Claude API client with rate limiting
3. Create structured parser for policies
4. Add environment configuration (.env, .env.example)

### Phase 2: Core Logic (Week 2)
1. Build priority filtering system
2. Develop prompt engineering templates
3. Implement batch processing pipeline
4. Add cost tracking and budgeting

### Phase 3: Reporting (Week 3)
1. Create report generation system
2. Build issue aggregation logic
3. Implement multiple output formats
4. Add progress tracking and logging

### Phase 4: Testing & Refinement (Week 4)
1. Test with sample policies of different ages
2. Tune confidence thresholds
3. Optimize prompts for accuracy
4. Document findings and patterns

## Critique of Original Plan & Improvements

### Strengths of Original Plan
1. ✅ Focus on material issues (avoids noise)
2. ✅ Age-based prioritization (smart resource allocation)
3. ✅ Avoids stylistic suggestions (respects legal constraints)
4. ✅ Uses web search for current Ed Code verification

### Suggested Improvements

1. **Batch Processing**: Instead of one-by-one, batch similar policies for efficiency
2. **Caching Layer**: Cache Ed Code lookups to reduce API calls
3. **Human-in-the-Loop**: Flag low-confidence issues for human review
4. **Change Detection**: Compare against previous compliance checks
5. **Cost Controls**: Implement spending limits and cost projections
6. **Progressive Enhancement**: Start with highest-risk policies, stop when budget exhausted
7. **Citation Validation**: Cross-reference found issues with CSBA advisories
8. **XML Format**: Use pseudo-XML instead of JSON for better Claude performance
9. **Model Flexibility**: Make the AI model configurable via environment variables

### Alternative Approach: Hybrid System

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Static Analysis │────▶│ Risk Scoring     │────▶│ AI Deep Dive    │
│ (Rule-based)    │     │ (Multiple factors)│     │ (High-risk only)│
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

Benefits:
- Reduce API costs by pre-filtering with static rules
- Focus expensive AI analysis on highest-risk policies
- Build knowledge base of common issues

## Cost Estimation

Assuming:
- ~500 policies to check
- Skip ~100 recent policies (2024+)
- Average 2,000 tokens per policy
- Claude 4 Sonnet pricing: ~$3/million input tokens, $15/million output tokens

Estimated costs:
- Input: 400 policies × 3,000 tokens = 1.2M tokens = ~$3.60
- Output: 400 policies × 500 tokens = 200K tokens = ~$3.00
- Total: ~$6.60 + margin for retries = ~$10-15

Note: Costs may vary based on the selected model (configurable via ANTHROPIC_MODEL)

## Configuration

### Environment Variables
```
ANTHROPIC_API_KEY=your-api-key-here
ANTHROPIC_MODEL=claude-4-sonnet-20250514
COMPLIANCE_BUDGET_USD=20.00
COMPLIANCE_BATCH_SIZE=10
COMPLIANCE_MAX_RETRIES=3
COMPLIANCE_CONFIDENCE_THRESHOLD=0.8
```

### Priority Weights
```
AGE_WEIGHT=0.5
SERIES_WEIGHT=0.3
TYPE_WEIGHT=0.2
```

## Risk Mitigation

1. **False Positives**: High confidence threshold + human review
2. **API Costs**: Budget limits + batch processing
3. **Rate Limits**: Exponential backoff + queue management
4. **Data Privacy**: All policies are public documents
5. **Legal Liability**: Clear disclaimers about non-authoritative nature

## Success Metrics

1. **Coverage**: % of high-risk policies analyzed
2. **Accuracy**: Validation of findings against manual review
3. **Cost Efficiency**: Cost per material issue found
4. **Time Saved**: vs. manual compliance review
5. **Actionability**: % of findings resulting in policy updates

## Next Steps

1. Review and refine this plan
2. Set up development environment
3. Implement MVP with 5-10 test policies
4. Iterate based on initial results
5. Scale to full policy set

## Conclusion

This architecture balances thoroughness with cost-effectiveness, focusing AI resources on highest-risk policies while maintaining high confidence standards for compliance findings. The system is designed to augment, not replace, human compliance review.