"""The boards tools/mame_netlist.py converts, and every judgement about them.

A target names its MAME file and netlist, the board record it writes, and what
in the file is simulation rather than circuit:

  defines     #defines fixed before the file is read (a variant switch, or a
              switch SWITCHES in mame_netlist.py does not know)
  undo        {line, text, action, why}: a NET_C that is a hack. `text` must be
              in the line at TAG, so a wrong number fails instead of undoing
              the wrong thing. action: "nc" (its pins have nothing attached),
              "drop" (the connection is not on the board), "port" + name (the
              pin goes somewhere MAME does not draw), "remove" + terms (some of
              its terms are not), "drop-line" (any statement)
  restore     [(first, last)]: commented-out lines that are the board's circuit
  not_parts   {MAME name: why}: a part MAME adds that stands in for something
              the board has (a sound chip's output); its nets become ports
  loads       {MAME name: why}: a dummy load MAME hangs on a pin the board
              leaves open; the pin becomes nc
  ports       {alias: why}: named nets that leave the board (the audio output)
  designators {MAME name: designator} where the rule (IC_A7 -> UA7, U8 -> U8,
              IC6 -> U6, passives as written) is not enough
  notes       what a repairer should know, including where MAME and the sheet
              were compared and how they differ

The rules that need no judgement -- HLE switches, unused-pin blocks, parked
parts, scaled values, commented-out declarations the real circuit uses -- are
in mame_netlist.py and apply to every target.
"""

CINEMATRONICS = """\
Cinematronics vector games carry a small audio board of their own, driven from the
CPU board's output latch: the latch bits arrive here as ports (OUT_0 ... OUT_7, MAME's
TTL_INPUT names), and the board's sound goes out to a final amplifier that MAME does
not simulate and this file therefore does not contain."""

SEGA = """\
Sega/Gremlin G-80 games carry a sound board of their own, driven from the CPU board's
output ports: the port bits arrive here as ports (MAME's TTL_INPUT names, HI_D0 ...
LO_D7 or SOUND_0 ...), and the mixed sound goes out to the amplifier."""

UNCHECKED = """\
Not compared with the sheet. MAME's designators, values and pin numbers are taken as
MAME has them; the checker shows the netlist is internally consistent (every pin exists,
no two outputs fight, nothing floats), which is not the same as matching the board."""


def sound(name, mfr, year, machine, docs, what, source, netlist, about, notes=(),
          compared="not read here", **kw):
    """A sound board converted from one MAME file."""
    return dict(
        source=source, netlist=netlist, title=f"{name} sound board",
        board=dict(
            name=f"{name} sound board", mfr=mfr, year=year, machine=machine,
            drawing=f"Sound board schematic in {docs} -- via MAME's netlist, {compared}",
            revision=what,
            coverage="Converted from MAME's netlist, which covers the sound circuits up to "
                     "the final amplifier. See the .nets file for what was undone and what "
                     "MAME leaves out.",
            singleSource=True, netsTraced=False, netsConverted="mame"),
        about=about, notes=list(notes), **kw)


# ---------------------------------------------------------------------------
# Tank (Kee Games / Atari, 1974): MAME's one pin-level whole-game netlist
# (Ryan Holtz, BSD-3-Clause). The game is two boards that share one grid of
# designators -- Board I's D11 is not Board II's D11 -- so MAME's single netlist
# is split by what each sheet draws. The sheets were read in full for this
# (2026-10-19): Board I 003110 rev J (doc 7387abff18bd, rev H b25600c0cfc9 and
# rev G f157add95612 for faint spots), Board II 003112 rev H sheet 1 (doc
# 6872a0725db0) and sheet 2 (the rev F print in doc 5169eb199193, which is the
# cleaner scan of the same sheet).
# ---------------------------------------------------------------------------

B1, B2 = "tank-board-1", "tank-board-2"

TANK_ABOUT = """\
Tank is two boards with no CPU. MAME's netlist (nl_tank.cpp) describes both as one circuit
at the pin level, on one grid of designators -- but the boards each have their own grid,
so Board I's D11 is not Board II's D11. This file is the part of MAME's circuit the sheets
put on {this}, with every net that crosses to the other board landing on the cable
contact {this}'s sheet prints for it (Board I J1/J2 to Board II J4/J5).

MAME's passive designators carry suffixes it added to tell the boards apart (R53A, R48B,
C33C, R4V, R102MX, R74M1); they are stripped here, so the designators are the sheet's.
Where a part's board was in doubt, the sheets decided: MAME's "A" mostly means Board I's
sheet 2, but R8A-R11A and R37A are Board II's."""

TANK_ABOUT_1 = TANK_ABOUT.format(this="Board I") + """

Board I: tank and shell motion (sheet 1); coin logic, the play timer, the antenna, noise,
shot and boom sounds and the audio mixers (sheet 2)."""

TANK_ABOUT_2 = TANK_ABOUT.format(this="Board II") + """

Board II: ROM multiplexing, playfield, minefield, the motion latches, the motor sounds and
video (sheet 1); sync, timing and control (sheet 2)."""

TANK_NOTES_1 = """\
Compared with both Board I sheets in full (003110 rev J; rev H and rev G for faint spots),
2026-10-19. MAME agrees with the sheet on the tank motion counters and their presets
(B1/B5 3-5 to P and 6 grounded; C2/C4/J1/J5 4 grounded), the clock inverters on A6, F3
and the WINDO outputs, the shell counters and the 2^7 latches cleared by /EXPL, shell 2's
latch routing, the shell and blast output gating, the coin flip-flops apart from B6, and
the play timer, noise, shot and boom values apart from R53. Its errors here, all corrected
above: B6 is a 7404, not a 7400; K6 and L6 are MFC6040s, whose pins are not the MC3340's;
C31 feeds K6's input, not its control pin; R53 is 330K; shell 1's 2^2 and 2^3 latches are
crossed between the F2 and C1 gates; M2's inputs are swapped (electrically the same NAND);
and Board I makes its own HMCE, /EXPL1 and /EXPL2 from what the cable brings, where MAME
takes Board II's. MAME's antenna tie, 25c hard-wiring, unused-input ties on N4 and A6 (the
antenna latch and the coin counter use them) and grounded mixer outputs are undone.

Open questions, each as printed and not settled:
* The cable. This sheet prints VLD1 on J1-9 and /FIRE1 on J1-24; Board II's prints
  FIRE1-bar on J4-9 and VLD1 on J4-24. Every other contact agrees pin for pin, and the
  only Board I load (M2, a 3-input NAND of both) cannot tell them apart. Each board is
  given its own sheet's contact.
* J6's second 7474 half is printed "J4" on rev H and rev J (pins 1-6, the coin latch). J4
  is a 9316 on sheet 1; MAME calls this half J6, and so does this file.
* BOOM COM reaches Q6 through two series 1N914s, both labelled CR22. MAME has one CR22;
  this file follows MAME.
* M1's first gate prints input "3" (MAME, and tank 2's M5, use 5); L3 prints an input
  "10" that is its own output (MAME uses 8); N1 and N5 print their /CLR numbers swapped
  (both go to /HRST, so it is harmless). MAME's pins are kept.
* SW1 and SW2 are the 25c/50c switch as drawn in two places; whether they are two poles of
  one switch is not on the sheet. The 50c contact of SW2 is drawn unconnected.

Ours, not printed: UX1 (the noise amplifier's 741, which has no grid position), VR1-VR3
(the PLAY TIME pot and the shot and boom noise pots), SW1, SW2. Not in this file: the
+5V, +12V and -12V supplies and the two LM380 amplifiers with their volume pots, which are
on sheet 2 and not in MAME; OUT1 and OUT2 are where the mixers hand over to them."""

TANK_NOTES_2 = """\
Compared with both Board II sheets in full (003112 sheet 1 rev H, sheet 2 rev F),
2026-10-19. MAME agrees with the sheet on the ROM's address and data wiring and the 74153
and 9322 multiplexers, the playfield shift register, the minefield and mine control (the
8277 included), video summing, the boom and shot one-shots, the motion latches apart from
HD1/HD2, the joystick and fire inputs (designators and values once MAME's suffixes are
dropped), the shell one-shots, the 556 blow-up timer, the speed and rotation counters, and
the 7492 at A12 -- which matters because MAME's own 7492 model swaps QB and QD against TI's
data sheet (the MiSTer Tank core's finding); the netlist's pin numbers are the sheet's.

MAME's errors here, all corrected above: the score counters (D11 QA and QD go to E11's CPA
and CPB the other way round, and SCR1E is D11 pin 12, not 11 -- MAME has SCR1E and SCR2C on
one pin); HD1 and HD2 are the Q-bar outputs of N8 and N12 (pin 6), not Q; the ROM's pin 9
and its output pull-downs R19-R26 go to -12V, not ground; and C50/C51 are .22uF, not 22uF.
MAME's ideal clock is replaced by the crystal oscillator the sheet draws on A7 (a 74H04);
its "unused" A7 pins 11 and 13 are the oscillator. The motor sounds, which MAME comments
out, are restored: its block agrees with the sheet apart from the MFC6040's output and
supply pins, C50/C51 and Q34's emitter (missing from MAME's +12V list), all corrected; the
555s' pin 3 is not drawn.

The ROM. The sheet prints "24-PIN EA ROM" at K10 -- an Electronic Arrays MOS ROM, with +5V
on pin 1 and -12V on pin 9. MAME models it as an MK28000 bipolar PROM, and a handwritten
note on the rev F print points to the MK28000P; an MK28000's pin 9 is GND, so the board as
drawn is not wired for one. The pin names here are MAME's MK28000 names, which are what
MAME's ROM dump is ordered by. R19-R26 have no value printed; MAME's 1K is its own guess.

Open questions, each as printed and not settled:
* The cable's VLD1 and /FIRE1 contacts disagree with Board I's sheet (see Board I's notes).
* J5-22/23 is labelled -12V beside the ROM and +12V in the regulator.
* R13 (PLAYFIELD SELECT, 4.7K to +5V) has a jumper to ground drawn beside it -- the
  alternate maze. MAME leaves it open, as this file does.
* R74 reads 120K on rev H and 180K on rev F; MAME and this file have 180K.
* A8's first half has its S and R pins marked "R" rather than "P".
* Player 1's lower stick pair is printed "#2 LEFT STICK" -- it feeds ACC1/STOP1/RR1/RL1.
* 1Ø2-1Ø4 and 2Ø2-2Ø4 reach this board in contact boxes with no number printed.

Designators that are not MAME's: J11 (MAME's "D11V" -- another gate of J11), K10 (MAME's
"R10"), R18 (MAME's "RUNK1", 47K). Ours, not printed: Y1 (the crystal), VR1 (the 50K shell
range pot, circled 'Shell Range' by hand on the sheet), VR2-VR5 (the motor volume pots and
rheostats). Not in this file: the +5V regulator (Q35-Q39 and its parts), not in MAME."""

TANK_BOARD_I = """\
IC_A1 IC_B1 IC_A2 IC_B2 IC_C2 IC_A3 IC_B3 IC_N1 IC_M1 IC_M2 IC_C1 IC_J3 IC_A6 IC_K3 IC_L3 IC_F3
IC_A5 IC_B5 IC_A4 IC_B4 IC_C4 IC_C3 IC_D3 IC_N5 IC_C6 IC_M5 IC_M4 IC_C5
IC_D1 IC_E1 IC_H1 IC_J1 IC_F1 IC_H2 IC_J2 IC_L1 IC_F2 IC_K1 IC_N4 IC_L2 IC_K2 IC_N3 IC_M3 IC_D2 IC_E2
IC_E4 IC_D4 IC_D5 IC_E5 IC_H4 IC_J4 IC_F5 IC_H5 IC_J5 IC_L5 IC_K4 IC_K5 IC_F4 IC_L4 IC_H3
IC_B6 IC_D6 IC_N6 IC_E6 IC_J6 IC_H6 IC_K6 IC_L6 IC_NOISE_OP
R4 R5 R6 R7 R8 R9 R10 R11 C110 C111
R53A R54A R55A R56A R59A R60A R63A R64A R69 R70A R71A R72A R73A
R102MX R103MX R104MX R106MX R107MX R108MX C101 C106
C24 C25 C27A C28A C30A C31A C32A C35A C36A C38A C39A C40A C41A C43A
CR19 CR22 Q2 Q3 Q4 Q6 Q7 PLAYTIME SHOT_NOISE_VOL BOOM_NOISE_VOL
Q1 Q5 C15A C16A C17A CR9A CR12A R41A R42A R49A R48A SW1 SW2 R100 R101 Q40 Q41""".split()


def both(b1, b2):
    """A signal's contact on each board: Board I's J1/J2, Board II's J4/J5."""
    out = {}
    if b1:
        out[B1] = b1
    if b2:
        out[B2] = b2
    return out


# The two boards are cabled J1-J4 and J2-J5. Each side is as its own sheet
# prints it; they agree pin for pin except VLD1 and /FIRE1 (see the notes).
TANK_CONTACTS = {
    "HD1": both("J1.1", "J4.1"), "HC1": both("J1.2", "J4.2"), "HB1": both("J1.3", "J4.3"),
    "HA1": both("J1.4", "J4.4"), "HRST1Q": both("J1.5", "J4.5"), "SRS1": both("J1.6", "J4.6"),
    "FLASH": both("J1.7", "J4.7"), "BLO_UP1": both("J1.8", "J4.8"),
    "VLD1": both("J1.9", "J4.24"), "FIRE1Q": both("J1.24", "J4.9"),
    "WINDO2": both("J1.11", None), "WINDO1": both("J1.12", None),
    "SHELL1": both("J1.13", "J4.13"), "BLAST1": both("J1.14", "J4.14"),
    "P1T4": both("J1.15", None), "VD1": both("J1.16", "J4.16"), "P1T3": both("J1.17", None),
    "VC1": both("J1.18", "J4.18"), "P1T2": both("J1.19", None), "VB1": both("J1.20", "J4.20"),
    "VA1": both("J1.21", "J4.21"), "VRST1Q": both("J1.22", "J4.22"),
    "EXPL1": both("J1.23", "J4.23"), "HMCEQ": both("J1.25", "J4.25"),
    "ROM_D0": both("J1.27", "J4.27"), "ROM_D7": both("J1.28", "J4.28"),
    "ROM_D1": both("J1.29", "J4.29"), "ROM_D6": both("J1.30", "J4.30"),
    "ROM_D2": both("J1.31", "J4.31"), "ROM_D5": both("J1.32", "J4.32"),
    "ROM_D3": both("J1.33", "J4.33"), "ROM_D4": both("J1.34", "J4.34"),
    "LDH1AQ": both("J1.35", "J4.35"), "LDH1BQ": both("J1.36", "J4.36"),
    "LDH2AQ": both("J1.37", "J4.37"), "LDH2BQ": both("J1.38", "J4.38"),
    "EXPL2": both("J1.39", "J4.39"), "GNE": both("J1.40", "J4.40"),
    "TANK1": both("J1.41", "J4.41"), "VD2": both("J1.43", "J4.43"), "P2T4": both("J1.44", None),
    "VC2": both("J1.45", "J4.45"), "P2T3": both("J1.46", None), "VB2": both("J1.47", "J4.47"),
    "P2T2": both("J1.48", None), "VA2": both("J1.49", "J4.49"), "VRST2Q": both("J1.50", "J4.50"),
    "FIRE2Q": both("J2.1", "J5.1"), "VLD2": both("J2.3", "J5.3"), "BLAST2": both("J2.4", "J5.4"),
    "SHELL2": both("J2.5", "J5.5"), "HD2": both("J2.6", "J5.6"), "HC2": both("J2.7", "J5.7"),
    "HB2": both("J2.8", "J5.8"), "HA2": both("J2.9", "J5.9"), "HRST2Q": both("J2.10", "J5.10"),
    "BLO_UP2": both("J2.11", "J5.11"), "SRS2": both("J2.12", "J5.12"),
    "TANK2": both("J2.13", "J5.13"), "START": both("J2.15", "J5.15"),
    "CLOCKQ": both("J2.17", "J5.17"), "H_COUNTQ": both("J2.18", "J5.18"),
    "ATTRACTQ": both("J2.24", "J5.24"), "V128": both("J2.26", None),
    "BOOM_COM": both("J2.28", "J5.28"), "SHOT_COM": both("J2.29", "J5.29"),
    "MOTOR2": both("J2.30", "J5.30"), "MOTOR1": both("J2.31", "J5.31"),
    # Board I's cabinet connector J3; Board II's controls and video on J6.
    "COIN1_NC": both("J3.13", None), "COIN1_NO": both("J3.14", None),
    "COIN2_NC": both("J3.11", None), "COIN2_NO": both("J3.12", None),
    "ANT": both("J3.9", None), "COIN_COUNTER": both("J3.20", None),
    "TV_GROUND": both("J3.21", None),
    "P1_RIGHT_UP": both(None, "J6.13"), "P1_RIGHT_DOWN": both(None, "J6.11"),
    "P1_LEFT_UP": both(None, "J6.12"), "P1_LEFT_DOWN": both(None, "J6.10"),
    "P2_RIGHT_UP": both(None, "J6.18"), "P2_RIGHT_DOWN": both(None, "J6.16"),
    "P2_LEFT_UP": both(None, "J6.17"), "P2_LEFT_DOWN": both(None, "J6.15"),
    "P1_FIRE": both(None, "J6.19"), "P2_FIRE": both(None, "J6.20"),
    "VIDEO_OUT": both(None, "J6.21"), "-12V": both(None, ["J5.22", "J5.23"]),
}


def sheet(why, *terms, name=None, section=""):
    return dict(terms=list(terms), why=why, name=name, section=section)


def part(name, kind, value, why, section=""):
    d = dict(name=name, kind=kind, why=why, section=section)
    d["part" if kind == "IC" else "value"] = value
    return d


ANT = "Board I sheet 2: the antenna circuit MAME replaces with a tie"
CNT = "Board I sheet 2: the coin counter driver, which MAME does not draw"
SW = ("Board I sheet 2: the 25c/50c switch, which MAME hard-wires in the 25c position. "
      "Not designated on the sheet; SW1/SW2 are ours")
OSC = "Board II sheet 2: the 14.318 MHz crystal oscillator, which MAME replaces with an ideal clock"

TANK = dict(
    source="src/mame/atari/nl_tank.cpp", netlist="tank",
    split={
        B1: dict(
            title="Tank Board I (003110)",
            board=dict(
                name="Tank Board I", mfr="Kee Games / Atari", year="1974", machine="tank",
                drawing="Schematic, Tank Board I, 003110 rev J sheets 1-2 (doc 7387abff18bd) -- "
                        "MAME's netlist, split by board and corrected from the sheets",
                revision="Tank Board I 003110 rev J: tank and shell motion (sheet 1); coin "
                         "logic, play timer, antenna, noise, shot and boom sounds and the audio "
                         "mixers (sheet 2).",
                coverage="Converted from MAME's netlist and corrected against both sheets. "
                         "Not in this file: the power supplies and the two LM380 amplifiers, "
                         "which MAME does not have.",
                singleSource=False, netsTraced=False, netsConverted="mame"),
            about=TANK_ABOUT_1, notes=[TANK_NOTES_1]),
        B2: dict(
            title="Tank Board II (003112)",
            board=dict(
                name="Tank Board II", mfr="Kee Games / Atari", year="1974", machine="tank",
                drawing="Tank Board II 003112 rev H sheet 1 (doc 6872a0725db0) and sheet 2 "
                        "(rev F print, doc 5169eb199193) -- MAME's netlist, split by board and "
                        "corrected from the sheets",
                revision="Tank Board II 003112: ROM multiplexing, playfield, minefield, motion "
                         "latches, motor sounds and video (sheet 1); sync, timing and control "
                         "(sheet 2).",
                coverage="Converted from MAME's netlist and corrected against both sheets; the "
                         "motor sounds, which MAME comments out, are restored. Not in this file: "
                         "the +5V regulator.",
                singleSource=False, netsTraced=False, netsConverted="mame"),
            about=TANK_ABOUT_2, notes=[TANK_NOTES_2]),
    },
    assign={B1: TANK_BOARD_I}, assign_default=B2,
    contacts=TANK_CONTACTS,
    strip_suffix=r"((?:R|C|CR|Q)\d+)(?:A|B|C|V|MX|M1|M2)",
    rename={"IC_D11V": "IC_J11"},
    designators={
        "IC_R10": "UK10", "IC_NOISE_OP": "UX1", "RUNK1": "R18",
        "PLAYTIME": "VR1", "SHOT_NOISE_VOL": "VR2", "BOOM_NOISE_VOL": "VR3",
        "FIRE1_ADJUST": "VR1", "MOTOR1_VOL": "VR2", "MOTOR1_VOL2": "VR3",
        "MOTOR2_VOL": "VR4", "MOTOR2_VOL2": "VR5",
    },
    restore=[(1797, 1833), (1837, 1872)],
    restore_why={(1797, 1833): "the Motor 1 sound, which MAME comments out; compared with Board "
                               "II sheet 1 and corrected below",
                 (1837, 1872): "the Motor 2 sound, likewise"},
    loads={"R555OUT1": "a 1K to ground on the 555's output, which the sheet leaves undrawn",
           "R555OUT2": "a 1K to ground on the 555's output, which the sheet leaves undrawn",
           "RVID": "MAME's 10K to ground standing in for the monitor's input"},
    fix_parts={
        "IC_B6": ("7404", "Board I sheet 2: two cross-coupled inverter pairs, not NAND latches"),
        "IC_K6": ("MFC6040", "Board I sheet 2 prints MFC6040; its pin numbers differ from the "
                             "MC3340's, so MAME's pins are mapped onto it"),
        "IC_L6": ("MFC6040", "Board I sheet 2 prints MFC6040; pins mapped as for K6"),
        "IC_N15": ("MFC6040", "Board II sheet 1 prints MFC6040; pins mapped as for K6"),
        "IC_F15": ("MFC6040", "Board II sheet 1 prints MFC6040; pins mapped as for K6"),
        "IC_A6": ("74H04", "Board I sheet 1 prints H04"),
        "IC_A7": ("74H04", "Board II sheet 2 prints H04 -- it is the crystal oscillator"),
        "IC_M1": ("74S20", "Board I sheet 1 prints S20"),
        "IC_M5": ("74S20", "Board I sheet 1 prints S20"),
        "IC_M3": ("74H08", "Board I sheet 1 prints H08"),
        "IC_R10": ("EA-ROM", "Board II sheet 1 prints '24-PIN EA ROM' at K10, no part number; "
                             "MAME's MK28000 is a substitute (see the notes)"),
    },
    fix_values={
        "R53A": ("330K", "Board I sheet 2 rev J, and rev G"),
        "C51M1": ("0.22uF", "Board II sheet 1 prints .22uf at C51"),
        "C50M2": ("0.22uF", "Board II sheet 1 prints .22uf at C50"),
    },
    repin={n: {"1": "3", "2": "2", "3": "1", "6": "6", "7": "5", "8": "4"}
           for n in ("IC_K6", "IC_L6", "IC_N15", "IC_F15")},
    undo=[
        dict(line=352, text="ALIAS(COIN1_NO, IC_B6.5)", action="drop-line", why="B6 is a 7404"),
        dict(line=353, text="ALIAS(COIN1_NC, IC_B6.1)", action="drop-line", why="B6 is a 7404"),
        dict(line=354, text="ALIAS(COIN2_NO, IC_B6.9)", action="drop-line", why="B6 is a 7404"),
        dict(line=355, text="ALIAS(COIN2_NC, IC_B6.13)", action="drop-line", why="B6 is a 7404"),
        dict(line=357, text="NET_C(IC_B6.2, IC_B6.6, IC_D6.9)", action="drop",
             why="MAME's 7400 latch; Board I sheet 2 draws a 7404 pair (below)"),
        dict(line=358, text="NET_C(IC_B6.4, IC_B6.3, IC_N6.5)", action="drop", why="as above"),
        dict(line=359, text="NET_C(IC_B6.12, IC_B6.8, IC_D6.8)", action="drop", why="as above"),
        dict(line=360, text="NET_C(IC_B6.10, IC_B6.11, IC_N6.6)", action="drop", why="as above"),
        dict(line=376, text="NET_C(GND, IC_D6.3)", action="drop",
             why="the 25c/50c switch in its 25c position; the switch is put back (SW1)"),
        dict(line=382, text="NET_C(PLAYTIME.1, R54A.1, R53A.1)", action="remove",
             terms=["R53A.1"], why="R53 is switched in by the 25c/50c switch (SW2), not fixed"),
        dict(line=395, text="NET_C(V5, IC_E6.10)", action="drop",
             why="'No antenna to spark, so we pretend we never get a spark'; the antenna "
                 "latch is put back"),
        dict(line=400, text="NET_C(GND, IC_N6.8)", action="drop", why="as above"),
        dict(line=404, text="ALIAS(STARTQ, IC_H3.4)", action="drop-line",
             why="Board II makes its own /START from START with M13 pins 3-4; MAME takes Board "
                 "I's H3.4 and ties M13 pin 3 off as unused"),
        dict(line=1826, text="NET_C(ATTRACT, IC_N13.1)", action="drop",
             why="Board II's ATTRACT is its own M13.2 (from /ATTRACT); MAME takes Board I's"),
        dict(line=1865, text="NET_C(ATTRACT, IC_N13.13)", action="drop", why="as above"),
        dict(line=434, text="NET_C(CLK.Q, IC_A7.1, IC_A7.3)", action="drop",
             why="an ideal 14.318 MHz clock; the crystal oscillator is put back"),
        dict(line=852, text="NET_C(IC_D11.12, IC_E11.1)", action="drop",
             why="Board II sheet 2: D11 QA (12) clocks E11 pin 14, not pin 1"),
        dict(line=853, text="NET_C(IC_D11.11, IC_E11.14)", action="drop",
             why="Board II sheet 2: D11 QD (11) clocks E11 pin 1, not pin 14"),
        dict(line=854, text="ALIAS(SCR1E, IC_D11.11)", action="drop-line",
             why="Board II sheet 2: SCR1E is D11 pin 12; pin 11 is SCR2C"),
        dict(line=1001, text="NET_C(GND, IC_R10.9)", action="drop",
             why="Board II sheet 1 takes K10 pin 9 to -12V"),
        dict(line=1019, text="NET_C(GND, IC_N13.7, R19.2", action="remove",
             terms=[f"R{n}.2" for n in range(19, 27)],
             why="Board II sheet 1 pulls the ROM outputs to -12V, not ground"),
        dict(line=1095, text="ALIAS(VIDEO_OUT, RVID.1)", action="drop-line",
             why="the video leaves through C29, which MAME does not have"),
        dict(line=1267, text="ALIAS(HD1, IC_N8.5)", action="drop-line",
             why="Board II sheet 1: HD1 is N8 pin 6 (Q-bar); pin 5 is a stub"),
        dict(line=1271, text="ALIAS(HD2, IC_N12.5)", action="drop-line",
             why="Board II sheet 1: HD2 is N12 pin 6 (Q-bar); pin 5 is not drawn"),
        dict(line=1494, text="NET_C(VLD1, IC_M2.1, IC_M2.2)", action="drop",
             why="Board I sheet 1 puts /FIRE1 on M2 pins 1-2 and VLD1 on 13"),
        dict(line=1495, text="NET_C(FIRE1Q, IC_M2.13)", action="drop", why="as above"),
        dict(line=1499, text="NET_C(HMCE, IC_F2.12", action="drop",
             why="Board I makes its own HMCE from /HMCE with J3 pins 9-8; MAME takes Board II's"),
        dict(line=1500, text="NET_C(IC_D2.5, IC_F2.13)", action="drop",
             why="Board I sheet 1: D2.5 goes to F2.12"),
        dict(line=1501, text="NET_C(IC_E2.5, IC_F2.4)", action="drop",
             why="Board I sheet 1: E2.5 goes to F2.5"),
        dict(line=1502, text="NET_C(IC_D2.9, IC_F2.10)", action="drop",
             why="Board I sheet 1: the 2^3 latch D2.9 goes to C1.1 (the NAND), not F2"),
        dict(line=1503, text="NET_C(IC_E2.9, IC_C1.2)", action="drop",
             why="Board I sheet 1: the 2^2 latch E2.9 goes to F2.9, not C1"),
        dict(line=1506, text="NET_C(EXPL1Q, IC_C1.5)", action="drop",
             why="Board I takes /EXPL1 from its own J3.12, not Board II's"),
        dict(line=1630, text="NET_C(HMCE, IC_F4.1", action="drop", why="as for line 1499"),
        dict(line=1662, text="NET_C(EXPL2Q, IC_C5.2)", action="drop",
             why="Board I takes /EXPL2 from its own H3.10, not Board II's"),
        dict(line=1748, text="NET_C(R71A.2, C40A.1, HLE_NOISE.1)", action="drop",
             why="a random-noise stand-in; the noise transistor Q5 is put back"),
        dict(line=1750, text="NET_C(GND, HLE_NOISE.2", action="remove", terms=["HLE_NOISE.2"],
             why="as above"),
        dict(line=1761, text="NET_C(C31A.2, IC_K6.2)", action="drop",
             why="C31 feeds K6's input (MFC6040 pin 3); MAME puts it on the control pin"),
        dict(line=1834, text="ALIAS(MOTOR1, GND)", action="drop-line",
             why="the motor sound MAME silences is restored"),
        dict(line=1873, text="ALIAS(MOTOR2, GND)", action="drop-line", why="as above"),
        dict(line=1884, text="NET_C(C101.2, GND)", action="port", name="OUT1",
             why="on to VOLUME 1 and the LM380 amplifier, which MAME does not have; MAME grounds it"),
        dict(line=1885, text="NET_C(C106.2, GND)", action="port", name="OUT2",
             why="on to VOLUME 2 and the second LM380, likewise"),
    ],
    add_parts=[
        part("Q1", "Q", "2N3643", ANT), part("C15A", "C", "0.1uF", ANT), part("C16A", "C", "0.1uF", ANT),
        part("C17A", "C", "0.1uF", ANT), part("CR9A", "D", "1N914", ANT), part("CR12A", "D", "1N914", ANT),
        part("R41A", "R", "4.7K", ANT), part("R42A", "R", "100K", ANT), part("R49A", "R", "1K", ANT),
        part("R101", "R", "1K", CNT), part("R100", "R", "100", CNT),
        part("Q40", "Q", "2N3643", CNT), part("Q41", "Q", "2N5190", CNT),
        part("SW1", "SW", "25c/50c (coin logic)", SW), part("SW2", "SW", "25c/50c (play time)", SW),
        part("R48A", "R", "560", SW),
        part("Q5", "Q", "2N3643 (selected noise transistor)",
             "Board I sheet 2: the noise source MAME simulates with random noise"),
        part("R1", "R", "330", OSC), part("R2", "R", "330", OSC), part("R12", "R", "680", OSC),
        part("C1", "C", "0.1uF", OSC), part("Y1", "Y", "14.318MHz", OSC + "; Y1 is ours"),
        part("C29", "C", "10uF", "Board II sheet 1: the video output coupling capacitor"),
    ],
    add=[
        # Board I: coin latches as a 7404 pair each.
        sheet("Board I sheet 2: coin 1 NC (J3-13) on B6.13, cross-coupled with B6.10",
              "IC_B6.13", "IC_B6.10", "IC_D6.9", name="COIN1_NC"),
        sheet("Board I sheet 2: coin 1 NO (J3-14) on B6.11, cross-coupled with B6.12",
              "IC_B6.11", "IC_B6.12", "IC_N6.5", name="COIN1_NO"),
        sheet("Board I sheet 2: coin 2 NO (J3-12) on B6.5, cross-coupled with B6.2",
              "IC_B6.5", "IC_B6.2", "IC_N6.6", name="COIN2_NO"),
        sheet("Board I sheet 2: coin 2 NC (J3-11) on B6.1, cross-coupled with B6.6",
              "IC_B6.1", "IC_B6.6", "IC_D6.8", name="COIN2_NC"),
        # Board I: the 25c/50c switch.
        sheet(SW, "IC_D6.3", "SW1.1", "R48A.1"), sheet(SW, "GND", "R48A.2", "SW1.2"),
        sheet(SW, "IC_N6.1", "SW1.3"),
        sheet(SW, "R53A.1", "SW2.1"), sheet(SW, "PLAYTIME.1", "SW2.2"),
        # Board I: the antenna latch.
        sheet(ANT, "C17A.1", name="ANT"),
        sheet(ANT, "C17A.2", "CR12A.K", "R42A.1", "C16A.2", "Q1.B"),
        sheet(ANT, "GND", "CR12A.A", "R42A.2", "CR9A.K", "C15A.2"),
        sheet(ANT, "V5", "R49A.1"), sheet(ANT, "R49A.2", "C15A.1", "C16A.1"),
        sheet(ANT, "Q1.E", "CR9A.A"), sheet(ANT, "Q1.C", "IC_N4.1", "R41A.1"),
        sheet(ANT, "IC_N4.2", "IC_N4.3", "IC_N6.8"), sheet(ANT, "IC_N4.4", "R41A.2", "IC_E6.10"),
        # Board I: the coin counter driver.
        sheet(CNT, "IC_D6.10", "IC_A6.13"), sheet(CNT, "IC_A6.12", "R101.1"),
        sheet(CNT, "R101.2", "Q40.B"), sheet(CNT, "V5", "R100.1"), sheet(CNT, "R100.2", "Q40.C"),
        sheet(CNT, "Q40.E", "Q41.B"), sheet(CNT, "Q41.C", name="COIN_COUNTER"),
        sheet(CNT, "Q41.E", name="TV_GROUND"),
        # Board I: the noise transistor.
        sheet("Board I sheet 2: Q5's emitter is the noise source; base and collector grounded",
              "R71A.2", "C40A.1", "Q5.E"),
        sheet("as above", "GND", "Q5.B", "Q5.C"),
        # Board I: shot attenuator input.
        sheet("Board I sheet 2: C31 into K6 pin 3", "C31A.2", "IC_K6.3"),
        # Board I: shell 1 latch routing, M2 inputs, local HMCE and /EXPL.
        sheet("Board I sheet 1", "IC_D2.5", "IC_F2.12"), sheet("Board I sheet 1", "IC_E2.5", "IC_F2.5"),
        sheet("Board I sheet 1", "IC_E2.9", "IC_F2.9"), sheet("Board I sheet 1", "IC_D2.9", "IC_C1.1"),
        sheet("Board I sheet 1: HMCE, inverted on the board from /HMCE (J1-25)", "IC_J3.8",
              "IC_F2.13", "IC_F2.4", "IC_F2.10", "IC_C1.2", "IC_F4.1", "IC_F4.4", "IC_F4.10",
              "IC_C5.4", name="HMCE_B1"),
        sheet("Board I sheet 1: /HMCE in from J1-25", "HMCEQ", "IC_J3.9"),
        sheet("Board I sheet 1", "VLD1", "IC_M2.13"),
        sheet("Board I sheet 1", "FIRE1Q", "IC_M2.1", "IC_M2.2"),
        sheet("Board I sheet 1: /EXPL1 from J3.12", "IC_J3.12", "IC_C1.5"),
        sheet("Board I sheet 1: /EXPL2 from H3.10", "IC_H3.10", "IC_C5.2"),
        # Board II: its own /START and ATTRACT.
        sheet("Board II sheet 2: START in from J5-15 to M13 pin 3", "START", "IC_M13.3"),
        sheet("Board II sheet 2: /START is M13 pin 4", "IC_M13.4", name="STARTQ"),
        sheet("Board II sheet 1: the motor sounds' ATTRACT is M13 pin 2", "IC_M13.2",
              "IC_N13.1", "IC_N13.13"),
        # Board II: the oscillator.
        sheet(OSC, "IC_A7.13", "R2.1", "R12.1", "Y1.1"),
        sheet(OSC, "IC_A7.12", "R2.2", "C1.1", "IC_A7.1", "IC_A7.3"),
        sheet(OSC, "C1.2", "IC_A7.11", "R1.1"), sheet(OSC, "IC_A7.10", "R1.2", "Y1.2"),
        sheet(OSC, "GND", "R12.2"),
        # Board II: score counters, HD1/HD2, ROM supply, video out, motor 2's Q34.
        sheet("Board II sheet 2: D11 QA clocks E11 CPA", "IC_D11.12", "IC_E11.14", name="SCR1E"),
        sheet("Board II sheet 2: D11 QD clocks E11 CPB", "IC_D11.11", "IC_E11.1"),
        sheet("Board II sheet 1: HD1 from N8 Q-bar", "IC_N8.6", name="HD1"),
        sheet("Board II sheet 1: HD2 from N12 Q-bar", "IC_N12.6", name="HD2"),
        sheet("Board II sheet 1: K10 pin 9 and the output pull-downs on -12V", "-12V",
              "IC_R10.9", *[f"R{n}.2" for n in range(19, 27)]),
        sheet("Board II sheet 1: the summed video through C29", "R3V.2", "C29.1"),
        sheet("Board II sheet 1: C29 to J6-21", "C29.2", name="VIDEO_OUT"),
        sheet("Board II sheet 1: Q34's emitter on +12V, which MAME's commented-out block omits",
              "V12", "Q34.E"),
    ],
)

TARGETS = {
    "tank": TANK,

    # -----------------------------------------------------------------------
    # Cinematronics / Vectorbeam (Aaron Giles, CC0-1.0)
    # -----------------------------------------------------------------------
    "barrier-sound": dict(
        source="src/mame/cinematronics/nl_barrier.cpp",
        netlist="barrier",
        title="Barrier audio board (Vectorbeam 18-10781)",
        board=dict(
            name="Barrier audio board", mfr="Vectorbeam", year="1979", machine="barrier",
            drawing="Audio Board Schematic (Barrier) 18-10781 Rev A, in the Barrier manual "
                    "(doc 458c844b4ab1 p23) -- via MAME's netlist, compared with the sheet",
            revision="Vectorbeam audio board 18-10781 Rev A: triangle, diamond and explosion "
                     "sounds from three latch bits, mixed into a TL081 power amplifier.",
            coverage="Converted from MAME's netlist, which stops at the summing node: the "
                     "final amplifier (U6, Q4, Q5, R20-R23, R28-R30, C12-C14) and the "
                     "regulators U4/U7 are on the sheet but not in the netlist.",
            singleSource=True, netsTraced=False, netsConverted="mame",
        ),
        about=CINEMATRONICS + """

MAME's file says it is derived from the schematics in the Barrier manual, and the board
uses that sheet's designators (U1-U9, R1-R38, C1-C22, CR1-CR6, Q1-Q7).""",
        undo=[dict(line=272, text="NET_C(R19.2, GND)", action="port", name="R19_TO_C12",
                   why="the sheet takes R19 on to C12 and the volume pot R29, in the final "
                       "amplifier MAME does not simulate; MAME grounds it instead")],
        ports={"OUTPUT": "on the sheet, U6 pin 3: the final amplifier, which MAME does not simulate"},
        notes=["""\
Compared with the sheet (doc 458c844b4ab1 p23, 600 dpi), 2026-10-19: the noise source
(CR1, CR2, Q1, Q2 -- Q2's base is left open on the sheet too), U1 and U3, the triangle
and diamond envelopes (U2, Q3, Q6, R6-R13, R25-R27, CR3-CR6), U8 and the TL182 switch
U5, and U9 with R31-R37 all agree with the sheet part for part, pin for pin and value
for value, diode and transistor orientation included. Two differences, both MAME's
deliberate:

* Open question. The sheet draws U8 pin 6 straight onto the summing line (R13, R15, R37
  and the jumper to C11): a T-junction on the U8.6/R38 line below R38, no dot. MAME leaves
  it out (its line 239, commented) because the op-amp output would then hold the summing
  node and swamp every other sound; the file's header calls it a suspected typo. This file
  follows MAME. Not checked against a board.
* The sheet's JUMPER between the summing line and C11 is not in MAME, which treats it as
  closed (R17 sits on the jumper's C11 side on the sheet, on the summing line in MAME --
  the same net while the jumper is in). R19 goes to C12 and the volume pot R29 on the
  sheet, which are part of the final amplifier; MAME grounds it (line 272)."""],
    ),
    "armora-sound": sound(
        "Armor Attack", "Cinematronics", "1980", "armora", "the Armor Attack manual (doc 94be099bc6ca)",
        "Cinematronics audio board for Armor Attack: tank treads (566 VCO), shells, explosions, "
        "a CA3080 mixer.",
        "src/mame/cinematronics/nl_armora.cpp", "armora", CINEMATRONICS,
        ports={"OUTPUT": "to the final amplifier, which MAME does not simulate"},
        notes=["""\
MAME's file says 'Entire schematic needs a verification pass'. With HLE_TANK_VCO off the
tread VCO is MAME's own description of the board's circuit; it uses Q1, which MAME
declares only in a comment ('not used' -- by the stand-in), so the declaration is
restored.""", UNCHECKED]),
    "boxingb-sound": sound(
        "Boxing Bugs", "Cinematronics", "1981", "boxingb", "the Boxing Bugs manual (doc 4cc749f9b585)",
        "Cinematronics audio board for Boxing Bugs: music, chirps, cannon and bounce VCOs, a "
        "CA3080 mixer.",
        "src/mame/cinematronics/nl_boxingb.cpp", "boxingb", CINEMATRONICS,
        ports={"OUTPUT": "to the final amplifier, which MAME does not simulate"},
        notes=["MAME's file calls this netlist 'WIP'.", UNCHECKED]),
    "ripoff-sound": sound(
        "Rip Off", "Cinematronics", "1980", "ripoff", "the Rip Off manual (doc 3a2cac26e2cb)",
        "Cinematronics audio board for Rip Off: laser, torpedo, motor and beep, two background "
        "VCOs, a CA3080 mixer.",
        "src/mame/cinematronics/nl_ripoff.cpp", "ripoff", CINEMATRONICS,
        ports={"OUTPUT": "to the final amplifier, which MAME does not simulate"},
        notes=["""\
MAME's two hacks here are value changes and both are undone by their switches: the
motor-1 and beep voltage triggers use the sheet's 4.7K (MAME's hack is 100 ohms), and
the resistances into the CA3080s IC12 and IC6 are the sheet's, not five times them.""",
               UNCHECKED]),
    "solarq-sound": sound(
        "Solar Quest", "Cinematronics", "1981", "solarq", "the Solar Quest manual (doc 289dbfe65fee)",
        "Cinematronics audio board for Solar Quest: music, capture and photon VCOs, a fire "
        "network of TL081s and CA3080s.",
        "src/mame/cinematronics/nl_solarq.cpp", "solarq", CINEMATRONICS,
        ports={"OUTPUT": "to the final amplifier, which MAME does not simulate"},
        notes=[UNCHECKED]),
    "speedfrk-sound": sound(
        "Speed Freak", "Vectorbeam", "1979", "speedfrk", "the Speed Freak manual (doc a9a0d255b9db)",
        "Vectorbeam audio board for Speed Freak: the engine sound, all TTL counters and shift "
        "registers into one TL081.",
        "src/mame/cinematronics/nl_speedfrk.cpp", "speedfrk", CINEMATRONICS,
        ports={"OUTPUT": "to the final amplifier, which MAME does not simulate"},
        notes=["""\
MAME's file calls the manual's schematics 'utterly terrible' and credits corrected
schematics from Brian Tarachi and connections verified by Frank Palazzolo, so this
reading has had more checking than most -- and may differ from the manual's sheet
where the manual is wrong. With HLE_CLOCK_GENERATOR off the 2 MHz clock is MAME's U10
pin 6 (an alias in the real-circuit branch).""", UNCHECKED]),
    "starcas-sound": sound(
        "Star Castle", "Cinematronics", "1980", "starcas", "the Star Castle manual (doc 7f01a2f3c820)",
        "Cinematronics audio board for Star Castle: background and laser VCOs (566), shield, "
        "explosion and fireball, a CA3080 mixer. War of the Worlds uses the same board with "
        "its inputs in a different order; this is the Star Castle wiring.",
        "src/mame/cinematronics/nl_starcas.cpp", "starcas", CINEMATRONICS,
        defines={"VARIANT_STARCASTLE": 0, "VARIANT_WOTW": 1, "SOUND_VARIANT": 0},
        compared="compared with sheet 2 of 2 (72-10861-02, p87)",
        ports={"OUTPUT": "to the final amplifier, which MAME does not simulate"},
        notes=["""\
MAME's file says it is derived from the schematics and parts list in the Star Castle
manual. Compared with sheet 2 of the audio board, 72-10861-02 (doc 7f01a2f3c820 p87),
2026-10-19: the noise generator (IC14 S2688, IC15 follower, C16-C18, R28), the +2.2V
reference (Q2, R29-R31, C19), the 60 Hz 555 IC16 (R32, R33, C20, C21), the laser VCO
(IC17 566, C22-C25, R41-R43, Q5, R44-R46, D10) with the 74LS393 IC12 and its taps
R47-R49, the CA3080 IC18's input network (R57-R62), the summing follower IC26 (R127, C48)
and the output amplifier IC27 (R125, R126, the SJ junction, the 10K volume pot R128) all
agree with MAME pin for pin and value for value. Sheet 1 (p86: latches, shift register,
the background VCO) was not compared, nor the other four CA3080 channels or the star
sound 555s beyond their values (R112-R119, which agree)."""]),
    "starhawk-sound": sound(
        "Starhawk", "Cinematronics", "1979", "starhawk", "the Star Hawk manual (doc 87193443ac92)",
        "Cinematronics audio board for Starhawk: ship and two laser VCOs (556), PROM-driven "
        "sequencing, a CA3080.",
        "src/mame/cinematronics/nl_starhawk.cpp", "starhawk", CINEMATRONICS,
        loads={"RDUMMY": "a 100K to ground on the 556's output, which MAME's file says the "
                         "board leaves unconnected"},
        ports={"OUTPUT": "to the final amplifier, which MAME does not simulate"},
        notes=["""\
This board's designators are column-and-row grid positions (IC5D, IC4A ...), written
U5D, U4A here. MAME's file credits Jay Gallagher with verifying the PCB components.""",
               UNCHECKED]),
    "sundance-sound": sound(
        "Sundance", "Cinematronics", "1979", "sundance", "the Sundance manual (doc 7130101e6e69)",
        "Cinematronics audio board for Sundance: pings and bongs (555s), a whoosh, a wideband "
        "noise generator, CA3080 mixing.",
        "src/mame/cinematronics/nl_sundance.cpp", "sundance", CINEMATRONICS,
        ports={"OUTPUT": "to the final amplifier, which MAME does not simulate"},
        notes=["""\
The wideband noise generator here is MAME's description of the real circuit (the
HLE_NOISE_GEN branch off). MAME has never run that branch -- it simulates the noise with
a random source -- so it is the least-checked part of this file.""", UNCHECKED]),
    "tailg-sound": sound(
        "Tailgunner", "Cinematronics", "1979", "tailg", "the Tail Gunner manual (doc 22a6fb78dd5a)",
        "Cinematronics audio board for Tailgunner: hyperspace and laser VCOs, explosion, a "
        "wideband noise generator.",
        "src/mame/cinematronics/nl_tailg.cpp", "tailg", CINEMATRONICS,
        ports={"OUTPUT": "to the final amplifier, which MAME does not simulate"},
        notes=["""\
Two MAME changes are undone by their switches: the diodes D8/D9 on the 74LS123's
Rext/Cext pins are back (MAME snips them for speed), and the pull-ups MAME adds to the
74LS125 outputs are gone. The hyperspace VCO's real circuit uses Q1, which MAME declares
only in a comment ('not used' -- by the stand-in); the declaration is restored.""", UNCHECKED]),

    # -----------------------------------------------------------------------
    # Sega / Gremlin (Aaron Giles, CC0-1.0)
    # -----------------------------------------------------------------------
    "astrob-sound": sound(
        "Astro Blaster", "Sega", "1981", "astrob", "the Astro Blaster manual (doc 7c9390526e01)",
        "Sega G-80 Astro Blaster sound board: sonar, two lasers, invaders, warp and bonus "
        "sounds from CD4000-series timing, 555s and TL084 filters.",
        "src/mame/sega/nl_astrob.cpp", "astrob", SEGA,
        defines={"ENABLE_SONAR_ALT": 0},
        ports={"OUTPUT": "the board's output, after the mute"},
        notes=["""\
Undone beyond the switches: twenty resistors in the sonar circuit that MAME multiplies by
1.001-1.049 (its comment: the circuit 'relies on subtle part differences') are written
at their nominal value; and ENABLE_SONAR_ALT, which adds four 1M
resistors to a 0.1V source to start the oscillators, is off. The four slow oscillators
MAME runs as ideal clocks (OSC1-OSC4) are ports, and the timing parts it parks on a rail
in their place are listed above. The mute is an AFUNC in MAME, so the output is a port
fed from it.""", UNCHECKED]),
    "elim-sound": sound(
        "Eliminator", "Gremlin", "1981", "elim2", "the Eliminator manual (doc cff008c00810)",
        "Sega G-80 Eliminator sound board: background, skitter, two torpedo and explosion "
        "sounds, CA3080 VCAs. Zektor uses the same board; this is the Eliminator wiring.",
        "src/mame/sega/nl_elim.cpp", "elim", SEGA,
        defines={"VARIANT_ELIMINATOR": 0, "VARIANT_ZEKTOR": 1, "SOUND_VARIANT": 0},
        not_parts={f"R_PSG_{i}": "a 1K from +5V standing in for one output of the sound chip "
                                 "(PSG) MAME emulates separately" for i in (1, 2, 3)},
        ports={"OUTPUT": "the board's output"},
        notes=["""\
The 200 Hz, 100 Hz, 50 Hz and 10 Hz clocks are ideal clocks in MAME (CLOCK), whatever
generates them on the board; their nets are ports, and the timing parts MAME parks on a
rail in their place are listed above. The PSG's three outputs arrive through resistors
MAME invents (R_PSG_1-3), so that summing node is a port.""", UNCHECKED]),
    "frogs-sound": sound(
        "Frogs", "Gremlin", "1978", "frogs", "the Frogs manual (doc a2ffd17fee9b)",
        "Gremlin Frogs sound board: hop, jump, zip, splash, buzz, boing and croak from 555s "
        "and 741 filters.",
        "src/mame/sega/nl_frogs.cpp", "frogs", SEGA,
        loads={"RU4": "a 100K to ground on a 555 output the board leaves unconnected -- MAME's "
                      "file says the netlist 'doesn't like unconnected 555 outputs'",
               "RU15": "a 100K to ground on a 555 output the board leaves unconnected -- MAME's "
                       "file says the netlist 'doesn't like unconnected 555 outputs'"},
        ports={"OUTPUT": "the board's output"},
        notes=[UNCHECKED]),
    "spacfury-sound": sound(
        "Space Fury", "Sega", "1981", "spacfury", "the Space Fury manual, which this site does not "
        "hold (its Space Fury documents are memos and a monitor note)",
        "Sega G-80 Space Fury sound board: star spin, shoot, explosions, craft and docking "
        "sounds, CA3080 VCAs.",
        "src/mame/sega/nl_spacfury.cpp", "spacfury", SEGA,
        not_parts={f"R_PSG_{i}": "a 1K from +5V standing in for one output of the sound chip "
                                 "(PSG) MAME emulates separately" for i in (1, 2, 3)},
        ports={"OUTPUT": "the board's output"},
        notes=["""\
The oscillators MAME runs as ideal clocks (CLOCK) are ports, and the timing parts it
parks on a rail in their place are listed above; SPLIT_SHARED_OSCILLATORS is off, so
each oscillator drives everything the board has it drive. The site holds no Space Fury
manual, so there is no sheet here to compare this with.""", UNCHECKED]),
}
