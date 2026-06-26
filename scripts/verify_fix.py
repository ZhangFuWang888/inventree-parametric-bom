#!/usr/bin/env python3
"""Verify the fix and check remaining issues."""
import re

path = '/root/inventree-source/InvenTree-master/src/backend/parametric_bom/templates/parametric_bom/configurator.html'
with open(path, 'rb') as f:
    data = f.read()

# Check for the old broken pattern: )">' followed by newline
old = b')">\'\n'
old_count = data.count(old)
print(f"Old broken pattern ')>\'\\n' found: {old_count} time(s)")

# Check for the new fixed pattern: )" + '>
new = b')" + \'>\'\n'
new_count = data.count(new)
print(f"New fixed pattern found: {new_count} time(s)")

# List all lines with potential issues
lines = data.split(b'\n')
for i, line in enumerate(lines):
    if i < 4915 or i > 4990:
        continue
    # Check for unclosed strings (line ends with ' or " and next line doesn't continue properly)
    if line.rstrip().endswith(b"'") and not line.rstrip().endswith(b"\\'"):
        next_line = lines[i+1] if i+1 < len(lines) else b''
        # Check if next line starts with a concatenation operator
        if not next_line.lstrip().startswith(b'+'):
            print(f"Line {i+1}: POTENTIAL ISSUE - ends with quote, next line doesn't start with +")
            print(f"  {line.decode('utf-8', errors='replace')[:100]}")

print("\nDone")
