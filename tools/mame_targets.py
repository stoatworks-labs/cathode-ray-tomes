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
              its terms are not), "drop-line" (any statement), "keep" (a tie in
              a block MAME calls unused that the sheet does draw)
  hack_macros {macro: why}: a function-like macro the file itself calls a hack;
              every tie it makes becomes nc
  restore     [(first, last)]: commented-out lines that are the board's circuit
  not_parts   {MAME name: why}: a part MAME adds that stands in for something
              the board has (a sound chip's output); its nets become ports
  loads       {MAME name: why}: a dummy load MAME hangs on a pin the board
              leaves open; the pin becomes nc
  ports       {alias: why}: named nets that leave the board (the audio output)
  designators {MAME name: designator} where the rule (IC_A7 -> UA7, U8 -> U8,
              IC6 -> U6, _6F -> U6F, passives as written) is not enough
  ic_names    a regex whose group 1 is an IC's board position, for a file
              that names ICs some other way (MC3340_H2 -> UH2)
  sections    [(macro, regex, part)]: declarations of one section of a
              package (LM3900(H5_3) is amplifier 3 of the LM3900 at H5); the
              regex's groups are the package and the section
  models      {MAME model: (stock part, why)}: a model MAME builds of a stock
              part under its own name (LM324_VM5V12 is an LM324)
  shorts      {MAME name: why}: a part MAME puts in series where the board has
              a wire; its two ends become one node
  values      {MAME name: (value, why)}: a part MAME declares by its model ("NPN",
              "D(BV=9.1 ...)") written by its part number -- not a correction
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


HOWELL = """\
Colin Douglas Howell's netlists for Midway's 8080 driving and shooting games are the most
carefully documented in MAME: every value is argued from the schematic, the PCB drawings
and board photos, and the file says where they disagree. ICs are named by their board
position. He declares each LM3900 amplifier on its own, numbered _1 to _4 as the LM3900
data sheet numbers them; they are written on their package's pins here. The CPU's sound
latches arrive as ports, named after the latch pin MAME's LOGIC_INPUT stands in for
(I_F4_2 is latch F4 pin 2)."""


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


def within(section, *adds):
    """Sheet corrections that belong to one section of MAME's file."""
    return [dict(a, section=section) for a in adds]


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
        *within('Coin Handling',
            sheet("Board I sheet 2: coin 1 NC (J3-13) on B6.13, cross-coupled with B6.10",
                  "IC_B6.13", "IC_B6.10", "IC_D6.9", name="COIN1_NC"),
            sheet("Board I sheet 2: coin 1 NO (J3-14) on B6.11, cross-coupled with B6.12",
                  "IC_B6.11", "IC_B6.12", "IC_N6.5", name="COIN1_NO"),
            sheet("Board I sheet 2: coin 2 NO (J3-12) on B6.5, cross-coupled with B6.2",
                  "IC_B6.5", "IC_B6.2", "IC_N6.6", name="COIN2_NO"),
            sheet("Board I sheet 2: coin 2 NC (J3-11) on B6.1, cross-coupled with B6.6",
                  "IC_B6.1", "IC_B6.6", "IC_D6.8", name="COIN2_NC")),
        # Board I: the 25c/50c switch.
        *within('Coin Handling',
            sheet(SW, "IC_D6.3", "SW1.1", "R48A.1"), sheet(SW, "GND", "R48A.2", "SW1.2"),
            sheet(SW, "IC_N6.1", "SW1.3"),
            sheet(SW, "R53A.1", "SW2.1"), sheet(SW, "PLAYTIME.1", "SW2.2")),
        # Board I: the antenna latch.
        *within('Antenna',
            sheet(ANT, "C17A.1", name="ANT"),
            sheet(ANT, "C17A.2", "CR12A.K", "R42A.1", "C16A.2", "Q1.B"),
            sheet(ANT, "GND", "CR12A.A", "R42A.2", "CR9A.K", "C15A.2"),
            sheet(ANT, "V5", "R49A.1"), sheet(ANT, "R49A.2", "C15A.1", "C16A.1"),
            sheet(ANT, "Q1.E", "CR9A.A"), sheet(ANT, "Q1.C", "IC_N4.1", "R41A.1"),
            sheet(ANT, "IC_N4.2", "IC_N4.3", "IC_N6.8"), sheet(ANT, "IC_N4.4", "R41A.2", "IC_E6.10")),
        # Board I: the coin counter driver.
        *within('Coin Counter',
            sheet(CNT, "IC_D6.10", "IC_A6.13"), sheet(CNT, "IC_A6.12", "R101.1"),
            sheet(CNT, "R101.2", "Q40.B"), sheet(CNT, "V5", "R100.1"), sheet(CNT, "R100.2", "Q40.C"),
            sheet(CNT, "Q40.E", "Q41.B"), sheet(CNT, "Q41.C", name="COIN_COUNTER"),
            sheet(CNT, "Q41.E", name="TV_GROUND")),
        # Board I: the noise transistor.
        *within('Noise Generation',
            sheet("Board I sheet 2: Q5's emitter is the noise source; base and collector grounded",
                  "R71A.2", "C40A.1", "Q5.E"),
            sheet("as above", "GND", "Q5.B", "Q5.C")),
        # Board I: shot attenuator input.
        *within('Shot Sound',
            sheet("Board I sheet 2: C31 into K6 pin 3", "C31A.2", "IC_K6.3")),
        # Board I: shell 1 latch routing, M2 inputs, local HMCE and /EXPL.
        *within('Shell 1 Motion',
            sheet("Board I sheet 1", "IC_D2.5", "IC_F2.12"), sheet("Board I sheet 1", "IC_E2.5", "IC_F2.5"),
            sheet("Board I sheet 1", "IC_E2.9", "IC_F2.9"), sheet("Board I sheet 1", "IC_D2.9", "IC_C1.1"),
            sheet("Board I sheet 1: HMCE, inverted on the board from /HMCE (J1-25)", "IC_J3.8",
                  "IC_F2.13", "IC_F2.4", "IC_F2.10", "IC_C1.2", "IC_F4.1", "IC_F4.4", "IC_F4.10",
                  "IC_C5.4", name="HMCE_B1"),
            sheet("Board I sheet 1: /HMCE in from J1-25", "HMCEQ", "IC_J3.9"),
            sheet("Board I sheet 1", "VLD1", "IC_M2.13"),
            sheet("Board I sheet 1", "FIRE1Q", "IC_M2.1", "IC_M2.2"),
            sheet("Board I sheet 1: /EXPL1 from J3.12", "IC_J3.12", "IC_C1.5"),
            sheet("Board I sheet 1: /EXPL2 from H3.10", "IC_H3.10", "IC_C5.2")),
        # Board II: its own /START and ATTRACT.
        *within('Game Timer / Attract',
            sheet("Board II sheet 2: START in from J5-15 to M13 pin 3", "START", "IC_M13.3"),
            sheet("Board II sheet 2: /START is M13 pin 4", "IC_M13.4", name="STARTQ"),
            sheet("Board II sheet 1: the motor sounds' ATTRACT is M13 pin 2", "IC_M13.2",
                  "IC_N13.1", "IC_N13.13")),
        # Board II: the oscillator.
        *within('Main Timing & Sync',
            sheet(OSC, "IC_A7.13", "R2.1", "R12.1", "Y1.1"),
            sheet(OSC, "IC_A7.12", "R2.2", "C1.1", "IC_A7.1", "IC_A7.3"),
            sheet(OSC, "C1.2", "IC_A7.11", "R1.1"), sheet(OSC, "IC_A7.10", "R1.2", "Y1.2"),
            sheet(OSC, "GND", "R12.2")),
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

# Eliminator's clocks, which MAME runs as ideal clocks with the oscillator's R and C parked:
# (MAME's first line, its CLOCK, the CD4069, its pins (in, out, in, out), R, C, where the
# clock goes, the sheet that draws it).
ELIM_OSC = [
    (864, "_200HZACLK", "U32", ("5", "6", "9", "8"), "R142", "C68", "R137.1", 8),
    (872, "_200HZBCLK", "U32", ("13", "12", "11", "10"), "R139", "C65", "R138.1", 8),
    (880, "_10HZCLK", "U32", ("1", "2", "3", "4"), "R143", "C69", "R144.2", 8),
    (888, "_50HZCLK", "U31", ("1", "2", "3", "4"), "R141", "C67", "R134.1", 8),
    (897, "_100HZCLK", "U31", ("5", "6", "9", "8"), "R140", "C66", "R135.1", 7),
]


def oscillator(u, pins, r, c, out, sht):
    """A two-inverter RC oscillator as the sheet draws it: R from the first inverter's output
    back to its input, C from that input to the second inverter's output, the clock."""
    i1, o1, i2, o2 = pins
    why = f"sheet {sht}: a CD4069 RC oscillator, which MAME replaces with an ideal clock"
    return [sheet(why, f"{u}.{o1}", f"{u}.{i2}", f"{r}.1"),
            sheet(why, f"{u}.{i1}", f"{r}.2", f"{c}.1"),
            sheet(why, f"{u}.{o2}", f"{c}.2", out)]


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
        compared="compared with the sheets (72-11141-02 rev A, pp84-86)",
        ports={"OUTPUT": "IC26's output, to J1-8 and the coin-door volume pot, whose wiper "
                         "returns to the final amplifier IC24, which MAME does not simulate"},
        notes=["""\
MAME's file says 'Entire schematic needs a verification pass'. With HLE_TANK_VCO off the
tread VCO is MAME's own description of the board's circuit; it uses Q1, which MAME
declares only in a comment ('not used' -- by the stand-in), so the declaration is
restored.""", """\
Compared with the audio board sheets 1-3, 72-11141-02 rev A (doc 94be099bc6ca pp84-86,
native 300 dpi), the assembly drawing 72-11141-01 (p87) and the parts list 38-11141-01
(pp57-59), 2026-10-20: the input buffers IC1 and IC27, the shift register IC2 and latch
IC3 (OUT 0+ to OUT 7+ on J2-11 to J2-16, MAME's port names), the tank motor (IC6 with
R2, R3, C11, C12; IC8 loaded from TS0+-TS3+; IC9, IC10, IC11; R6, R7, C13, C14), the tread
squeak (IC13, the 7406 IC7, the low-leakage switches Q14-Q19 and R95-R109 on sheet 2,
R14-R23, C18, C19) with the 566 VCO IC15 (R11, C15-C17) and the converter Q1, R4, R12, R13,
D5, D8 exactly as MAME's HLE_TANK_VCO-off branch has them, the noise source (IC17, C20,
C21, R26, IC18), all five envelope switches and CA3080 channels (Q2-Q11, R27-R83, R94,
C22-C34, IC19-IC22), the beep 555 IC23 (R81-R83, C35-C37) and the summing follower IC25
with C43, R91 and the SJ amplifier IC26 (R90, R92) all agree with MAME pin for pin and
value for value, transistor and diode orientation included. The parts list agrees with
every IC, transistor (Q1 is a 2N3904), diode and capacitor; C28, which MAME's file could
not place, is one of six 0.1uF bypass capacitors on -15V. Nothing needed correcting.

Open question, as printed and not settled:
* The parts list gives 111 resistors where both drawings place 109: it carries an 82K and
  a second 910K that neither the sheets nor the assembly drawing have (R82 is 8.2K on
  both; at 82K IC23 would not oscillate). Its 2.7K and 4.7K counts (13 and 8) are also
  swapped against both drawings (8 and 13). This file follows the drawings.

Not in this file: the final amplifier (IC24, Q12, Q13, R24, R25, R84-R89, C38-C42, the
volume pot R93) and the regulators IC4/IC5, which are on sheets 1 and 3 with the values
MAME's comments give."""]),
    "boxingb-sound": sound(
        "Boxing Bugs", "Cinematronics", "1981", "boxingb", "the Boxing Bugs manual (doc 4cc749f9b585)",
        "Cinematronics audio board for Boxing Bugs: music, chirps, cannon and bounce VCOs, a "
        "CA3080 mixer.",
        "src/mame/cinematronics/nl_boxingb.cpp", "boxingb", CINEMATRONICS,
        compared="compared with the sheets (72-11516-00 rev X14, pp94-99)",
        undo=[dict(line=786, text="NET_C(U25.5, GND)", action="drop",
                   why="a typo for U2.5, the 74S04 input MAME's HLE branch borrows (its line "
                       "781); sheet 6 draws U25 pin 5 (1Q) unconnected, as MAME's own HINT at "
                       "line 1602 says"),
              dict(line=1160, text="NET_C(U58.7, GND)", action="nc",
                   why="sheet 3 draws U58 pin 7 (DIS) unconnected; MAME's own comment says "
                       "'not connected'")]
             + [dict(line=n, text=t, action="drop-line",
                     why="MAME's ideal clock standing in for the crystal Y1")
                for n, t in ((438, "CLOCK(Y1"), (439, "Y1.GND"), (440, "Y1.VCC"))],
        undo_notes=["lines 438-440: MAME's CLOCK(Y1) and its supply ties are dropped; Y1 is the "
                    "crystal the sheet draws"],
        add_parts=[part("Y1", "Y", "20MHz", "sheet 6: the crystal of the U2 oscillator, which "
                                            "MAME declares as an ideal clock")],
        add=[sheet("sheet 6: U2's three spare inputs tied together to ground",
                   "GND", "U2.5", "U2.9", "U2.11"),
             sheet("sheet 5: U20 pin 6 is WC1+, to the shaft encoder", "U20.6", name="WC1_P"),
             sheet("sheet 5: U20 pin 4 is WC2+, to the shaft encoder", "U20.4", name="WC2_P"),
             sheet("sheet 5: Q29's collector into U20 pin 5", "U20.5", name="Q29_COLLECTOR"),
             sheet("sheet 5: Q30's collector into U20 pin 3", "U20.3", name="Q30_COLLECTOR")],
        ports={"OUTPUT": "U54's output, to J1-8 and the coin-door volume pot, whose wiper "
                         "returns on J1-3 to the final amplifier, which MAME does not simulate",
               **{p: "the shaft encoder on sheet 5, which MAME does not emulate"
                  for p in ("WC1_P", "WC2_P", "Q29_COLLECTOR", "Q30_COLLECTOR")}},
        notes=["MAME's file calls this netlist 'WIP'.", """\
Compared with the audio board schematic 72-11516-00 "Audio Board 'BB'" rev X14, sheets 1-6
(doc 4cc749f9b585 pp94-99, native 300 dpi), 2026-10-20: all 55 ICs' types; the input
conditioning from J2 (OUTPUT 0-4 and 7 on J2-11 to J2-16, through D25-D30, U50, U40, U30,
R177/R180/R181 and C67/C69/C70) and the serial latches U49/U39 into U48, U38 and U47; the
crystal oscillator, U23, U13/U9/U29 and the divide-by-eleven music clock U43/U24/U33/U44;
the noise register U1, U11, U12, U32, U35; every sound channel -- bell, chirping birds,
dying bug, egg cracking, beetle on screen, bounce, cannon, loud and soft explosions, bug
pushing -- with its 566s, 555s and CA3080s; the music generator U46/U36/U37, U25, U34,
U15, U35, U45 and its CA3080 U67 with Q31-Q34; and the summing amplifier U54 with the CS
follower U55 all agree with MAME pin for pin and value for value (R9-R209, C11-C75),
transistor and diode orientation included. The manual has no audio board parts list.
Corrected from the sheet, none of it in a sound path: U25 pin 5 is unconnected and U2's
spare inputs 5, 9 and 11 are grounded (MAME's line 786 ties "U25.5" to ground, a typo for
U2.5); U58's discharge pin 7 is unconnected, not grounded; Y1 is a 20 MHz crystal, not an
ideal clock; and U20 pins 3-6 are the shaft encoder's (sheet 5), not bare pins.

Open questions, as printed and not settled:
* The sheet labels U36's LOAD (pin 9) "MLOAD+", where U46 and U37 beside it read
  "MLOAD-". MAME uses MLOAD- on purpose ("schems say MLOAD_P, but solarq says MLOAD_M"),
  the theory text (p35) says all three counters load on M Load-, and on MLOAD+ the middle
  four bits of the divider could never count. This file follows MAME.
* The theory text (p33) takes the beetle oscillator's output from U20-4; the sheet and
  MAME take it from pin 2, and sheet 5 gives U20 3/4 to the shaft encoder.

Drafting slips where MAME follows the part, not the label: U1's second half is labelled
clock 12, CLR 13 (the 74LS393 is the other way round); U9's second half K 10, CLR 11; the
dying bug's 39K is labelled R31 (it is R37 by position, as MAME has it); R196 is labelled
R96. Not in this file: the shaft encoder (sheet 5, which also carries U6, a 74LS74 MAME's
list of omitted parts leaves out), the regulators (U69 7815 and U68 7915 on the sheet,
the other way round in MAME's comments) and +2.2V reference, and the final amplifier."""]),
    "ripoff-sound": sound(
        "Rip Off", "Cinematronics", "1980", "ripoff", "the Rip Off manual (doc 3a2cac26e2cb)",
        "Cinematronics audio board for Rip Off: laser, torpedo, motor and beep, two background "
        "VCOs, a CA3080 mixer.",
        "src/mame/cinematronics/nl_ripoff.cpp", "ripoff", CINEMATRONICS,
        compared="compared with the sheet (SD207201 Rev A, p80)",
        undo=[dict(line=679, text="NET_C(GND, IC14.2, IC14.3, IC15.2, IC15.3)", action="remove",
                   terms=["IC14.2", "IC15.2", "IC15.3"],
                   why="of these the sheet grounds only IC14 pin 3; IC14 pin 2 is the "
                       "pre-amplifier's summing junction, and IC15's inputs are the final "
                       "amplifier's")],
        add=[sheet("p80: R45 and R49 meet at IC14 pin 2", "R45.1", "IC14.2"),
             sheet("p80: IC14 pin 6 drives the final amplifier", "IC14.6", name="FINAL_AMP")],
        ports={"OUTPUT": "R45 and R49 into IC14 pin 2, the pre-amplifier's summing junction "
                         "(R46 12K feedback)",
               "FINAL_AMP": "IC14 pin 6, into the final amplifier (R46, IC15, Q6, Q7, the "
                            "volume pot), which MAME does not simulate"},
        notes=["""\
MAME's two hacks here are value changes and both are undone by their switches: the
motor-1 and beep voltage triggers use the sheet's 4.7K (MAME's hack is 100 ohms), and
the resistances into the CA3080s IC12 and IC6 are the sheet's, not five times them.""", """\
Compared with the sheet, Schematic Audio Board - Rip Off SD207201 Rev A (doc 3a2cac26e2cb
p80, native 300 dpi), with the assembly drawing AE207201 Rev A (p79) and the parts list
PL207201 (pp58-60), 2026-10-20: the input buffers IC25 (J4-11/12/13), the shift register
IC8 and latch IC9 with R24; the background DAC (IC10, R23, D1, R25-R30, IC19, R76), both
background VCOs (IC20, IC21, C30, C31, R77-R82, D6-D11), the level translator Q10
(R83-R85) and the counter IC22 with R86-R91 and C32; the laser and torpedo channels (R56,
R66, C26-C29, D2-D5, IC16, IC17, R57-R61, R67-R71, Q8, Q9, and IC18 with R62-R65 and
R72-R75 into R47, R48 and C21); the explosion (IC1 S2688, R1-R10, C1-C8, IC2, the one-shot
IC4, Q1, IC3), beep (IC5, R11-R18, R20-R22, C9-C11, Q2, Q3, IC6) and motor 1 (IC11, IC13,
R31-R44, C14-C19, Q4, Q5, IC12) channels; and the summing node (R19, D12/D13, the
follower IC7, C12, R45, R49) all agree with MAME pin for pin and value for value, diode
and transistor orientation included. The values MAME's hacks change are the sheet's: R11
and R40 are 4.7K, R18 is 820K and R36 is 1M on the schematic, the assembly drawing and in
the parts list's counts. IC18's taps are not binary-ordered (QC takes the smallest
resistor); the sheet draws both halves that way and MAME follows it. MAME differs only at
the final-amplifier boundary: R45 and R49 go into IC14 pin 2 and only IC14 pin 3 is
grounded (MAME line 679 grounds both inputs of IC14 and IC15); corrected above.

Open questions, as printed and not settled:
* The parts list gives one 1N5240 where both drawings have three (D1, D12, D13, and note
  3 names all three), and three 470-ohm and eight 1K resistors where both drawings have
  two and nine; the totals agree and the list names no positions. This file follows the
  drawings.
* IC4's reset (pin 4) is not drawn; MAME ties it to +5V ("not documented in schematics"),
  the only way the one-shot works.

The jumpers W1-W8 are taken as fitted, as MAME takes them; R50 is drawn dashed and noted
optional, and C13 and C20 are not used (note 6). Not in this file: the final amplifier and
regulators (R46, IC15, Q6, Q7, IC23, IC24), which are on the sheet. MAME's comment calls
Q6 (2N6292) a PNP; it is an NPN, and the sheet draws it as one."""]),
    "solarq-sound": sound(
        "Solar Quest", "Cinematronics", "1981", "solarq", "the Solar Quest manual (doc 289dbfe65fee)",
        "Cinematronics audio board for Solar Quest: music, capture and photon VCOs, a fire "
        "network of TL081s and CA3080s.",
        "src/mame/cinematronics/nl_solarq.cpp", "solarq", CINEMATRONICS,
        compared="compared with the sheets (72-11366 rev B, pp97-99, and rev A, pp90-92)",
        undo=[dict(line=n, text=t, action="drop-line",
                   why="MAME's ideal clock standing in for the crystal Y1")
              for n, t in ((317, "CLOCK(Y1"), (318, "Y1.GND"), (319, "Y1.VCC"))],
        undo_notes=["lines 317-319: MAME's CLOCK(Y1) and its supply ties are dropped; Y1 is the "
                    "crystal the sheet draws"],
        add_parts=[part("Y1", "Y", "20MHz", "sheet 2: the crystal of the U24 oscillator, which "
                                            "MAME declares as an ideal clock; parts list item 92")],
        fix_parts={u: ("CA3080A", "sheet 2 and the parts list (item 22, 'IC (Special)', qty "
                                  "2): the fire network's two CA3080s are the A grade")
                   for u in ("U44", "U46")},
        ports={"OUTPUT": "U50's output, to J1-8 and the coin-door volume pot R152, whose wiper "
                         "returns on J1-3 to the final amplifier U51, which MAME does not "
                         "simulate"},
        notes=["""\
Compared with the audio board schematic 72-11366 "Solar Quest Audio" rev B, sheets 1-3
(doc 289dbfe65fee pp97-99, native 300 dpi), with the rev A printing (pp90-92) for faint
values, and the audio parts list (pp65-67), 2026-10-20: all 50 ICs' types; the inputs from
J2 (OUTPUT 0, 1, 4 and 7 on J2-11, -12, -15 and -16, as the CPU board's J4 table on p80
gives them) through the 7414s U1/U2 into the shift registers U3/U4 and the latches U5, U6
and U7; the music divider U8-U10 with its latch gating U19-U23; the clock chain (U24, U25,
the divide-by-eleven U26/U15, U27); the nuke generator (U13, U14, the divide-by-191
U11/U12, U15-U18); the noise register U28-U31 with U18, U24 and U32; every channel --
loud and soft explosion, thrust, capture (Q11-Q13, U42 566, U21), photon (U35, Q7-Q10,
U36-U41), fire (Q14/Q15, U43-U47) and the three music envelopes (Q16-Q21) into U48 -- and
the CS follower U49 and summing amplifier U50 all agree with MAME pin for pin and value for
value (R1-R164, C1-C31), transistor and diode orientation included. The parts list agrees
with every IC, resistor, capacitor, diode and transistor quantity, except R155 in the final
amplifier. Corrected from the sheet, none of it in a sound path: Y1 is a 20 MHz crystal, not
an ideal clock, and U44 and U46 are CA3080As (the parts list's 'special' grade, same
pinout), not plain CA3080s. The two printings differ only in labels.

Open questions, as printed and not settled:
* The theory text's sound check table (p33) puts Capture on U7 pin 9 and Fire on pin 12;
  both printings of the sheet, and MAME, have FIRE- on 9 and CAPTURE- on 12. This file
  follows the sheet.
* R155 in the final amplifier is printed 150K; the parts list has no 150K and two 150-ohm
  resistors. Not in this file.

Drafting slips where MAME follows the part, not the label: U10's pins 9 and 7 are labelled
ENP and LOAD inside the box (the signals on them, MLOAD- and MEN+, are right); rev B's sheet
2 prints U18 as "-S86" (LS86 on rev A, on sheet 1 and in the parts list). MAME grounds U2
pins 8 and 10, which are 7414 outputs, and leaves the inputs 9 and 11 open -- the sheet's
note 6 says all four are unused, and this file has all four nc. Not in this file: the final
amplifier (U51, Q22, Q23, R152-R160, C32-C36, D9, D10), the regulators U52/U53 with D1-D4
and C37-C43, and the unnumbered decoupling capacitors."""]),
    "speedfrk-sound": sound(
        "Speed Freak", "Vectorbeam", "1979", "speedfrk", "the Speed Freak manual (doc a9a0d255b9db)",
        "Vectorbeam audio board for Speed Freak: the engine sound, all TTL counters and shift "
        "registers into one TL081.",
        "src/mame/cinematronics/nl_speedfrk.cpp", "speedfrk", CINEMATRONICS,
        compared="compared with the sheet (Figure A-14 Audio PCB Logic, p73)",
        undo=[dict(line=295, text="NET_C(R13.2, GND)", action="port", name="LAMP",
                   why="the sheet takes the 150-ohm collector resistor on to the START LIGHT "
                       "LED in the start switch, whose other side is +5V (Figure A-12: LED to "
                       "J2-9, +5 to J2-12); MAME grounds it as a load")],
        ports={"OUTPUT": "to the final amplifier, which MAME does not simulate"},
        notes=["""\
MAME's file calls the manual's schematics 'utterly terrible' and credits corrected
schematics from Brian Tarachi and connections verified by Frank Palazzolo, so this
reading has had more checking than most -- and may differ from the manual's sheet
where the manual is wrong. With HLE_CLOCK_GENERATOR off the 2 MHz clock is MAME's U10
pin 6 (an alias in the real-circuit branch).""", """\
Compared with the sheet, Figure A-14 Audio PCB Logic (doc a9a0d255b9db p73, 600 dpi; no
title block or revision), the parts list 30-10554-01 Rev. 4 (pp53-54) and the theory and
troubleshooting text (pp25, 37), 2026-10-20: the J4 inputs (O0-O4 and O7 on J4-11, 12, 6,
14, 15, 16, the logic PCB's clock on J4-2), the TL081 clock receiver U3 (R27, R28, CR3),
the 2 MHz oscillator U10 (R30, R31, C12, C13), the U5/U4 tripler (preset 9), the shift
register U13/U14 into the modulo-N counters U15/U9/U8 and the latch U12, the crash gates
U11 with R16-R19 bit for bit, the noise generator U20/U24/U19, the horn flip-flops U17 with
U23, the tire-squeal 555 U22 (R44-R46, C17, C23) and its gate, and the motor counter U7
(R22-R24) all agree with MAME pin for pin and value for value, and every value in this file
is in the parts list except 3.3K (R21) and 3.9K (R19), which the sheet prints and the list
lacks. Where the sheet and MAME differ, MAME is the one the rest of the manual supports: U23
is printed 74LS136 (it is a 74LS163); U24's pins 1 and 12 are swapped on the sheet; two of
U19's XORs are drawn as ANDs; U4's and U18's clocks and U5B's Q-bar are misnumbered; R29 is
printed 22K and R25/R26 4.7K where the parts list has 2.2K and 18K and no 22K; and the
sheet's U18 outputs disagree with the troubleshooting timings (2.2 ms and 3.0 ms at U17
pins 3 and 5), which fit MAME's pins 8, 10 and 11 exactly. Corrected from the sheet: MAME
grounds R13 as a stand-in, and on the sheet it goes to the START LIGHT LED in the start
switch (+5V on its other side), so LAMP is now a port.

Open questions, as printed and not settled:
* The sheet puts R21 and C20 on the crash DAC's branch (U11, through an unvalued resistor)
  and takes the motor counter U7's resistors straight to the output; MAME has it the other
  way round, U7 through C20 and R21 and the DAC through R20 (all marked 'PCB verified').
  This file follows MAME.
* The sheet draws U3 pin 4 to an unlabelled supply arrow, not ground, and the clamp diode
  on U3's output suggests the board's -15V; MAME grounds it.
* The sheet shorts U2 pin 6 onto O1 at the AND gate's input; MAME's reading (U12 enabled by
  the gated O1, U6 pin 5 from U2 pin 6) is the one the theory and troubleshooting text
  support. U6 pin 4 comes from raw O0 on the sheet, from U2 pin 2 in MAME -- the same level.
* The troubleshooting text calls the lamp transistor Q4 and the board photo (p41) points to
  Q1-Q4; MAME calls it Q3, the name the amplifier sheet gives its bias transistor. This file
  keeps MAME's Q3.

The manual's own designators collide elsewhere (its R16-R18 at the TL081, regulators
labelled U8/U9 beside counters U8/U9); MAME's look like the board's. Not compared: U23's
preset and U4/U23's ENT, which the sheet does not draw (MAME's "need to verify" ties are
what the text needs); R20's value, which it does not print; and the amplifier and
regulators (Figure A-14, p74), which MAME leaves out and whose values agree with MAME's
commented-out lines."""]),
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
        compared="compared with the sheet (2-30008 Rev X3, p43)",
        undo=[dict(line=436, text="NET_C(R22.2, GND)", action="port", name="R22_TO_4C",
                   why="the sheet takes R22 to 4C pin 2, the final amplifier's inverting input "
                       "(R23 and the pot R25 as feedback), which MAME does not simulate; MAME "
                       "grounds it instead")],
        ports={"OUTPUT": "3A pin 13 (the TL182's 2D), through R22 into the final amplifier"},
        notes=["""\
This board's designators are column-and-row grid positions (IC5D, IC4A ...), written
U5D, U4A here. MAME's file credits Jay Gallagher with verifying the PCB components.""", """\
Compared with the sheet, Schematic, Audio Board (Star Hawk) 2-30008 Rev X3, 1-9-79 (doc
87193443ac92 p43; a 300 dpi 1-bit scan read from the native image at 2-6x; the manual has
no parts list), 2026-10-20: every IC's type and position; the J2 inputs (J2-11 explosion,
J2-12 and J2-13 lazers, J2-14 K on/off, J2-15 master on/off, J2-16 K exit -- MAME's OUT_0-4
and OUT_7 in that order) with the 74LS04 6C and 7406 7C; the noise generator (6D, the
74LS164s 8C/8D/9C/9D, 9E, 10C/10D/10E, R1-R15, C7-C15, CR1, CR2, 6B and the CA3080 6A's
inputs); the explosion one-shot and Q1 (R5, R7, R16, R17, C5, C6, C17); the killer-ship
ramp, the 5D wobble oscillator and the ship VCO (R26-R38, CR3-CR6, C9, C20, C27, 4B, 5A,
5B); both lazer VCOs with their 74LS393 counters, 74S287 PROMs (the counter-to-PROM wiring
read on 4E; 7E's tap numbers are illegible but wired the same) and DACs (R39-R60, C22-C26,
CR7-CR10, Q4, Q5); and the TL182 3A with the summing node (6A pin 6, R19, C26, 3A pin 14,
3A pin 1 into 4A) all agree with MAME pin for pin and value for value, diode and transistor
orientation included. 5D pin 5 is not drawn, so RDUMMY stands in for an open output. MAME
differs only at the final amplifier: R22 goes into 4C pin 2, its inverting input, where
MAME grounds it (line 436); corrected above.

Open questions, as printed and not settled:
* C21 (5D's timing capacitor, the ship-wobble rate) is printed "22 TANT 35V", 22uF. MAME
  uses 0.22uF, marked "PCB verified", and keeps the sheet's 22uF behind its SLOW_SHIP_WOBBLE
  debug switch (about 0.6 Hz against 60 Hz). This file follows MAME's board.
* R6 (the explosion one-shot's timing resistor) is lettered "190K" against MAME's 150K;
  190K is not a stock value and the print may be a slip. This file follows MAME.

Labels that read wrongly on this scan but are MAME's designators by position: CR6 (reads
like CR8), C26 (C28), R46 (R48). Not in this file: the final amplifier (4C, Q2, Q3, R20,
R21, R23-R25, C16, C18, C19) and the regulators 2C and 2D, which are on the sheet with the
values MAME's comments give."""]),
    "sundance-sound": sound(
        "Sundance", "Cinematronics", "1979", "sundance", "the Sundance manual (doc 7130101e6e69)",
        "Cinematronics audio board for Sundance: pings and bongs (555s), a whoosh, a wideband "
        "noise generator, CA3080 mixing.",
        "src/mame/cinematronics/nl_sundance.cpp", "sundance", CINEMATRONICS,
        compared="compared with the sheet (SD203200, p20)",
        undo=[dict(line=472, text="NET_C(R64.2, GND)", action="drop",
                   why="the sheet takes R64 on to IC20 pin 2, the final amplifier's summing "
                       "junction (with C32 and R75); MAME grounds it instead"),
              dict(line=479, text="NET_C(GND, IC20.2, IC20.3)", action="remove", terms=["IC20.2"],
                   why="the sheet grounds IC20 pin 3 only; pin 2 is the final amplifier's "
                       "summing junction")],
        add=[sheet("p20: R64 into IC20 pin 2", "R64.2", "IC20.2"),
             sheet("p20: IC20 pin 6 drives the output stage", "IC20.6", name="FINAL_AMP")],
        ports={"OUTPUT": "the summing line SN, on to R64 and the final amplifier IC20",
               "FINAL_AMP": "IC20 pin 6 into the output stage (C32-C34, R65-R67, Q7, Q9, the "
                            "volume pot R76), which MAME does not simulate"},
        notes=["""\
The wideband noise generator here is MAME's description of the real circuit (the
HLE_NOISE_GEN branch off). MAME has never run that branch -- it simulates the noise with
a random source -- but it agrees with the sheet part for part (below).""", """\
Compared with the sheet, Audio Board Schematic (Sundance) SD203200 (doc 7130101e6e69 p20,
600 dpi), and the values printed on the assembly drawing (p21; the manual has no audio
parts list), 2026-10-20: the noise generator (D1 1N5240, R1, R3-R10, C1-C5, IC1-IC3 and
the D2/D3 limiter), the whoosh (IC11, the four LM3900 sections of IC4, Q1-Q3, R11-R23,
R34-R42, R47, R48, C6, C13-C15, C21, IC12), the explosion (IC7, Q4, R24-R33, C7-C12, IC8,
IC10), the hatch, the two pings and the bong (IC13's four tri-state enables with R49,
Q5/Q6/Q8/Q10, R50-R63, R68-R74, R77, R78, C22-C31, C35-C39, IC9 and IC14-IC19) and all six
CA3080 outputs on the SN line all agree with MAME pin for pin and value for value, every
IC type and every transistor and diode orientation included. MAME differs only where the
sheet goes on into the final amplifier, which it does not simulate: IC20 pin 3 is grounded
rather than unconnected, and R64 goes into IC20 pin 2 rather than to ground (MAME lines
479 and 472); both are corrected above.

Open questions, as printed and not settled:
* The sheet labels J2-11 "O5"; MAME calls it OUT_0. The CPU board's latch F2 (p13) has no
  O5 to give -- its Q5 is R_COIN -- and it brings out O0-O4 and O7, as do the
  troubleshooting text ("F-2 pins 4, 5, 6, 7, 9 & 12") and MAME's input mask. This file
  keeps OUT_0; the harness between the boards is not drawn in the manual.
* R66 in the final amplifier is 2.2K on the sheet and the assembly drawing; MAME's
  commented-out line has 22K. It is not in this file.

Not in this file: the final amplifier (IC20's feedback and output stage) and the
regulators IC5/IC6, which are on the sheet."""]),
    "tailg-sound": sound(
        "Tailgunner", "Cinematronics", "1979", "tailg", "the Tail Gunner manual (doc 22a6fb78dd5a)",
        "Cinematronics audio board for Tailgunner: hyperspace and laser VCOs, explosion, a "
        "wideband noise generator.",
        "src/mame/cinematronics/nl_tailg.cpp", "tailg", CINEMATRONICS,
        compared="compared with the sheet (SD205202 sheet 1, p55)",
        undo=[dict(line=670, text="NET_C(R70.2, GND)", action="drop",
                   why="the sheet takes R70 on to IC19 pin 2, the final amplifier's summing "
                       "junction (C34, R74 and the pot R75 as feedback); MAME grounds it instead"),
              dict(line=676, text="NET_C(GND, IC19.2, IC19.3)", action="remove", terms=["IC19.2"],
                   why="the sheet grounds IC19 pin 3 only; pin 2 is the final amplifier's "
                       "summing junction")],
        add=[sheet("p55: R70 into IC19 pin 2", "R70.2", "IC19.2"),
             sheet("p55: IC19 pin 6 drives the output stage", "IC19.6", name="FINAL_AMP"),
             sheet("p55: IC23 pin 11 (Q6) leaves the board at J3-9, 'TO START BUTTON LIGHT'",
                   "IC23.11", name="START_LIGHT")],
        ports={"OUTPUT": "the summing line, on to R70 and the final amplifier IC19",
               "FINAL_AMP": "IC19 pin 6 into the output stage (R71-R73, Q6, Q7), which MAME "
                            "does not simulate",
               "START_LIGHT": "J3-9, to the start button lamp (latch bit Q6)"},
        notes=["""\
Two MAME changes are undone by their switches: the diodes D8/D9 on the 74LS123's
Rext/Cext pins are back (MAME snips them for speed), and the pull-ups MAME adds to the
74LS125 outputs are gone. The hyperspace VCO's real circuit uses Q1, which MAME declares
only in a comment ('not used' -- by the stand-in); the declaration is restored.""", """\
Compared with sheet 1 of the audio board, Schematic Audio Board - Tailgunner SD205202 (doc
22a6fb78dd5a p55, 600 dpi), and the parts list PL205202 (pp41-43), 2026-10-20: the trigger
port IC23 with its J4 inputs (O0-O4 on J4-11 to J4-15) and its six used outputs; the noise
generator (D1, IC1-IC3, but see below); the explosion (IC9, IC10, IC12, Q3), rumble (IC6,
Q4) and shield (IC4, Q5, IC13, the 555s IC16 and IC17 with their RC ladders); the shield
bounce (IC14, IC15, IC18, IC12, Q8, IC22); the hyperspace and laser VCOs (IC7/Q1,
IC11/Q2) with the 74LS393 IC8 and its taps R17-R20 and R35-R38; and the summing line into
R70 all agree with MAME pin for pin and value for value, diode and transistor orientation
included, and every value MAME has (R1-R70, R76-R84, C1-C33, C41-C44) agrees with the parts
list. The three MAME changes this file undoes are what the sheet draws: D8 and D9 on the
74LS123's pins 15 and 7, no pull-ups on the 74LS125 outputs (pins 3 and 6), and the
hyperspace VCO built from IC7 and Q1 into IC5 pin 1. Corrected from the sheet: IC23 pin 11
(Q6), which MAME leaves unconnected, goes to J3-9 "TO START BUTTON LIGHT"; and R70 goes
into IC19 pin 2, the final amplifier's inverting input, rather than to ground, with IC19
pin 3 grounded (MAME lines 670 and 676).

Open question, as printed and not settled:
* The sheet draws the noise amplifier IC1 with C3/R2 on pin 2 (-) and R4/C4 on pin 3 (+),
  and MAME copies it (its lines 325 and 328, in the branch it never runs). As drawn R4 is
  positive feedback and the op-amp would latch; the manual's own text (p24) gives IC1 a
  gain of 1000, which is 1 + R4/R3 only with R4 on the inverting input; and Sundance's
  sheet SD203200, the same circuit by the same drafter, draws C3 into pin 3 and the
  feedback into pin 2. This file follows the sheet. Not checked against a board.

Slips in the parts list that change nothing here: item 32 gives R22 as 22K (R22 is 1K on
the sheet and in item 24; the 22K is the final amplifier's R72), and items 14 and 18 garble
C45-C49. The theory text says Q5 for the rumble transistor (the sheet: Q4) and Q1 for the
laser squarer (Q2). IC1's printed type is unreadable on this scan; the parts list gives
TL081. Not in this file: sheet 2 (p65, the joystick circuitry on the same board, IC24-IC28),
and the final amplifier and regulators (R71-R75, C34-C40, Q6, Q7, IC20, IC21), whose values
agree with MAME's commented-out lines."""]),

    # -----------------------------------------------------------------------
    # Sega / Gremlin (Aaron Giles, CC0-1.0)
    # -----------------------------------------------------------------------
    "astrob-sound": sound(
        "Astro Blaster", "Sega", "1981", "astrob", "the Astro Blaster manual (doc 7c9390526e01)",
        "Sega G-80 Astro Blaster sound board: sonar, two lasers, invaders, warp and bonus "
        "sounds from CD4000-series timing, 555s and TL084 filters.",
        "src/mame/sega/nl_astrob.cpp", "astrob", SEGA,
        defines={"ENABLE_SONAR_ALT": 0},
        compared="compared with the sheets (800-3122 rev B sheets 7-8, pp57-58)",
        undo=[dict(line=n, text=t, action="drop-line",
                   why="MAME's ideal clock and the oscillator parts it parks in its place")
              for n, t in ((863, "CLOCK(OSC1"), (864, "OSC1.GND"), (865, "OSC1.VCC"),
                           (866, "OSC1.Q"), (867, "NET_C(R18.1"),
                           (884, "CLOCK(OSC2"), (885, "OSC2.GND"), (886, "OSC2.VCC"),
                           (887, "OSC2.Q"), (889, "NET_C(R46.1"),
                           (1098, "CLOCK(OSC3"), (1099, "OSC3.GND"), (1100, "OSC3.VCC"),
                           (1101, "OSC3.Q"), (1102, "NET_C(R22.1"),
                           (1154, "CLOCK(OSC4"), (1155, "OSC4.GND"), (1156, "OSC4.VCC"),
                           (1157, "OSC4.Q"), (1158, "NET_C(R80.1"))]
             + [dict(line=n, text=t, action="drop-line",
                     why="MAME's mute function, standing in for the output stage")
                for n, t in ((1048, "AFUNC(MUTEFUNC"), (1049, "MUTEFUNC.A0"),
                             (1050, "MUTEFUNC.A1"), (1051, "ALIAS(OUTPUT, MUTEFUNC.Q)"))]
             + [dict(line=1197, text="NET_C(GND, U7.5, U7.6, U7.12, U7.13)", action="remove",
                     terms=["U7.5", "U7.6", "U7.13"],
                     why="the sheet grounds U7 pin 12 only; pin 13 is the summing node and pins "
                         "5 and 6 the mute comparator's inputs, in the output stage MAME does "
                         "not simulate")],
        undo_notes=["""\
lines 863-1158: MAME's four ideal clocks (OSC1-OSC4), the oscillator parts it parks on GND
in their place and their supply ties are dropped; the CD4011 oscillators are put back from
the sheets ("Corrected from the sheet", above).
lines 1048-1051: MAME's mute is a function (AFUNC) on the summing node; on the sheet it is
the comparator U7B driving the 2N4093 switch Q4 on the output, which MAME does not
simulate. The function is dropped, and U7's output-stage pins are ports."""],
        add=[sheet("sheet 7: OSC1, a CD4011 RC oscillator", "U9.5", "U9.6", "R18.2", "C3.1"),
             sheet("sheet 7: OSC1, a CD4011 RC oscillator", "U9.4", "U9.1", "U9.2", "R18.1"),
             sheet("sheet 7: OSC1, a CD4011 RC oscillator", "U9.3", "C3.2", "U3.14"),
             sheet("sheet 7: OSC2, a CD4011 RC oscillator", "U9.10", "U9.12", "U9.13", "R46.1",
                   "U4.4"),
             sheet("sheet 7: OSC2, a CD4011 RC oscillator", "R46.2", "U9.8", "U9.9", "C20.2"),
             sheet("sheet 7: OSC2, a CD4011 RC oscillator", "U9.11", "C20.1"),
             sheet("sheet 8: OSC3, a CD4011 RC oscillator", "U11.12", "U11.13", "R22.2", "C5.1"),
             sheet("sheet 8: OSC3, a CD4011 RC oscillator", "U11.11", "U11.8", "U11.9", "R22.1"),
             sheet("sheet 8: OSC3, a CD4011 RC oscillator", "U11.10", "C5.2", "U12.2"),
             sheet("sheet 8: OSC4, a CD4011 RC oscillator", "U10.8", "U10.9", "R80.2", "C35.1"),
             sheet("sheet 8: OSC4, a CD4011 RC oscillator", "U10.10", "U10.12", "U10.13",
                   "R80.1"),
             sheet("sheet 8: OSC4, a CD4011 RC oscillator", "U10.11", "C35.2", "R79.1"),
             sheet("sheet 7: the summing bus goes straight to U7 pin 13", "U7.13", "C55.2",
                   name="OUTPUT"),
             sheet("sheet 7: U7 pin 14, the summing amplifier's output", "U7.14", name="U7_OUT"),
             sheet("sheet 7: U7 pin 5, the mute comparator's reference", "U7.5", name="MUTE_REF"),
             sheet("sheet 7: U7 pin 6, the mute comparator's input", "U7.6", name="MUTE_IN"),
             sheet("sheet 7: U7 pin 7, the mute comparator's output", "U7.7", name="MUTE_GATE")],
        ports={"OUTPUT": "the summing bus, into U7 pin 13, the inverting input of the summing "
                         "amplifier U7D (R144 22K from pin 14), which MAME does not simulate",
               "U7_OUT": "U7 pin 14, through C58 and the 2N4093 mute switch Q4 to P1-1 (AUDIO "
                         "OUTPUT); R144 back to pin 13, R143 from P1-3 (EXT INPUT)",
               "MUTE_REF": "the R115/R116/R117 divider on U7 pin 5",
               "MUTE_IN": "MUTE (U32 pin 5) through R123 1K, with R124 100K to GND",
               "MUTE_GATE": "U7 pin 7 through D13 to Q4's gate"},
        notes=["""\
Undone beyond the switches: twenty resistors in the sonar circuit that MAME multiplies by
1.001-1.049 (its comment: the circuit 'relies on subtle part differences') are written
at their nominal value; and ENABLE_SONAR_ALT, which adds four 1M
resistors to a 0.1V source to start the oscillators, is off.""", """\
Compared with the sound board sheets, Astro Blaster Sound 800-3122 rev B sheets 7 and 8 of
8 (doc 7c9390526e01 pp57-58, the 300 dpi scan read at up to 5x), and with its parts list
(pp33, 35-36), 2026-10-20. Every resistor and capacitor value in MAME's file (R1-R186,
C1-C82) and every IC, diode and transistor type agrees with the parts list, quantities
included; the sonar resistors MAME scales are the list's nominal values. The sheets agree
with MAME net for net and pin for pin, diode and transistor orientation included, in the
latch outputs and their 7406/7407 buffers (U26, U29-U31); the four sonar oscillators (U1,
U2) and their trigger (U11, D2, Q1-Q3, U7A); both lasers (U25, U24/U19, U20/U14, the
real VCO branch); refill (U3, U4, U5, Q7) and attack, rate reset and warp (U21, U15,
D14-D23, U16B); explosions (U27, U21, U8, Q6, U16A/C) and astroids (U16D, Q5, U7C); the
four invaders (U22, U23/U18/Q8, U13/U12, U17, U37/U28/U38) and bonus (U10, U6); and the
summing bus (R98-R103, R118-R122, C55).

Corrected from the sheets: the four oscillators MAME runs as ideal clocks are CD4011 RC
oscillators (U9 with R18/C3 and R46/C20, U11 with R22/C5, U10 with R80/C35), on exactly
the gates MAME parks, and they are put back. MAME's "unconnected" U7 pins are the output
stage: pin 12 is grounded, pin 13 is the summing node (now joined to it), and pins 5-7
are the mute comparator, which with Q4 is what MAME's mute function stands in for.

Open questions, as printed and not settled:
* The sonar trigger's 1K (MAME's R117) is printed "R119 1K". The same sheet prints R119
  470K in the mixer and an R117 1K in the mute circuit, and the parts list's 1K entry
  carries an R19 that neither sheet prints, so it is probably R19. This file keeps MAME's
  R117, which names a different resistor on the board.
* Q5 and Q6 (2N4093): the sheet labels S on the signal node and D on ground. MAME swaps
  them on purpose ("D and S swapped on schematics???"). This file follows MAME.
* The attack capacitor is printed "C69 .05uf", a second C69 beside the explosion's 4.7uF
  C69. MAME's C67 is what the parts list's counts allow.

Sheet misprints, MAME right: U2's first output is printed "4", and U38's supply pin "5".
Not in this file: the rest of the output stage (U7D's feedback, C58, Q4, D13, R115-R117,
R123, R124, R135, R141-R144, C48, P1), the port decoder and latches U32-U36, and the
power decoupling."""]),
    "elim-sound": sound(
        "Eliminator", "Gremlin", "1981", "elim2", "the Eliminator manual (doc cff008c00810)",
        "Sega G-80 Eliminator sound board: background, skitter, two torpedo and explosion "
        "sounds, CA3080 VCAs. Zektor uses the same board; this is the Eliminator wiring.",
        "src/mame/sega/nl_elim.cpp", "elim", SEGA,
        defines={"VARIANT_ELIMINATOR": 0, "VARIANT_ZEKTOR": 1, "SOUND_VARIANT": 0},
        compared="compared with the sheets (800-3174 rev B sheets 7-8, pp65-68)",
        not_parts={f"R_PSG_{i}": "a 1K from +5V standing in for one output of the sound chip "
                                 "(PSG) MAME emulates separately; on the sheet U30's three "
                                 "outputs (pins 1, 4, 5) are tied straight onto R133" for i in (1, 2, 3)},
        fix_parts={u: ("NE555", "the sheet (800-3174 sheet 7) and parts list item 25 print "
                                "NE555; MAME's LM555 is the same timer")
                   for u in ("U5", "U13")},
        undo=[dict(line=n + i, text=t, action="drop-line",
                   why="MAME's ideal clock and the oscillator parts it parks in its place")
              for n, clk, u, p, r, *_ in ELIM_OSC
              for i, t in enumerate((f"CLOCK({clk}", f"{clk}.VCC", f"{clk}.GND", f"{clk}.Q",
                                     f"NET_C({r}.1", f"HINT({u}.{p[1]}", f"HINT({u}.{p[3]}"))],
        undo_notes=["""\
lines 864-903: MAME's five ideal clocks (_200HZA, _200HZB, _10HZ, _50HZ, _100HZ), the
oscillator parts it parks on GND in their place, and its HINT(NC)s on the inverter
outputs, are dropped; the oscillators are put back from the sheet ("Corrected from the
sheet", above)."""],
        add=[a for _, _, *osc in ELIM_OSC for a in oscillator(*osc)],
        ports={"OUTPUT": "the summing node: on the sheet, U2 pin 6, the final amplifier's "
                         "inverting input, which MAME does not simulate"},
        notes=["""\
Compared with the Sound Board drawing 800-3174 rev B, sheets 7 and 8 of 8 (doc
cff008c00810 pp65-68, each sheet printed in two halves), and its parts list (pp30-35),
2026-10-20. Every passive value in this file agrees with the parts list -- 188 parts, none
different -- and the list shows that R24 and C42, which MAME's file queries, do not exist.
All values are the Eliminator ones in MAME's variant table (R79 2M is fitted), and no
Zektor part or jumper is drawn. The latch bit assignment (U34 74LS374 for the HI port, U35
for the LO port, D0 unused on the LO side), the 7406/7407 buffers, the noise source (U4,
U3) and sum buffer U12, the thrust, skitter, enemy ship and background channels (U10, U11,
U5, U1, U13, U15, U16, U25), the PSG input U29, explosions 1-3, fireball and bounce (U6-U9,
U14, the CD4011 one-shots U17-U19), the torpedo VCOs and counters (U20-U23) and the summing
resistors R6-R10 all agree with MAME pin for pin and value for value, transistor and diode
orientation included; R36 does feed torpedo 2's D6, as with DISABLE_TORPEDO2_NOISE off.

The 200 Hz A/B, 10 Hz, 50 Hz and 100 Hz clocks, which MAME runs as ideal clocks, are
CD4069 RC oscillators on the sheet (U32 and U31 with R139-R143 and C65-C69), on exactly the
pins MAME parks, with the values MAME's comment gives; they are put back here. U5 and U13
are printed NE555 (MAME: LM555, the same part). The PSG's three outputs (U30 pins 1, 4, 5)
are tied straight onto R133 680 ohm; R_PSG_1-3 are only MAME's model of the chip, so that
node stays a port.

Open questions, as printed and not settled: this scan drops two short line segments --
Q3's base lead (sheet 7, zone C3) and U19 pin 4 into its second gate (sheet 8, zone D6) --
where MAME's reading is the only one the drawing allows; the identical one-shots elsewhere
on sheet 8 draw the line. MAME's is kept.

Not in this file: the CPU interface (U30 AY-3-8912, U33-U41), the final amplifier and mute
(U2, Q1, R1-R5, R11-R13, C1, C4) and the bypass capacitors, which are on the sheets with
the values MAME's comments give. R3 is not part of the final amplifier's gain network, as
MAME's comment says: it brings contact 3 onto the summing node."""]),
    "frogs-sound": sound(
        "Frogs", "Gremlin", "1978", "frogs", "the Frogs manual (doc a2ffd17fee9b)",
        "Gremlin Frogs sound board: hop, jump, zip, splash, buzz, boing and croak from 555s "
        "and 741 filters.",
        "src/mame/sega/nl_frogs.cpp", "frogs", SEGA,
        loads={"RU4": "a 100K to ground on a 555 output the board leaves unconnected -- MAME's "
                      "file says the netlist 'doesn't like unconnected 555 outputs'",
               "RU15": "a 100K to ground on a 555 output the board leaves unconnected -- MAME's "
                       "file says the netlist 'doesn't like unconnected 555 outputs'"},
        compared="compared with the sheet (821-0002 Rev A sheet 5, p50)",
        undo=[dict(line=552, text="NET_C(R90.2, GND)", action="port", name="U13_OUT",
                   why="the sheet takes R90 to U13 pin 6: it is the feedback resistor of the "
                       "741 summing amplifier U13, which MAME leaves out as the final amp")],
        add=[sheet("p50 (zone A6): R47's wiper is drawn on Q15's base; MAME connects neither",
                   "R47.2", "Q15.B"),
             sheet("p50 (zone B4): each mixer pot's wiper is tied to its bus end, a rheostat; "
                   "MAME leaves the wipers open",
                   "R91.2", "R92.2", "R93.2", "R94.2", "R95.2", "R96.2", "R90.1")],
        ports={"OUTPUT": "the summing bus: on the sheet, U13 pin 2, the inverting input of the "
                         "741 summing amplifier U13, which MAME does not simulate",
               "U13_OUT": "on the sheet, U13 pin 6, which drives C58 to AUDIO OUT (contacts "
                          "26/17)"},
        notes=["""\
Compared with the sheet, Schematic Frogs Sound Board 821-0002 Rev A sheet 5 of 6 (doc
a2ffd17fee9b p50, 600 dpi), and with the board's parts list, 821-0002 sheets 1-4 (pp44-47),
2026-10-20: every IC type (U1 MM5837, the ten NE555s, the eight LM741s), every transistor
type and all 163 resistor and capacitor values agree with the parts list, and the six
channels -- the input inverters Q1-Q6 (FLY driving Q1's emitter), the trigger 555s U2-U7,
HOP (D2, R31, R32, Q9, Q10, U10), JUMP (the U11 band-pass, Q21 and the Q19/Q20 pair, U19,
U20, U16), TONGUE/ZIP (U4, Q11-Q13, U15), CAPTURE (U3 holding U9's reset, D4, Q17, Q18, U8),
SPLASH (Q14, U1's noise through D5/D1, U14) and FLY (U7 resetting U12, Q7, D6, U17, D8/D9,
U18) -- agree with MAME pin for pin and value for value, diode and transistor orientation
included. The sheet calls HOP's 33K a second R22; the parts list calls it R32, as MAME
does. U4 and U15 pin 3 are drawn unconnected, so RU4 and RU15 are MAME's loads, not parts.
Three differences, all corrected above:

* Q15's base is on R47's wiper (zone A6). MAME connects neither, so in its netlist both
  float.
* The six mixer pots R91-R96 have their wipers tied to the summing bus: they are rheostats.
  MAME leaves the wipers open.
* R90 56K is the feedback resistor of U13, the 741 summing amplifier that drives C58 to the
  AUDIO OUT contacts (26/17). MAME leaves U13 out as the final amp and grounds R90; here
  R90 goes on to U13 pin 6, a port, and OUTPUT is U13's inverting input.

Weakly read: the top strip of JUMP (R33, Q8, C44, Q16, R57, R58, R70, R71) is faint on the
scan; it agrees with MAME where legible, and its values are the parts list's. Not in this
file: U13 with R60, C34, C35 and C58, and the supply bypasses C1/C2, which are on the
sheet."""]),
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


# ---------------------------------------------------------------------------
# The second batch (2026-10-20): the licence-clean, DIP-level files the first
# survey left, each of which needed something the converter did not yet do --
# a sub-netlist pulled in with INCLUDE, function-like macros, one LM3900
# amplifier declared at a time, a part's named pins, a supply MAME wires
# backwards.
# ---------------------------------------------------------------------------

def circuit(name, mfr, year, machine, drawing, revision, coverage, corrected=False):
    """A board record for a netlist that is MAME's reading of a sheet -- and, once
    corrected from the sheet, not a single source any more."""
    return dict(name=name, mfr=mfr, year=year, machine=machine, drawing=drawing,
                revision=revision, coverage=coverage, singleSource=not corrected,
                netsTraced=False, netsConverted="mame")


LM3900_SECTIONS = [("LM3900", r"([A-Z]\d)_([1-4])", "LM3900")]
LATCH_PORTS = "to the audio power amplifier, which MAME does not simulate"


def zzzap(variant, slug_machine, title, drawing, revision, notes):
    return dict(
        source="src/mame/midw8080/nl_280zzzap.cpp", netlist=slug_machine,
        title=title,
        defines={"VARIANT_280ZZZAP": 0, "VARIANT_LAGUNAR": 1, "SOUND_VARIANT": variant},
        board=circuit(title, "Dave Nutting Associates / Midway", "1976" if variant == 0 else "1977",
                      slug_machine, drawing, revision,
                      "Converted from MAME's netlist: the engine, skid and crash sounds and the "
                      "final mix, up to the audio power amplifier. The CPU's sound latches (F4, "
                      "F5) are ports; the rest of the game logic board is not in MAME."),
        sections=LM3900_SECTIONS, ic_names=r"(?:MC3340_)?([A-Z]\d)",
        values={"ZD_1N5239": ("1N5239", "a 9.1V zener; MAME's name says which")},
        ports={"OUTPUT": LATCH_PORTS},
        about=HOWELL + """

The noise generator is the real circuit (FAST_HLE_NOISE_GEN off): a 1N5239 zener
biased near breakdown through RNOISE0 from +12V, amplified by the LM3900 at H4.
MAME adds its own noise source in series with the zener, which is how it models the
zener's noise; here the zener's anode and H4's input are one node. The schematics do
not number the discrete parts; Howell gives them the Super Speed Race numbers, which
mostly correspond, and invents RNOISE0-3, CNOISE0 and CNOISE for the noise
generator's, which Super Speed Race does not have.""",
        notes=notes)


ZZZAP_COMPARED = """\
Compared with both Laguna Racer game logic sheets, A084-90700-B622 (doc 1461b5f1ef33) and
-A622 (doc 2e04e6b435f0), on 2026-10-20 -- every wire and port line of this file, not a
sample. The two sheets have one circuit and one set of pin numbers; 86 of the 89 lines
agree on both, and all sixteen LM3900 amplifiers are on the pins the data sheet numbers
them by, as this file puts them. The noise generator agrees part for part (the zener is
printed IN5239). Two pins are not numbered on either sheet and are MAME's: G4 switch A's
input (pin 1 by elimination) and the MC3340's ground and output (3 and 7).

The three that differ are one switch. Both sheets print the bottom (76 Hz) oscillator's J4
switch as pins 4, 3 and 5 -- switch B, which the middle oscillator also uses -- and MAME
puts it on 10, 11 and 12 (switch D). Its comment: 'mislabeled pin numbers on the
schematics for 280-ZZZAP and both Laguna Racer versions ... The Super Speed Race schematic
correctly shows this oscillator using pins 10, 11, 12'. Two oscillators cannot share one
switch, so this file follows MAME; it is a correction of the sheet, logged, not read.

Neither sheet draws the LM3900s' or CD4016s' supply pins, so +5V on 14 and ground on 7 are
MAME's ('these aren't shown on the schematics'); nor the unused switches G5_D, J4_C and
G4_D, so whether the board ties their pins or leaves them open is not on the sheet. The
sheet's +12V here is '+12V DECOUPLED' -- connector A pin 3 through 100 ohms with 500uF to
ground, neither of which MAME has -- and the LM377 bridge amplifier at J1 that OUTPUT and
J5 pin 9 feed is on the sheet and not in MAME."""

TARGETS.update({
    # -----------------------------------------------------------------------
    # Midway (Colin Douglas Howell, CC0-1.0)
    # -----------------------------------------------------------------------
    "280zzzap-sound": zzzap(
        0, "280zzzap", "280-ZZZAP sound circuits",
        "280 ZZZAP Game Logic P.C. 0610-00907A, which this site does not hold -- via MAME's "
        "netlist, compared with its near copy, Laguna Racer A622 (doc 2e04e6b435f0)",
        "280-ZZZAP game logic board, sound section: engine (two LM3900 oscillators into an "
        "MC3340 attenuator), skid and crash noise, and the mix.",
        [ZZZAP_COMPARED + """

This is the 280-ZZZAP variant, compared with the A622 sheet, which MAME's file says is a
near copy of the 280-ZZZAP schematic (the site does not hold that one; A622 even keeps its
change-note letters E-H, the notes blanked). C18 47uF and R30 110K are A622's. R46, R48,
R51 and R11 are not: A622 prints 2M, 480K, 480K and 100K, and MAME takes B622's 2.2M,
470K, 470K and 120K for both games -- 'these seem to be errors in that schematic. 480 Kohm
is not even a standard resistor value', agreeing with the Laguna Racer PCB drawings and
Andrew Welburn's photo of a 280-ZZZAP board. MAME also notes 280-ZZZAP's own change
notes E and F: on the first 325 machines R18 was 6.8K and R65 4.3K."""]),
    "lagunar-sound": zzzap(
        1, "lagunar", "Laguna Racer sound circuits",
        "Laguna Racer Game Logic A084-90700-B622 (doc 1461b5f1ef33) and -A622 (doc "
        "2e04e6b435f0) -- via MAME's netlist, compared with both",
        "Laguna Racer game logic board, sound section: as 280-ZZZAP's with C18 22uF and R30 "
        "100K.",
        [ZZZAP_COMPARED + """

This is the Laguna Racer variant, and every value in it agrees with the B622 sheet,
including the six where B622 and A622 differ (R46 2.2M, R48 470K, R51 470K, R11 120K, C18
22uF tantalum, R30 100K -- the last read with moderate confidence, its middle digit faint)."""]),
    "gunfight-sound": dict(
        source="src/mame/midw8080/nl_gunfight.cpp", netlist="gunfight",
        title="Gun Fight sound generator",
        board=circuit(
            "Gun Fight sound generator", "Dave Nutting Associates / Midway", "1975", "gunfight",
            "Gun Fight Sound Generator Detail P.C. 597-907E -- via MAME's netlist",
            "Gun Fight sound generator, P.C. 597-907E: a zener noise source filtered into "
            "four transistor 'bang' generators, mixed to left and right.",
            "Converted from MAME's netlist, which stops at the two master volume pots: the "
            "power amplifier ICs after them are not in it."),
        ports={"OUT_L": "to the left power amplifier, which MAME does not simulate",
               "OUT_R": "to the right power amplifier, which MAME does not simulate"},
        values={"D304": ("1N5239", "MAME's file: 'a 9.1-volt zener diode (D304, a 1N5239)'")},
        about="""\
Colin Douglas Howell's netlist of Gun Fight's sound generator, every part labelled as on
the schematic. The four effect switches are the real transistor switches (FAST_SWITCHES
off), driven from the CPU's sound latch, whose bits arrive here as ports. MAME models
the zener D304's noise as a source in series with it; here D304's anode and Q302's base
are one node, as on the board.""",
        notes=["""\
Not compared with the sheet. MAME's sheet, 'Gun Fight Sound Generator Detail P.C.
597-907E', is in none of the Gun Fight documents the site holds (read 2026-10-20): the
'Gunfight Schematics' PDF (doc d66a80e04858) has the mother board, the game logic board
-- on which the sound generator is a dashed block -- and the cabinet wiring; the manual
and parts catalog list no board parts. The catalogue's 'Game Logic and Sound (597-907E)'
PDF (doc 8eaf458a433e) was never fetched, and an archive.org copy exists. What the site's
sheets do show agrees where they reach: the four triggers enter the sound block from the
7404 at H6 (L.SHOT on pin 2, R.SHOT on 12), as MAME's comment says. The supply is printed
'+16V' on the wiring diagram and '+15V' on the mother board schematic for the same pin;
MAME uses 16V. The manual names six pots (A-B hit, C-D shot, E-F master, left and right),
which by this circuit are R110, R210, R123, R223, R103 and R203 -- an inference, not a
reading.""", UNCHECKED]),

    # -----------------------------------------------------------------------
    # Taito / Midway Super Speed Race (Colin Douglas Howell, CC0-1.0). The noise
    # generator is on the motherboard and the rest on the audio board, whose
    # designators overlap; MAME prefixes the motherboard's NOISE_.
    # -----------------------------------------------------------------------
    "sspeedr": dict(
        source="src/mame/taito/nl_sspeedr.cpp", netlist="sspeedr",
        split={
            "sspeedr-sound": dict(
                title="Super Speed Race audio board",
                board=circuit(
                    "Super Speed Race audio board", "Taito (Midway license)", "1979", "sspeedr",
                    "Audio board schematic in the Super Speed Race Parts and Operating Manual "
                    "(doc 8c0560561bb9) -- via MAME's netlist",
                    "Super Speed Race audio board: engine, skid and crash sounds as 280-ZZZAP's, "
                    "rearranged, with a SILENCE input.",
                    "Converted from MAME's netlist, up to the audio output. The noise comes from "
                    "the motherboard (sspeedr-noise); the sound latches are ports."),
                corrected_from="the audio board schematic (M051-00762-A003, manual p. 31)",
                about=HOWELL + """

Super Speed Race's sound is 280-ZZZAP's circuit rearranged onto an audio board of its
own, with the noise generator moved to the motherboard. Its schematic numbers the
discrete parts, and MAME uses those numbers. The sound latches are on this board, 74174s
at D2 and C2 -- MAME keeps 280-ZZZAP's names for them, F4 and F5, so its I_F4_2 is D2 pin
2 -- and the board's output is a bridge: OUTPUT is 'AUDIO 180 deg' and AUDIO_0 'AUDIO 0
deg', pins 1 and 4 of its 4-pin connector.""",
                notes=["""\
Compared with the audio board schematic, M051-00762-A003 (manual doc 8c0560561bb9, p. 31
of the print, PDF p. 34), on 2026-10-20: 21 groups of nets covering every IC, and every
value in the file -- all agree, the oscillator resistors included once MAME's frontier
values are undone, and so do the SILENCE input (D6, D7, R71, R72), C30 across R50, and C25.
Thirteen of the fifteen LM3900 amplifiers drawn print exactly the data sheet's pins; the
other two are misprints on the sheet, where MAME's pin is the only one possible: C1
amplifier 3's minus input is printed 6 (amplifier 1's) and H2 amplifier 3's is printed 9
(its own output; the read is about 75% sure). The CD4016 sections drawn and the MC3340's
pins agree. Added from the sheet: J1 pin 10 is the bridge's second output, AUDIO_0, which
MAME leaves as an internal net.

Not in this file, and on the sheet: the board's '+5V DEC' rail -- +5V through R24 (10 ohms)
with C12 (500uF) to ground -- which is what the analogue parts MAME puts on +5V actually sit
on, MC3340 pin 8 included; and the supply parts C26-C29. Neither the unused switch sections
(A2 10-12, B1 6, 8, 9), J1's third amplifier nor the MC3340's pins 4-6 are drawn."""]),
            "sspeedr-noise": dict(
                title="Super Speed Race motherboard noise generator",
                board=circuit(
                    "Super Speed Race noise generator", "Taito (Midway license)", "1979", "sspeedr",
                    "Motherboard schematic in the Super Speed Race Parts and Operating Manual "
                    "(doc 8c0560561bb9) -- via MAME's netlist",
                    "Super Speed Race motherboard, noise generator section: a CD4006 shift "
                    "register with CD4070 feedback.",
                    "Converted from MAME's netlist: the noise generator only, a section of the "
                    "motherboard. Its output goes to the audio board (sspeedr-sound)."),
                about="""\
The digital noise generator on Super Speed Race's motherboard: an 18-stage CD4006 shift
register at H5 with XOR feedback at J5, started by NOISE_C9/NOISE_CR3. MAME prefixes
these parts NOISE_ because the audio board uses the same numbers; the prefix is dropped
here, since this file is the motherboard's alone.""",
                corrected_from="the motherboard schematic (M051-00078-0000, manual p. 25)",
                notes=["""\
Compared with the Z-80 compact motherboard schematic, M051-00078-0000 (manual doc
8c0560561bb9, p. 25 of the print, PDF p. 26), on 2026-10-20: every net and value agrees.
C9 goes straight to +12V, so MAME's 1 ohm 'dummy' is rightly a wire here. J5 is printed
4030, the older quad XOR with the 4070's pins, and is written so. The designators do
collide with the audio board's, as MAME says: R22-R25, R62, C8 and C9 are on both boards
with different values (C8 and C9 have theirs swapped). NOISE_OUT leaves on the 72-pin
connector's 'NOISE GENERATOR' contacts (J-A and K-50), crosses the game logic board on
Molex C pin 14 and enters the audio board on pin 14 of its 17-pin connector, NOISE."""]),
        },
        assign={"sspeedr-noise": "H5_SHFTREG J5_XORx4 NOISE_R22 NOISE_R23 NOISE_R24 NOISE_R25 "
                                 "NOISE_R62 NOISE_C8 NOISE_C9 NOISE_CR3".split()},
        assign_default="sspeedr-sound",
        sections=LM3900_SECTIONS, ic_names=r"(?:MC3340_)?([A-Z]\d)",
        designators={"H5_SHFTREG": "UH5", "J5_XORx4": "UJ5"},
        strip_suffix=r"NOISE_((?:R|C|CR)\d+)",
        shorts={"NOISE_RDUMMY": "a 1 ohm resistor MAME adds between +12V and C9 'to make the "
                                "noise source's startup circuit voltage behave properly'"},
        fix_parts={"J5_XORx4": ("CD4030", "the motherboard schematic prints 4030")},
        add=[sheet("the audio board schematic: J1 pin 10 is 'AUDIO 0 deg', pin 4 of the 4-pin "
                   "connector -- the second output of the bridge", "IC_J1.10", name="AUDIO_0")],
        ports={"OUTPUT": "'AUDIO 180 deg', pin 1 of the audio board's 4-pin connector, to the "
                         "speaker in bridge with AUDIO_0",
               "AUDIO_0": "'AUDIO 0 deg', pin 4 of the 4-pin connector, to the speaker in bridge "
                          "with OUTPUT"}),
})


ATARI = """\
Ryan Holtz's netlist of the sound circuits on the game board, which his file says is
derived from the schematics in the manual. The game logic's sound-enable and sound-data
lines arrive as ports (MAME's TTL_INPUT names), and so do the video timing signals the
sounds are clocked from, which MAME runs as ideal clocks."""

TARGETS.update({
    # -----------------------------------------------------------------------
    # Atari (Ryan Holtz; Destroyer BSD-3-Clause, Flyball CC0-1.0)
    # -----------------------------------------------------------------------
    "destroyr-sound": dict(
        source="src/mame/atari/nl_destroyr.cpp", netlist="destroyr",
        title="Destroyer sound circuits",
        board=circuit(
            "Destroyer sound circuits", "Atari", "1977", "destroyr",
            "Sound section of the Destroyer game board schematic, sheet 4 of 5, technical "
            "manual TM-106 (doc 50fd79545404, p. 37) -- via MAME's netlist, compared with it",
            "Destroyer game board, sound section: noise (two 74LS164s), explosion, sonar, "
            "launch and motor sounds, mixed into the volume pot.",
            "Converted from MAME's netlist and compared with sheet 4, up to the volume pot's "
            "wiper; the TDA1004 amplifier after it is not in MAME. The spare gates MAME ties "
            "off are other circuits' on the board, and are ports here.",
            corrected=True),
        models={"LM324_VM5V12": ("LM324", "MAME's LM324 with output limits for the -5V/+12V "
                                          "supply it runs on here")},
        fix_parts={"IC_K8": ("7428", "sheet 4 prints '28' in all four gates, and the parts list "
                                     "has a 7428 at K8; MAME's comment agrees ('Should be a 7428'), "
                                     "and its 7402 has the same pins"),
                   "IC_L9": ("74LS164", "sheet 4 and the parts list"),
                   "IC_M9": ("74LS164", "sheet 4 and the parts list")},
        corrected_from="sheet 4 of the schematic (TM-106 p. 37) and sheets 3 and 5",
        undo=[*[dict(line=n, text=t, action="drop",
                     why="these gates are used elsewhere on the board (sheets 3-5), not tied off")
                for n, t in ((162, "NET_C(GND, IC_L7.1,  IC_L7.2)"),
                             (163, "NET_C(GND, IC_L7.4,  IC_L7.5)"),
                             (165, "NET_C(GND, IC_M8.4,  IC_M8.5)"),
                             (166, "NET_C(GND, IC_M8.9,  IC_M8.10)"),
                             (167, "NET_C(GND, IC_M8.12, IC_M8.13)"),
                             (171, "NET_C(GND, IC_K9.1,  IC_K9.5, IC_K9.9, IC_K9.11, IC_K9.13)"))],
              *[dict(line=n, text=f"HINT({t}, NC)", action="drop-line",
                     why="this output is used elsewhere on the board")
                for n, t in ((275, "IC_K9.2"), (276, "IC_K9.6"), (277, "IC_K9.8"),
                             (278, "IC_K9.10"), (279, "IC_K9.12"), (293, "IC_L7.3"),
                             (294, "IC_L7.6"), (296, "IC_M8.6"), (297, "IC_M8.8"),
                             (298, "IC_M8.11"))]],
        add=[sheet(f"{where}: {ic} pin {pin} is used there, not by the sound", f"IC_{ic}.{pin}",
                   name=f"{ic}_{pin}")
             for ic, pins, where in (("K9", (1, 2, 5, 6), "sheet 5"), ("K9", (9, 8), "sheet 4's "
                                     "output-strobe decode (ABUS3 in, out to E8 pin 5)"),
                                     ("K9", (13, 12, 11, 10), "sheet 3 (H7/J7 to the H4/J4 "
                                     "strobes)"),
                                     ("M8", (4, 5, 6, 9, 10, 8, 12, 13, 11), "sheet 5's video "
                                     "summing"),
                                     ("L7", (1, 2, 3, 4, 5, 6), "sheet 5's object video"))
             for pin in pins],
        ports={"OUTPUT": "the volume pot's wiper, on through C81 to the TDA1004 amplifier at "
                         "B10, which MAME does not simulate",
               **{f"{ic}_{pin}": f"a spare gate of the sound's {ic}, used by another circuit on "
                                 "the board" for ic, pins in (("K9", range(1, 14)), ("M8", range(4, 14)),
                                                              ("L7", range(1, 7)))
                  for pin in pins}},
        about=ATARI, notes=["""\
Compared with the schematic, sheet 4 of 5 (TM-106 p. 37, a clean 300 ppi scan), with the
other four sheets and the parts list (pp. 64-65), on 2026-10-20: all 64 of MAME's nets in
the sound circuit agree with the sheet, pin for pin and value for value, and so do the
supplies (the LM324s at C9 and H9 on +12V and -5V, from a 7812 and a 7905; the MC3340 at
D10 on +5V and -5V). The ports are the sheet's: F8 (a 9334) drives SONGATE, LAUNCH, EXPLO,
SONLAT, HE and LE (addresses 1002-1007, HE 'high explosion', LE 'low explosion'); F7 (a
74174) drives MOTOR_SPEED and ATTRACT, and NOISE -- the shift registers' clear -- is F7 pin
5, which sheet 1's address map calls 'KICKER'.

What MAME's 'Tie off unused gates and pins' block gets wrong is the board, not the sound:
every K9 inverter, M8's gates on 4-6, 8-10 and 11-13, and L7's on 1-6 are used by the video
and strobe logic on sheets 3-5, so they are ports here, not nc. The 556's RESETs (H8 4 and
10) and its outputs 5 and 9 are bare stubs on the sheet, as nc says; MAME ties the RESETs
to +5V. A9's spare gates and L7 8-10 appear on no sheet (a visual sweep, not certain).

On the sheet and not in this file: the decoupling capacitors C50, C60 (+12V), C54, C65 and
C73 (-5V); a second, open jumper from the D10 pin 6 / Q4 node to the TDA1004's pin 5 and
C83, beside the closed one this file has; and the TDA1004 amplifier itself (C81 from the
volume pot's wiper, C82-C90, the speaker on edge pin 7). On all six electrolytics MAME's
pin 1 is the + end. R78 has a pen scribble through its value; it reads 5.6K, and the parts
list agrees."""]),
    "flyball-sound": dict(
        source="src/mame/atari/nl_flyball.cpp", netlist="flyball",
        title="Flyball sound circuits",
        board=circuit(
            "Flyball sound circuits", "Atari", "1976", "flyball",
            "Sound section of the Flyball game board schematic, technical manual TM-075 "
            "(doc 99d8167a63a1) -- via MAME's netlist",
            "Flyball game board, sound section: a 74164 noise generator, bat (556), footstep "
            "and crowd sounds through two MC3340 attenuators, and the mixer.",
            "Converted from MAME's netlist, compared with sheet 7 and corrected from it, up to "
            "the mixer's output capacitor; the TDA1004 amplifier after it is not in MAME.",
            corrected=True),
        ports={"OUTPUT": "on to the audio amplifier, which MAME does not simulate"},
        corrected_from="sheet 7 of the schematic (005629 rev A, TM-075 pp. 56-57)",
        undo=[dict(line=73, text="NET_C(VCC, IC_E7.14, IC_B7.14, IC_C7.14, IC_D7.14, IC_E7.13,",
                   action="remove", terms=["IC_E7.13", "IC_B7.9", "IC_B7.2", "IC_C7.9", "IC_C7.2"],
                   why="sheet 7 pulls E7.13 up through R25, and draws B7 and C7 pins 2 and 9 as "
                       "bare stubs"),
              dict(line=91, text="NET_C(VCC, IC_D7.13, IC_D7.1)", action="remove",
                   terms=["IC_D7.1"], why="sheet 7 pulls D7.1 up through R25"),
              dict(line=111, text="NET_C(V5, IC_E7.2, R73.1, R74.1)", action="remove",
                   terms=["IC_E7.2"], why="sheet 7 pulls E7.2 up through R25")],
        add_parts=[part("R25", "R", "1K", "sheet 7: 'P,R25', one of the 1K pull-ups the power "
                                          "supply corner lists (R1, 4, 5, 23, 25, 29)")],
        add=[sheet("sheet 7: the pull-up R25 ('P,R25') on D7.1, E7.2 and E7.13", "V5", "R25.1"),
             sheet("as above", "R25.2", "IC_D7.1", "IC_E7.2", "IC_E7.13")],
        about=ATARI, notes=["""\
Compared with the schematic, sheet 7 of 9 'Sound Generator' (005629 rev A, TM-075 pp.
56-57, the sheet scanned in two halves), with parts list A005629-01 (pp. 62-65), on
2026-10-20: 39 of MAME's 41 nets agree pin for pin -- the noise generator (all ten of its
connections), the band-pass filter, the bat sound's 556, the footstep envelope, the crowd
and whistle control and the mixer -- and the supplies are as MAME has them (+18V, an
unregulated rail, on A8, C8 and D8). Corrected above from the sheet: D7.1, E7.2 and E7.13
go to +5V through the 1K pull-up R25, which MAME leaves out, and B7 and C7 pins 2 and 9
(B gate and CLR) are drawn as bare stubs, which MAME ties to +5V -- an open TTL input
floats high, the level the circuit needs, so the board may tie them, but the drawing does
not. D7.13 is drawn 'P', an unnamed pull-up, and is left on +5V here.

Kept as MAME has them, each against the sheet: R79 is 820K on the sheet and the parts list
and 1K in MAME, whose comment says 'Verified as 1K on a real board'; R97B (24.4K, in
parallel with R97) is on neither, and MAME's comment says it was 'verified to exist on a
real board'; C46/C47 are .01 on the sheet and .015 on the parts list, which MAME follows;
R80 is 330K on the sheet and 330 ohms on the parts list, and MAME follows the sheet. A8 and
C8 are printed 'MFC3340P' with the MFC6040's pin numbers in brackets beside each pin, and
the parts list fits MFC6040s, with the MFC3340 as the substitute 'when stock of MFC6040 is
depleted'; this file is the MFC3340 wiring, so a board carrying MFC6040s has the bracketed
pins instead (as Tank's do). E7's fourth gate (4, 5, 6), which MAME grounds, is not on
sheet 7, and the output amplifier (the TDA1004 at B9) is on it and not in MAME."""]),

    # -----------------------------------------------------------------------
    # Namco (Tank Battalion: Ryan Holtz, BSD-3-Clause; Rally-X: Ricardo
    # Bittencourt, CC0-1.0). Namco designators are number-first (6F).
    # -----------------------------------------------------------------------
    "tankbatt-sound": dict(
        source="src/mame/namco/nl_tankbatt.cpp", netlist="tankbatt",
        title="Tank Battalion sound circuits",
        board=circuit(
            "Tank Battalion sound circuits", "Namco", "1980", "tankbatt",
            "Sound section of the Tank Battalion schematic, service manual (doc 73495cc3ecf0) "
            "-- via MAME's netlist",
            "Tank Battalion, sound section: CD4006 noise, hit and shoot through CD4066 "
            "switches and LM324 filters, engine rumble from a 7492, mixed.",
            "Converted from MAME's netlist, up to the summing node; the amplifier after it is "
            "not in MAME."),
        undo=[dict(line=87, text="NET_C(VCC, _5K.5, _6F.VDD, _6J.4, _6K.7,", action="remove",
                   terms=["_6K.7"], why="pin 7 of the 7486 at 6K is its ground"),
              dict(line=88, text="NET_C(GND, _5K.10, _6F.VSS, _6J.11, _6K.14,", action="remove",
                   terms=["_6K.14"], why="pin 14 of the 7486 at 6K is its supply")],
        corrected_from="the 7486's standard pinout -- the site holds no Tank Battalion PCB schematic",
        add=[sheet("pin 14, the 7486's VCC, on +5V (MAME's lines 87-88 swap its supply pins; "
                   "its TTL_7486_DIP model does not use them)", "V5", "_6K.14"),
             sheet("pin 7, the 7486's GND, on ground", "GND", "_6K.7")],
        ports={},
        about="""\
Ryan Holtz's netlist of Tank Battalion's discrete sound, which his file says is derived
from the schematics in the manual. The sound latch bits (S1, S2, OFF, ENGINE_HI, SHOOT,
HIT) and the video counter's 2V and 4V arrive as ports. MAME reaches into the 7486's
gates by name (6K.A.Q) and declares the CD4006 without its package; both are put on
their pins by MAME's own DIP models. The diodes are generic in MAME: 'types not listed
on schematic'.""",
        notes=["""\
MAME's netlist ends at the summing node of R35, R36, R56_1, R56_2 and R59, so this file
has no output port of its own; the node is a plain net here. R56 appears twice in MAME
(R56_1, R56_2), one on each of the hit and shoot channels.

Not compared with the sheet: the site's Tank Battalion manual (doc 73495cc3ecf0, the
upright service manual) has no PCB schematic -- operation, test, cabinet parts lists,
the harness (p29) and a block diagram (p30) only (read 2026-10-20); MAME worked from a
printing that has one. What the manual does show is where the sound goes after this
file: a volume pot on the PCB (Fig. 5-7), the audio output on J1 pin 18 (the speaker
check is #18 to Z), a second volume pot behind the coin door on J4 pins 12-14 and the
speaker on J6, and a 12V AC centre-tapped winding for 'audio power', so a power
amplifier on the board that MAME does not have. So the 7486 supply fix rests on the
part's pinout alone, and R46/R49 are MAME's 4.7K against what its own comment says the
schematic prints (47K).""", UNCHECKED]),
    "rallyx-bang": dict(
        source="src/mame/namco/nl_rallyx.cpp", netlist="rallyx",
        title="Rally-X explosion sound",
        board=circuit(
            "Rally-X explosion sound", "Namco", "1980", "rallyx",
            "Logic Bd I schematic A082-91385-C000, Rally-X Parts and Operating Manual (doc "
            "1cc6c9614736, PDF p. 39) -- via MAME's netlist, compared with it and corrected",
            "Rally-X Logic Board I, explosion ('BANG') circuit: CD4006/CD4070 noise gated by a "
            "CD4066, a uA741 stage at 12E and an MB3730 bridge amplifier at 12A.",
            "Converted from MAME's netlist and corrected from the sheet: the explosion circuit "
            "and the power amplifier, with the Namco WSG's audio arriving as a port. The rest "
            "of the board's sound is a MAME device, not a netlist.",
            corrected=True),
        designators={"SR": "U11A", "XOR": "U11C", "SW": "U11D", "U741": "U12E",
                     "U3730": "U12A"},
        not_parts={"SPK": "the speaker, bridged across the amplifier's outputs, which MAME "
                          "models as an 8 ohm resistor ('assumed 8 ohm')"},
        corrected_from="the Logic Bd I schematic (A082-91385-C000, manual PDF p. 39)",
        undo=[dict(line=138, text="NET_C(VR1.2, GND)", action="drop",
                   why="VR1 is a pot on the sheet, not a resistor: its bottom is grounded and "
                       "C4 is on its wiper"),
              dict(line=165, text="NET_C(R30.2, C4.1)", action="drop",
                   why="the sheet takes C4 from VR1's wiper, not from VR1's top"),
              dict(line=168, text="NET_C(U3730.2, C26.1)", action="drop",
                   why="the sheet puts C27 (22uF) on MB3730 pin 2, not C26"),
              dict(line=171, text="NET_C(U3730.3, C27.1)", action="drop",
                   why="the sheet puts C26 (220uF) on MB3730 pin 3, not C27"),
              dict(line=174, text="NET_C(U3730.6, R70.1, SPK.1)", action="remove",
                   terms=["R70.1"], why="the sheet's Zobel on pin 6 is R69/C32"),
              dict(line=177, text="NET_C(U3730.5, R69.1, SPK.2)", action="remove",
                   terms=["R69.1"], why="the sheet's Zobel on pin 5 is R70/C31")],
        add_parts=[part("VR1", "POT", "1K", "the sheet's volume pot, which MAME writes as a "
                                             "resistor at full volume"),
                   part("C25", "C", "100uF", "the sheet: 100uF 16V on the MB3730's +12V"),
                   part("C3", "C", "0.1uF", "the sheet: 0.1uF on the MB3730's +12V")],
        add=[sheet("the sheet: VR1's bottom to ground, its wiper to C4", "GND", "VR1.3"),
             sheet("as above", "VR1.2", "C4.1"),
             sheet("the sheet: MB3730 pin 2 to C27 (22uF), pin 3 to C26 (220uF)", "U3730.2",
                   "C27.1"),
             sheet("as above", "U3730.3", "C26.1"),
             sheet("the sheet: the Zobel on pin 6 is R69/C32, on pin 5 R70/C31", "U3730.6",
                   "R69.1"),
             sheet("as above", "U3730.5", "R70.1"),
             sheet("the sheet: C25 and C3 decouple the MB3730's +12V", "I_V12", "C25.1", "C3.1"),
             sheet("as above", "GND", "C25.2", "C3.2"),
             sheet("the speaker's leads: MB3730 pin 6 to edge pin 19, pin 5 to edge pin W, both "
                   "'SPKR'", "U3730.6", name="SPEAKER_M"),
             sheet("as above", "U3730.5", name="SPEAKER_I")],
        ports={"SPEAKER_M": "to the speaker on edge pin 19 ('SPKR'), bridged with SPEAKER_I",
               "SPEAKER_I": "to the speaker on edge pin W ('SPKR'), bridged with SPEAKER_M"},
        about="""\
Ricardo Bittencourt's netlist of Rally-X's explosion sound, which his file says is
reconstructed from the hand-drawn schematic. It names the noise ICs by position (11A
CD4006, 11C CD4070, 11D CD4066); the uA741 and the MB3730 it calls U741 and U3730, which
are at 12E and 12A on the sheet and the assembly drawing. The Namco WSG's audio is fed
in by MAME at R28 (I_AUDIO), so it is a port here, and the 'BANG' latch bit (12M 74LS259
Q0 on the sheet) is a port.""",
        notes=["""\
Compared with the Logic Bd I schematic, A082-91385-C000 dated 1/9/81 (PDF p. 39 of the
manual, doc 1cc6c9614736, with p. 40's overlap; the 'fold-out', doc 47826bd174c7, is the
assembly drawings), on 2026-10-20 -- every net in the file. The noise generator agrees pin
for pin, including the spare 4070 and 4066 sections, which the sheet does ground as MAME
does, and C35's grounded end; so do the uA741 stage, the WSG mix and every value. Corrected
above from the sheet: the MB3730's capacitors and Zobel networks were on each other's pins
in MAME (pin 2 has C27 22uF and pin 3 C26 220uF; pin 6 has R69/C32 and pin 5 R70/C31), VR1
is a pot with C4 on its wiper, and C25 and C3 decouple the amplifier's +12V.

The MB3730's pin names (FB on 2, BYPASS on 3) are MAME's model of the part; with the
capacitors where the sheet puts them, either those names or MAME's placement was wrong,
and no Fujitsu data sheet has been read to say which. MAME's comment calls C6 'across
R41'; on the sheet, and in MAME's own connections, it runs from the input node to the
741's output. D1 is printed '1S15..' with the last digits filled in, and the assembly
notes say D1-D5 are 1N914B; MAME's 1S1588 is kept. The CD4xxx supply pins are not drawn;
+5V and ground on 14 and 7 are assumed."""]),

    # -----------------------------------------------------------------------
    # Irem M62 (Andrew Gardner, Couriersud, BSD-3-Clause)
    # -----------------------------------------------------------------------
    "kidniki-sound": dict(
        source="src/mame/irem/nl_kidniki.cpp", netlist="kidniki",
        title="Kid Niki sound board (Irem M62)",
        board=circuit(
            "Kid Niki sound board", "Irem", "1986", "kidniki",
            "Nanao M62-A-B sheet 4/4 (E-C0066-4), in the Kid Niki conversion kit manual (doc "
            "2e7a6f4d8772, p. 22) -- via MAME's netlist, which was made from a KiCad redraw of "
            "it; compared with the sheet",
            "Irem M62 sound board, analogue section: the drum and cymbal generators, the "
            "MSM5205 and AY-3-8910 mixing, the output stage.",
            "Converted from MAME's netlist: the analogue sound circuits. The two AY-3-8910s "
            "and the MSM5205s are MAME devices; their outputs are ports."),
        ic_names=r"XU(\d+)",
        fix_parts={"XU1": ("LM324", "sheet 4/4 prints LM324 (the LM2902 MAME names has its pins)")},
        corrected_from="sheet 4/4 of the M62 schematic (E-C0066-4)",
        not_parts={n: "the AY-3-8910's own output resistance, which MAME draws as a 1K "
                      "resistor" for n in ("R_AY45L_A", "R_AY45L_B", "R_AY45L_C",
                                           "R_AY45M_A", "R_AY45M_B", "R_AY45M_C")},
        loads={"SINH_DUMMY": "a 10M resistor where D6 would be: MAME's file says D6 is missing "
                             "on the M62 boards in PCB pictures, though its pads exist"},
        about="""\
Couriersud's netlist of the Irem M62 sound board, made from a KiCad redraw of the Kid
Niki schematic (the file keeps the EESCHEMA header), so the designators are the redraw's:
XU1 (LM2902), XU2 (LM358), XU3 (MC14584B), written U1-U3 here; R65_1 and R48_2 are the
redraw's names for parts the schematic numbers again. The AY-3-8910s and MSM5205s are
MAME devices; what they drive arrives as ports. Three of MAME's judgements about the
schematic are kept as MAME has them, all switches at the top of its file: FIX_SCHEMATIC_
ERRORS (XU1 section B given the feedback the schematic omits, and D4, D5 and Q4 wired as
the Kung-Fu Master schematic's manual corrections have them); D4_AND_D5_CONNECTED, which
MAME marks 'needs verification'; and J4 set to take channel C to the sound IC.""",
        notes=["""\
Compared with sheet 4/4 of the M62-A-B schematic (E-C0066-4, the conversion kit manual's
p. 22), with sheets 2/4 and 3/4 for J4 and D6, on 2026-10-20: 80 of the file's 84 nets
agree with the sheet, and every value printed. Three values are not fully legible: R98
reads '6?0K' (680K is the only standard value it fits), C36's last digit is under a line,
and R76 has none printed. The sheet prints LM324 at XU1 (written so above) and MC14584 at
XU3.

The disagreements are MAME's FIX_SCHEMATIC_ERRORS, kept as MAME has them: the sheet draws
XU1 section B with no feedback (pin 7 drives only R45), and joins D4's and D5's cathodes,
TR4's collector, C42 and the C43/R46/C35 node in one net -- MAME's uncorrected line --
where MAME follows the Kung-Fu Master schematic's manual corrections, which the site does
not hold. The MSM5205s reach the OKI node on sheet 3/4 through two resistors (one legibly
R64) and a capacitor (apparently C46); MAME's R200, R201 and C200 are its own names for
them, and on sheet 4/4 the line comes straight to R76, with no C200. D6 is drawn on sheet
2/4, between 1H pin 2 (a 74LS175) and the S-INH line, cathode at the latch; MAME's
reason for leaving it out is board photos, which the sheet cannot settle. J4 is a
three-terminal jumper on sheet 3/4 with no link drawn; J4 = 1 is MAME's choice."""]),

    # -----------------------------------------------------------------------
    # Nintendo Popeye (Couriersud, BSD-3-Clause)
    # -----------------------------------------------------------------------
    "popeye-sound": dict(
        source="src/mame/nintendo/nl_popeye.cpp", netlist="popeye",
        title="Popeye audio output stage",
        board=circuit(
            "Popeye audio output stage", "Nintendo", "1982", "popeye",
            "TPP2-CPU schematic, sheet 2 of 3, in the Popeye operation manual (doc a4dc252b9a5e, "
            "p. 35) -- via MAME's netlist, compared with it and corrected",
            "Popeye CPU board TPP2-CPU, audio: the AY-3-8910's three channels filtered and "
            "mixed, and the two-transistor output stage to the TV's audio.",
            "Converted from MAME's netlist: the AY-3-8910's filters, mixer and output stage. "
            "The AY is a MAME device; its outputs are ports.",
            corrected=True),
        rename={**{f"R_AY1_{i}": f"AY_{ch}" for i, ch in ((1, "A"), (2, "B"), (3, "C"))},
                "ROUT": "TV_AUDIO"},
        not_parts={**{f"AY_{ch}": "the AY-3-8910's own output resistance on channel " + ch +
                                  ", which MAME draws as a 1K resistor from +5V (R_AY1_" + str(i) +
                                  ")" for i, ch in ((1, "A"), (2, "B"), (3, "C"))},
                   "TV_AUDIO": "the load on the output, which MAME's file says is 'actually "
                               "located in TV' (ROUT); R67 goes to edge pin W, 'TV AUDIO'"},
        fix_values={"R65": ("5.1K", "the schematic prints 5.1K, and the parts list has R65 among "
                                    "its 5.1K resistors")},
        corrected_from="the TPP2-CPU schematic, sheet 2 of 3 (manual p. 35)",
        about="""\
Couriersud's netlist of Popeye's audio: the three AY-3-8910 channels through R52-R60 and
C4-C6 to a mixing node (R51, R57, R60, R61, C40) and C7, then the impedance changer Q8/Q9
(R62-R67), which MAME's file calls 'solely an impedance changer', to the TV's audio on edge
pin W. The AY's outputs are ports.""",
        notes=["""\
Compared with the TPP2-CPU schematic, sheet 2 of 3 (manual doc a4dc252b9a5e p. 35, clearly
legible), and the typeset parts list (p. 27), on 2026-10-20: all 14 nets agree, and every
value but one -- R65 is 5.1K on both the sheet and the parts list, where MAME has 2.1K,
corrected above. Q8 is a 2SC1815 and Q9 a 2SA1015 as MAME has them. One designator is in
doubt: the schematic letters the mixer's 20K 'R51', as MAME does, but also prints an R51
on sheet 3, a 100 ohm in the sync buffer, and the parts list has R51 at 100 ohms and R54 as
its only 20K -- so on the board this is most likely R54. Where R52's lead crosses channel
B the drawing is broken; only this file's reading (R52 from the AY's pin 4 to ground)
works. D2 (1S1595), a clamp on the AY's supply, is on the sheet and not in MAME."""]),

    # -----------------------------------------------------------------------
    # Universal Cheeky Mouse (Vas Crabb, CC0-1.0)
    # -----------------------------------------------------------------------
    "cheekyms-sound": dict(
        source="src/mame/universal/nl_cheekyms.cpp", netlist="cheekyms",
        title="Cheeky Mouse sound circuits",
        board=circuit(
            "Cheeky Mouse sound circuits", "Universal", "1980", "cheekyms",
            "Sound section of the Cheeky Mouse schematic (doc 8bf94944bfe5) -- via MAME's "
            "netlist",
            "Cheeky Mouse, sound: mute, cheese (a transistor noise source), mouse, hammer and "
            "pest (556 timers gated by an LM324), mouse and pest dies, coin, mixed.",
            "Converted from MAME's netlist, up to the volume pot."),
        sections=[("NE555", r"IC(\d)_([12])", "NE556")],
        add_parts=[part("Q2", "Q", "2SC945", "the cheese noise source: a 2SC945 whose base-emitter "
                                             "junction makes the noise, collector unconnected; "
                                             "MAME replaces it with a current-noise macro")],
        undo=[dict(line=53, text="NET_C(I_V5.Q, IC1.11, IC1.13)", action="nc",
                   why="'shut the netlist parser up about unconnected inputs'")],
        about="""\
Vas Crabb's netlist of Cheeky Mouse's sound, with Couriersud's notes. Each 556 is declared
one timer at a time as an NE555 (IC4_1, IC4_2 ...); they are written on the 556's pins
here. The sound latch bits arrive as ports. VPLUS is the supply MAME approximates as
12.9V: its file says '15V dropped by three diodes and filtered'.""",
        notes=["""\
Not compared with the sheet: the site's one Cheeky Mouse schematic (doc 8bf94944bfe5,
'Main Block Diagram', drawing 8004) is the CPU and video board, and shows the sound board
only as the connector pins it is wired to -- E1 (LS273) pins 2, 5, 6, 9, 12, 15, 16 and
19 and two of E2's go to it, and A7's coin pulse (read 2026-10-20). So two things here
are assumptions, not readings: which timer of each 556 a sound uses (MAME's IC4_1 is
taken as timer 1, pins 1-6, and IC4_2 as timer 2, pins 8-13; the sheet's own 556 at A7
is numbered that way, which says nothing about the sound board's), and Q2's collector,
which Couriersud's note says the schematic shows unconnected and this file leaves out.""",
               UNCHECKED]),
})


S16B_MACHINES = ("aceattac aliensyn aurail bayroute bullet cotton dddoor ddux dunkshot "
                 "eswat exctleag fantzn2x fpoint goldnaxe hwchamp mvp passsht riotcity ryukyu "
                 "sjryuko sonicbom suprleag timescan toryumon tturf ultracin wb3 wfishing "
                 "wrestwar wwthomas").split()

TARGETS.update({
    # -----------------------------------------------------------------------
    # Sega/Gremlin Borderline (beta-tester, CC0-1.0)
    # -----------------------------------------------------------------------
    "brdrline-sound": dict(
        source="src/mame/sega/nl_brdrline.cpp", netlist="brdrline",
        title="Borderline sound board (834-0055)",
        board=circuit(
            "Borderline sound board", "Sega", "1981", "brdrline",
            "Sound Board Assembly 834-0055 Rev. A, sheets 6 and 7 of 7, in the Borderline "
            "manual (doc 7756fbdad1fb, pp. 26-27) -- via MAME's netlist",
            "Borderline sound board 834-0055 Rev. A: gun, jeep, point, hit, animal, "
            "'emar', walk and cry sounds from 555s, 74123s, LM324s and MB4391 VCAs, mixed "
            "through eight volume pots.",
            "Converted from MAME's netlist and compared with both sheets, up to the mixer's "
            "output capacitor C76 and edge pin 4. The sound latch on the logic board is ports.",
            corrected=True),
        ic_names=r"IC(\d+)",
        hack_macros={
            "UNUSED_OP_PLUS": "which ties an unused op-amp input to a reference MAME adds; "
                              "the file calls it a hack",
            "UNUSED_OP_OUT_MINUS": "which ties an unused op-amp's output to its inverting "
                                   "input; the file calls it a hack",
            "UNUSED_TTL_I": "which grounds an unused TTL input; the file calls it a hack",
        },
        not_parts={"UNUSED_OP_RES": "a 20K divider MAME adds from +12V to bias the unused "
                                    "op-amp inputs it ties off"},
        loads={"Rsound": "MAME's 'dummy load' on the output",
               **{f"NC_IC{n}_OUT": "a 1M MAME hangs on a 555 output that is 'not connected in "
                                   "schematics'" for n in (1, 6, 7, 8, 10, 11, 12, 13, 14, 16, 17,
                                                           18, 19)}},
        values={**{f"TR{n}": ("2SC458", "MAME's C458() macro, 'npn transistor 2SC458', declares "
                                        "it as a generic NPN") for n in range(1, 17)},
                **{f"D{n}": ("MA150", "MAME's MA150() macro declares it as a generic diode")
                   for n in range(1, 7)}},
        ports={"SOUND_OUT": "edge pin 4, 'SOUND' (edge pin 3, 'OUT', is its ground return), to "
                            "the amplifier"},
        corrected_from="sheet 6 of the sound board (834-0055 Rev. A)",
        undo=[dict(line=447, text="NET_C(IC30.6/*QQ1*/, IC29.4/*A2*/)", action="drop",
                   why="sheet 6 feeds IC29 pin 5 from IC30 pin 6, and pin 4 from pin 8"),
              dict(line=448, text="NET_C(IC30.8/*QQ2*/, IC29.5/*B2*/, R123.1)", action="drop",
                   why="as above")],
        add=[sheet("sheet 6: IC29 gate 2's inputs the other way round from MAME's (the same AND, "
                   "so the same circuit)", "IC30.6", "IC29.5"),
             sheet("as above", "IC30.8", "IC29.4", "R123.1")],
        about="""\
beta-tester's netlist of the Borderline sound board, from the schematics in the
Borderline Quest Owner's Manual (420-0613), sheets 6 and 7 of 7 -- the file's header
lists each sound's trigger and the sheet grid squares it runs through. ICs are IC1-IC38
on the sheet, written U1-U38 here. Two of MAME's notes about the sheet are carried: the
transistors of the sound generators are drawn with base and collector swapped on the
schematic, which MAME corrects (so this file is wired as MAME has it, not as drawn); and
the MB4391 is a part MAME has no model of -- its file's MB4391 is 'a fake substitution',
its behaviour guessed, though the pins it puts things on are the sheet's. The eight
sound triggers arrive as ports from the logic board's LS374 latch; MAME's file gives
the latch-to-trigger order as it wires the cabinet (D0 ANIMAL ... D7 GUN).""",
        notes=["""\
Compared with both sound board sheets, 834-0055 Rev. A sheets 6 and 7 of 7 (the Borderline
manual, doc 7756fbdad1fb, PDF pp. 27-28 -- MAME's 'page 26' and '27' -- with the parts list
on pp. 17-20), on 2026-10-20: 42 groups of nets, about 230 pin connections, touching every
IC from IC1 to IC38, and about 150 values. All agree but one, IC29 gate 2's two inputs,
which MAME has the other way round (the same AND, so the same circuit; corrected above).
The sheet letters the MB4391s' IN, CON and OUT pins (1, 2, 15 and 5, 6, 11) as MAME has
them, and draws pins 14 and 10 to the 680pF capacitors; the name RO for those, and the
supplies on 3, 7, 12 and 16, are MAME's -- no MB4391 supply pin is drawn. MAME's base-and-
collector correction holds on all sixteen 2SC458s: as drawn, the 555's DIS could not
switch the transistor and nothing would oscillate (a likely cause is the 2SC458's E-C-B
leads traced as E-B-C). IC28's RESET is not drawn at all, so nc is the sheet's; a 555 needs
it high to run, so the board presumably ties it to +5V with a trace the drawing omits, as
it omits every supply pin. All thirteen 555 outputs MAME loads are undrawn, and the spare
gates of IC29, IC36 and IC27 are not drawn either.

On the sheet and not in this file: +6V is not a supply but a divider -- R135 and R136, 1K
each from +12V, with a 100uF capacitor on each side -- and the supplies come in on edge pins
20 (+12V), 17 (+5V) and 16 (ground), with decoupling MAME leaves out. The triggers enter
on edge pins 5-12 (GUN, JEEP, POINT, HIT, ANIMAL, EMAR, WALK, CRY), active low with 1K
pull-ups; which latch bit drives which is not on the sheet. The sheet prints LS08, LS74 and
LS123 where MAME has plain TTL, no designator on the ANIMAL 555 (MAME's IC1, which sheet
6's reset list supports) or on the 1uF at IC14 pin 5 (MAME's C2), and '555' beside two of
IC9's op-amp sections -- a slip; the parts list makes IC9 an LM324. The top of sheet 7 is
cut off by the scan (IC34's B/CLR tie, R109's label). The site's 'Star Raker' schematics
filed under Borderline (doc 6b1a0aeb2bbe) are Star Raker's logic board, not this one."""]),

    # -----------------------------------------------------------------------
    # Sega System 16B (Couriersud, CC0-1.0): the audio section of the CPU board
    # every System 16B game runs on (bar the Philko boards, which MAME gives a
    # different sound).
    # -----------------------------------------------------------------------
    "segas16b-audio": dict(
        source="src/mame/sega/nl_segas16b.cpp", netlist="segas16b_audio",
        title="Sega System 16B audio section",
        board=dict(circuit(
            "Sega System 16B audio section", "Sega", "1987", "altbeast",
            "Audio section of the System 16B CPU board schematic, which this site does not "
            "hold -- via MAME's netlist",
            "Sega System 16B CPU board, audio: the YM3012 DAC's two channels and the uPD7759 "
            "speech through TL084 and LM324 filters to the mixer and preamplifier.",
            "Converted from MAME's netlist, up to the power amplifier's input. The YM2151/"
            "YM3012 and uPD7759 are MAME devices; their outputs are ports."),
            machines=S16B_MACHINES),            # the rest, as for Sega System 18
        designators={"D20": "UD20", "XC20": "UC20"},
        loads={"AMP_IN": "a 100K MAME assumes for the M51516L amplifier's input"},
        ports={"OUT": "to the power amplifier (an M51516L, MAME's file says), which MAME does "
                      "not simulate"},
        about="""\
Couriersud's netlist of the audio section of the System 16B CPU board, used for every
System 16B game in MAME. The two YM3012 channels arrive as ports (CH1, CH2: MAME feeds
the YM2151's output in directly and replaces the YM3012's sample-and-hold with the
two RCOM resistors, as its file explains), and the uPD7759's speech as a current sink
(SPEECH). The two op-amps are D20 (TL084) and XC20 (LM324): MAME's X keeps the IC at
C20 apart from the capacitor C20, and both are written by position here, UD20 and UC20.
VR1 is a resistor in MAME that is 'actually a potentiometer'.""",
        notes=["""\
MAME's file marks its own doubts, and they are kept as it has them. It puts the mixer
stage on XC20 pins 9, 8 and 10 where, its comments say, the schematic reads 9, 7 and 8 --
7 is already the speech filter's output, so MAME moved the stage onto the third section
and asks 'other AMP?' of each. C19 and C22 'need verification', and the op-amps' supply
is assumed: 'no information on schematics, assume 12V'. The site holds no System 16B
schematic to settle any of it.""", UNCHECKED]),
})
