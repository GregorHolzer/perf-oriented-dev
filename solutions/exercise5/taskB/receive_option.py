import re
import subprocess

O2_CMD = "gcc -Q --help=optimizers -O2"
O3_CMD = "gcc -Q --help=optimizers -O3"


def get_options(cmd: str) -> dict:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    options = {}
    for line in result.stdout.splitlines():
        parts = line.split()
        if not parts:
            continue

        flag = re.sub(r'\[(?!enabled|disabled)[^\]]*\]', '', parts[0]).rstrip()

        value = None
        for token in reversed(parts[1:]):
            if not token.startswith("[") or token in ("[enabled]", "[disabled]"):
                value = token
                break

        options[flag] = value
    return options


def get_diffs() -> list[tuple[str, str, str]]:
    o2 = get_options(O2_CMD)
    o3 = get_options(O3_CMD)
    diffs = []
    for flag in sorted(set(o2) | set(o3)):
        v2, v3 = o2.get(flag), o3.get(flag)
        if v2 != v3:
            diffs.append((flag, v2, v3))

    print(f"{'Flag':<50} {'O2':<20} {'O3':<20}")
    print("-" * 90)
    for flag, v2, v3 in diffs:
        print(f"{flag:<50} {str(v2):<20} {str(v3):<20}")
    return diffs