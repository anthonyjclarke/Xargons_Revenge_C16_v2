"""Translate the original MOS assembler syntax without changing instructions.

Adapted from the Dorks Dilemma and Tycoon Tex restorations by Anthony Clarke.
Xargon's Revenge uses no macros, so any .MAC block is rejected rather than
guessed.
"""

import json
import re

OPCODES = set("ADC AND ASL BCC BCS BEQ BIT BMI BNE BPL BRK BVC BVS CLC CLD CLI CLV CMP CPX CPY DEC DEX DEY EOR INC INX INY JMP JSR LDA LDX LDY LSR NOP ORA PHA PHP PLA PLP ROL ROR RTI RTS SBC SEC SED SEI STA STX STY TAX TAY TSX TXA TXS TYA".split())


def split_comment(line):
    """Keep semicolons in quoted data, including old single-character operands."""
    position = 0
    while position < len(line):
        char = line[position]
        if char == ";":
            return line[:position].rstrip(), line[position:]
        if char in "\"'":
            end = line.find(char, position + 1)
            position = end + 1 if end >= 0 else position + 2
        else:
            position += 1
    return line.rstrip(), ""


def flatten(sources, name, stack=()):
    """Expand .LIB includes in original order; each file stops at its .END."""
    if name in stack:
        raise ValueError(f"Recursive include: {name}")
    result = []
    for number, line in enumerate(sources[name], 1):
        code, _ = split_comment(line)
        if code.strip().upper().startswith(".LIB "):
            pattern = code.split()[1].rstrip("*")
            matches = [key for key in sources if key.startswith(pattern)]
            if len(matches) != 1:
                raise ValueError(f"{name}:{number}: ambiguous/missing include {pattern}: {matches}")
            result.extend(flatten(sources, matches[0], stack + (name,)))
        elif code.strip().upper() == ".END":
            break
        else:
            result.append((name, number, line))
    return result


def convert(lines):
    output = ['; Generated from recovered C16 source. See recovery-manifest.json.',
              '.setcpu "6502"', '.feature force_range']
    previous = None
    for name, number, line in lines:
        if previous != name:
            output.append(f"; SOURCE: {name}:{number}")
            previous = name
        code, comment = split_comment(line)
        code = code.strip()
        if code.startswith(".MAC") or code == ".MND":
            raise ValueError(f"{name}:{number}: unexpected macro definition")
        if code.startswith(".OPT "):
            continue
        if not code:
            output.append(comment)
            continue
        origin = re.fullmatch(r"\*=\$([0-9A-F]+)", code)
        if origin:
            address = int(origin[1], 16)
            output.extend([f'.segment "AT_{address:04X}"', f'.org ${address:04X}'])
            continue
        reserve = re.fullmatch(r"(?:(\w+)\s+)?\*=\*\+(.+)", code)
        if reserve:
            code = (reserve[1] + ': ' if reserve[1] else '') + '.res ' + reserve[2]
        elif re.match(r"^\w+\s*=", code):
            pass  # Equates must retain the complete expression.
        else:
            first, *rest = code.split(None, 1)
            if not first.startswith('.') and first not in OPCODES:
                code = first + ':' + (' ' + rest[0] if rest else '')
            # MOS data strings use single quotes; ca65 strings use double quotes.
            if re.search(r"\.BYT(?:E)?\b", code):
                code = re.sub(r"'([^']*)'", lambda m: json.dumps(m[1]), code)
                code = re.sub(r"\.BYT\b", '.byte', code)
            # The original assembler permits an opening quote plus one character.
            code = re.sub(r"#'([^'])(?!')(?=\s*$)", r"#'\1'", code)
        output.append(code + (' ' + comment if comment else ''))
    return '\n'.join(output) + '\n'
