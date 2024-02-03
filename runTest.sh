#!/bin/bash

# Get total RAM in KB
TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
# Calculate 85% of total RAM
LIMIT_KB=$(echo "$TOTAL_RAM_KB * 0.85 / 1" | bc)

# Set the ulimit for virtual memory
ulimit -v "$LIMIT_KB"

# Run your Python script
python3 pyperplan/__main__.py benchmarks/Blocksworld-GTOHP/domain.hddl benchmarks/Blocksworld-GTOHP/p12.hddl -mh TaskDecomposition
