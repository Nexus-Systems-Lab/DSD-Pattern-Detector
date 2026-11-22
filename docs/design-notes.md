# Engineering notes

## Scope and source

These notes describe the supplied IE3004 Group 10 report and Proteus archive. They distinguish documented behavior from behavior verified in code. The project target is the serial sequence `0010`.

## Functional blocks

| Block | Purpose | Documented implementation |
|---|---|---|
| Pattern source | Produce 4-bit pseudo-random words | Four-bit LFSR with XOR feedback; the precise taps and seed are not stated unambiguously in the report |
| Test selection | Substitute a manually chosen word | Report describes `R3..R0`, `W3..W0`, selected `T3..T0` |
| PISO | Capture a four-bit word, emit one bit per valid clock | 74LS74 storage with combinational selection logic; MSB-first `P3` output |
| Detector | Recognize serial `0010` | Four-state Mealy FSM with two state bits |
| Indication | Display a detection event | Logic and LED indicators in schematic; report mentions `MATCH`, registered `DETECT`, and optional sticky `SEEN` |

The report identifies 74LS74 dual positive-edge D flip-flops; 74LS04 inverters; 74LS08 AND; 74LS32 OR; and 74LS86 XOR gates. Clock, logic-state input, LEDs and resistors are visible in the supplied schematic. The report describes EasyEDA layouts for the two-bit counter, pseudo-parallel generator and PISO, plus Proteus timing and a physical implementation photograph. Editable EasyEDA PCB files were not supplied.

## Timing contract

All sequential blocks share a positive-edge clock. The report describes `LOAD` and `VALID` control, with the detector consuming the bit held at `P3` **before** each valid rising edge. The PISO changes after the edge, so using the post-edge value as the just-consumed bit would shift the detector's interpretation by one bit.

| Signal | Direction | Intended meaning |
|---|---|---|
| `CLK` | Input | Common positive-edge clock |
| `RESET_N` | Input | Active-low initialization |
| `LOAD` | Control | Parallel capture of next word |
| `VALID` | Control | Detector processes `X` on this edge |
| `X` | PISO → FSM | Serial bit from PISO `P3` |
| `MATCH` | FSM combinational | High for state `S3` and input `0` |
| `DETECT` | Output | Report describes a registered, one-cycle match pulse |
| `SEEN` | Optional output | Sticky indication since reset, as described in report |

The report does not provide a complete cycle-by-cycle controller table. Verify actual load/shift/valid sequencing against the schematic and waveform before using this design as a timing reference. A four-bit word boundary is particularly important: the detector may either retain state across words to detect a continuous stream, or reset state per word to detect only within a word. Those policies yield different answers for a match spanning two words.

## Transition model

`S0=00` has no useful prefix, `S1=01` means suffix `0`, `S2=10` means suffix `00`, and `S3=11` means suffix `001`.

| `Q1Q0` | `X` | Next `Q1+Q0+` | `MATCH` |
|---:|---:|---:|---:|
| `00` | `0` | `01` | `0` |
| `01` | `0` | `10` | `0` |
| `10` | `0` | `10` | `0` |
| `11` | `0` | `01` | `1` |
| `00` | `1` | `00` | `0` |
| `01` | `1` | `00` | `0` |
| `10` | `1` | `11` | `0` |
| `11` | `1` | `00` | `0` |

For D flip-flops, `D1=Q1+` and `D0=Q0+` when the FSM is enabled. During invalid cycles, the actual controller must hold or otherwise control the state.

### Corrected equations for this table

```text
D1    = Q1·¬Q0 + ¬Q1·Q0·¬X
D0    = ¬Q1·¬Q0·¬X + Q1·¬Q0·X + Q1·Q0·¬X
MATCH = Q1·Q0·¬X
```

The equations are a direct sum-of-products derivation from the eight rows. They describe the *enabled* transition logic and omit reset/enable gating.

## Report consistency and verification boundary

1. **Overlapping vs non-overlapping:** The state table and page 5 workflow transition `S3 → S1` on the matching `0`. This retains the `0` as the next prefix and allows overlapping matches. Several other report paragraphs and the diagram description say non-overlapping and describe a return to `S0`. A truly non-overlapping machine would change that row to `S3, X=0 → S0, MATCH=1`, which also changes `D0` logic. This repository uses the report's explicit state table as the reference model; inspect the actual schematic to determine its implemented behavior.
2. **Printed `D0` expression:** The report gives `D0 = ¬Q1·¬Q0·¬X + Q1·¬Q0·X`. For `Q1Q0=11` and `X=0`, it evaluates to `0`, while the transition table requires next state `01` and therefore `D0=1`. The corrected expression adds `Q1·Q0·¬X`.
3. **Output semantics:** The report mentions combinational `MATCH`, registered `DETECT`, and optional latched `SEEN`. These should not be treated as identical signals without tracing the netlist and timing waveform.
4. **LFSR detail:** The report names a four-bit LFSR but does not specify an unambiguous feedback polynomial, seed, or period. No maximal-length claim is made here.
5. **Validation:** `verification/verify_fsm.py` proves consistency of the reference FSM against the table and sliding-window software model for all streams through length 13. It cannot establish that `ROOT.DSN`, PCB layout, or physical assembly matches the model.

## Reproduction checklist

1. Open `proteus/PROJECT.XML` (or `ROOT.DSN`) in Proteus 8.
2. Confirm all 74LS parts, supply rails, reset defaults and clock source resolve.
3. Step a known word, such as `0010`, through `LOAD` and four valid sample edges.
4. Probe `CLK`, `LOAD`, `VALID`, `X`, `Q1`, `Q0`, `MATCH`, and any `DETECT` register.
5. Check `0010010` for two matches if implementing the table's overlap-aware behavior.
6. Check a pattern that spans two loaded words to determine the implemented boundary policy.
7. Compare simulation observations with the report's waveform; document any deviation before hardware use.
