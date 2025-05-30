# Running Compliance Checks

## Quick Start

1. Ensure you have your Anthropic API key configured:
```bash
cp .env.example .env
# Edit .env and add your API key
```

2. Test on a single policy:
```bash
python test_compliance_single.py
```

3. Run batch compliance checks:
```bash
# Check top 10 highest priority policies
python compliance_check_batch.py --max 10

# Check all policies (will take time and use API credits)
python compliance_check_batch.py
```

## Output Structure

The batch processor creates a `compliance_reports/` directory with:

```
compliance_reports/
├── 3550_report.json          # Structured data for each policy
├── 3550_report.txt           # Human-readable report
├── compliance_summary.json   # Summary of all checks
└── executive_summary.txt     # High-level findings
```

## Report Contents

Each policy report includes:

1. **Material Compliance Issues**
   - Specific Education Code violations
   - Federal regulation conflicts
   - Confidence levels (only shows 75%+ confidence)
   - Exact statutory text quoted

2. **Required Language**
   - Specific text that must be added
   - Source statute or regulation

3. **Sample Policy Language**
   - CSBA sample text
   - Examples from other California districts
   - Dates showing currency of samples

4. **Recommended Actions**
   - Prioritized list of changes
   - Specific locations in policy

## Priority Scoring

Policies are prioritized by:
- **Age**: 5 points per year since last review
- **Series**: 4000/5000 (personnel/students) highest priority
- **Keywords**: Nutrition, discrimination, safety, etc. add priority
- **Recent updates**: Skip if updated in 2024 or later

## Cost Considerations

- Each policy check costs approximately $0.02-0.03
- Full corpus (~400 older policies) estimated at $10-15
- API includes rate limiting (2 second delay between calls)

## Interpreting Results

Focus on:
1. **Material issues with 85%+ confidence** - These need immediate attention
2. **Effective dates** - Shows when requirements became law
3. **CSBA samples** - Use exact language where possible
4. **Multiple citations** - Higher confidence when multiple sources agree

## Next Steps

After running compliance checks:

1. Review executive summary for highest-risk policies
2. Work with legal counsel on material issues
3. Use sample language to draft updates
4. Cross-reference with CSBA current policies
5. Present findings to Board with recommended updates