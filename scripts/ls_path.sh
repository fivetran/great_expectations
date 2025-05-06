#!/bin/bash

# Save the current directory
current_dir=$(pwd)

# Split the PATH variable by ':' and loop through each directory
for dir in $(echo "$PATH" | tr ":" "\n"); do
  # Check if the directory exists
  if [ -d "$dir" ]; then
    echo "Listing contents of: $dir"
    # Change to the directory
    cd "$dir"
    # List all files and directories in the current directory
    ls -la
    echo ""
  else
    echo "Directory not found: $dir"
  fi
  # Change back to the original directory
  cd "$current_dir"
done
