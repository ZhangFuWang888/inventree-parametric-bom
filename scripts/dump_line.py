#!/usr/bin/env python3
"""Print the exact bytes of line 4982 to debug the JS syntax error."""
path = '/root/inventree-source/InvenTree-master/src/backend/parametric_bom/templates/parametric_bom/configurator.html'
with open(path, 'rb') as f:
    lines = f.read().split(b'\n')

line = lines[4981]  # 0-indexed
print(f'Line 4982 length: {len(line)} bytes')

# Print the FULL line with character-by-character breakdown
print('\nFull line (showing ranges):')
# Print in chunks
for i in range(0, len(line), 80):
    chunk = line[i:min(i+80, len(line))]
    print(f'  [{i:4d}-{i+len(chunk)-1:4d}]: {chunk}')

print('\nLast 30 chars hex:')
for i in range(max(0, len(line)-30), len(line)):
    ch = line[i]
    if 32 <= ch < 127:
        display = chr(ch)
    else:
        display = f'\\x{ch:02x}'
    print(f'  [{i:4d}]: {ch:3d} ({display})')
