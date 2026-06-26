#!/usr/bin/env python3
"""Fix quote escaping in loadBomFormulaConfigs by using onclick+BomToggle approach."""
path = '/root/inventree-source/InvenTree-master/src/backend/parametric_bom/templates/parametric_bom/configurator.html'

with open(path, 'r') as f:
    content = f.read()

# Fix 1: Replace the broken onchange pattern with onclick+BomToggle
old = (
    '+ \'onchange="onBomModeToggle(\' + item.pk + ", \'" + m.key + "\', this.checked)">"\''
)
new = (
    "+ 'onclick=\"BomToggle(this)\">'"
)

count = content.count(old)
if count > 0:
    content = content.replace(old, new)
    print(f"Fix 1: Replaced {count} onchange occurrence(s)")
else:
    print("Fix 1: Pattern NOT found, checking...")
    # Try to find it
    idx = content.find('onchange="onBomModeToggle(')
    if idx >= 0:
        print(f"  onchange found at {idx}")
        # Print surrounding 200 chars
        print(repr(content[idx-30:idx+100]))
    else:
        print("  onchange pattern not in file at all")
        # Check all onchange occurrences
        import re
        for m in re.finditer('onchange', content):
            pos = m.start()
            line = content[:pos].count('\n') + 1
            print(f"  onchange at line {line}")

# Fix 2: Replace the resetBomConfig call  
old2 = (
    '+ (hasCfg ? \'<button class="btn btn-secondary" onclick="resetBomConfig(\''
)
new2 = (
    '+ (hasCfg ? \'<button class="btn btn-secondary" data-bom-id="\' + item.pk + \'" onclick="resetBomConfig(this)">\u21a9\ufe0f \u91cd\u7f6e</button>\' : \'\')'
)

# That's too complex with escaping. Simpler approach: just find the reset line
idx2 = content.find('resetBomConfig(')
if idx2 >= 0:
    line_start = content.rfind('\n', 0, idx2) + 1
    line_end = content.find('\n', idx2)
    old_line = content[line_start:line_end]
    print(f"\nFix 2: Found resetBomConfig at line:\n  {repr(old_line)}")

with open(path, 'w') as f:
    f.write(content)
print("\nDone")
