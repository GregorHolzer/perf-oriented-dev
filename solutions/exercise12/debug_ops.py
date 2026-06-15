#!/usr/bin/env python3
import sys
from collections import Counter

filename = sys.argv[1] if len(sys.argv) > 1 else "lua-profile-debug.out"

counts = Counter()
with open(filename, "rb") as f:  # binary mode, faster
    for line in f:
        # find the semicolon
        sep = line.find(b";")
        if sep == -1:
            continue
        opcode = line[sep+1:].strip()
        counts[opcode] += 1

total = sum(counts.values())
print(f"{'Opcode':<30} {'Count':>12} {'%':>8}")
print("-" * 52)
for opcode, count in sorted(counts.items(), key=lambda x: -x[1]):
    print(f"{opcode.decode():<30} {count:>12} {100*count/total:>7.2f}%")

print(f"\nTotal: {total:,}")