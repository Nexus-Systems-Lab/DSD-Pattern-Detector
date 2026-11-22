"""Verify the report's overlap-aware 0010 transition table as a software model.

This script does not parse or simulate the Proteus schematic.
"""

from itertools import product


# (state, input) -> (next_state, match), transcribed from the report table.
TABLE = {
    (0b00, 0): (0b01, 0),
    (0b01, 0): (0b10, 0),
    (0b10, 0): (0b10, 0),
    (0b11, 0): (0b01, 1),
    (0b00, 1): (0b00, 0),
    (0b01, 1): (0b00, 0),
    (0b10, 1): (0b11, 0),
    (0b11, 1): (0b00, 0),
}


def equations(state: int, bit: int) -> tuple[int, int]:
    """Return (next_state, match) from corrected sum-of-products logic."""
    q1, q0 = (state >> 1) & 1, state & 1
    d1 = (q1 and not q0) or (not q1 and q0 and not bit)
    d0 = ((not q1 and not q0 and not bit)
          or (q1 and not q0 and bit)
          or (q1 and q0 and not bit))
    match = q1 and q0 and not bit
    return (int(d1) << 1) | int(d0), int(match)


def fsm_matches(bits: tuple[int, ...]) -> list[int]:
    state = 0
    matches = []
    for position, bit in enumerate(bits, start=1):
        state, match = TABLE[state, bit]
        if match:
            matches.append(position)
    return matches


def window_matches(bits: tuple[int, ...]) -> list[int]:
    return [end for end in range(4, len(bits) + 1)
            if bits[end - 4:end] == (0, 0, 1, 0)]


def main() -> None:
    for key, expected in TABLE.items():
        assert equations(*key) == expected, (key, equations(*key), expected)

    total = 0
    for length in range(14):
        for bits in product((0, 1), repeat=length):
            assert fsm_matches(bits) == window_matches(bits), bits
            total += 1

    example = (0, 0, 1, 0, 0, 1, 0)
    assert fsm_matches(example) == [4, 7]
    print(f"PASS: 8 transition rows and {total:,} streams (lengths 0–13)")
    print("0010010: matches end at bit positions 4 and 7")


if __name__ == "__main__":
    main()
