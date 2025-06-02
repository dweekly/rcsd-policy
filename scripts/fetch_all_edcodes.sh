#!/bin/bash
# Master script for fetching Ed Code sections
# Generated: 2025-06-02T01:03:22.046676+00:00
# Total batches: 16

# To process a batch:
# 1. Run: python scripts/process_edcode_batch.py <batch_num>
# 2. Execute the WebFetch commands shown
# 3. Move to next batch

echo 'Ed Code Batch Fetching System'
echo '============================='
echo
echo 'Total batches to process: 16'
echo

# Process batches
for i in {0..15}; do
    echo "Processing batch $i..."
    python scripts/process_edcode_batch.py $i
    echo
    echo 'Press Enter to continue to next batch...'
    read
done

echo 'All batches processed!'