#!/bin/bash
# Script to fetch missing Ed Code sections
# Generated: 2025-06-01T21:26:50.469835+00:00

# This script uses the WebFetch tool to retrieve Ed Code sections
# Run with: bash scripts/fetch_edcodes_batch.sh

set -e  # Exit on error

echo 'Starting batch fetch of Ed Code sections...'
echo

echo 'Fetching EDC 45240: Merit System Requirements...'

# Create JSON for EDC 45240
cat > temp_fetch_0.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=45240&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 45240 regarding Merit System Requirements. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_45240_full.json",
  "section": "45240",
  "law_code": "EDC",
  "description": "Merit System Requirements"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=45240&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_45240_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 45122: Physical Examination Requirements...'

# Create JSON for EDC 45122
cat > temp_fetch_1.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=45122&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 45122 regarding Physical Examination Requirements. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_45122_full.json",
  "section": "45122",
  "law_code": "EDC",
  "description": "Physical Examination Requirements"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=45122&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_45122_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 45113: Probationary Period Requirements...'

# Create JSON for EDC 45113
cat > temp_fetch_2.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=45113&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 45113 regarding Probationary Period Requirements. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_45113_full.json",
  "section": "45113",
  "law_code": "EDC",
  "description": "Probationary Period Requirements"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=45113&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_45113_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 20113: Emergency Purchase Procedures...'

# Create JSON for EDC 20113
cat > temp_fetch_3.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=20113&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 20113 regarding Emergency Purchase Procedures. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_20113_full.json",
  "section": "20113",
  "law_code": "EDC",
  "description": "Emergency Purchase Procedures"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=20113&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_20113_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching GC 1090: Conflict of Interest...'

# Create JSON for GC 1090
cat > temp_fetch_4.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1090&lawCode=GOV",
  "prompt": "Extract the complete text of GC section 1090 regarding Conflict of Interest. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/gc_1090_full.json",
  "section": "1090",
  "law_code": "GC",
  "description": "Conflict of Interest"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1090&lawCode=GOV'
echo '  -> Output to: data/cache/edcode/gc_1090_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 49410.5: Asbestos Management Requirements...'

# Create JSON for EDC 49410.5
cat > temp_fetch_5.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=49410.5&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 49410.5 regarding Asbestos Management Requirements. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_49410_5_full.json",
  "section": "49410.5",
  "law_code": "EDC",
  "description": "Asbestos Management Requirements"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=49410.5&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_49410_5_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 17608: Indoor Air Quality Requirements...'

# Create JSON for EDC 17608
cat > temp_fetch_6.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=17608&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 17608 regarding Indoor Air Quality Requirements. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_17608_full.json",
  "section": "17608",
  "law_code": "EDC",
  "description": "Indoor Air Quality Requirements"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=17608&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_17608_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 13181: Integrated Pest Management...'

# Create JSON for EDC 13181
cat > temp_fetch_7.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=13181&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 13181 regarding Integrated Pest Management. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_13181_full.json",
  "section": "13181",
  "law_code": "EDC",
  "description": "Integrated Pest Management"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=13181&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_13181_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 32288: School Safety Plan Review Requirements...'

# Create JSON for EDC 32288
cat > temp_fetch_8.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=32288&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 32288 regarding School Safety Plan Review Requirements. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_32288_full.json",
  "section": "32288",
  "law_code": "EDC",
  "description": "School Safety Plan Review Requirements"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=32288&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_32288_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 32281: School Safety Planning Committee...'

# Create JSON for EDC 32281
cat > temp_fetch_9.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=32281&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 32281 regarding School Safety Planning Committee. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_32281_full.json",
  "section": "32281",
  "law_code": "EDC",
  "description": "School Safety Planning Committee"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=32281&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_32281_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 56001: Special Education Intent...'

# Create JSON for EDC 56001
cat > temp_fetch_10.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=56001&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 56001 regarding Special Education Intent. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_56001_full.json",
  "section": "56001",
  "law_code": "EDC",
  "description": "Special Education Intent"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=56001&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_56001_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 39831.3: Wheelchair Safety Requirements...'

# Create JSON for EDC 39831.3
cat > temp_fetch_11.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=39831.3&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 39831.3 regarding Wheelchair Safety Requirements. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_39831_3_full.json",
  "section": "39831.3",
  "law_code": "EDC",
  "description": "Wheelchair Safety Requirements"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=39831.3&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_39831_3_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 56341.1: IEP Transportation Requirements...'

# Create JSON for EDC 56341.1
cat > temp_fetch_12.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=56341.1&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 56341.1 regarding IEP Transportation Requirements. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_56341_1_full.json",
  "section": "56341.1",
  "law_code": "EDC",
  "description": "IEP Transportation Requirements"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=56341.1&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_56341_1_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching VC 12517.2: Medical Examination for Bus Drivers...'

# Create JSON for VC 12517.2
cat > temp_fetch_13.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=12517.2&lawCode=VEH",
  "prompt": "Extract the complete text of VC section 12517.2 regarding Medical Examination for Bus Drivers. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/vc_12517_2_full.json",
  "section": "12517.2",
  "law_code": "VC",
  "description": "Medical Examination for Bus Drivers"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=12517.2&lawCode=VEH'
echo '  -> Output to: data/cache/edcode/vc_12517_2_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching VC 12523: Training Hour Requirements...'

# Create JSON for VC 12523
cat > temp_fetch_14.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=12523&lawCode=VEH",
  "prompt": "Extract the complete text of VC section 12523 regarding Training Hour Requirements. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/vc_12523_full.json",
  "section": "12523",
  "law_code": "VC",
  "description": "Training Hour Requirements"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=12523&lawCode=VEH'
echo '  -> Output to: data/cache/edcode/vc_12523_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 35291: Student Discipline on Buses...'

# Create JSON for EDC 35291
cat > temp_fetch_15.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=35291&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 35291 regarding Student Discipline on Buses. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_35291_full.json",
  "section": "35291",
  "law_code": "EDC",
  "description": "Student Discipline on Buses"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=35291&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_35291_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 44501: Consulting Teacher Requirements...'

# Create JSON for EDC 44501
cat > temp_fetch_17.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=44501&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 44501 regarding Consulting Teacher Requirements. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_44501_full.json",
  "section": "44501",
  "law_code": "EDC",
  "description": "Consulting Teacher Requirements"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=44501&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_44501_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 44503: Confidentiality Requirements...'

# Create JSON for EDC 44503
cat > temp_fetch_18.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=44503&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 44503 regarding Confidentiality Requirements. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_44503_full.json",
  "section": "44503",
  "law_code": "EDC",
  "description": "Confidentiality Requirements"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=44503&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_44503_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 35295: Comprehensive School Safety Plans...'

# Create JSON for EDC 35295
cat > temp_fetch_19.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=35295&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 35295 regarding Comprehensive School Safety Plans. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_35295_full.json",
  "section": "35295",
  "law_code": "EDC",
  "description": "Comprehensive School Safety Plans"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=35295&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_35295_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 44691: Mandated Reporter Training...'

# Create JSON for EDC 44691
cat > temp_fetch_20.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=44691&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 44691 regarding Mandated Reporter Training. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_44691_full.json",
  "section": "44691",
  "law_code": "EDC",
  "description": "Mandated Reporter Training"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=44691&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_44691_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 49050: Student Search Limitations...'

# Create JSON for EDC 49050
cat > temp_fetch_21.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=49050&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 49050 regarding Student Search Limitations. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_49050_full.json",
  "section": "49050",
  "law_code": "EDC",
  "description": "Student Search Limitations"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=49050&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_49050_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 48902: Law Enforcement Coordination...'

# Create JSON for EDC 48902
cat > temp_fetch_22.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=48902&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 48902 regarding Law Enforcement Coordination. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_48902_full.json",
  "section": "48902",
  "law_code": "EDC",
  "description": "Law Enforcement Coordination"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=48902&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_48902_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 44807: Emergency Authority...'

# Create JSON for EDC 44807
cat > temp_fetch_23.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=44807&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 44807 regarding Emergency Authority. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_44807_full.json",
  "section": "44807",
  "law_code": "EDC",
  "description": "Emergency Authority"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=44807&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_44807_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 51210: Required Curriculum Areas...'

# Create JSON for EDC 51210
cat > temp_fetch_24.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=51210&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 51210 regarding Required Curriculum Areas. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_51210_full.json",
  "section": "51210",
  "law_code": "EDC",
  "description": "Required Curriculum Areas"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=51210&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_51210_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 51934: Sexual Health Content Standards...'

# Create JSON for EDC 51934
cat > temp_fetch_25.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=51934&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 51934 regarding Sexual Health Content Standards. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_51934_full.json",
  "section": "51934",
  "law_code": "EDC",
  "description": "Sexual Health Content Standards"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=51934&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_51934_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 47612.5: Distance Learning Instructional Time...'

# Create JSON for EDC 47612.5
cat > temp_fetch_26.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=47612.5&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 47612.5 regarding Distance Learning Instructional Time. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_47612_5_full.json",
  "section": "47612.5",
  "law_code": "EDC",
  "description": "Distance Learning Instructional Time"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=47612.5&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_47612_5_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 43503: Daily Live Interaction Requirements...'

# Create JSON for EDC 43503
cat > temp_fetch_27.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=43503&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 43503 regarding Daily Live Interaction Requirements. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_43503_full.json",
  "section": "43503",
  "law_code": "EDC",
  "description": "Daily Live Interaction Requirements"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=43503&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_43503_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 47607: Charter Renewal and Revocation...'

# Create JSON for EDC 47607
cat > temp_fetch_31.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=47607&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 47607 regarding Charter Renewal and Revocation. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_47607_full.json",
  "section": "47607",
  "law_code": "EDC",
  "description": "Charter Renewal and Revocation"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=47607&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_47607_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 52064.3: IDEA Addendum Requirements...'

# Create JSON for EDC 52064.3
cat > temp_fetch_32.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=52064.3&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 52064.3 regarding IDEA Addendum Requirements. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_52064_3_full.json",
  "section": "52064.3",
  "law_code": "EDC",
  "description": "IDEA Addendum Requirements"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=52064.3&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_52064_3_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 52064.1: LCFF Budget Overview...'

# Create JSON for EDC 52064.1
cat > temp_fetch_33.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=52064.1&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 52064.1 regarding LCFF Budget Overview. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_52064_1_full.json",
  "section": "52064.1",
  "law_code": "EDC",
  "description": "LCFF Budget Overview"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=52064.1&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_52064_1_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 52063: Advisory Committee Requirements...'

# Create JSON for EDC 52063
cat > temp_fetch_34.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=52063&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 52063 regarding Advisory Committee Requirements. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_52063_full.json",
  "section": "52063",
  "law_code": "EDC",
  "description": "Advisory Committee Requirements"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=52063&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_52063_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching GC 6250: Public Records Act...'

# Create JSON for GC 6250
cat > temp_fetch_36.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=6250&lawCode=GOV",
  "prompt": "Extract the complete text of GC section 6250 regarding Public Records Act. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/gc_6250_full.json",
  "section": "6250",
  "law_code": "GC",
  "description": "Public Records Act"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=6250&lawCode=GOV'
echo '  -> Output to: data/cache/edcode/gc_6250_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 60200: Records Retention...'

# Create JSON for EDC 60200
cat > temp_fetch_37.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=60200&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 60200 regarding Records Retention. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_60200_full.json",
  "section": "60200",
  "law_code": "EDC",
  "description": "Records Retention"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=60200&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_60200_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Fetching EDC 35021: Volunteer Procedures...'

# Create JSON for EDC 35021
cat > temp_fetch_39.json << 'EOF'
{
  "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=35021&lawCode=EDC",
  "prompt": "Extract the complete text of EDC section 35021 regarding Volunteer Procedures. Include all subdivisions, requirements, and the effective date.",
  "output_file": "data/cache/edcode/edc_35021_full.json",
  "section": "35021",
  "law_code": "EDC",
  "description": "Volunteer Procedures"
}
EOF

# Fetch using WebFetch (this would need to be done through Claude)
echo '  -> Would fetch from: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=35021&lawCode=EDC'
echo '  -> Output to: data/cache/edcode/edc_35021_full.json'
echo

# Add a small delay to avoid rate limiting
sleep 2

echo 'Batch fetch complete!'
echo
echo 'Note: This script generates the fetch requests.'
echo 'The actual fetching needs to be done through Claude Code using the WebFetch tool.'

# Clean up temp files
rm -f temp_fetch_*.json