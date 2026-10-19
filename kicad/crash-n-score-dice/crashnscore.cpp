/* Crash-N-Score by Atari 1975 */

//Last Update 10/04/2013

//todo: page1, barrier select switch - temp using p1 button 2
//todo: improve sound

#include "../circuit_desc.h"
#include "../circuit.h"


#define DEBUG
#undef DEBUG

#ifdef DEBUG
static VcdLogDesc vcd_log_desc
(
    "output_crashnscore.vcd",
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


static RomDesc d2_desc("crashnscore", "cns.d2", 0x683B203B);    
static RomDesc e2_desc("crashnscore", "cns.e2", 0x478AFAC2);
static RomDesc f6_desc("crashnscore", "cns.f6", 0xB3443354);  
static RomDesc f7_desc("crashnscore", "cns.f7", 0x01DCA5B9);   
static RomDesc p6_desc("crashnscore", "cns.p6", 0xB3443354);
static RomDesc p7_desc("crashnscore", "cns.p7", 0x01DCA5B9);  

static Astable555Desc d10_555_desc(K_OHM(250.0), K_OHM(10.0), U_FARAD(0.01));
//static Astable555Desc m10_555_desc(K_OHM(150.0), K_OHM(10.0), U_FARAD(1.0));
static Astable555Desc r10_555_desc(K_OHM(510.0), K_OHM(470.0), U_FARAD(10.0));

static Mono555Desc c1_555_desc(K_OHM(330), U_FARAD(0.1));   // R130, C70
static Mono555Desc b7_555_desc(K_OHM(39.0), U_FARAD(5.0));  //R108, C59	
static Mono555Desc k7_555_desc(K_OHM(39.0), U_FARAD(5.0));  //R50, C18	

static PotentimeterAstable555Desc pot1_desc("playtime", "Play Time", K_OHM(510.0), K_OHM(10.0), K_OHM(1010.0), r10_555_desc);

//static DipswitchDesc sw1_desc("barrier", "dice_dipswitch_1", "Barrier Select", 1, "Barriers Disabled", "Barriers Enabled");
static DipswitchDesc sw2play_desc("coinage", "dice_dipswitch_2", "Coinage", 0, "1 Coin / 1 Credit", "1 Coin / 2 Credits");
static Dipswitch4SP4TDesc sw2_desc("bonus_credit", "dice_dipswitch16_1", "Bonus Credit", 6, "None", 
                                   "10", "20", "30", "40", "50", "60", "70", "80", "90");

static Wheel1Desc wheel1_desc;
static Wheel2Desc wheel2_desc;

static Mono9602Desc h4_desc(K_OHM(27.0), U_FARAD(100.0), K_OHM(27.0), U_FARAD(100.0));
static Mono9602Desc r1_desc(K_OHM(33.0), U_FARAD(100.0), K_OHM(33.0), U_FARAD(100.0));

static CapacitorDesc cap2_desc(P_FARAD(100));
static CapacitorDesc cap6_desc(P_FARAD(390));
static CapacitorDesc cap17_desc(P_FARAD(100));
static CapacitorDesc cap40_desc(P_FARAD(100));
static CapacitorDesc cap46_desc(P_FARAD(390));
static CapacitorDesc cap58_desc(P_FARAD(100));
static CapacitorDesc cap70_desc(P_FARAD(100));

static MixerDesc mixer_desc({K_OHM(56.0), K_OHM(100.0), K_OHM(200.0) /*Fake*/, K_OHM(200.0)}, 0, 0, U_FARAD(0.1)); // TODO: Add op-amps and everything else

static CHIP_DESC( CRASHNSCORE_SPEED_CONTROL ) = 
{
    // Adjusts D10 frequency based on state of speed inputs
    // TODO: Improve accuracy    
    CUSTOM_CHIP_START([](Chip* chip, int mask)
    {
        chip->inputs  ^= mask;
        double val = (chip->inputs+2) / 32.0;

        d10_555_desc.r1 = K_OHM(250.0) / val;

        //printf("in:%d val:%g\n", chip->inputs, d10_555_desc.r1);

        chip->deactivate_outputs(); // TODO: is this necessary?
        chip->pending_event = chip->circuit->queue_push(chip, 0);
    })
    INPUT_PINS( 1, 2, 3, 4, 5 )
    OUTPUT_PIN( i3 ),

	CHIP_DESC_END
};


static VIDEO_DESC( crashnscore )
    VIDEO_RESISTANCE(1, OHM(1500))
    VIDEO_RESISTANCE(2, OHM(220))
    VIDEO_CONTRAST(4.0)
    VIDEO_RETRO_V_SIZE(259)
VIDEO_DESC_END

static AUDIO_DESC( crashnscore )
    AUDIO_GAIN(20.0)
    AUDIO_SPEAKER_CONFIG(MONO) // TODO: Stereo
AUDIO_DESC_END

static INPUT_DESC( crashnscore )
    INPUT_INFO(WHEEL1_INPUT, "Rotate White Car")
    INPUT_INFO(BUTTONS1_INPUT, {{ 1 }}, "Accelerate")
    INPUT_INFO(BUTTONS1_INPUT, {{ 2 }}, "Toggle Barriers")
    
    INPUT_INFO(WHEEL2_INPUT, "Rotate Grey Car")
    INPUT_INFO(BUTTONS2_INPUT, {{ 1 }}, "Accelerate")

    INPUT_INFO(COIN_INPUT, {{ 1 }}, "Insert Coin")
    INPUT_INFO(START_INPUT, {{ 1 }}, "Start 1-Player Game")
    INPUT_INFO(START_INPUT, {{ 2 }}, "Start 2-Player Game")
INPUT_DESC_END

//**************************************************************


CIRCUIT_LAYOUT( crashnscore )

/* chips */

CHIP("A1",  7404)
CHIP("A2",  9316)
CHIP("A3",  7400)
CHIP("A4",  7493)
CHIP("A5",  7474)
CHIP("A6",  7404)
CHIP("A7",  7474)
CHIP("A8",  7474)
//NO "A9"
CHIP("B1",  7430)
CHIP("B2",  9316)
CHIP("B3",  7474)
CHIP("B4",  7485)
CHIP("B5",  7400)
CHIP("B6",  7410)
CHIP("B7",  555_Mono, &b7_555_desc)
//CHIP("B8", 7490)
//CHIP("B9", 7492)
CHIP("C1",  555_Mono, &c1_555_desc) 
CHIP("C2",  9316)
CHIP("C3",  7404)
CHIP("C4",  7420)
CHIP("C5",  9316)
CHIP("C6",  9316)
CHIP("C7",  74107)
CHIP("C8",  7402)
CHIP("C9",  7400)
CHIP("C10", 7404)
CHIP("D1",  7493)
CHIP("D2",  74S287, &d2_desc)  //ROM 004248
CHIP("D3",  7410)
CHIP("D4",  7486)
CHIP("D5",  9316)
CHIP("D6",  9316)
CHIP("D7",  7404)
CHIP("D8",  7493)
CHIP("D9",  7485)
CHIP("D10", 555_Astable, &d10_555_desc)  
CHIP("DE1", 7474)
CHIP("E1",  7493)
CHIP("E2",  74S287, &e2_desc)  //ROM 004247
CHIP("E3",  74192)
CHIP("E4",  7400)
CHIP("E5",  9316)
CHIP("E6",  7402)
//NO "E7"
CHIP("E8",  7420)
CHIP("E9",  74193)
CHIP("E10", 7404)
CHIP("F1",  7402)
CHIP("F2",  74153)
CHIP("F3",  7408)
CHIP("F4",  7402)
CHIP("F5",  74107)
CHIP("F6",  82S115, &f6_desc)  //ROM 003186
CHIP("F7",  82S123, &f7_desc)  //ROM 003187
CHIP("F8",  74193)
CHIP("F9",  7400)
CHIP("F10", 7410)
CHIP("FH1", 74107)
CHIP("H1",  9312)
CHIP("H2",  7402)
CHIP("H3",  7400)
CHIP("H4",  9602, &h4_desc)
CHIP("H5",  9312)
//NO "H6"
CHIP("H7",  7475)
CHIP("H8",  74193)
CHIP("H9",  7474)
CHIP("H10", 7404)
CHIP("J1",  7448)
CHIP("J2",  9312)
CHIP("J3",  7404)
CHIP("J4",  7400)
CHIP("J5",  7474)
CHIP("J6",  7404)
CHIP("J7",  7474)
CHIP("J8",  7408)
CHIP("J9",  7404)
CHIP("K1",  74153)
CHIP("K2",  74153)
CHIP("K3",  7474)
CHIP("K4",  7474)
CHIP("K5",  7400)
CHIP("K6",  7410)
CHIP("K7",  555_Mono, &k7_555_desc)
CHIP("K8",  7490)
CHIP("K9",  7492)
CHIP("L1",  7490)
CHIP("L2",  7490)
CHIP("L3",  7486)
CHIP("L4",  7402)
CHIP("L5",  9316)
CHIP("L6",  9316)
CHIP("L7",  74107)
CHIP("L8",  7402)
CHIP("L9",  7400)
CHIP("L10", 7406)
CHIP("M1",  7490)
CHIP("M2",  7490)
CHIP("M3",  7486)
CHIP("M4",  7474)
CHIP("M5",  9316)
CHIP("M6",  9316)
CHIP("M7",  7404)
CHIP("M8",  7493)
CHIP("M9",  7485)
//CHIP("M10", 555_Astable, &m10_555_desc)
CHIP("MN1", 7408)
CHIP("MN2", 74279)
CHIP("N1",  7474)
CHIP("N2",  74279)
CHIP("N3",  7420)
CHIP("N4",  7402)
CHIP("N5",  9316)
CHIP("N6",  7402)
//NO "N7"
CHIP("N8",  7420)
CHIP("N9",  74193)
CHIP("N10", 7404)
CHIP("P1",  74107)
CHIP("P2",  7410)
CHIP("P3",  7400)
CHIP("P4",  74193)
CHIP("P5",  74107)
CHIP("P6",  82S115, &p6_desc)  //ROM 003186
CHIP("P7",  82S123, &p7_desc)  //ROM 003187
CHIP("P8",  74193)
CHIP("P9",  7400)
CHIP("P10", 7490)
CHIP("R1",  9602, &r1_desc)
CHIP("R2",  7474)
CHIP("R3",  7404)
CHIP("R4",  7432)
CHIP("R5",  9312)
//NO "R6"
CHIP("R7",  7475)
CHIP("R8",  74193)
CHIP("R9",  7474)
CHIP("R10", 555_Astable, &r10_555_desc)  

CHIP("CAP2",  CAPACITOR, &cap2_desc)
CHIP("CAP6",  CAPACITOR, &cap6_desc)
CHIP("CAP17", CAPACITOR, &cap17_desc)
CHIP("CAP40", CAPACITOR, &cap40_desc)
CHIP("CAP46", CAPACITOR, &cap46_desc)
CHIP("CAP58", CAPACITOR, &cap58_desc)
CHIP("CAP70", CAPACITOR, &cap70_desc)

CHIP("CRYSTAL",    CLOCK_14_318_MHZ)
CHIP("LATCH",      LATCH)
CHIP("COIN_IN",    COIN_INPUT)
CHIP("START_IN",   START_INPUT)
CHIP("CARIWHEEL",  WHEEL1_INPUT, &wheel1_desc)  
CHIP("CARIIWHEEL", WHEEL2_INPUT, &wheel2_desc)
CHIP("CARIGAS",    BUTTONS1_INPUT)
CHIP("CARIIGAS",   BUTTONS2_INPUT)
CHIP("CARGASAND", 7408)
//CHIP("SW1",        DIPSWITCH, &sw1_desc)
CHIP("SW2PLAY",    DIPSWITCH, &sw2play_desc)
CHIP("SW2",        DIPSWITCH_4SPST, &sw2_desc)
CHIP("POT1",       POT_555_ASTABLE, &pot1_desc)
POTENTIOMETER_CONNECTION("POT1", "R10") 

CHIP("SPEED1", CRASHNSCORE_SPEED_CONTROL)
POTENTIOMETER_CONNECTION("SPEED1", "D10") 

// TODO: Rest of audio
CHIP("MIXER", MIXER, &mixer_desc)

OPTIMIZATION_HINT("E2", 512, 128)
OPTIMIZATION_HINT("F2", 1024, 64)
OPTIMIZATION_HINT("K3", 4096, 64)
OPTIMIZATION_HINT("H5", 2048, 64)
OPTIMIZATION_HINT("R5", 2048, 64)
//OPTIMIZATION_HINT("H3", 4096, 64)


VIDEO(crashnscore)
AUDIO(crashnscore)
INPUT(crashnscore)

#ifdef DEBUG
	CHIP("LOG1", VCD_LOG, &vcd_log_desc)
#endif



/* signals */

/* sheet 1 */

#define _CLOCK       "A1", 2
#define _CLOCKn      "A1", 4
#define _1H          "A2", 14
#define _4H          "A2", 12
#define _8H          "A2", 11
#define _16H         "C2", 14
#define _32H         "C2", 13
#define _64H         "C2", 12
#define _128H        "C2", 11
#define _256H        "B2", 14
#define _512H        "B2", 13
#define _HRESETn     "A3", 8
#define _VRESETn     "B3", 5
#define _VRESET      "B3", 6
#define _VSYNC       "F1", 10
#define _VSYNCn      "F1", 13
#define _1V          "E1", 12
#define _2V          "E1", 9
#define _4V          "E1", 8
#define _8V          "E1", 11
#define _16V         "D1", 12
#define _32V         "D1", 9
#define _64V         "D1", 8
#define _128V        "D1", 11
#define _256V        "FH1", 3
#define _256Vn       "FH1", 2
#define _VCLOCKn     "C4", 8
#define _128Vn       "A1", 8  //wrong on diagram
#define _32Hn        "J3", 4
#define _1Hn         "J3", 2
#define _512Hn       "C3", 12
#define _128Hn       "C3", 10
#define _64Hn        "C3", 8
#define _256Hn       "C3", 4
#define _8Vn         "A1", 6
#define _64Vn        "C3", 6
#define _HSYNC       "B3", 8
#define _OBJ0        "D2", 12
#define _OBJ1        "D2", 11
#define _OBJ2        "D2", 10
#define _OBJ3        "D2", 9
#define _SHAPES      "K3", 9
#define _FLAGSn      "H3", 6
#define _FLAGS       "J3", 8
#define _BARRIORSn   "H3", 11
#define _SLICKSn     "H3", 3
#define _CARIPLUSSLICKS "J4", 11
#define _CARIIPLUSSLICKS "J4", 3
#define _BARRIERVIDEO "R3", 12
#define _BBFI        "F4", 13
#define _BBFII       "F4", 10

#define _SCOREWINDOW "F1", 1
#define _WHITESCORE  "H2", 4
#define _BLACKSCOREn "H3", 8

#define _HIT1        "H4", 6
#define _HIT1n       "H4", 7
#define _HIT2        "H4", 10
#define _HIT2n       "H4", 9
#define _HIT         "D4", 6
#define _SCORETONE   "F3", 8
#define _SA          "E4", 3
#define _SB          "E4", 6
#define _WHITEFLAG   "C3", 2
#define _BLACKFLAGS  "N4", 13
#define _BLACKFLAGSn "R3", 10
#define _FC          "C1", 3
#define _CARRESETI   "M4", 5
#define _CARRESET2   "N4", 10

/* sheet 2 */

#define _COIN        "P3", 8
#define _COIN1n      "A7", 9
#define _1CRSTARTn   "K4", 8
#define _2CRSTARTn   "K4", 6
#define _2PLAYERn    "M4", 9
#define _2PLAYER     "M4", 8
#define _STARTn      "C10", 4
#define _START       "K5", 3
#define _ATTRACTn    "J7", 5
#define _ATTRACT     "J7", 6
#define _ATTRACTI    "C10", 12
#define _GT1         "P10", 9
#define _GT2         "P10", 8
#define _ENDGAME     "P10", 11
#define _ENDGAMEn    "N10", 10
#define _FLASHn      "F10", 8
#define _2CREDITn    "N4",4
#define _2CREDIT     "R3", 2
#define _1OR2CREDIT  "P3", 3
#define _1OR2CREDITn "R3", 6
#define _Qn          "LATCH", 3
#define _Q           "E10", 10
#define _BG1n        "N1", 5
#define _BG2n        "N1", 9
#define _BONUSCOIN   "P3", 6
#define _FREEGAMETONE "MN1", 6

/* sheet 3 */

#define _R0I         "F8", 6  //R for rotation
#define _R1I         "F8", 7
#define _R2I         "H8", 3
#define _R3I         "H8", 2
#define _R4I         "H8", 6
#define _D1I         "H7", 16 //D for direction (latched rotation)
#define _D2I         "H7", 15
#define _D3I         "H7", 10
#define _D4I         "H7", 9
#define _1FI         "D8", 12 //F for frame
#define _2FI         "D8", 9
#define _4FI         "D8", 8
#define _8FI         "D8", 11
#define _16FIn       "C7", 6
#define _SPEED1I     "E9", 3
#define _SPEED2I     "E9", 2
#define _SPEED3I     "E9", 6
#define _SPEED4I     "E9", 7
#define _SPEED5I     "C7", 3
#define _SPEED5In    "C7", 2
#define _STOPI       "C9", 6
#define _GOI         "D9", 5
#define _SKIDI       "B7", 3
#define _SKIDIn      "D7", 10
#define _CRASHSEQIn  "A5", 9
#define _CRASHIn     "B5", 8

#define _CLOCKI      "A6", 8
#define _VRESETIn    "A6", 10
#define _C0I         "E5", 14 //C for column
#define _C1I         "E5", 13
#define _C2I         "E5", 12
#define _C3I         "E5", 11
#define _C4I         "D5", 14
#define _L0I         "D6", 13 //L for line
#define _L1I         "D6", 12
#define _L2I         "D6", 11
#define _CARRESETIn  "A6", 2
#define _128CVI      "F5", 5
#define _VTCIn       "B6", 6 //Vertical Terminal Count
#define _VTCI        "A6", 6
#define _CARWINDOWIn "B6", 8
#define _CARI        "F5", 3
#define _CARIn       "F5", 2
#define _MFI         "D10", 3

/* sheet 4 */

#define _R0II        "P8", 6
#define _R1II        "P8", 7
#define _R2II        "R8", 3
#define _R3II        "R8", 2
#define _R4II        "R8", 6
#define _D1II        "R7", 16
#define _D2II        "R7", 15
#define _D3II        "R7", 10
#define _D4II        "R7", 9
#define _1FII        "M8", 12
#define _2FII        "M8", 9
#define _4FII        "M8", 8
#define _8FII        "M8", 11
#define _16FIIn      "L7", 6
#define _SPEED1II    "N9", 3
#define _SPEED2II    "N9", 2
#define _SPEED3II    "N9", 6
#define _SPEED4II    "N9", 7
#define _SPEED5II    "L7", 3
#define _SPEED5IIn   "L7", 2
#define _STOPII      "L9", 6
#define _GOII        "M9", 5
#define _SKIDII      "K7", 3
#define _SKIDIIn     "M7", 10
#define _CRASHSEQIIn "J5", 9
#define _CRASHIIn    "K5", 8
#define _CLOCKII     "J6", 8
#define _VRESETIIn   "J6", 10
#define _C0II        "N5", 14
#define _C1II        "N5", 13
#define _C2II        "N5", 12
#define _C3II        "N5", 11
#define _C4II        "M5", 14
#define _L0II        "M6", 13
#define _L1II        "M6", 12
#define _L2II        "M6", 11
#define _CARRESETIIn "J6", 2
#define _128CVII     "P5", 5
#define _VTCIIn      "K6", 6
#define _VTCII       "J6", 6
#define _CARWINDOWIIn "K6", 8
#define _CARII       "P5", 3
#define _CARIIn      "P5", 2


//*****circuit layout  *****
//from (output pins) - to (input pins)

/* * * Sheet 1, Left * * */

/* clock and sync (sheet1, left, top) */

CONNECTION("CRYSTAL", 1,     "A1", 1)

CONNECTION("A1", 2,          "A1", 3)

CONNECTION(GND,              "A2", 3)
CONNECTION(GND,              "A2", 4)
CONNECTION(VCC,              "A2", 5)
CONNECTION(GND,              "A2", 6)
CONNECTION(_HRESETn,         "A2", 9)
CONNECTION(VCC,              "A2", 7)
CONNECTION(VCC,              "A2", 10)
CONNECTION(_CLOCK,           "A2", 2)
CONNECTION(VCC,              "A2", 1)

CONNECTION(VCC,              "C2", 3)
CONNECTION(VCC,              "C2", 4)
CONNECTION(VCC,              "C2", 5)
CONNECTION(GND,              "C2", 6)
CONNECTION(_HRESETn,         "C2", 9)
CONNECTION("A2", 15,         "C2", 7)
CONNECTION(VCC,              "C2", 10)
CONNECTION(_CLOCK,           "C2", 2)
CONNECTION(VCC,              "C2", 1)

CONNECTION(GND,              "B2", 3)
CONNECTION(GND,              "B2", 4)
CONNECTION(VCC,              "B2", 5)
CONNECTION(VCC,              "B2", 6)
CONNECTION(_HRESETn,         "B2", 9)
CONNECTION("A2", 15,         "B2", 7)
CONNECTION("C2", 15,         "B2", 10)
CONNECTION(_CLOCK,           "B2", 2)
CONNECTION(VCC,              "B2", 1)

CONNECTION("A2", 15,         "A3", 9)
CONNECTION("B2", 15,         "A3", 10)

CONNECTION(_256V,            "D3", 13)
CONNECTION(_4V,              "D3", 1)
CONNECTION(_2V,              "D3", 2)

CONNECTION(VCC,              "B3", 4)
CONNECTION("D3", 12,         "B3", 2)
CONNECTION(_512H,            "B3", 3)
CONNECTION(VCC,              "B3", 1)

CONNECTION(_4V,              "F1", 8)
CONNECTION(_VSYNCn,          "F1", 9)

CONNECTION(_VSYNC,           "F1", 11)
CONNECTION(_VRESET,          "F1", 12)

CONNECTION(_VRESET,          "E1", 2)
CONNECTION(_VRESET,          "E1", 3)
CONNECTION(_512H,            "E1", 14)
CONNECTION(_1V,              "E1", 1)

CONNECTION(_VRESET,          "D1", 2)
CONNECTION(_VRESET,          "D1", 3)
CONNECTION(_8V,              "D1", 14)
CONNECTION(_16V,             "D1", 1)

CONNECTION(VCC,              "FH1", 1)
CONNECTION(_128V,            "FH1", 12)
CONNECTION(VCC,              "FH1", 4)
CONNECTION(_VRESETn,         "FH1", 13)  //pin number missing on diagram

CONNECTION(_VSYNCn,          "C4", 13)
CONNECTION(_HSYNC,           "C4", 12)
CONNECTION(_256Vn,           "C4", 10)
CONNECTION(_16H,             "C4", 9)

CONNECTION(_256H,            "A3", 4)
CONNECTION(_64H,             "A3", 5)

CONNECTION("A3", 6,          "B3", 10)
CONNECTION(_512H,            "B3", 12)
CONNECTION(_256H,            "B3", 11)
CONNECTION(VCC,              "B3", 13)

CONNECTION(_128V,            "A1", 9)  //wrong on diagram

CONNECTION(_32H,             "J3", 3)

CONNECTION(_1H,              "J3", 1)

CONNECTION(_512H,            "C3", 13)

CONNECTION(_128H,            "C3", 11)

CONNECTION(_64H,             "C3", 9)

CONNECTION(_256H,            "C3", 3)

CONNECTION(_64V,             "C3", 5)

CONNECTION(_8V,              "A1", 5) 


/* playfield (sheet1, left, middle) */

CONNECTION(_32H,             "D2", 5)
CONNECTION(_64H,             "D2", 6)
CONNECTION(_128H,            "D2", 7)
CONNECTION(_256H,            "D2", 4)
CONNECTION(_16V,             "D2", 3)
CONNECTION(_32V,             "D2", 2)
CONNECTION(_64V,             "D2", 1)
CONNECTION(_128V,            "D2", 15)
CONNECTION(GND,              "D2", 13)
CONNECTION(GND,              "D2", 14)

CONNECTION(_16H,             "E2", 5)
CONNECTION(_1V,              "E2", 6)
CONNECTION(_2V,              "E2", 7)
CONNECTION(_4V,              "E2", 4)
CONNECTION(_OBJ0,            "E2", 3)
CONNECTION(_OBJ1,            "E2", 2)
CONNECTION(_OBJ2,            "E2", 1)
CONNECTION(_OBJ3,            "E2", 15)
CONNECTION(GND,              "E2", 13)
CONNECTION(GND,              "E2", 14)

CONNECTION(_512Hn,           "F2", 1)
CONNECTION("E2", 12,         "F2", 6)
CONNECTION("E2", 11,         "F2", 5)
CONNECTION("E2", 10,         "F2", 4)
CONNECTION("E2", 9,          "F2", 3)
CONNECTION(_4H,              "F2", 14)
CONNECTION(_8H,              "F2", 2)

CONNECTION(VCC,              "K3", 10)
CONNECTION("F2", 7,          "K3", 12)
CONNECTION(_1Hn,             "K3", 11)
CONNECTION(_8V,              "K3", 13)

CONNECTION(_OBJ3,            "J3", 11)

CONNECTION("J3", 10,         "H3", 5)
CONNECTION(_SHAPES,          "H3", 4)

CONNECTION(_FLAGSn,          "J3", 9)

CONNECTION(_OBJ1,            "D3", 3)
CONNECTION(_OBJ2,            "D3", 4)
CONNECTION(_OBJ3,            "D3", 5)

CONNECTION("D3", 6,          "J3", 13)

CONNECTION(_SHAPES,          "H3", 1)
CONNECTION("J3", 12,         "H3", 2)

CONNECTION(_CARIn,           "J4", 13)
CONNECTION(_SLICKSn,         "J4", 12)

CONNECTION(_SLICKSn,         "J4", 2)
CONNECTION(_CARIIn,          "J4", 1)

CONNECTION("J3", 12,         "H2", 2)
CONNECTION("J3", 10,         "H2", 3)

CONNECTION(_SHAPES,          "H3", 12)
CONNECTION("H2", 1,          "H3", 13)

CONNECTION(_Qn,              "L8", 9)
CONNECTION(_ATTRACTn,        "L8", 8)

CONNECTION("L8", 10,         "J8", 12)
CONNECTION("CARIGAS", i2,    "J8", 13)  //temp P1 button 2

CONNECTION(VCC,              "J7", 10)
CONNECTION("J7", 8,          "J7", 12)
CONNECTION("J8", 11,         "J7", 11)
CONNECTION(_Q,               "J7", 13)

CONNECTION("H3", 11,         "F3", 2)
CONNECTION("J7", 9,          "F3", 1)

CONNECTION("F3", 3,          "F4", 6)
CONNECTION("J7", 8,          "F4", 5)

CONNECTION("F4", 4,          "R3", 13)

CONNECTION("F4", 4,          "F4", 3)
CONNECTION(_BLACKFLAGS,      "F4", 2)

CONNECTION(_HIT1,            "F4", 11)
CONNECTION("F4", 1,          "F4", 12)

CONNECTION("F4", 1,          "F4", 8)
CONNECTION(_HIT2,            "F4", 9)


/* Hit detect (sheet 1, right, center) */

CONNECTION(_CARI,            "J4", 4)
CONNECTION(_WHITEFLAG,       "J4", 5)

CONNECTION(_WHITEFLAG,       "J4", 9)
CONNECTION(_CARII,           "J4", 10)

CONNECTION("J4", 6,          "H4", 5)
CONNECTION(_HIT1,            "H4", 4)
CONNECTION(_HIT2n,           "H4", 3)

CONNECTION("J4", 8,          "H4", 11)
CONNECTION(_HIT2,            "H4", 12)
CONNECTION(_HIT1n,           "H4", 13)

CONNECTION(_HIT1n,           "D4", 4)
CONNECTION(_HIT2n,           "D4", 5)

CONNECTION(_2FI,             "F3", 4)
CONNECTION("E3", 13,         "F3", 5)

CONNECTION(GND,              "E3", 15)
CONNECTION(_OBJ0,            "E3", 1)
CONNECTION(_OBJ1,            "E3", 10)
CONNECTION(_OBJ2,            "E3", 9)
CONNECTION(_ATTRACTn,        "E3", 5)
CONNECTION("F3", 6,          "E3", 4)
CONNECTION("DE1", 8,         "E3", 11)
CONNECTION(_START,           "E3", 14)

CONNECTION("E3", 13,         "J3", 5)

CONNECTION(VCC,              "DE1", 10)
CONNECTION(VCC,              "DE1", 12)
CONNECTION(_HIT,             "DE1", 11)
CONNECTION("J3", 6,          "DE1", 13)

CONNECTION("E4", 11,         "F3", 13)
CONNECTION("E3", 3,          "F3", 12)

CONNECTION(_8V,              "F3", 9)
CONNECTION("F3", 11,         "F3", 10)

CONNECTION(_HIT1,            "E4", 2)
CONNECTION("F3", 11,         "E4", 1)

CONNECTION("F3", 11,         "E4", 4)
CONNECTION(_HIT2,            "E4", 5)

CONNECTION(_1FI,             "C10", 5)

CONNECTION(_GT1,             "J8", 9)
CONNECTION(_GT2,             "J8", 10)

CONNECTION("C10", 6,         "E4", 12)
CONNECTION("J8", 8,          "E4", 13)

// pick white flag and black flags

CONNECTION(_MFI,             "E4", 10)
CONNECTION(_FC,              "E4", 9)

CONNECTION("E4", 8,          "CAP70", 1)  

CONNECTION(GND,              "A4", 2)
CONNECTION(GND,              "A4", 3)
CONNECTION("CAP70", 2,       "A4", 14) 
CONNECTION("A4", 12,         "A4", 1)

CONNECTION("A4", 8,          "B4", 10)
CONNECTION("A4", 11,         "B4", 12)
CONNECTION("A4", 12,         "B4", 13)
CONNECTION("A4", 9,          "B4", 15)
CONNECTION(GND,              "B4", 4)
CONNECTION(VCC,              "B4", 3)
CONNECTION(GND,              "B4", 2)
CONNECTION(_128H,            "B4", 9)
CONNECTION(_256H,            "B4", 11)
CONNECTION(_64V,             "B4", 14)
CONNECTION(_128V,            "B4", 1)

CONNECTION(_FLAGS,           "A3", 13)
CONNECTION("B4", 6,          "A3", 12)

CONNECTION("A3", 11,         "C3", 1)

CONNECTION("B4", 6,          "N4", 11)
CONNECTION(_FLAGSn,          "N4", 12)

CONNECTION(_BLACKFLAGS,      "R3", 11)

CONNECTION(_HIT,             "C1", 2)
CONNECTION(_HIT,             "C1", 4)


/* score display (sheet 1, left, top) */

CONNECTION(GND,              "L1",6)
CONNECTION(GND,              "L1",7)
CONNECTION(_START,           "L1",2)
CONNECTION(VCC,              "L1",3)
CONNECTION(_SA,              "L1",14)
CONNECTION("L1", 12,         "L1",1)

CONNECTION(GND,              "L2",6)
CONNECTION(GND,              "L2",7)
CONNECTION(_START,           "L2",2)
CONNECTION(VCC,              "L2",3)
CONNECTION("L1", 11,         "L2",14)
CONNECTION("L2", 12,         "L2",1)

CONNECTION(GND,              "M1",6)
CONNECTION(GND,              "M1",7)
CONNECTION(_START,           "M1",2)
CONNECTION(VCC,              "M1",3)
CONNECTION(_SB,              "M1",14)
CONNECTION("M1", 12,         "M1",1)

CONNECTION(GND,              "M2",6)
CONNECTION(GND,              "M2",7)
CONNECTION(_START,           "M2",2)
CONNECTION(VCC,              "M2",3)
CONNECTION("M1", 11,         "M2",14)
CONNECTION("M2", 12,         "M2",1)

CONNECTION(_256H,            "D4", 9)
CONNECTION(_64Hn,            "D4", 10)

CONNECTION(_512Hn,           "B1",12)
CONNECTION(_128H,            "B1",2)
CONNECTION("D4", 8,          "B1",1)
CONNECTION(_128Vn,           "B1",4)
CONNECTION(_64V,             "B1",6)
CONNECTION(_32V,             "B1",5)
CONNECTION(_16V,             "B1",3)
CONNECTION(VCC,              "B1",11)

CONNECTION(_64H,             "F1", 5)
CONNECTION(_2PLAYER,         "F1", 6)

CONNECTION("B1", 8,          "F1", 2)
CONNECTION("F1", 4,          "F1", 3)

CONNECTION("L2", 12,         "K1", 3)
CONNECTION("L1", 12,         "K1", 4)
CONNECTION("M2", 12,         "K1", 5)
CONNECTION("M1", 12,         "K1", 6)
CONNECTION("L2", 9,          "K1", 13)
CONNECTION("L1", 9,          "K1", 12)
CONNECTION("M2", 9,          "K1", 11)
CONNECTION("M1", 9,          "K1", 10)
CONNECTION(_32Hn,            "K1", 14)
CONNECTION(_256H,            "K1", 2)
CONNECTION(GND,              "K1", 1)
CONNECTION(GND,              "K1", 15)

CONNECTION("L2", 8,          "K2", 3)
CONNECTION("L1", 8,          "K2", 4)
CONNECTION("M2", 8,          "K2", 5)
CONNECTION("M1", 8,          "K2", 6)
CONNECTION("L2", 11,         "K2", 13)
CONNECTION("L1", 11,         "K2", 12)
CONNECTION("M2", 11,         "K2", 11)
CONNECTION("M1", 11,         "K2", 10)
CONNECTION(_32Hn,            "K2", 14)
CONNECTION(_256H,            "K2", 2)
CONNECTION(GND,              "K2", 1)
CONNECTION(GND,              "K2", 15)

CONNECTION("K1", 7,          "J1", 7)
CONNECTION("K1", 9,          "J1", 1)
CONNECTION("K2", 7,          "J1", 2)
CONNECTION("K2", 9,          "J1", 6)
CONNECTION(_FLASHn,          "J1", 4)
CONNECTION(VCC,              "J1", 3)  //not shown
CONNECTION(VCC,              "J1", 5)  //not shown

CONNECTION("J1", 11,         "J2", 9)
CONNECTION(GND,              "J2", 7)
CONNECTION("J1", 9,          "J2", 6)
CONNECTION(GND,              "J2", 5)
CONNECTION("J1", 12,         "J2", 4)
CONNECTION(GND,              "J2", 3)
CONNECTION("J1", 15,         "J2", 2)
CONNECTION(GND,              "J2", 1)
CONNECTION(_8H,              "J2", 11)
CONNECTION(_16H,             "J2", 12)
CONNECTION(_8V,              "J2", 13)
CONNECTION(GND,              "J2", 10)

CONNECTION("J1", 10,         "H1", 9)
CONNECTION("J1", 10,         "H1", 7)
CONNECTION(GND,              "H1", 6)
CONNECTION("J1", 14,         "H1", 5)
CONNECTION("J1", 14,         "H1", 4)
CONNECTION(GND,              "H1", 3)
CONNECTION("J1", 13,         "H1", 2)
CONNECTION("J1", 13,         "H1", 1)
CONNECTION(_2V,              "H1", 11)
CONNECTION(_4V,              "H1", 12)
CONNECTION(_8V,              "H1", 13)
CONNECTION("H2", 10,         "H1", 10)

CONNECTION(_8H,              "H2", 8)
CONNECTION(_16H,             "H2", 9)

CONNECTION("J2", 15,         "H2", 12)
CONNECTION("H1", 15,         "H2", 11)

CONNECTION(_SCOREWINDOW,     "K3", 4)
CONNECTION("H2", 13,         "K3", 2)
CONNECTION(_1Hn,             "K3", 3)
CONNECTION(VCC,              "K3", 1)

CONNECTION(_256Hn,           "H2", 5)
CONNECTION("K3", 5,          "H2", 6)

CONNECTION("K3", 6,          "H3", 9)
CONNECTION(_256Hn,           "H3", 10)


/* car reset (sheet1, right, middle) */

CONNECTION(_STARTn,          "M4", 4)
CONNECTION(GND,              "M4", 2)
CONNECTION(_256V,            "M4", 3)  
CONNECTION(VCC,              "M4", 1)

CONNECTION(_256Hn,           "D3", 11)
CONNECTION(_128Hn,           "D3", 10)
CONNECTION(_64Hn,            "D3", 9)

CONNECTION("M4", 6,          "N4", 9)
CONNECTION("D3", 8,          "N4", 8)


/* video (sheet1, right, middle) */

CONNECTION("VIDEO", Video::VBLANK_PIN, _VSYNC)
CONNECTION("VIDEO", Video::HBLANK_PIN, _HSYNC)

CONNECTION(_CARIIn,          "C4", 1)
CONNECTION(_BLACKSCOREn,     "C4", 2)
CONNECTION(_BLACKFLAGSn,     "C4", 4)
CONNECTION(_SLICKSn,         "C4", 5)

CONNECTION(_WHITEFLAG,       "A3", 2)
CONNECTION(_8FI,             "A3", 1)

CONNECTION(_CARI,            "L4", 9)
CONNECTION(_WHITESCORE,      "L4", 8)

CONNECTION(_BARRIERVIDEO,    "P2", 5)
CONNECTION("A3", 3,          "P2", 3)
CONNECTION("L4", 10,         "P2", 4)

CONNECTION("C4", 6,          "VIDEO", 1)  //GRAY
CONNECTION("P2", 6,          "VIDEO", 2)  //WHITE


/* * * * * * * sheet 2 * * * * * * */


/* coin (sheet 2, left, top) */

CONNECTION("COIN_IN", i1,  "A7", 4)
CONNECTION("COIN_IN", 1,   "A7", 2)
CONNECTION(_64V,           "A7", 3)
CONNECTION(VCC,            "A7", 1)

CONNECTION("COIN_IN", i1,  "A7", 10)
CONNECTION("A7", 5,        "A7", 12)
CONNECTION(_64V,           "A7", 11)
CONNECTION(VCC,            "A7", 13)

CONNECTION(VCC,            "R2", 4)
CONNECTION("A7", 8,        "R2", 2)
CONNECTION(_16V,           "R2", 3)
CONNECTION(VCC,            "R2", 1)

CONNECTION("R2", 5,        "N2", 15)
CONNECTION(_16V,           "N2", 14)

CONNECTION(VCC,            "SW2PLAY", 1)  // 25 cents for 2 play
CONNECTION(_4V,            "SW2PLAY", 2)  // 25 cents for 1 play

CONNECTION("SW2PLAY", 3,   "P2", 2)
CONNECTION("R2", 5,        "P2", 1)
CONNECTION("N2", 13,       "P2", 13)

CONNECTION("P2", 12,       "P3", 9) 
CONNECTION(VCC,            "P3", 10)  // skip coin 2

// skipping coin 2 circuit



/* start (sheet 2, left, bottom) */

//unpressed = hi, pressed = lo

CONNECTION("START_IN", 1, "J9", 3)

CONNECTION(_1OR2CREDITn, "L4", 12)
CONNECTION(_ATTRACTn,    "L4", 11)

CONNECTION(VCC,          "K4", 10)
CONNECTION("J9", 4,      "K4", 12)
CONNECTION(_64V,         "K4", 11)
CONNECTION("L4", 13,     "K4", 13)

CONNECTION("START_IN", 2, "J9", 1)

CONNECTION(_128V,        "MN2", 15)
CONNECTION(_2CREDITn,    "MN2", 14)

CONNECTION(_ATTRACTn,    "L4", 2)
CONNECTION("MN2", 13,    "L4", 3)

CONNECTION(VCC,          "K4", 4)
CONNECTION("J9", 2,      "K4", 2)
CONNECTION(_64V,         "K4", 3)
CONNECTION("L4", 1,      "K4", 1)

CONNECTION(_1CRSTARTn,   "M4", 10)
CONNECTION(VCC,          "M4", 12)
CONNECTION(VCC,          "M4", 11)
CONNECTION(_2CRSTARTn,   "M4", 13)

CONNECTION(_1CRSTARTn,   "K5", 1)
CONNECTION(_2CRSTARTn,   "K5", 2)

CONNECTION("K5", 3,      "C10", 3)

CONNECTION(VCC,          "J7", 4)
CONNECTION(_START,       "J7", 2)
CONNECTION("J8", 3,      "J7", 3)
CONNECTION("J8", 6,      "J7", 1)

CONNECTION(_32V,         "J8", 1)
CONNECTION("J7", 6,      "J8", 2)

CONNECTION(_Q,           "J8", 5)
CONNECTION(_ENDGAMEn,    "J8", 4)

CONNECTION(_ATTRACTn,    "C10", 13)


/* Latch (sheet 2, left, top) */

//latch in/out is active low
//CONNECTION(_ENDGAMEn,    "LATCH", 1)  //latch in:set

CONNECTION(_1OR2CREDITn, "B5", 2)  
CONNECTION(_ENDGAME,     "B5", 1)  

CONNECTION("B5", 3,      "LATCH", 1)  //latch in:set
CONNECTION(_COIN1n,      "LATCH", 2)  //latch in:reset
CONNECTION("LATCH", 3,   "E10", 11)   //latch out


/* game timer (sheet 2, left, bottom and right, top) */

CONNECTION(_ENDGAMEn,    "R10", 4)

CONNECTION("R10", 3,     "P10", 14)
CONNECTION(_START,       "P10", 2)
CONNECTION(_START,       "P10", 3)
CONNECTION(_Qn,          "P10", 6)
CONNECTION(_Qn,          "P10", 7)
CONNECTION("P10", 12,    "P10", 1)

CONNECTION(_ENDGAME,     "N10", 11)

CONNECTION(_GT1,         "F10", 9)
CONNECTION(_GT2,         "F10", 10)
CONNECTION(_8FI,         "F10", 11)


/* credit (sheet 2, right, top) */

CONNECTION(_BONUSCOIN,   "N4", 2)
CONNECTION(_COIN,        "N4", 3)

CONNECTION(_8Vn,         "R4", 12)
CONNECTION(_2CRSTARTn,   "R4", 13)

CONNECTION(_1CRSTARTn,   "MN1", 1)
CONNECTION("R4", 11,     "MN1", 2)

CONNECTION(VCC,          "P4", 15)
CONNECTION(VCC,          "P4", 10)
CONNECTION(VCC,          "P4", 9)
CONNECTION(VCC,          "P4", 1)
CONNECTION("P4", 12,     "P4", 11)
CONNECTION("P3", 11,     "P4", 14)
CONNECTION("N4", 1,      "P4", 5)
CONNECTION("MN1", 3,     "P4", 4)

CONNECTION(_Q,           "P3", 12)
CONNECTION("P4", 13,     "P3", 13)

CONNECTION("P4", 6,      "R4", 9)
CONNECTION("P4", 2,      "R4", 10)

CONNECTION("P4", 7,      "N4", 6)
CONNECTION("R4", 8,      "N4", 5)

CONNECTION(_2CREDITn,    "R3", 1)

CONNECTION("P4", 3,      "R3", 3)

CONNECTION(_2CREDITn,    "P3", 1)
CONNECTION("R3", 4,      "P3", 2)

CONNECTION(_1OR2CREDIT,  "R3", 5)


/* Free game selector (sheet 2, right, bottom) */

CONNECTION(VCC,         "SW2", 1)
CONNECTION(GND,         "SW2", 2)

CONNECTION(VCC,         "SW2", 3)
CONNECTION(GND,         "SW2", 4)

CONNECTION(VCC,         "SW2", 5)
CONNECTION(GND,         "SW2", 6)

CONNECTION(VCC,         "SW2", 7)
CONNECTION(GND,         "SW2", 8)

CONNECTION("L2", 12,    "L3", 5) //1E
CONNECTION("SW2", 9,    "L3", 4)

CONNECTION("L2", 9,     "L3", 12) //1F
CONNECTION("SW2", 10,   "L3", 13)

CONNECTION("L2", 8,     "L3", 2) //1G
CONNECTION("SW2", 11,   "L3", 1)
 
CONNECTION("L2", 11,    "L3", 9) //1H
CONNECTION("SW2", 12,   "L3", 10)

CONNECTION("L3", 6,     "N3", 10)
CONNECTION("L3", 11,    "N3", 12)
CONNECTION("L3", 3,     "N3", 13)
CONNECTION("L3", 8,     "N3", 9)

CONNECTION(_ENDGAMEn,   "N2", 3)
CONNECTION(_BG1n,       "N2", 2)
CONNECTION("N3", 8,     "N2", 1)

CONNECTION(_Q,          "N1", 4)
CONNECTION("N2", 4,     "N1", 2)
CONNECTION(_ENDGAME,    "N1", 3)
CONNECTION(VCC,         "N1", 1)

CONNECTION(_ATTRACTn,   "P1", 1)
CONNECTION("N2", 4,     "P1", 12)
CONNECTION(GND,         "P1", 4)
CONNECTION(_HRESETn,    "P1", 13)

CONNECTION("M2", 12,    "M3", 5) //2E
CONNECTION("SW2", 9,    "M3", 4)

CONNECTION("M2", 9,     "M3", 12) //2F
CONNECTION("SW2", 10,   "M3", 13)

CONNECTION("M2", 8,     "M3", 2) //2G
CONNECTION("SW2", 11,   "M3", 1)

CONNECTION("M2", 11,    "M3", 9) //2H
CONNECTION("SW2", 12,   "M3", 10)

CONNECTION("L3", 6,     "N3", 4)
CONNECTION("L3", 11,    "N3", 2)
CONNECTION("L3", 3,     "N3", 1)
CONNECTION("L3", 8,     "N3", 5)

CONNECTION(_ENDGAMEn,   "N2", 12)
CONNECTION(_BG2n,       "N2", 11)
CONNECTION("N3", 6,     "N2", 10)

CONNECTION(_Q,          "N1", 10)
CONNECTION("N2", 9,     "N1", 12)
CONNECTION(_ENDGAME,    "N1", 11)
CONNECTION(VCC,         "N1", 13)

CONNECTION(_ATTRACTn,   "P1", 8)
CONNECTION("N2", 9,     "P1", 9)
CONNECTION(GND,         "P1", 11)
CONNECTION(_HRESETn,    "P1", 10)

CONNECTION("P1", 2,     "P3", 5)
CONNECTION("P1", 6,     "P3", 4)

  /* sound */

CONNECTION(VCC,         "R1", 11)
CONNECTION(_BONUSCOIN,  "R1", 12)
CONNECTION(VCC,         "R1", 13)

CONNECTION(_4V,         "MN1", 4)
CONNECTION("R1", 10,    "MN1", 5)

/* * * * * * * sheet 3 * * * * * * */


/* car I steering (sheet 3, left, top) */
CONNECTION(_ATTRACTI,    "A6", 13)

CONNECTION("CARIWHEEL", Wheel::A, "H10", 3)

CONNECTION(VCC,          "H9", 4)
CONNECTION("A6", 12,     "H9", 2)
CONNECTION("H10", 4,     "H9", 3)
CONNECTION(_VTCIn,       "H9", 1)

CONNECTION("CARIWHEEL", Wheel::B, "H10", 5)

CONNECTION("A6", 12,     "H9", 10)
CONNECTION("H10", 4,     "H9", 12)
CONNECTION("H10", 6,     "H9", 11)
CONNECTION(VCC,          "H9", 13)

CONNECTION(_SKIDI,       "F9", 10)
CONNECTION(_VTCI,        "F9", 9)

CONNECTION("F9", 8,      "F9", 13)
CONNECTION("H9", 6,      "F9", 12)

CONNECTION("F9", 11,     "F9", 1)
CONNECTION("H9", 9,      "F9", 2)

CONNECTION("H9", 8,      "F9", 5)
CONNECTION("F9", 11,     "F9", 4)

CONNECTION("F9", 3,      "F8", 5)
CONNECTION("F9", 6,      "F8", 4)
CONNECTION(VCC,          "F8", 15)
CONNECTION(GND,          "F8", 1)
CONNECTION(VCC,          "F8", 10)
CONNECTION(GND,          "F8", 9)
CONNECTION(_CARRESETIn,  "F8", 11)
CONNECTION(GND,          "F8", 14)

CONNECTION("F8", 12,     "H8", 5)
CONNECTION("F8", 13,     "H8", 4)
CONNECTION(GND,          "H8", 15)
CONNECTION(VCC,          "H8", 1)
CONNECTION(GND,          "H8", 10)
CONNECTION(VCC,          "H8", 9)
CONNECTION(_CARRESETIn,  "H8", 11)
CONNECTION(GND,          "H8", 14)

CONNECTION(_SKIDIn,      "H7", 4)
CONNECTION(_SKIDIn,      "H7", 13)
CONNECTION(_R1I,         "H7", 2)
CONNECTION(_R2I,         "H7", 3)
CONNECTION(_R3I,         "H7", 6)
CONNECTION(_R4I,         "H7", 7)
//nn CONNECTION(VCC,          "H7", 5)
//nn CONNECTION(GND,          "H7", 12)


/* car I gas (sheet 3, left, bottom) */

//frame counter

CONNECTION(_128CVI,      "D8", 14)
CONNECTION(_1FI,         "D8", 1)
CONNECTION(GND,          "D8", 2)
CONNECTION(GND,          "D8", 3)

CONNECTION(VCC,          "C7", 8)
CONNECTION(_8FI,         "C7", 9)
CONNECTION(VCC,          "C7", 11)
CONNECTION(VCC,          "C7", 10)

//accellerate

CONNECTION(_VTCI,        "E8", 12)
CONNECTION(_1FI,         "E8", 13)
CONNECTION(_2FI,         "E8", 10)
CONNECTION(_4FI,         "E8", 9)

CONNECTION(_SPEED5I,     "E8", 1)
CONNECTION(_SPEED4I,     "E8", 2)
CONNECTION(_SPEED3I,     "E8", 4)
CONNECTION(_SPEED2I,     "E8", 5)

CONNECTION(_ATTRACT, "L10", 9)

// Wire AND of GAS with L10
CONNECTION("L10", 8, "CARGASAND", 1)
CONNECTION("CARIGAS", 1, "CARGASAND", 2)

CONNECTION("CARGASAND", 3, "H10", 13) //unpressed=HI, pressed=LOW

CONNECTION("H10", 12,    "F10", 2)
CONNECTION("E8", 8,      "F10", 1)
CONNECTION("E8", 6,      "F10", 13)

CONNECTION("CARGASAND", 3, "C9", 1)
CONNECTION("E8", 8,      "C9", 2)

CONNECTION(_SPEED1I,     "C9", 13)
CONNECTION(_16FIn,       "C9", 12)

CONNECTION(GND,          "E9", 15) //not shown
CONNECTION(GND,          "E9", 1)  //not shown
CONNECTION(GND,          "E9", 10) //not shown
CONNECTION(GND,          "E9", 9)  //not shown
CONNECTION(VCC,          "E9", 11)
CONNECTION("F10", 12,    "E9", 5)
CONNECTION("C9", 3,      "E9", 4)
CONNECTION(_STOPI,       "E9", 14) //diagram has stopii

CONNECTION("E9", 12,     "C9", 9)
CONNECTION("E9", 13,     "C9", 10)

CONNECTION("C8", 1,      "C9", 5)
CONNECTION(_STARTn,      "C9", 4)

CONNECTION(VCC,          "C7", 1)
CONNECTION("C9", 8,      "C7", 12)
CONNECTION(VCC,          "C7", 4)
CONNECTION("C8", 1,      "C7", 13)

CONNECTION(_SPEED5I,     "C8", 6)
CONNECTION("E9", 13,     "C8", 5)

CONNECTION(_CRASHIn,     "C8", 11)
CONNECTION(_CRASHIn,     "C8", 12)

CONNECTION("C8", 13,     "C8", 2)
CONNECTION("C8", 4,      "C8", 3)

CONNECTION(_SPEED2I,     "D9", 10)
CONNECTION(_SPEED3I,     "D9", 12)
CONNECTION(_SPEED4I,     "D9", 13)
CONNECTION(_SPEED5I,     "D9", 15)
CONNECTION(VCC,          "D9", 4)
CONNECTION("C9", 11,     "D9", 3)
CONNECTION(VCC,          "D9", 2)
CONNECTION(_8FI,         "D9", 9)
CONNECTION(_4FI,         "D9", 11)
CONNECTION(_2FI,         "D9", 14)
CONNECTION(_1FI,         "D9", 1)


/* clock I  (sheet 3, left, top) */

CONNECTION(_CLOCKn,     "A6", 9)


/* car I motion  (sheet3, middle, top) */

CONNECTION(_VRESET,     "A6", 11)

CONNECTION(_GOI,        "D7", 13)

//nn CONNECTION(VCC,         "F7", 16)
CONNECTION("D7", 12,    "F7", 15)
CONNECTION(_D4I,        "F7", 14)
CONNECTION(_D3I,        "F7", 13)
CONNECTION(_D2I,        "F7", 12)
CONNECTION(_D1I,        "F7", 11)
CONNECTION(_R0I,        "F7", 10)
//nn CONNECTION(GND,         "F7", 8)

CONNECTION(_VRESETIn,   "CAP46", 1)

CONNECTION("F7", 9,     "E6", 9)
CONNECTION("CAP46", 2,  "E6", 8)

CONNECTION("F7", 7,     "E6", 12)
CONNECTION("CAP46", 2,  "E6", 11)

CONNECTION("F7", 6,     "E6", 2)
CONNECTION("CAP46", 2,  "E6", 3)

CONNECTION("F7", 5,     "E6", 5)
CONNECTION("CAP46", 2,  "E6", 6)

CONNECTION("E6", 13,    "D7", 9)

CONNECTION("E6", 4,     "E5", 3)
CONNECTION("E6", 1,     "E5", 4)
CONNECTION("D7", 8,     "E5", 5)
CONNECTION("E6", 10,    "E5", 6)
CONNECTION("B5", 6,     "E5", 9)
CONNECTION(VCC,         "E5", 7)
CONNECTION(VCC,         "E5", 10)
CONNECTION(_CLOCKI,     "E5", 2)
CONNECTION(_CARRESETIn, "E5", 1)

CONNECTION(VCC,         "D5", 3)
CONNECTION(VCC,         "D5", 4)
CONNECTION(VCC,         "D5", 5)
CONNECTION(GND,         "D5", 6)
CONNECTION("B5", 6,     "D5", 9)
CONNECTION("E5", 15,    "D5", 7)
CONNECTION(VCC,         "D5", 10)
CONNECTION(_CLOCKI,     "D5", 2)
CONNECTION(_CARRESETIn, "D5", 1)

CONNECTION(GND,         "C5", 3)
CONNECTION(GND,         "C5", 4)
CONNECTION(VCC,         "C5", 5)
CONNECTION(VCC,         "C5", 6)
CONNECTION("B5", 6,     "C5", 9)
CONNECTION("E5", 15,    "C5", 7)
CONNECTION("D5", 15,    "C5", 10)
CONNECTION(_CLOCKI,     "C5", 2)
CONNECTION(_CARRESETIn, "C5", 1)

CONNECTION("E5", 15,    "B5", 5)
CONNECTION("C5", 15,    "B5", 4)

CONNECTION("F7", 3,     "D7", 5)

CONNECTION("F7", 2,     "D7", 3)

CONNECTION("F7", 1,     "D7", 1)

CONNECTION(_VCLOCKn,    "A6", 3)

CONNECTION(_CARRESETI,  "A6", 1)

CONNECTION("D7", 2,     "D6", 3)
CONNECTION("D7", 4,     "D6", 4)
CONNECTION("D7", 6,     "D6", 5)
CONNECTION("F7", 4,     "D6", 6)
CONNECTION(_VTCIn,      "D6", 9)
CONNECTION(VCC,         "D6", 7)
CONNECTION(VCC,         "D6", 10)
CONNECTION("A6", 4,     "D6", 2)
CONNECTION(_CARRESETIn, "D6", 1)

CONNECTION(GND,         "C6", 3)
CONNECTION(GND,         "C6", 4)
CONNECTION(GND,         "C6", 5)
CONNECTION(GND,         "C6", 6)
CONNECTION(_VTCIn,      "C6", 9)
CONNECTION("D6", 15,    "C6", 7)
CONNECTION(VCC,         "C6", 10)
CONNECTION("A6", 4,     "C6", 2)
CONNECTION(_CARRESETIn, "C6", 1)

CONNECTION(VCC,         "F5", 8)
CONNECTION("C6", 11,    "F5", 9)
CONNECTION(VCC,         "F5", 11)
CONNECTION(_CARRESETIn, "F5", 10)

CONNECTION("C5", 15,    "B6", 9)
CONNECTION("C6", 15,    "B6", 11)
CONNECTION("F5", 6,     "B6", 10)

CONNECTION("D6", 15,    "B6", 3)
CONNECTION("C6", 15,    "B6", 4)
CONNECTION("F5", 6,     "B6", 5)

CONNECTION(_VTCIn,      "A6", 5)

//nn CONNECTION(GND,         "F6", 12)
//nn CONNECTION(VCC,         "F6", 24)
// SPEED HACK
//CONNECTION(_CARWINDOWIn,"CLK_GATE", 1)
//CONNECTION(_C3I,        "CLK_GATE", 2)
//CONNECTION("CLK_GATE", 3, "F6", 18)
CONNECTION(_C3I,        "F6", 18)
CONNECTION(_C4I,        "F6", 21)
CONNECTION(_L0I,        "F6", 22)
CONNECTION(_L1I,        "F6", 23)
CONNECTION(_L2I,        "F6", 1)
CONNECTION(_R0I,        "F6", 2)
CONNECTION(_R1I,        "F6", 3)
CONNECTION(_R2I,        "F6", 4)
CONNECTION(_R3I,        "F6", 5)
CONNECTION(_R4I,        "F6", 6)
//nn CONNECTION(GND,         "F6", 20)
//nn CONNECTION(VCC,         "F6", 19)

CONNECTION("F6", 7,     "CAP40", 1)

CONNECTION(_CARWINDOWIn, "H5", 10)
CONNECTION(_C0I,        "H5", 11)
CONNECTION(_C1I,        "H5", 12)
CONNECTION(_C2I,        "H5", 13)

CONNECTION("CAP40", 2,  "H5", 1)
CONNECTION("F6", 8,     "H5", 2)
CONNECTION("F6", 9,     "H5", 3)
CONNECTION("F6", 10,    "H5", 4)
CONNECTION("F6", 14,    "H5", 5)
CONNECTION("F6", 15,    "H5", 6)
CONNECTION("F6", 16,    "H5", 7)
CONNECTION("F6", 17,    "H5", 9)

CONNECTION("H5", 15,    "F5", 1)
CONNECTION(_CLOCKI,     "F5", 12)
CONNECTION("H5", 14,    "F5", 4)
CONNECTION("C5", 15,    "F5", 13)


/* car I skid (sheet 3, left, bottom) */

CONNECTION(_CRASHSEQIn,  "B6", 1)
CONNECTION(_CARI,        "B6", 2)
CONNECTION(_CARIIPLUSSLICKS, "B6", 13)

CONNECTION(_CRASHSEQIn,  "B7", 4)
CONNECTION("B6", 12,     "B7", 2)

CONNECTION("B7", 3,      "D7", 11)


/* car I crash seq (sheet 3, left, bottom) */

CONNECTION(_BBFI,        "CAP58", 1)

CONNECTION(_CARI,        "B5", 13)
CONNECTION("CAP58", 2,   "B5", 12)  //?

CONNECTION(VCC,          "A5", 4)
CONNECTION(VCC,          "A5", 2)
CONNECTION(_VRESETIn,    "A5", 3)
CONNECTION("B5", 11,     "A5", 1)

CONNECTION(VCC,          "A5", 10)
CONNECTION("A5", 5,      "A5", 12)
CONNECTION(_VRESETIn,    "A5", 11)
CONNECTION(VCC,          "A5", 13)

CONNECTION("A5", 9,      "B5", 9)
CONNECTION("A5", 6,      "B5", 10)

/* car I MFI signal (sheet 3, left, bottom) */

CONNECTION(_SPEED1I, "SPEED1", 1)
CONNECTION(_SPEED2I, "SPEED1", 2)
CONNECTION(_SPEED3I, "SPEED1", 3)
CONNECTION(_SPEED4I, "SPEED1", 4)
CONNECTION(_SPEED5In, "SPEED1", 5)

CONNECTION(VCC,          "D10", 4)

/* * * * * * * sheet 4 * * * * * * */


/* car II steering (sheet 4, left, top) */
CONNECTION(_ATTRACT,     "J6", 13)

CONNECTION("CARIIWHEEL", Wheel::A, "H10", 9)

CONNECTION(VCC,          "R9", 4)
CONNECTION("J6", 12,     "R9", 2)
CONNECTION("H10", 8,     "R9", 3)
CONNECTION(_VTCIIn,       "R9", 1)

CONNECTION("CARIIWHEEL", Wheel::B, "H10", 1)

CONNECTION("J6", 12,     "R9", 10)
CONNECTION("H10", 8,     "R9", 12)
CONNECTION("H10", 2,     "R9", 11)
CONNECTION(VCC,          "R9", 13)

CONNECTION(_SKIDII,      "P9", 10)
CONNECTION(_VTCII,       "P9", 9)

CONNECTION("P9", 8,      "P9", 13)
CONNECTION("R9", 6,      "P9", 12)

CONNECTION("P9", 11,     "P9", 1)
CONNECTION("R9", 9,      "P9", 2)

CONNECTION("R9", 8,      "P9", 5)
CONNECTION("P9", 11,     "P9", 4)

CONNECTION("P9", 3,      "P8", 5)
CONNECTION("P9", 6,      "P8", 4)
CONNECTION(VCC,          "P8", 15)
CONNECTION(GND,          "P8", 1)
CONNECTION(GND,          "P8", 10)
CONNECTION(GND,          "P8", 9)
CONNECTION(_CARRESETIIn, "P8", 11)
CONNECTION(GND,          "P8", 14)

CONNECTION("P8", 12,     "R8", 5)
CONNECTION("P8", 13,     "R8", 4)
CONNECTION(GND,          "R8", 15)
CONNECTION(VCC,          "R8", 1)
CONNECTION(VCC,          "R8", 10)
CONNECTION(VCC,          "R8", 9)
CONNECTION(_CARRESETIIn, "R8", 11)
CONNECTION(GND,          "R8", 14)

CONNECTION(_SKIDIIn,     "R7", 4)
CONNECTION(_SKIDIIn,     "R7", 13)
CONNECTION(_R1II,        "R7", 2)
CONNECTION(_R2II,        "R7", 3)
CONNECTION(_R3II,        "R7", 6)
CONNECTION(_R4II,        "R7", 7)
//nn CONNECTION(VCC,          "R7", 5)
//nn CONNECTION(GND,          "R7", 12)


/* car II gas (sheet 4, left, bottom) */

//frame counter

CONNECTION(_128CVII,     "M8", 14)
CONNECTION(_1FII,        "M8", 1)
CONNECTION(GND,          "M8", 2)
CONNECTION(GND,          "M8", 3)

CONNECTION(VCC,          "L7", 8)
CONNECTION(_8FII,        "L7", 9)
CONNECTION(VCC,          "L7", 11)
CONNECTION(VCC,          "L7", 10)

//accellerate

CONNECTION(_VTCII,       "N8", 12)
CONNECTION(_1FII,        "N8", 13)
CONNECTION(_2FII,        "N8", 10)
CONNECTION(_4FII,        "N8", 9)

CONNECTION(_SPEED5II,    "N8", 1)
CONNECTION(_SPEED4II,    "N8", 2)
CONNECTION(_SPEED3II,    "N8", 4)
CONNECTION(_SPEED2II,    "N8", 5)

CONNECTION(_ATTRACT, "L10", 5)

// Wire AND of GAS with L10
CONNECTION("L10", 6, "CARGASAND", 4)
CONNECTION("CARIIGAS", 1, "CARGASAND", 5)

CONNECTION("CARGASAND", 6, "H10", 11) //unpressed=HI, pressed=LOW

CONNECTION("H10", 10,    "F10", 3)
CONNECTION("N8", 8,      "F10", 5)
CONNECTION("N8", 6,      "F10", 4)

CONNECTION("CARGASAND", 6, "L9", 1)
CONNECTION("N8", 8,      "L9", 2)

CONNECTION(_SPEED1II,    "L9", 13)
CONNECTION(_16FIIn,      "L9", 12)

CONNECTION(GND,          "N9", 15) //not shown
CONNECTION(GND,          "N9", 1)  //not shown
CONNECTION(GND,          "N9", 10) //not shown
CONNECTION(GND,          "N9", 9)  //not shown
CONNECTION(VCC,          "N9", 11)
CONNECTION("F10", 6,     "N9", 5)
CONNECTION("L9", 3,      "N9", 4)
CONNECTION(_STOPII,      "N9", 14) 

CONNECTION("N9", 12,     "L9", 9)
CONNECTION("N9", 13,     "L9", 10)

CONNECTION("L8", 1,      "L9", 5)
CONNECTION(_STARTn,      "L9", 4)

CONNECTION(VCC,          "L7", 1)
CONNECTION("L9", 8,      "L7", 12)
CONNECTION(VCC,          "L7", 4)
CONNECTION("L8", 1,      "L7", 13)

CONNECTION(_SPEED5II,    "L8", 6)
CONNECTION("N9", 13,     "L8", 5)

CONNECTION(_CRASHIIn,    "L8", 11)
CONNECTION(_CRASHIIn,    "L8", 12)

CONNECTION("L8", 13,     "L8", 2)
CONNECTION("L8", 4,      "L8", 3)

CONNECTION(_SPEED2II,    "M9", 10)
CONNECTION(_SPEED3II,    "M9", 12)
CONNECTION(_SPEED4II,    "M9", 13)
CONNECTION(_SPEED5II,    "M9", 15)
CONNECTION(VCC,          "M9", 4)
CONNECTION("L9", 11,     "M9", 3)
CONNECTION(VCC,          "M9", 2)
CONNECTION(_8FII,        "M9", 9)
CONNECTION(_4FII,        "M9", 11)
CONNECTION(_2FII,        "M9", 14)
CONNECTION(_1FII,        "M9", 1)


/* clock II  (sheet 4, left, top) */

CONNECTION(_CLOCKn,     "J6", 9)


/* car II motion  (sheet3, middle, top) */

CONNECTION(_VRESET,     "J6", 11)

CONNECTION(_GOII,       "M7", 13)

//nn CONNECTION(VCC,         "P7", 16)
CONNECTION("M7", 12,    "P7", 15)
CONNECTION(_D4II,       "P7", 14)
CONNECTION(_D3II,       "P7", 13)
CONNECTION(_D2II,       "P7", 12)
CONNECTION(_D1II,       "P7", 11)
CONNECTION(_R0II,       "P7", 10)
//nn CONNECTION(GND,         "P7", 8)

CONNECTION(_VRESETIIn,  "CAP6", 1)

CONNECTION("P7", 9,     "N6", 9)
CONNECTION("CAP6", 2,   "N6", 8)

CONNECTION("P7", 7,     "N6", 12)
CONNECTION("CAP6", 2,   "N6", 11)

CONNECTION("P7", 6,     "N6", 2)
CONNECTION("CAP6", 2,   "N6", 3)

CONNECTION("P7", 5,     "N6", 5)
CONNECTION("CAP6", 2,   "N6", 6)

CONNECTION("N6", 13,    "M7", 9)

CONNECTION("N6", 4,     "N5", 3)
CONNECTION("N6", 1,     "N5", 4)
CONNECTION("M7", 8,     "N5", 5)
CONNECTION("N6", 10,    "N5", 6)
CONNECTION("K5", 6,     "N5", 9)
CONNECTION(VCC,         "N5", 7)
CONNECTION(VCC,         "N5", 10)
CONNECTION(_CLOCKII,    "N5", 2)
CONNECTION(_CARRESETIn, "N5", 1)

CONNECTION(VCC,         "M5", 3)
CONNECTION(VCC,         "M5", 4)
CONNECTION(VCC,         "M5", 5)
CONNECTION(GND,         "M5", 6)
CONNECTION("K5", 6,     "M5", 9)
CONNECTION("N5", 15,    "M5", 7)
CONNECTION(VCC,         "M5", 10)
CONNECTION(_CLOCKII,    "M5", 2)
CONNECTION(_CARRESETIIn, "M5", 1)

CONNECTION(GND,         "L5", 3)
CONNECTION(GND,         "L5", 4)
CONNECTION(VCC,         "L5", 5)
CONNECTION(VCC,         "L5", 6)
CONNECTION("K5", 6,     "L5", 9)
CONNECTION("N5", 15,    "L5", 7)
CONNECTION("M5", 15,    "L5", 10)
CONNECTION(_CLOCKII,    "L5", 2)
CONNECTION(_CARRESETIIn, "L5", 1)

CONNECTION("N5", 15,    "K5", 5)
CONNECTION("L5", 15,    "K5", 4)

CONNECTION("P7", 3,     "M7", 5)

CONNECTION("P7", 2,     "M7", 3)

CONNECTION("P7", 1,     "M7", 1)

CONNECTION(_VCLOCKn,    "J6", 3)

CONNECTION(_CARRESET2,  "J6", 1)

CONNECTION("M7", 2,     "M6", 3)
CONNECTION("M7", 4,     "M6", 4)
CONNECTION("M7", 6,     "M6", 5)
CONNECTION("P7", 4,     "M6", 6)
CONNECTION("K6", 6,     "M6", 9)
CONNECTION(VCC,         "M6", 7)
CONNECTION(VCC,         "M6", 10)
CONNECTION("J6", 4,     "M6", 2)
CONNECTION(_CARRESETIIn, "M6", 1)

CONNECTION(GND,         "L6", 3)
CONNECTION(GND,         "L6", 4)
CONNECTION(GND,         "L6", 5)
CONNECTION(GND,         "L6", 6)
CONNECTION("K6", 6,     "L6", 9)
CONNECTION("M6", 15,    "L6", 7)
CONNECTION(_2PLAYER,    "L6", 10)
CONNECTION("J6", 4,     "L6", 2)
CONNECTION(_CARRESETIIn, "L6", 1)

CONNECTION(VCC,         "P5", 8)
CONNECTION("L6", 11,    "P5", 9)
CONNECTION(VCC,         "P5", 11)
CONNECTION(_CARRESETIIn, "P5", 10)

CONNECTION("L5", 15,    "K6", 9)
CONNECTION("L6", 15,    "K6", 11)
CONNECTION("P5", 6,     "K6", 10)

CONNECTION("M6", 15,    "K6", 3)
CONNECTION("L6", 15,    "K6", 4)
CONNECTION("P5", 6,     "K6", 5)

CONNECTION(_VTCIIn,     "J6", 5)

//nn CONNECTION(GND,         "P6", 12)
//nn CONNECTION(VCC,         "P6", 24)
CONNECTION(_C3II,       "P6", 18)
CONNECTION(_C4II,       "P6", 21)
CONNECTION(_L0II,       "P6", 22)
CONNECTION(_L1II,       "P6", 23)
CONNECTION(_L2II,       "P6", 1)
CONNECTION(_R0II,       "P6", 2)
CONNECTION(_R1II,       "P6", 3)
CONNECTION(_R2II,       "P6", 4)
CONNECTION(_R3II,       "P6", 5)
CONNECTION(_R4II,       "P6", 6)
//nn CONNECTION(GND,         "P6", 20)
//nn CONNECTION(VCC,         "P6", 19)

CONNECTION("P6", 7,     "CAP2", 1)

CONNECTION(_CARWINDOWIIn, "R5", 10)
CONNECTION(_C0II,       "R5", 11)
CONNECTION(_C1II,       "R5", 12)
CONNECTION(_C2II,       "R5", 13)
CONNECTION("CAP2", 2,   "R5", 1)
CONNECTION("P6", 8,     "R5", 2)
CONNECTION("P6", 9,     "R5", 3)
CONNECTION("P6", 10,    "R5", 4)
CONNECTION("P6", 14,    "R5", 5)
CONNECTION("P6", 15,    "R5", 6)
CONNECTION("P6", 16,    "R5", 7)
CONNECTION("P6", 17,    "R5", 9)

CONNECTION("R5", 15,    "P5", 1)
CONNECTION(_CLOCKII,     "P5", 12)
CONNECTION("R5", 14,    "P5", 4)
CONNECTION("L5", 15,    "P5", 13)


/* car II skid (sheet 4, left, bottom) */

CONNECTION(_CRASHSEQIIn, "K6", 1)
CONNECTION(_CARII,       "K6", 2)
CONNECTION(_CARIPLUSSLICKS, "K6", 13)

CONNECTION(_CRASHSEQIIn, "K7", 4)
CONNECTION("K6", 12,     "K7", 2)

CONNECTION("K7", 3,      "M7", 11)


/* car II crash seq (sheet 4, left, bottom) */

CONNECTION(_BBFII,       "CAP17", 1)

CONNECTION(_CARII,       "K5", 13)
CONNECTION("CAP17", 2,   "K5", 12)  

CONNECTION(VCC,          "J5", 4)
CONNECTION(VCC,          "J5", 2)
CONNECTION(_VRESETIIn,   "J5", 3)
CONNECTION("K5", 11,     "J5", 1)

CONNECTION(VCC,          "J5", 10)
CONNECTION("J5", 5,      "J5", 12)
CONNECTION(_VRESETIIn,   "J5", 11)
CONNECTION(VCC,          "J5", 13)

CONNECTION("J5", 9,      "K5", 9)
CONNECTION("J5", 6,      "K5", 10)


/* audio hookup */

CONNECTION(_FREEGAMETONE,  "AUDIO", 1)
CONNECTION(_SCORETONE,     "AUDIO", 2)  
CONNECTION(_SKIDIn,        "AUDIO", 3) 
CONNECTION(_SKIDIIn,       "AUDIO", 4) 

CONNECTION("AUDIO", i1, "MIXER", 1)
CONNECTION("AUDIO", i2, "MIXER", 2)
CONNECTION("AUDIO", i3, "MIXER", 3)
CONNECTION("AUDIO", i4, "MIXER", 4)

CONNECTION("AUDIO", Audio::OUTPUT_MONO, "MIXER", i1)

/* not implemented: lamps..... */

#ifdef DEBUG
CONNECTION("CARIGAS", "LOG1", 1)
CONNECTION(_SPEED2I, "LOG1", 2)
CONNECTION(_SPEED3I, "LOG1", 3)
CONNECTION(_SPEED4I, "LOG1", 4)
CONNECTION(_SPEED5In, "LOG1", 5)
CONNECTION(_MFI,             "LOG1", 6)
CONNECTION(_FC,              "LOG1", 7)
CONNECTION("E4", 8,              "LOG1", 8)
CONNECTION("D10", 3,              "LOG1", 9)


//CONNECTION(_C0I, "LOG1", 1)
//CONNECTION(_C1I, "LOG1", 2)
//CONNECTION(_C2I, "LOG1", 3)
//CONNECTION(_C3I, "LOG1", 4)
//CONNECTION(_C4I, "LOG1", 5)
//CONNECTION(_16V, "LOG1", 5)
//CONNECTION(_32V, "LOG1", 6)
//CONNECTION(_64V, "LOG1", 7)
//CONNECTION(_128V, "LOG1", 8)

#endif


CIRCUIT_LAYOUT_END

