/* Jet Fighter by Atari 1975 */

//WIP 09/17/2013
/* todo: speed hacks? */

// jet1 (player 2/game) is black, jet2 (player 1) is white.


#include "../circuit_desc.h"
#include "../circuit.h"


#define DEBUG
#undef DEBUG

#ifdef DEBUG
static VcdLogDesc vcd_log_desc
(
    "output_jetfighter.vcd",
    1, "A",
    2, "B",
    3, "C",
    4, "D",
    5, "E",
    6, "F",
    7, "G",
    8, "H",
    9, "I",
    10, "J",
    11, "K",
    12, "L",
    13, "M",
    14, "N",
    15, "O",
    16, "P"
);
#endif

/*
 static RomDesc a4_desc("jetfighter", "jet1.a4", 0x08A0B011);
static RomDesc j1_desc("jetfighter", "jet1.j1", 0xBEE62D20);
static RomDesc j5_desc("jetfighter", "jet1.j5", 0xC58EE65D);
static RomDesc k5_desc("jetfighter", "jet1.k5", 0x0D5648A9);
static RomDesc m1_desc("jetfighter", "jet1.m1", 0xBEE62D20);
static RomDesc r5_desc("jetfighter", "jet1.r5", 0xBD95F87E);
*/
static RomDesc a4_desc("jetfighter", "004252.a4", 0x08A0B011);
static RomDesc j1_desc("jetfighter", "004250.j1", 0xBEE62D20);
static RomDesc j5_desc("jetfighter", "004253-02.j5", 0xC58EE65D);
static RomDesc k5_desc("jetfighter", "004253-01.k5", 0x0D5648A9);
static RomDesc m1_desc("jetfighter", "004250.m1", 0xBEE62D20);
static RomDesc r5_desc("jetfighter", "004251.r5", 0xBD95F87E);

static N8225Desc m8_desc;
static N8225Desc n8_desc;

static Astable555Desc k9_555_desc(K_OHM(510.0), K_OHM(470.0), U_FARAD(10.0));

static PotentimeterAstable555Desc pot1_desc("playtime", "Play Time", K_OHM(510.0), K_OHM(10.0), K_OHM(1010.0), k9_555_desc);

static DipswitchDesc dipswitch1_desc("coinage", "dice_dipswitch_1", "Coinage", 0, "25 Cents/2 players", "50 Cents/2 players");

static VIDEO_DESC( jetfighter )
    VIDEO_RESISTANCE(1, OHM(470))
    VIDEO_RESISTANCE(2, OHM(470))
    VIDEO_RESISTANCE(3, OHM(470))
    VIDEO_RESISTANCE(4, OHM(470))
    VIDEO_CONTRAST(2.0)
    VIDEO_RETRO_V_SIZE(252)
VIDEO_DESC_END

static INPUT_DESC( jetfighter )
    INPUT_INFO(JOYSTICK1_INPUT, {{ Joystick::LEFT, Joystick::RIGHT }}, "Rotate White Plane")
    INPUT_INFO(JOYSTICK1_INPUT, {{ Joystick::UP }}, "Increase Speed")
    INPUT_INFO(JOYSTICK1_INPUT, {{ Joystick::DOWN }}, "Decrease Speed")
    INPUT_INFO(BUTTONS1_INPUT, {{ 1 }}, "Fire Gun")
    
    INPUT_INFO(JOYSTICK2_INPUT, {{ Joystick::LEFT, Joystick::RIGHT }}, "Rotate Black Plane")
    INPUT_INFO(JOYSTICK2_INPUT, {{ Joystick::UP }}, "Increase Speed")
    INPUT_INFO(JOYSTICK2_INPUT, {{ Joystick::DOWN }}, "Decrease Speed")
    INPUT_INFO(BUTTONS2_INPUT, {{ 1 }}, "Fire Gun")

    INPUT_INFO(COIN_INPUT, {{ 1 }}, "Insert Coin")
    INPUT_INFO(START_INPUT, {{ 1 }}, "Start 1-Player Game")
    INPUT_INFO(START_INPUT, {{ 2 }}, "Start 2-Player Game")
INPUT_DESC_END

//**************************************************************


CIRCUIT_LAYOUT( jetfighter )

/* chips */

CHIP("A1", 7486)
CHIP("A2", 9316)
CHIP("A3", 74153)
CHIP("A4", 74S287, &a4_desc) // score number image
CHIP("A5", 9322)
CHIP("A6", 7493)
//CHIP("A7", 7403)
//CHIP("A8", 7403)
//CHIP("A9", 74)
CHIP("B1", 74164)
CHIP("B2", 9316)
CHIP("B3", 7474)
CHIP("B4", 9316)
CHIP("B5", 7493)
CHIP("B6", 7474)
//CHIP("B7", 7474)
//CHIP("B8", 7474)
//CHIP("B9", 324)
CHIP("C1", 7400)
CHIP("C2", 7404)
CHIP("C3", 7400)
CHIP("C4", 9316)
CHIP("C5", 7427)
CHIP("C6", 7420)
CHIP("C7", 7404)
CHIP("C8", 7474)
//CHIP("C9", 74)
CHIP("D1", 7432)
CHIP("D2", 74175)
CHIP("D3", 74175)
CHIP("D4", 7400)
CHIP("D5", 7490)
CHIP("D6", 7402)
CHIP("D7", 9316)
CHIP("D8", 7400)
CHIP("D9", 7413)
CHIP("E1", 7410)
CHIP("E2", 7420)
CHIP("E3", 7437)
CHIP("E4", 7408)
CHIP("E5", 7410)
CHIP("E6", 9316)
CHIP("E7", 7474)
CHIP("E8", 74279)
CHIP("E9", 7413)
CHIP("F1", 74175)
CHIP("F2", 9316)
CHIP("F3", 7410)
CHIP("F4", 74165)
//CHIP("F5", 74S, &f5_desc) // jet image and speed code ROM C
CHIP("F6", 7474)
CHIP("F7", 7400)
CHIP("F8", 7404)
//CHIP("F9", 556)
CHIP("H1", 9312)
CHIP("H2", 9316)
CHIP("H3", 7408)
CHIP("H4", 74165)
//CHIP("H5", 74)
CHIP("H6", 74193)
CHIP("H7", 7408)
CHIP("H8", 74153)
CHIP("H9", 7414)
CHIP("J1", 82S123, &j1_desc) //shell image ROM
CHIP("J2", 9316)
CHIP("J3", 74116)
CHIP("J4", 74165)
CHIP("J5", 82S131, &j5_desc) // jet image and speed code ROM A
CHIP("J6", 9322)
CHIP("J7", 74193)
CHIP("J8", 9322)
CHIP("J9", 7414)
CHIP("K1", 7400)
CHIP("K2", 9316)
//CHIP("K3", 74)
CHIP("K4", 74165)
CHIP("K5", 82S131, &k5_desc) // jet image and speed code ROM B
CHIP("K6", 9322)
CHIP("K7", 7486)
CHIP("K8", 7432)
CHIP("K9", 555_Astable, &k9_555_desc)  
CHIP("L1", 7400)
CHIP("L2", 9316)
CHIP("L3", 74116)
CHIP("L4", 74153)
CHIP("L5", 7400)
CHIP("L6", 9316)
CHIP("L7", 9316)
CHIP("L8", 7404)
//CHIP("L9", 74153)
CHIP("M1", 82S123, &m1_desc) //shell image ROM
CHIP("M2", 9316)
//CHIP("M3", 74)
CHIP("M4", 74153)
CHIP("M5", 9316)
CHIP("M6", 9316)
CHIP("M7", 7404)
CHIP("M8", 8225, &m8_desc)
CHIP("M9", 7493)
CHIP("N1", 9312)
CHIP("N2", 9316)
CHIP("N3", 7408)
CHIP("N4", 7474)
CHIP("N5", 9316)
CHIP("N6", 9316)
CHIP("N7", 7408)
CHIP("N8", 8225, &n8_desc)
CHIP("N9", 7493)
CHIP("P1", 7474)
CHIP("P2", 9316)
CHIP("P3", 7492)
CHIP("P4", 7474)
CHIP("P5", 74175)
CHIP("P6", 9316)
CHIP("P7", 9316)
CHIP("P8", 7400)
CHIP("P9", 7474)
CHIP("R1", 74H04)
CHIP("R2", 7410)
//CHIP("R3", 7474)
CHIP("R4", 7474)
CHIP("R5", 82S123, &r5_desc) //single player ROM 
CHIP("R6", 74153)
CHIP("R7", 7402)
//CHIP("R8", )
//CHIP("R9", 7474)

CHIP("CRYSTAL", CLOCK_12_096_MHZ)
CHIP("LATCH", LATCH)
CHIP("COIN_IN", COIN_INPUT)
CHIP("START_IN", START_INPUT)
//RR reverse controls because in one player mode the game controls plane 1, so we want player one to control plane 2.  
CHIP("JOYSTICK2", JOYSTICK1_INPUT)  
CHIP("JOYSTICK1", JOYSTICK2_INPUT)
CHIP("BUTTONS2", BUTTONS1_INPUT)
CHIP("BUTTONS1", BUTTONS2_INPUT)
CHIP("DSW1", DIPSWITCH, &dipswitch1_desc)
CHIP("POT1", POT_555_ASTABLE, &pot1_desc)
POTENTIOMETER_CONNECTION("POT1", "K9") 


/* 555 556
    1   7   ground
    2  6/8  trigger
    3  5/9  output
    4  4/10 reset
    5  3/11 control voltage
    6  2/12 threshold
    7  1/13 discharge
    8   14  Vcc   */


VIDEO(jetfighter)
INPUT(jetfighter)

OPTIMIZATION_HINT("K5", 256, 64)
OPTIMIZATION_HINT("J5", 256, 64)
OPTIMIZATION_HINT("F4", 256, 64)
OPTIMIZATION_HINT("H4", 256, 64)
OPTIMIZATION_HINT("J4", 256, 64)
OPTIMIZATION_HINT("K4", 256, 64)

#ifdef DEBUG
	CHIP("LOG1", VCD_LOG, &vcd_log_desc)
#endif

/* signals */

/* page 1 */

#define _12MHZ     "CRYSTAL", 1
#define _CLOCK     "D2", 15 
#define _CLOCKn    "D2", 14 
#define _1H        "F1", 15
#define _2H        "A2", 14 
#define _4H        "A2", 13
#define _8H        "A2", 12 
#define _16H       "A2", 11 
#define _32H       "B2", 14
#define _64H       "B2", 13
#define _128H      "B2", 12
#define _256H      "B2", 11
#define _64Hn      "C2", 4
#define _HSYNCn    "B3", 9
#define _HSYNC     "B3", 8 
#define _HBLANKn   "B3", 5
#define _HBLANK    "B3", 6
#define _HCLOCK    "E3", 8
#define _1V        "D3", 10
#define _2V        "B4", 14 
#define _4V        "B4", 13
#define _8V        "B4", 12 
#define _16V       "B4", 11 
#define _32V       "C4", 14
#define _64V       "C4", 13
#define _128V      "C4", 12
#define _256V      "C4", 11
#define _VSYNCn    "B6", 5
#define _VSYNC     "B6", 6 
#define _VBLANKn   "B6", 9
#define _VBLANK    "B6", 8
#define _VCLOCK    "E3", 6
#define _VRESETn   "C2", 12
#define _VRESET    "E3", 11
#define _1F        "C8", 9
#define _2F        "P3", 12
#define _3F        "P3", 9
#define _6F        "P3", 8
#define _SCORE1n   "C3", 11
#define _SCORE2n   "C3", 3
#define _64Hxnor128H "A1", 11
#define _R4        "J6", 4
#define _R3        "J6", 7
#define _R2        "J6", 12
#define _R1        "J6", 9
#define _R0        "K6", 4
#define _L4        "K6", 7
#define _L2        "K6", 12
#define _L1        "K6", 9
#define _ROM0      "J5", 12 
#define _ROM1      "J5", 11 
#define _ROM2      "J5", 10
#define _ROM3      "J5", 9
#define _ROM4      "K5", 12
#define _ROM5      "K5", 11
#define _ROM6      "K5", 10
#define _ROM7      "K5", 9
#define _S1C0      "L3", 5
#define _S1C1      "L3", 7
#define _S1C2      "L3", 9
#define _S1C3      "L3", 11
#define _S1C4      "L3", 17
#define _S1C5      "L3", 19
#define _S1C6      "L3", 21
#define _S1C7      "L3", 23
#define _S2C0      "J3", 5
#define _S2C1      "J3", 7
#define _S2C2      "J3", 9
#define _S2C3      "J3", 11
#define _S2C4      "J3", 17
#define _S2C5      "J3", 19
#define _S2C6      "J3", 21
#define _S2C7      "J3", 23
#define _J1C1      "N8", 5
#define _J1C0      "N8", 7
#define _J1C3      "N8", 9
#define _J1C2      "N8", 11
#define _J2C1      "M8", 5
#define _J2C0      "M8", 7
#define _J2C3      "M8", 9
#define _J2C2      "M8", 11
#define _LOAD3n    "C1", 3
#define _LOAD2n    "C1", 6
#define _LOAD1n    "C1", 8
#define _LOAD0n    "C1", 11
#define _NP        "L8", 2

/* in the manual it says:
LOAD0n = shell1 speed data, jet1 video
LOAD1n = jet1 speed data, jet1 video
LOAD2n = shell2 speed data, jet2 video
LOAD3n = jet2 speed data, jet2 video
each jet has 7 vertical lines, each with 16 bits of horizontal info
each shell has 8 vertical lines, each with 8 bits of horizontal info
*/


/* page 2 */

#define _J1H4      "P7", 12
#define _J1H64     "P6", 12
#define _J1H128    "P6", 11
#define _J1HWINDO  "D2", 7
#define _J1HWINDOn "D2", 6
#define _J1V1      "N6", 14
#define _J1V2      "N6", 13
#define _J1V4      "N6", 12
#define _J1V64     "N5", 12
#define _J1V128    "N5", 11
#define _VDATA1n   "L5", 6
#define _JET1n     "E2", 6
#define _JET1      "C2", 6
#define _J1S1      "A6", 12
#define _J1S2      "A6", 9
#define _J1S4      "A6", 8
#define _J1S8      "A6", 11
#define _J2H4      "L7", 12
#define _J2HWINDO  "D2", 2
#define _J2HWINDOn "D2", 3
#define _J2V1      "M6", 14
#define _J2V2      "M6", 13
#define _J2V4      "M6", 12
#define _VDATA2n   "L5", 3  //VDATA2 on diagram
#define _JET2n     "E2", 8
#define _JET2      "C2", 8
#define _J2S1      "B5", 12
#define _J2S2      "B5", 9
#define _J2S4      "B5", 8
#define _J2S8      "B5", 11
#define _HIT1      "E7", 6
#define _HIT1n     "E7", 5
#define _BLOUP2n   "E8", 7
#define _HIT2      "E7", 8
#define _HIT2n     "E7", 9
#define _BLOUP1n   "E8", 9
#define _FIRE1n    "E6", 15
#define _FIRE1     "C7", 6
#define _EXPL1n    "D8", 11
#define _EXPLO1TRIG "D6", 1
#define _FIRE2n    "D7", 15
#define _FIRE2     "C7", 10
#define _EXPL2n    "D8", 8
#define _EXPLO2TRIG "D6", 13
#define _S1H1      "N2", 14
#define _S1H2      "N2", 13
#define _S1H4      "N2", 12
#define _S1V1      "M2", 14 
#define _S1V2      "M2", 13
#define _S1V4      "M2", 12
#define _SHELL1n   "F1", 2
#define _SHELL1    "F1", 3
#define _S2H1      "H2", 14
#define _S2H2      "H2", 13
#define _S2H4      "H2", 12
#define _S2V1      "J2", 14 
#define _S2V2      "J2", 13
#define _S2V4      "J2", 12
#define _SHELL2n   "F1", 7
#define _SHELL2    "F1", 6

/* page 3 */

#define _J1R0       "H6", 3 
#define _J1R1       "H6", 2
#define _J1R2       "H6", 6
#define _J1R3       "H6", 7
#define _J1R4       "F6", 5
#define _J1R4n      "F6", 6
#define _J2R0       "J7", 3 
#define _J2R1       "J7", 2
#define _J2R2       "J7", 6
#define _J2R3       "J7", 7
#define _J2R4       "F6", 9
#define _J2R4n      "F6", 8
#define _SPLEFT1    "R7", 13 
#define _SPFIRECOM1 "R7", 4 
#define _SPRIGHT1   "R7", 10 
#define _SLOW1      "J8", 7
#define _LEFT1      "J8", 9
#define _RIGHT1     "J8", 12
#define _FIRECOM1   "J8", 4
#define _GO1n       "H8", 7 
#define _GO2n       "H8", 9
#define _1CREDIT    "D8", 6 
#define _2CREDIT    "C8", 5
#define _COIN       "C7", 2 
#define _COINn      "C5", 6
#define _START      "D3", 15
#define _STARTn     "D3", 14 
#define _1PLAY      "E8", 13
#define _Q          "F8", 6
#define _Qn         "F8", 8
#define _ATTRACTn   "C7", 8 
#define _ATTRACT    "D5", 11
#define _ENDGAMEn   "E8", 4
#define _GNEn       "E5", 8  // Game Near End (flashes score)
#define _FAST1n     "JOYSTICK1", Joystick::UP 
#define _SLOW1STAR  "J9", 2
#define _LEFT1STAR  "J9", 10
#define _RIGHT1STAR "J9", 12
#define _FIRECOM1STAR "J9", 4
#define _SLOW1      "J8", 7
#define _LEFT1      "J8", 9
#define _RIGHT1     "J8", 12
#define _FIRECOM1   "J8", 4
#define _FAST2n     "JOYSTICK2", Joystick::UP 
#define _SLOW2      "H9", 2
#define _LEFT2      "H9", 10
#define _RIGHT2     "H9", 12
#define _FIRECOM2   "H9", 4
#define _CP1n       "F8", 4
#define _CP2n       VCC // ignore coin 2 circuit


//*****circuit layout  *****
//from (output pins) - to (input pins)

/* * * * * * * page 1 * * * * * * */


/* clock (page 1, top left) */

CONNECTION("CRYSTAL", 1, "D2", 9)
CONNECTION("D2", 14,     "D2", 13)
CONNECTION(VCC,          "D2", 1)

CONNECTION(_CLOCK,       "F1", 9)
CONNECTION("F1", 14,     "F1", 13)
CONNECTION(VCC,          "F1", 1)


/* H sync */

CONNECTION(_CLOCK,       "A2", 2)
CONNECTION(_1H,          "A2", 10)
CONNECTION(_1H,          "A2", 7)
CONNECTION(VCC,          "A2", 1)
CONNECTION(VCC,          "A2", 9)
CONNECTION(GND,          "A2", 3) //not shown
CONNECTION(GND,          "A2", 4) //not shown
CONNECTION(GND,          "A2", 5) //not shown
CONNECTION(GND,          "A2", 6) //not shown

CONNECTION(_CLOCK,       "B2", 2)
CONNECTION("A2", 15,     "B2", 10)
CONNECTION("A2", 15,     "B2", 7)
CONNECTION(VCC,          "B2", 1) 
CONNECTION("C2", 10,     "B2", 9)
CONNECTION(GND,          "B2", 3)
CONNECTION(GND,          "B2", 4)
CONNECTION(VCC,          "B2", 5)
CONNECTION(GND,          "B2", 6)

CONNECTION("B2", 15,     "C2", 11)
CONNECTION(_64H,         "C2", 3)

CONNECTION("C2", 4,      "B3", 10)
CONNECTION(_256H,        "B3", 12)
CONNECTION(_32H,         "B3", 11)
CONNECTION(VCC,          "B3", 13)


/* V sync and V reset */

CONNECTION(_HSYNCn,      "D3", 9)
CONNECTION("D3", 11,     "D3", 12)
CONNECTION(VCC,          "D3", 1)

CONNECTION(_HSYNCn,      "B4", 2)
CONNECTION(_1V,          "B4", 10)
CONNECTION(_1V,          "B4", 7)
CONNECTION(VCC,          "B4", 1) 
CONNECTION(_VRESETn,     "B4", 9)
CONNECTION(GND,          "B4", 3)
CONNECTION(GND,          "B4", 4)
CONNECTION(GND,          "B4", 5)
CONNECTION(VCC,          "B4", 6)

CONNECTION(_HSYNCn,      "C4", 2)
CONNECTION("B4", 15,     "C4", 10)
CONNECTION("B4", 15,     "C4", 7)
CONNECTION(VCC,          "C4", 1) 
CONNECTION(_VRESETn,     "C4", 9)
CONNECTION(VCC,          "C4", 3)
CONNECTION(VCC,          "C4", 4)
CONNECTION(VCC,          "C4", 5)
CONNECTION(GND,          "C4", 6)

CONNECTION("C4", 15,     "C2", 13)

CONNECTION(_VRESETn,     "E3", 12)
CONNECTION(_VRESETn,     "E3", 13)

CONNECTION(_VRESETn,     "B6", 1)
CONNECTION(_2V,          "B6", 3)
CONNECTION(VCC,          "B6", 2)
CONNECTION(VCC,          "B6", 4)


/* H clock (page 1, top right) */

CONNECTION(VCC,          "B3", 4)
CONNECTION(_256H,        "B3", 2)
CONNECTION(_4H,          "B3", 3)
CONNECTION(_256H,        "B3", 1)

CONNECTION(_HBLANKn,     "E3", 10)
CONNECTION(_CLOCKn,      "E3", 9)


/* V clock */

CONNECTION(VCC,          "B6", 10)
CONNECTION(_256V,        "B6", 12)
CONNECTION(_4V,          "B6", 11)
CONNECTION(_256V,        "B6", 13)

CONNECTION(_VBLANKn,     "E3", 4)
CONNECTION(_HSYNC,       "E3", 5)


/* frame counter */

CONNECTION(VCC,          "C8", 10)
CONNECTION("C8", 8,      "C8", 12)
CONNECTION(_VSYNCn,      "C8", 11)
CONNECTION(VCC,          "C8", 13)

//nn CONNECTION(GND,          "P3", 2)
//nn CONNECTION(GND,          "P3", 3)
CONNECTION(GND,          "P3", 6)
CONNECTION(GND,          "P3", 7)
CONNECTION(_1F,          "P3", 1)
CONNECTION(_1F,          "P3", 14)


/* score display (page 1, mid-left) */

CONNECTION(_128H,        "A5", 1)
CONNECTION(_J1S8,        "A5", 2)
CONNECTION(_J2S8,        "A5", 3)
CONNECTION(_J1S4,        "A5", 5)
CONNECTION(_J2S4,        "A5", 6)
CONNECTION(_J1S2,        "A5", 14)
CONNECTION(_J2S2,        "A5", 13)
CONNECTION(_J1S1,        "A5", 11)
CONNECTION(_J2S1,        "A5", 10)
CONNECTION(GND,          "A5", 15)

CONNECTION("A5", 4,      "A4", 15)
CONNECTION("A5", 7,      "A4", 1)
CONNECTION("A5", 12,     "A4", 2)
CONNECTION("A5", 9,      "A4", 3)
CONNECTION(_8V,          "A4", 4)
CONNECTION(_4V,          "A4", 7)
CONNECTION(_2V,          "A4", 6)
CONNECTION(_4H,          "A4", 5)
CONNECTION(GND,          "A4", 13)
CONNECTION(GND,          "A4", 14)

CONNECTION("A4", 12,     "A3", 10)
CONNECTION("A4", 11,     "A3", 11)
CONNECTION("A4", 10,     "A3", 12)
CONNECTION("A4", 9,      "A3", 13)
CONNECTION(_16H,         "A3", 2)
CONNECTION(_8H,          "A3", 14)
CONNECTION("C6", 8,      "A3", 15)

CONNECTION("A3", 9,      "F1", 12)
// dup CONNECTION(_CLOCK,       "F1", 9)

CONNECTION(_32H,         "C3", 12)
CONNECTION("F1", 10,     "C3", 13)

CONNECTION("F1", 10,     "C3", 1)
CONNECTION(_128H,        "C3", 2)

CONNECTION(_128V,        "C5", 11)
CONNECTION(_64V,         "C5", 10)
CONNECTION(_32V,         "C5", 9)

CONNECTION(_16V,         "E4", 9)
CONNECTION(_GNEn,        "E4", 10)

CONNECTION(_64Hn,        "A1", 13)
CONNECTION(_128H,        "A1", 12)

CONNECTION(_128H,        "A1", 2)
CONNECTION(_32H,         "A1", 1)

CONNECTION("C5", 8,      "C6", 9)
CONNECTION("E4", 8,      "C6", 12)
CONNECTION("A1", 11,     "C6", 13)
CONNECTION("A1", 3,      "C6", 10)


/* ROM read - plane motion codes (page 1, bottom left) */

CONNECTION(_32H,         "J6", 1)
CONNECTION(_J1R4,        "J6", 2)
CONNECTION(_J2R4,        "J6", 3)
CONNECTION(_J1R3,        "J6", 5)
CONNECTION(_J2R3,        "J6", 6)
CONNECTION(_J1R2,        "J6", 14)
CONNECTION(_J2R2,        "J6", 13)
CONNECTION(_J1R1,        "J6", 11)
CONNECTION(_J2R1,        "J6", 10)
CONNECTION(GND,          "J6", 15)

CONNECTION(_R4,          "J5", 14)  //004253-02
CONNECTION(_R3,          "J5", 15)
CONNECTION(_R2,          "J5", 1)
CONNECTION(_R1,          "J5", 2)
CONNECTION(_R0,          "J5", 3)
CONNECTION(_L4,          "J5", 4)
CONNECTION(_L2,          "J5", 7)
CONNECTION(_L1,          "J5", 6)
CONNECTION(_16H,         "J5", 5)
CONNECTION(GND,          "J5", 13)

CONNECTION(_32H,         "K6", 1)
CONNECTION(_J1R0,        "K6", 2)
CONNECTION(_J2R0,        "K6", 3)
CONNECTION(_J1V4,        "K6", 5)
CONNECTION(_J2V4,        "K6", 6)
CONNECTION(_J1V2,        "K6", 14)
CONNECTION(_J2V2,        "K6", 13)
CONNECTION(_J1V1,        "K6", 11)
CONNECTION(_J2V1,        "K6", 10)
CONNECTION(GND,          "K6", 15)

CONNECTION(_R4,          "K5", 14)  //004253-01
CONNECTION(_R3,          "K5", 15)
CONNECTION(_R2,          "K5", 1)
CONNECTION(_R1,          "K5", 2)
CONNECTION(_R0,          "K5", 3)
CONNECTION(_L4,          "K5", 4)
CONNECTION(_L2,          "K5", 7)
CONNECTION(_L1,          "K5", 6)
CONNECTION(_16H,         "K5", 5)
CONNECTION(GND,          "K5", 13)


/* Load signal generator (page 1, lower right) */

CONNECTION(_256H,        "E1", 13)
CONNECTION(_64H,         "E1", 1)
CONNECTION(_32H,         "E1", 2)

CONNECTION("E1", 12,     "C3", 5)
CONNECTION(_HSYNCn,      "C3", 4)

//note a3 appears twice on page 1
CONNECTION(_64Hxnor128H, "A3", 1)  
CONNECTION(GND,          "A3", 6)
CONNECTION(GND,          "A3", 5)
CONNECTION(GND,          "A3", 4)
CONNECTION("C3", 6,      "A3", 3)
// dup CONNECTION(_16H,         "A3", 2)
// dup CONNECTION(_8H,          "A3", 14) 

CONNECTION("A3", 7,      "B1", 1)
CONNECTION("A3", 7,      "B1", 2)
CONNECTION(_4H,          "B1", 8)
CONNECTION(VCC,          "B1", 9)

CONNECTION(_J2HWINDO,    "D3", 5)
CONNECTION(_J1HWINDO,    "D3", 4)
// dup CONNECTION(_HSYNCn,      "D3", 9) 

CONNECTION(_256H,        "A1", 10)
CONNECTION("D3", 6,      "A1", 9)
 
CONNECTION(_256H,        "A1", 4)
CONNECTION("D3", 3,      "A1", 5)

CONNECTION("B1", 13,     "C1", 1)
CONNECTION("A1", 8,      "C1", 2)

CONNECTION("B1", 11,     "C1", 4)
CONNECTION("A1", 8,      "C1", 5)

CONNECTION("B1", 6,      "C1", 9)
CONNECTION("A1", 6,      "C1", 10)

CONNECTION("B1", 4,      "C1", 12)
CONNECTION("A1", 6,      "C1", 13)

 
/* video (page 1, middle center)*/

CONNECTION(_JET1n,       "F3", 1) 
CONNECTION(_SHELL1n,     "F3", 2) 
CONNECTION(_SCORE1n,     "F3", 13) 

CONNECTION(_JET2n,       "F3", 11) 
CONNECTION(_SHELL2n,     "F3", 9) 
CONNECTION(_SCORE2n,     "F3", 10) 

// note: not using C5 and the Power Reset circuitry

CONNECTION(VCC,          "D4", 2) 
CONNECTION("F3", 12,     "D4", 1) 

CONNECTION(VCC,          "E4", 4) 
CONNECTION("F3", 8,      "E4", 5) 

CONNECTION("VIDEO", 1,   "D4", 3) 
CONNECTION("VIDEO", 2,   "E4", 6)  

CONNECTION("VIDEO", Video::VBLANK_PIN, _VBLANK)
CONNECTION("VIDEO", Video::HBLANK_PIN, _HBLANK) 


/* Shell 1 ROM access (page 1, middle, center) */

CONNECTION(_VDATA1n,     "D1", 1)
CONNECTION(_LOAD0n,      "D1", 2)

CONNECTION(_EXPL1n,      "N3", 10)
CONNECTION(_HIT1n,       "N3", 9)

CONNECTION(_ROM0,        "L3", 4)
CONNECTION(_ROM1,        "L3", 6)
CONNECTION(_ROM2,        "L3", 8)
CONNECTION(_ROM3,        "L3", 10)
CONNECTION(_ROM4,        "L3", 16)
CONNECTION(_ROM5,        "L3", 18)
CONNECTION(_ROM6,        "L3", 20)
CONNECTION(_ROM7,        "L3", 22)
CONNECTION("D1", 3,      "L3", 14)
CONNECTION("D1", 3,      "L3", 2)
CONNECTION(_FIRE1,       "L3", 3)
CONNECTION(_FIRE1,       "L3", 15)
CONNECTION("N3", 8,      "L3", 1)
CONNECTION("N3", 8,      "L3", 13)


/* Jet 1 ROM access (page 1, bottom center) */

CONNECTION(_GO1n,        "D6", 5)
CONNECTION(_VDATA1n,     "D6", 6)

CONNECTION(VCC,          "N4", 4)
CONNECTION("N4", 8,      "N4", 2)
CONNECTION("D6", 4,      "N4", 3)
CONNECTION(VCC,          "N4", 1)

CONNECTION(VCC,          "N4", 10)
CONNECTION("N4", 5,      "N4", 12)
CONNECTION("D6", 4,      "N4", 11)
CONNECTION(VCC,          "N4", 13)

CONNECTION("N4", 6,      "M4", 14)
CONNECTION("N4", 9,      "M4", 2)
CONNECTION(_ROM4,        "M4", 10)
CONNECTION(_ROM5,        "M4", 11)
CONNECTION(_ROM6,        "M4", 12)
CONNECTION(_ROM7,        "M4", 13)
CONNECTION(_ROM0,        "M4", 6)
CONNECTION(_ROM1,        "M4", 5)
CONNECTION(_ROM2,        "M4", 4)
CONNECTION(_ROM3,        "M4", 3)
CONNECTION(_GO1n,        "M4", 1)
CONNECTION(_GO1n,        "M4", 15)

CONNECTION(_VDATA1n,     "D1", 4)
CONNECTION(_LOAD1n,      "D1", 5)

CONNECTION(_J1R4n,       "P8", 1)
CONNECTION("M4", 9,      "P8", 2)

CONNECTION("M4", 9,      "L8", 5)

CONNECTION("M4", 7,      "L8", 3)

CONNECTION(_J1R4,        "K7", 4)
CONNECTION(_J1R3,        "K7", 5)

CONNECTION("M4", 7,      "P8", 4)
CONNECTION("K7", 6,      "P8", 5)

CONNECTION("D1", 6,      "L8", 1)

CONNECTION(GND,          "N9", 2)
CONNECTION(GND,          "N9", 3)
CONNECTION("L8", 2,      "N9", 14)
CONNECTION("N9", 12,     "N9", 1)

CONNECTION("N9", 12,     "N8", 1)
CONNECTION("N9", 9,      "N8", 15)
CONNECTION("N9", 8,      "N8", 14)
CONNECTION("N9", 11,     "N8", 13)
CONNECTION("P8", 3,      "N8", 4)
CONNECTION("L8", 6,      "N8", 6)
CONNECTION("L8", 4,      "N8", 12)
CONNECTION("P8", 6,      "N8", 10)
CONNECTION("D1", 6,      "N8", 3)
CONNECTION(GND,          "N8", 2)


/* Shell 2 ROM access (page 1, middle, center) */

CONNECTION(_VDATA2n,     "D1", 10)
CONNECTION(_LOAD2n,      "D1", 9)

CONNECTION(_EXPL2n,      "H3", 5)
CONNECTION(_HIT2n,       "H3", 4)

CONNECTION(_ROM0,        "J3", 4)
CONNECTION(_ROM1,        "J3", 6)
CONNECTION(_ROM2,        "J3", 8)
CONNECTION(_ROM3,        "J3", 10)
CONNECTION(_ROM4,        "J3", 16)
CONNECTION(_ROM5,        "J3", 18)
CONNECTION(_ROM6,        "J3", 20)
CONNECTION(_ROM7,        "J3", 22)
CONNECTION("D1", 8,      "J3", 14)
CONNECTION("D1", 8,      "J3", 2)
CONNECTION(_FIRE2,       "J3", 3)
CONNECTION(_FIRE2,       "J3", 15)
CONNECTION("H3", 6,      "J3", 1)
CONNECTION("H3", 6,      "J3", 13)


/* Jet 2 ROM access (page 1, middle, right) */

CONNECTION(_GO2n,        "D6", 9)
CONNECTION(_VDATA2n,     "D6", 8)

CONNECTION(VCC,          "P4", 4)
CONNECTION("P4", 8,      "P4", 2)
CONNECTION("D6", 10,     "P4", 3)
CONNECTION(VCC,          "P4", 1)

CONNECTION(VCC,          "P4", 10)
CONNECTION("P4", 5,      "P4", 12)
CONNECTION("D6", 10,     "P4", 11)
CONNECTION(VCC,          "P4", 13)

CONNECTION("P4", 6,      "L4", 14)
CONNECTION("P4", 9,      "L4", 2)
CONNECTION(_ROM4,        "L4", 10)
CONNECTION(_ROM5,        "L4", 11)
CONNECTION(_ROM6,        "L4", 12)
CONNECTION(_ROM7,        "L4", 13)
CONNECTION(_ROM0,        "L4", 6)
CONNECTION(_ROM1,        "L4", 5)
CONNECTION(_ROM2,        "L4", 4)
CONNECTION(_ROM3,        "L4", 3)
CONNECTION(_GO2n,        "L4", 1)
CONNECTION(_GO2n,        "L4", 15)

CONNECTION(_VDATA2n,     "D1", 13)
CONNECTION(_LOAD3n,      "D1", 12)

CONNECTION(_J2R4n,       "P8", 12)
CONNECTION("L4", 9,      "P8", 13)

CONNECTION("L4", 9,      "L8", 9)

CONNECTION("L4", 7,      "L8", 11)

CONNECTION(_J2R4,        "K7", 10)
CONNECTION(_J2R3,        "K7", 9)

CONNECTION("L4", 7,      "P8", 9)
CONNECTION("K7", 8,      "P8", 10)

CONNECTION("D1", 11,     "L8", 13)

CONNECTION(GND,          "M9", 2)
CONNECTION(GND,          "M9", 3)
CONNECTION("L8", 12,     "M9", 14)
CONNECTION("M9", 12,     "M9", 1)

CONNECTION("M9", 12,     "M8", 1)
CONNECTION("M9", 9,      "M8", 15)
CONNECTION("M9", 8,      "M8", 14)
CONNECTION("M9", 11,     "M8", 13)
CONNECTION("P8", 11,     "M8", 4)
CONNECTION("L8", 8,      "M8", 6)
CONNECTION("L8", 10,     "M8", 12)
CONNECTION("P8", 8,      "M8", 10)
CONNECTION("D1", 11,     "M8", 3)
CONNECTION(GND,          "M8", 2)



/* * * * * * * page 2 * * * * * * */



/* Jet 1 (page 2, top, left)  */
 
CONNECTION(_J1C1,        "N7", 5)
CONNECTION(_VRESET,      "N7", 4)

CONNECTION(_VRESET,      "N7", 2)
CONNECTION(_J1C0,        "N7", 1)

CONNECTION("N7", 6,      "M7", 3)

CONNECTION(VCC,          "P7", 7)
CONNECTION(VCC,          "P7", 10)
CONNECTION(_HCLOCK,      "P7", 2)
CONNECTION("N7", 3,      "P7", 3)
CONNECTION("N7", 6,      "P7", 4)
CONNECTION("M7", 4,      "P7", 5)
CONNECTION(GND,          "P7", 6)
CONNECTION("L5", 8,      "P7", 9)
CONNECTION(_STARTn,      "P7", 1)

CONNECTION("P7", 15,     "P6", 7)
CONNECTION("P7", 11,     "P6", 10)
CONNECTION(_HCLOCK,      "P6", 2)
CONNECTION(GND,          "P6", 3)
CONNECTION(GND,          "P6", 4)
CONNECTION(VCC,          "P6", 5)
CONNECTION(VCC,          "P6", 6)
CONNECTION(_STARTn,      "P6", 9)
CONNECTION(VCC,          "P6", 1)

CONNECTION("P6", 15,     "L5", 10)
CONNECTION("P7", 15,     "L5", 9)

CONNECTION("P6", 15,     "D2", 5)
// dup CONNECTION(_12MHZ,       "D2", 9)  

CONNECTION(_J1C3,        "M7", 1)

CONNECTION(_VBLANKn,     "N6", 7)
CONNECTION(_VBLANKn,     "N6", 10)
CONNECTION(_VCLOCK,      "N6", 2)
CONNECTION(_J1C2,        "N6", 3)
CONNECTION(_J1C3,        "N6", 4)
CONNECTION("M7", 2,      "N6", 5)
CONNECTION(GND,          "N6", 6)
CONNECTION("L5", 6,      "N6", 9)
CONNECTION(VCC,          "N6", 1)

CONNECTION("N6", 15,     "N5", 7)
CONNECTION("N6", 11,     "N5", 10)
CONNECTION(_VCLOCK,      "N5", 2)
CONNECTION(GND,          "N5", 3)
CONNECTION(GND,          "N5", 4)
CONNECTION(GND,          "N5", 5)
CONNECTION(GND,          "N5", 6)
CONNECTION(VCC,          "N5", 9)
CONNECTION(VCC,          "N5", 1)

CONNECTION("N5", 15,     "L5", 4)
CONNECTION("N6", 15,     "L5", 5)

CONNECTION(VCC,          "R4", 10)
CONNECTION(_VDATA1n,     "R4", 12)
CONNECTION(_LOAD0n,      "R4", 11)
CONNECTION("N5", 15,     "R4", 13)

CONNECTION(_HBLANKn,     "D4", 4)
CONNECTION(_J1HWINDO,    "D4", 5)

CONNECTION(_ROM0,        "F4", 11)
CONNECTION(_ROM1,        "F4", 12)
CONNECTION(_ROM2,        "F4", 13)
CONNECTION(_ROM3,        "F4", 14)
CONNECTION(_ROM4,        "F4", 3)
CONNECTION(_ROM5,        "F4", 4)
CONNECTION(_ROM6,        "F4", 5)
CONNECTION(_ROM7,        "F4", 6)
CONNECTION(GND,          "F4", 10)
CONNECTION(_LOAD1n,      "F4", 1)
CONNECTION(_12MHZ,       "F4", 2)
CONNECTION("D4", 6,      "F4", 15)

CONNECTION(_ROM0,        "H4", 11)
CONNECTION(_ROM1,        "H4", 12)
CONNECTION(_ROM2,        "H4", 13)
CONNECTION(_ROM3,        "H4", 14)
CONNECTION(_ROM4,        "H4", 3)
CONNECTION(_ROM5,        "H4", 4)
CONNECTION(_ROM6,        "H4", 5)
CONNECTION(_ROM7,        "H4", 6)
CONNECTION("F4", 9,      "H4", 10)
CONNECTION(_LOAD0n,      "H4", 1)
CONNECTION(_12MHZ,       "H4", 2)
CONNECTION("D4", 6,      "H4", 15)

CONNECTION(_BLOUP1n,     "K8", 10)
CONNECTION(_3F,          "K8", 9)

CONNECTION("H4", 7,      "K7", 12)
CONNECTION("K8", 8,      "K7", 13)

CONNECTION("K7", 11,     "E2", 2)
CONNECTION("R4", 9,      "E2", 1)
CONNECTION(_HBLANKn,     "E2", 4)
CONNECTION(_J1HWINDO,    "E2", 5)

CONNECTION(_JET1n,       "C2", 5)


/* Score 1 (page 2, middle, left) */

CONNECTION(_START,       "A6", 2)
CONNECTION(_START,       "A6", 3)
CONNECTION(_HIT1,        "A6", 14)
CONNECTION(_J1S1,        "A6", 1)


/* Blow up 1 (page 2, bottom, left) */

CONNECTION(_SHELL2,     "E1", 10)
CONNECTION(_JET1,       "E1", 9)
CONNECTION(_BLOUP1n,    "E1", 11)

CONNECTION(VCC,         "E7", 10)
CONNECTION(VCC,         "E7", 12)
CONNECTION(_3F,         "E7", 11)
CONNECTION("E1", 8,     "E7", 13)

CONNECTION(_HIT2n,      "E8", 10)
CONNECTION(_FIRE2,      "E8", 11)
CONNECTION(_FIRE2,      "E8", 12)  //not shown ?

/* Fire 1 (page 2, bottom, left) */

CONNECTION(_ATTRACTn,   "E5", 2)
CONNECTION(_FIRE1n,     "E5", 1)
CONNECTION(_FIRECOM1,   "E5", 13)

CONNECTION("E5", 12,    "E4", 13)
CONNECTION(_HIT1n,      "E4", 12)

CONNECTION(_FIRE1,      "E6", 7)
CONNECTION(VCC,         "E6", 10)
CONNECTION(_3F,         "E6", 2)
CONNECTION(GND,         "E6", 3)
CONNECTION(GND,         "E6", 4)
CONNECTION(GND,         "E6", 5)
CONNECTION(_HIT1,       "E6", 6)
CONNECTION("E4", 11,    "E6", 9)
CONNECTION(VCC,         "E6", 1)

CONNECTION(_FIRE1n,     "C7", 5)

CONNECTION(_FIRE1,      "D8", 12)
CONNECTION("E6", 11,    "D8", 13)

CONNECTION("E6", 12,    "D6", 2)
CONNECTION("E6", 13,    "D6", 3)


/* Shell 1 (page 2, top, right) */

CONNECTION(_VRESET,     "N3", 12)
CONNECTION(_S1C3,       "N3", 13)

CONNECTION(_VRESET,     "L1", 12)
CONNECTION(_S1C2,       "L1", 13)

CONNECTION(_VRESET,     "N3", 2)
CONNECTION(_S1C1,       "N3", 1)

CONNECTION(_VRESET,     "N3", 4)
CONNECTION(_S1C0,       "N3", 5)

CONNECTION("N3", 6,     "N2", 3)
CONNECTION("N3", 3,     "N2", 4)
CONNECTION("L1", 11,    "N2", 5)
CONNECTION("N3", 11,    "N2", 6)
CONNECTION("L1", 6,     "N2", 9)
CONNECTION(VCC,         "N2", 7)
CONNECTION(VCC,         "N2", 10)
CONNECTION(_HCLOCK,     "N2", 2)
CONNECTION("P1", 5,     "N2", 1)

CONNECTION(GND,         "P2", 3)
CONNECTION(GND,         "P2", 4)
CONNECTION(GND,         "P2", 5)
CONNECTION(GND,         "P2", 6)
CONNECTION(VCC,         "P2", 9)
CONNECTION("N2", 15,    "P2", 7)
CONNECTION("N2", 11,    "P2", 10)
CONNECTION(_HCLOCK,     "P2", 2)
CONNECTION("P1", 5,     "P2", 1)

CONNECTION("P2", 15,    "L1", 4)
CONNECTION("N2", 15,    "L1", 5)

CONNECTION("P2", 15,    "R2", 2)
CONNECTION(_FIRE1,      "R2", 13)
CONNECTION("L2", 15,    "R2", 1)

CONNECTION(_S1V1,       "M1", 10)
CONNECTION(_S1V2,       "M1", 11)
CONNECTION(_S1V4,       "M1", 12)
CONNECTION(_3F,         "M1", 13)
CONNECTION(_EXPL1n,     "M1", 14)
// nn CONNECTION(GND,         "M1", 15)

CONNECTION("M1", 1,     "N1", 1)
CONNECTION("M1", 2,     "N1", 2)
CONNECTION("M1", 3,     "N1", 3)
CONNECTION("M1", 4,     "N1", 4)
CONNECTION("M1", 5,     "N1", 5)
CONNECTION("M1", 6,     "N1", 6)
CONNECTION("M1", 7,     "N1", 7)
CONNECTION("M1", 9,     "N1", 9)
CONNECTION("R2", 12,    "N1", 10)
CONNECTION(_S1H4,       "N1", 13)
CONNECTION(_S1H2,       "N1", 12)
CONNECTION(_S1H1,       "N1", 11)

CONNECTION("N1", 14,    "F1", 4)
// dup CONNECTION(_CLOCK,      "F1", 9)  

CONNECTION(_S1C6,       "R1", 9)

CONNECTION("L2", 15,    "L1", 2)
CONNECTION("M2", 15,    "L1", 1)

CONNECTION(_S1C4,       "M2", 3)
CONNECTION(_S1C5,       "M2", 4)
CONNECTION("R1", 8,     "M2", 5)
CONNECTION(_S1C7,       "M2", 6)
CONNECTION("L1", 3,     "M2", 9)
CONNECTION(VCC,         "M2", 7)
CONNECTION(VCC,         "M2", 10)
CONNECTION(_VCLOCK,     "M2", 2)
CONNECTION("P1", 5,     "M2", 1)

CONNECTION(GND,         "L2", 3)
CONNECTION(GND,         "L2", 4)
CONNECTION(GND,         "L2", 5)
CONNECTION(GND,         "L2", 6)
CONNECTION(VCC,         "L2", 9)
CONNECTION("M2", 15,    "L2", 7)
CONNECTION("M2", 11,    "L2", 10)
CONNECTION(_VCLOCK,     "L2", 2)
CONNECTION("P1", 5,     "L2", 1)

CONNECTION(_JET1,       "R2", 5)
CONNECTION(_J1H4,       "R2", 4)
CONNECTION(_J1V4,       "R2", 3)

CONNECTION("R2", 6,     "R1", 13)

CONNECTION(VCC,         "P1", 4)
CONNECTION(VCC,         "P1", 2)
CONNECTION("R1", 12,    "P1", 3)
CONNECTION(_FIRE1,      "P1", 1)


/* Jet 2 (page 2, left, bottom) */
 
CONNECTION(_J2C1,        "N7", 9)
CONNECTION(_VRESET,      "N7", 10)

CONNECTION(_VRESET,      "N7", 12)
CONNECTION(_J2C0,        "N7", 13)

CONNECTION("N7", 8,      "M7", 5)

CONNECTION(VCC,          "L7", 7)
CONNECTION(VCC,          "L7", 10)
CONNECTION(_HCLOCK,      "L7", 2)
CONNECTION("N7", 11,     "L7", 3)
CONNECTION("N7", 8,      "L7", 4)
CONNECTION("M7", 6,      "L7", 5)
CONNECTION(GND,          "L7", 6)
CONNECTION("L5", 11,     "L7", 9)
CONNECTION(_STARTn,      "L7", 1)

CONNECTION("L7", 15,     "L6", 7)
CONNECTION("L7", 11,     "L6", 10)
CONNECTION(_HCLOCK,      "L6", 2)
CONNECTION(GND,          "L6", 3)
CONNECTION(GND,          "L6", 4)
CONNECTION(VCC,          "L6", 5)
CONNECTION(GND,          "L6", 6)
CONNECTION(_STARTn,      "L6", 9)
CONNECTION(VCC,          "L6", 1)

CONNECTION("L6", 15,     "L5", 12)
CONNECTION("L7", 15,     "L5", 13)

CONNECTION("L6", 15,     "D2", 4)
// dup CONNECTION(_12MHZ,       "D2", 9)

CONNECTION(_J2C3,        "M7", 9)

CONNECTION(_VBLANKn,     "M6", 7)
CONNECTION(_VBLANKn,     "M6", 10)
CONNECTION(_VCLOCK,      "M6", 2)  //?VCLOCKn on diagram
CONNECTION(_J2C2,        "M6", 3)
CONNECTION(_J2C3,        "M6", 4)
CONNECTION("M7", 8,      "M6", 5)
CONNECTION(GND,          "M6", 6)
CONNECTION("L5", 3,      "M6", 9)
CONNECTION(VCC,          "M6", 1)

CONNECTION("M6", 15,     "M5", 7)
CONNECTION("M6", 11,     "M5", 10)
CONNECTION(_VCLOCK,      "M5", 2)  //?VCLOCKn on diagram
CONNECTION(GND,          "M5", 3)
CONNECTION(GND,          "M5", 4)
CONNECTION(GND,          "M5", 5)
CONNECTION(GND,          "M5", 6)
CONNECTION(VCC,          "M5", 9)
CONNECTION(VCC,          "M5", 1)

CONNECTION("M5", 15,     "L5", 1)
CONNECTION("M6", 15,     "L5", 2)

CONNECTION(VCC,          "R4", 4)
CONNECTION(_VDATA2n,     "R4", 2)
CONNECTION(_LOAD2n,      "R4", 3)
CONNECTION("M5", 15,     "R4", 1)

CONNECTION(_HBLANKn,     "L1", 9)
CONNECTION(_J2HWINDO,    "L1", 10)

CONNECTION(_ROM0,        "J4", 11)
CONNECTION(_ROM1,        "J4", 12)
CONNECTION(_ROM2,        "J4", 13)
CONNECTION(_ROM3,        "J4", 14)
CONNECTION(_ROM4,        "J4", 3)
CONNECTION(_ROM5,        "J4", 4)
CONNECTION(_ROM6,        "J4", 5)
CONNECTION(_ROM7,        "J4", 6)
CONNECTION(GND,          "J4", 10)
CONNECTION(_LOAD3n,      "J4", 1)
CONNECTION(_12MHZ,       "J4", 2)
CONNECTION("L1", 8,      "J4", 15)

CONNECTION(_ROM0,        "K4", 11)
CONNECTION(_ROM1,        "K4", 12)
CONNECTION(_ROM2,        "K4", 13)
CONNECTION(_ROM3,        "K4", 14)
CONNECTION(_ROM4,        "K4", 3)
CONNECTION(_ROM5,        "K4", 4)
CONNECTION(_ROM6,        "K4", 5)
CONNECTION(_ROM7,        "K4", 6)
CONNECTION("J4", 9,      "K4", 10)
CONNECTION(_LOAD2n,      "K4", 1)
CONNECTION(_12MHZ,       "K4", 2)
CONNECTION("L1", 8,      "K4", 15)

CONNECTION(_BLOUP2n,     "K8", 4)
CONNECTION(_3F,          "K8", 5)

CONNECTION("K4", 7,      "K7", 1)
CONNECTION("K8", 6,      "K7", 2)

CONNECTION("K7", 3,      "E2", 9)
CONNECTION("R4", 5,      "E2", 13)
CONNECTION(_HBLANKn,     "E2", 10)
CONNECTION(_J2HWINDO,    "E2", 12)

CONNECTION(_JET2n,       "C2", 9)


/* Score 2 (page 2, middle, left) */

CONNECTION(_START,       "B5", 2)
CONNECTION(_START,       "B5", 3)
CONNECTION(_HIT2,        "B5", 14)
CONNECTION(_J2S1,        "B5", 1)


/* Blo up 2 (page 1, bottom, left) */

CONNECTION(_SHELL1,     "E1", 4)
CONNECTION(_JET2,       "E1", 5)
CONNECTION(_BLOUP2n,    "E1", 3)

CONNECTION(VCC,         "E7", 4)
CONNECTION(VCC,         "E7", 2)
CONNECTION(_3F,         "E7", 3)
CONNECTION("E1", 6,     "E7", 1)

CONNECTION(_HIT1n,      "E8", 5)
CONNECTION(_FIRE1,      "E8", 6)


/* fire 2 (page 2, bottom, center) */

CONNECTION(_ATTRACTn,   "E5", 3)
CONNECTION(_FIRE2n,     "E5", 5)
CONNECTION(_FIRECOM2,   "E5", 4)

CONNECTION("E5", 6,     "E4", 1)
CONNECTION(_HIT2n,      "E4", 2)

CONNECTION(_FIRE2,      "D7", 7)
CONNECTION(VCC,         "D7", 10)
CONNECTION(_3F,         "D7", 2)
CONNECTION(GND,         "D7", 3)
CONNECTION(GND,         "D7", 4)
CONNECTION(GND,         "D7", 5)
CONNECTION(_HIT2,       "D7", 6)
CONNECTION("E4", 3,     "D7", 9)
CONNECTION(VCC,         "D7", 1)

CONNECTION(_FIRE2n,     "C7", 11)

CONNECTION(_FIRE2,      "D8", 10)
CONNECTION("D7", 11,    "D8", 9)

CONNECTION("D7", 12,    "D6", 12)
CONNECTION("D7", 13,    "D6", 11)


/* Shell 2 (page 2, bottom, right) */

CONNECTION(_VRESET,     "H3", 9)
CONNECTION(_S2C3,       "H3", 10)

CONNECTION(_VRESET,     "K1", 10)
CONNECTION(_S2C2,       "K1", 9)

CONNECTION(_VRESET,     "H3", 13)
CONNECTION(_S2C1,       "H3", 12)

CONNECTION(_VRESET,     "H3", 1)
CONNECTION(_S2C0,       "H3", 2)

CONNECTION("H3", 3,     "H2", 3)
CONNECTION("H3", 11,    "H2", 4)
CONNECTION("K1", 8,     "H2", 5)
CONNECTION("H3", 8,     "H2", 6)
CONNECTION("K1", 6,     "H2", 9)
CONNECTION(VCC,         "H2", 7)
CONNECTION(VCC,         "H2", 10)
CONNECTION(_HCLOCK,     "H2", 2)  //wrong on diagram
CONNECTION("P1", 9,     "H2", 1)

CONNECTION(GND,         "F2", 3)
CONNECTION(GND,         "F2", 4)
CONNECTION(GND,         "F2", 5)
CONNECTION(GND,         "F2", 6)
CONNECTION(VCC,         "F2", 9)
CONNECTION("H2", 15,    "F2", 7)
CONNECTION("H2", 11,    "F2", 10)
CONNECTION(_HCLOCK,     "F2", 2) //wrong on diagram
CONNECTION("P1", 9,     "F2", 1)

CONNECTION("F2", 15,    "K1", 4)
CONNECTION("H2", 15,    "K1", 5)

CONNECTION("F2", 15,    "F3", 5)
CONNECTION(_FIRE2,      "F3", 3)
CONNECTION("K2", 15,    "F3", 4)

CONNECTION(_S2V1,       "J1", 10)
CONNECTION(_S2V2,       "J1", 11)
CONNECTION(_S2V4,       "J1", 12)
CONNECTION(_3F,         "J1", 13)
CONNECTION(_EXPL2n,     "J1", 14)
// nn CONNECTION(GND,         "J1", 15)

CONNECTION("J1", 1,     "H1", 1)
CONNECTION("J1", 2,     "H1", 2)
CONNECTION("J1", 3,     "H1", 3)
CONNECTION("J1", 4,     "H1", 4)
CONNECTION("J1", 5,     "H1", 5)
CONNECTION("J1", 6,     "H1", 6)
CONNECTION("J1", 7,     "H1", 7)
CONNECTION("J1", 9,     "H1", 9)
CONNECTION("F3", 6,     "H1", 10)
CONNECTION(_S2H4,       "H1", 13)
CONNECTION(_S2H2,       "H1", 12)
CONNECTION(_S2H1,       "H1", 11)

CONNECTION("H1", 14,    "F1", 5)
// dup CONNECTION(_CLOCK,      "F1", 9)

CONNECTION(_S2C6,       "C2", 1)

CONNECTION("K2", 15,    "K1", 13)
CONNECTION("J2", 15,    "K1", 12)

CONNECTION(_S2C4,       "J2", 3)
CONNECTION(_S2C5,       "J2", 4)
CONNECTION("C2", 2,     "J2", 5)
CONNECTION(_S2C7,       "J2", 6)
CONNECTION("K1", 11,    "J2", 9)
CONNECTION(VCC,         "J2", 7)
CONNECTION(VCC,         "J2", 10)
CONNECTION(_VCLOCK,     "J2", 2)
CONNECTION("P1", 9,     "J2", 1)

CONNECTION(GND,         "K2", 3)
CONNECTION(GND,         "K2", 4)
CONNECTION(GND,         "K2", 5)
CONNECTION(GND,         "K2", 6)
CONNECTION(VCC,         "K2", 9)
CONNECTION("J2", 15,    "K2", 7)
CONNECTION("J2", 11,    "K2", 10)
CONNECTION(_VCLOCK,     "K2", 2)
CONNECTION("P1", 9,     "K2", 1)

CONNECTION(_JET2,       "R2", 9)
CONNECTION(_J2H4,       "R2", 10)
CONNECTION(_J2V4,       "R2", 11)

CONNECTION("R2", 8,     "R1", 11)

CONNECTION(VCC,         "P1", 10)
CONNECTION(VCC,         "P1", 12)
CONNECTION("R1", 10,    "P1", 11)
CONNECTION(_FIRE2,      "P1", 13)


/* * * * * * * page 3 * * * * * * */


/* input (page 3, top, left) */


/* joysticks pressed=LO and unpressed=HI */

CONNECTION("JOYSTICK1", Joystick::LEFT,    "J9", 11)
CONNECTION("JOYSTICK1", Joystick::RIGHT,   "J9", 13)  
//CONNECTION("JOYSTICK1", Joystick::UP,  //fast
CONNECTION("JOYSTICK1", Joystick::DOWN,    "J9", 1)  //slow

CONNECTION("JOYSTICK2", Joystick::LEFT,    "H9", 11)
CONNECTION("JOYSTICK2", Joystick::RIGHT,   "H9", 13)  
//CONNECTION("JOYSTICK2", Joystick::UP,  //fast
CONNECTION("JOYSTICK2", Joystick::DOWN,    "H9", 1)  //slow

CONNECTION("BUTTONS1", 1,  "J9", 3)

CONNECTION("BUTTONS2", 1,  "H9", 3)


/* coin (page 3, middle, left) */

CONNECTION("COIN_IN", i1,  "F8", 3)

CONNECTION(VCC,            "P9", 10)
CONNECTION("COIN_IN", i1,  "P9", 12)
CONNECTION(_128V,          "P9", 11)
CONNECTION("COIN_IN", i1,  "P9", 13)

CONNECTION(VCC,            "P9", 4)
CONNECTION("P9", 9,        "P9", 2)
CONNECTION(_128V,          "P9", 3)
CONNECTION("COIN_IN", i1,  "P9", 1)

// skipping coin 2 circuit
//CONNECTION(GND,            "F8", 11)

//CONNECTION(VCC,            "R9", 10)
//CONNECTION(GND,            "R9", 12)
//CONNECTION(_256V,          "R9", 11)
//CONNECTION(GND,            "R9", 13)

//CONNECTION(VCC,            "R9", 4)
//CONNECTION("R9", 9,        "R9", 2)
//CONNECTION(_256V,          "R9", 3)
//CONNECTION(GND,            "R9", 1)

CONNECTION("P9", 5,        "D4", 12)
CONNECTION("R9", 5,        "D4", 13)

CONNECTION(GND,            "DSW1", 1)  // 25 cents for 2 player
CONNECTION("D4", 11,       "DSW1", 2)  // 50 cents for 2 player

CONNECTION("P9", 5,        "C5", 4)
//CONNECTION("R9", 5,        "C5", 3)
CONNECTION(GND,            "C5", 3)
CONNECTION(GND,            "C5", 5)

CONNECTION(_COINn,         "C7", 1)

CONNECTION("DSW1", 3,      "C8", 4)
//CONNECTION(VCC,  "C8", 4)  //test
CONNECTION(_Q,             "C8", 2)
CONNECTION(_COIN,          "C8", 3)
CONNECTION(VCC,            "C8", 1)

CONNECTION("DSW1", 3,      "D8", 4)
CONNECTION("C8", 5,        "D8", 5)


/* start (page 3, bottom, left) */

CONNECTION("START_IN", i1, "D9", 1)
CONNECTION(_1CREDIT,     "D9", 5)
CONNECTION(_Q,           "D9", 2)
CONNECTION(_ATTRACT,     "D9", 4)

CONNECTION(_ATTRACT,     "D9", 10)
CONNECTION("START_IN", i2, "D9", 13)
CONNECTION(_Q,           "D9", 12)
CONNECTION(_2CREDIT,     "D9", 9)

CONNECTION("D9", 6,      "D8", 2)
CONNECTION("D9", 8,      "D8", 1)

CONNECTION("D8", 3,      "D3", 13)
// dup CONNECTION(_HSYNCn,      "D3", 9) 

CONNECTION(_Q,           "E8", 15)
CONNECTION("D9", 8,      "E8", 14)

//latch in/out is active low
CONNECTION(_ENDGAMEn,    "LATCH", 1)  //latch in:set
CONNECTION(_COINn,       "LATCH", 2)  //latch in:reset
CONNECTION("LATCH", 3,   "F8", 5)     //latch out

CONNECTION(_Q,           "F8", 9)


/* game timer (page 3, bottom, right) */

CONNECTION(_ATTRACTn,    "K9", 4)

CONNECTION("K9", 3,      "J9", 5)

CONNECTION("J9", 6,      "D5", 14)
CONNECTION(_START,       "D5", 2)
CONNECTION(_START,       "D5", 3)
CONNECTION(_Qn,          "D5", 6)
CONNECTION(_Qn,          "D5", 7)
CONNECTION("D5", 12,     "D5", 1)

CONNECTION("D5", 11,     "C7", 9)

CONNECTION("D5", 8,      "E5", 9)
CONNECTION("D5", 9,      "E5", 10)
CONNECTION(_6F,          "E5", 11)

CONNECTION("D5", 12,     "C7", 13)

CONNECTION("C7", 12,     "D4", 9)
CONNECTION(_ATTRACT,     "D4", 10)

CONNECTION("D4", 8,      "E8", 1)
CONNECTION(_CP1n,         "E8", 2)
CONNECTION(_CP2n,         "E8", 3)


/* controls for jet 1 (person or compuer) (page 3, top left) */

CONNECTION(_SLOW1STAR,   "J8", 5)
CONNECTION(_SPFIRECOM1,  "J8", 6)
CONNECTION(_LEFT1STAR,   "J8", 11)
CONNECTION(_SPLEFT1,     "J8", 10)
CONNECTION(_RIGHT1STAR,  "J8", 14)
CONNECTION(_SPRIGHT1,    "J8", 13)
CONNECTION(_FIRECOM1STAR, "J8", 2)
CONNECTION(_SPFIRECOM1,  "J8", 3)
CONNECTION(_1PLAY,       "J8", 1)
CONNECTION(GND,          "J8", 15)


/* plane "GO" signals (page3, middle, left) */

CONNECTION(_ATTRACT,     "H8", 1)
CONNECTION(_ATTRACT,     "H8", 15)
CONNECTION(_SLOW1,       "H8", 6)
CONNECTION(GND,          "H8", 5)
CONNECTION(_FAST1n,      "H8", 4)
CONNECTION(GND,          "H8", 3)
CONNECTION(_SLOW2,       "H8", 10)
CONNECTION(GND,          "H8", 11)
CONNECTION(_FAST2n,      "H8", 12)
CONNECTION(GND,          "H8", 13)
CONNECTION(_1F,          "H8", 14)
CONNECTION(_2F,          "H8", 2)


/* game logic for single player game */

CONNECTION(_J1V128,      "P5", 5)
CONNECTION(_J1V64,       "P5", 4)
CONNECTION(_J1H128,      "P5", 13)
CONNECTION(_J1H64,       "P5", 12)
CONNECTION(_JET2n,       "P5", 9)
CONNECTION(VCC,          "P5", 1)

CONNECTION("P5", 7,      "R5", 14)
CONNECTION("P5", 2,      "R5", 13)
CONNECTION("P5", 15,     "R5", 12)
CONNECTION("P5", 10,     "R5", 11)
CONNECTION(_J1R4,        "R5", 10)
// nn CONNECTION(GND,          "R5", 15)

CONNECTION(GND,          "R6", 1)
CONNECTION(GND,          "R6", 15)
CONNECTION("R5", 1,      "R6", 6)
CONNECTION("R5", 2,      "R6", 5)
CONNECTION("R5", 3,      "R6", 4)
CONNECTION("R5", 4,      "R6", 3)
CONNECTION("R5", 5,      "R6", 10)
CONNECTION("R5", 6,      "R6", 11)
CONNECTION("R5", 7,      "R6", 12)
CONNECTION("R5", 9,      "R6", 13)
CONNECTION(_J1R2,        "R6", 14)
CONNECTION(_J1R3,        "R6", 2)

CONNECTION("R6", 7,      "M7", 13)

CONNECTION("R6", 9,      "M7", 11)

CONNECTION("R6", 9,      "R7", 11)
CONNECTION("M7", 12,     "R7", 12)

CONNECTION("R6", 9,      "R7", 5)
CONNECTION("R6", 7,      "R7", 6)

CONNECTION("M7", 10,     "R7", 9)
CONNECTION("R6", 7,      "R7", 8)


/* jet rotation logic (page 3, top, center) */

CONNECTION(_1F,          "C6", 5)
CONNECTION(_3F,          "C6", 4)
CONNECTION(_NP,          "C6", 1)
CONNECTION(_ATTRACTn,    "C6", 2)

CONNECTION("C6", 6,      "C7", 3)

/* Jet 1 rotate (page 3, top, center) */

CONNECTION(_BLOUP1n,     "K8", 12)
CONNECTION(_1F,          "K8", 13)

CONNECTION("C7", 4,      "F7", 12)
CONNECTION(_RIGHT1,      "F7", 13)

CONNECTION("C7", 4,      "F7", 10)
CONNECTION(_LEFT1,       "F7", 9)

CONNECTION("K8", 11,     "H7", 4)
CONNECTION("F7", 11,     "H7", 5)

CONNECTION(VCC,          "H6", 11)
CONNECTION(_START,       "H6", 14)
CONNECTION("H7", 6,      "H6", 5)
CONNECTION("F7", 8,      "H6", 4)
CONNECTION(GND,          "H6", 1)  //not shown
CONNECTION(GND,          "H6", 9)  //not shown
CONNECTION(GND,          "H6", 10)  //not shown
CONNECTION(GND,          "H6", 15)  //not shown

CONNECTION("H6", 13,     "H7", 9)
CONNECTION("H6", 12,     "H7", 10)
 
CONNECTION(VCC,          "F6", 4)
CONNECTION("F6", 6,      "F6", 2)
CONNECTION("H7", 8,      "F6", 3)
CONNECTION(_STARTn,      "F6", 1)

/* jet 2 rotation (page 3, top, center) */

CONNECTION(_BLOUP2n,     "K8", 2)
CONNECTION(_1F,          "K8", 1)

CONNECTION("C7", 4,      "F7", 2)
CONNECTION(_RIGHT2,      "F7", 1)

CONNECTION("C7", 4,      "F7", 4)
CONNECTION(_LEFT2,       "F7", 5)

CONNECTION("K8", 3,      "H7", 1)
CONNECTION("F7", 3,      "H7", 2)

CONNECTION(VCC,          "J7", 11)
CONNECTION(_START,       "J7", 14)
CONNECTION("H7", 3,      "J7", 5)
CONNECTION("F7", 6,      "J7", 4)
CONNECTION(GND,          "J7", 15) //not shown
CONNECTION(GND,          "J7", 1)  //not shown
CONNECTION(GND,          "J7", 10) //not shown
CONNECTION(GND,          "J7", 9)  //not shown

CONNECTION("J7", 13,     "H7", 13)
CONNECTION("J7", 12,     "H7", 12)
 
CONNECTION(VCC,          "F6", 10)
CONNECTION(_J2R4n,       "F6", 12)
CONNECTION("H7", 11,     "F6", 11)
CONNECTION(_STARTn,      "F6", 13)

/* not implemented: pwr reset circuit, lamps, coin counter, coin2, sound circuits */

#ifdef DEBUG

//CONNECTION(_FIRECOM2, "LOG1", 1)
//CONNECTION(_FIRE2, "LOG1", 2)
//CONNECTION(_EXPL2n, "LOG1", 3)
//CONNECTION(_HIT2n, "LOG1", 4)
//CONNECTION(_EXPL1n, "LOG1", 5)
//CONNECTION(_HIT1n, "LOG1", 6)

//CONNECTION(_S2C1, "LOG1", 5) no signal?
//CONNECTION(_S2C0, "LOG1", 6)

//CONNECTION("F3", 6, "LOG1", 4)
//CONNECTION(_J2R0, "LOG1", 6)
//CONNECTION(_J2R1, "LOG1", 7)
//CONNECTION(_J2R2, "LOG1", 8)
//CONNECTION(_J2R3, "LOG1", 9)

//CONNECTION(_START, "LOG1", 7)

//CONNECTION(_HSYNC, "LOG1", 8)


#endif


CIRCUIT_LAYOUT_END

