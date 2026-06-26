#!/usr/bin/env python3
"""Fix the quote escaping in loadBomFormulaConfigs - replace only the broken lines."""
import re

path = '/root/inventree-source/InvenTree-master/src/backend/parametric_bom/templates/parametric_bom/configurator.html'
with open(path, 'r') as f:
    content = f.read()

# Fix 1: The toggleHtml checkbox - lines containing the broken onchange pattern
# Old: ' onchange=\"onBomModeToggle(' + item.pk + \", '\" + m.key + \"', this.checked)\">\"'
# New: ' onchange="onBomModeToggle(' + item.pk + ", '" + m.key + "', this.checked)" + '>'

# Actually the simplest approach: find and fix the pattern directly
# Pattern 1: onchange in toggleHtml checkbox
old = "' onchange=\\\"onBomModeToggle(' + item.pk + \\\", '\\\" + m.key + \\\"', this.checked)\\\">\\\"'"
new = "' onchange=\"onBomModeToggle(' + item.pk + \", '\" + m.key + \"', this.checked)\" + '>'"

# Try to replace it
count = content.count(old)
if count > 0:
    content = content.replace(old, new)
    print(f"Replaced {count} occurrences of pattern 1")
else:
    print("Pattern 1 not found, trying alternative...")
    # The actual content might be different. Let me check what's actually there
    idx = content.find('onchange=\\\"onBomModeToggle(')
    if idx >= 0:
        print(f"Found at position {idx}")
        print(repr(content[idx:idx+80]))
    else:
        print("Could not find the pattern either")

# Pattern 2: resetBomConfig button
old2 = "\\\", '\\\" + subPartName.replace(/'/g,\\\"\\\\'\\\") + \\\"')\"
>↩️ 重置</button>\""
new2 = "\", '" + " + subPartName.replace(/'/g,\"\\\\'\") + " + "')" + '>↩️ 重置</button>'

with open(path, 'w') as f:
    f.write(content)
print("File written")
