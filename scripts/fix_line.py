#!/usr/bin/env python3
"""Fix the broken string ending: "', this.checked)">"' → "', this.checked)" + '>'"""
path = '/root/inventree-source/InvenTree-master/src/backend/parametric_bom/templates/parametric_bom/configurator.html'

with open(path, 'r') as f:
    c = f.read()

# The broken pattern at end of line:
# + m.key + "\', this.checked)">"'
# Should be:
# + m.key + "', this.checked)" + '>'

import re
# Find the pattern: "+ m.key + "\\', this.checked)">"'
# In the raw file, this is: + m.key + "\', this.checked)">"'
old = '+ m.key + "\\\', this.checked)">"\''
new = '+ m.key + "\', this.checked)" + \'>\''

count = c.count(old)
if count > 0:
    c = c.replace(old, new)
    print(f"Fixed {count} occurrence(s)")
    with open(path, 'w') as f:
        f.write(c)
else:
    print("Pattern not found")
    # Try to find similar
    idx = c.find("+ m.key + ")
    while idx >= 0:
        end = c.find('\n', idx)
        snippet = c[idx:end]
        if 'this.checked' in snippet:
            print(f"Found at {idx}: {repr(snippet)}")
        idx = c.find("+ m.key + ", idx + 1)
        if idx > 0:
            break
