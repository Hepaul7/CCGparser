#!/bin/bash

output_file="pmb_functions.txt"

# Clear or create the output file
> "$output_file"

# Temporary file to hold all predicates before filtering
temp_file=$(mktemp)

# Loop through all Prolog files
for file in *.ccg; do
    echo "Processing $file..." >> "$output_file"

    # Use grep to extract predicate declarations like ccg/2, fa/2, etc.
    # Adjusted regex to match:
    # - Predicates in op/3, multifile/2, discontiguous/2, and function calls (e.g., ccg/2, fa/2)
    grep -oE '\w+\([0-9]+\)' "$file" >> "$temp_file"

    echo "" >> "$output_file" # Add a blank line between files
done

# Sort and remove duplicates, then save to the output file
sort "$temp_file" | uniq > "$output_file"

# Clean up the temporary file
rm "$temp_file"

echo "Gathered unique predicates have been saved to $output_file."
