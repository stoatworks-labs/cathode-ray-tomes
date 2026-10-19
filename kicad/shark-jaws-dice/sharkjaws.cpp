/* sharkjaws by atari 1976 */

//WIP 07/09/2013
//todo: check screen edge image breakup 


#include "../circuit_desc.h"
#include "../circuit.h"



#define DEBUG
#undef DEBUG

#ifdef DEBUG
static VcdLogDesc vcd_log_desc
(
    "output_sharkjaws.vcd",
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

static CapacitorDesc cap35_desc(P_FARAD(470));

/*
 static RomDesc d1a_desc("sharkjaws", "004182.1da", 0x05242912);  //shark-fish
static RomDesc d1b_desc("sharkjaws", "004183.1db", 0xB161B889);  //diver
 */

static RomDesc d1a_desc("sharkjaws", "004182.da1", 0x05242912);  //shark-fish
static RomDesc d1b_desc("sharkjaws", "004183.db1", 0xB161B889);  //diver

static Mono555Desc c9a_555_desc(K_OHM(470.0), U_FARAD(1.0));

static Astable555Desc c9b_555_desc(K_OHM(470.0), K_OHM(15.0), U_FARAD(1.0));

//static Astable555Desc c10a_555_desc(K_OHM(1.0), K_OHM(10.0), U_FARAD(0.1));

//static Astable555Desc c10b_555_desc(K_OHM(1.0), K_OHM(8.2), U_FARAD(0.1));

static Mono555Desc n9a_555_desc(K_OHM(970.0), U_FARAD(100.0));

static Astable555Desc n9b_555_desc(K_OHM(4.7), K_OHM(680.0), U_FARAD(0.22));

static Mono555Desc n8_555_desc(K_OHM(220.0), U_FARAD(100.0));

static DipswitchDesc dipswitch1_desc("coinage", "dice_dipswitch_1", "Coinage", 0, "1 Coin / 1 Credit", "1 Coin / 2 Credits");

static PotentimeterMono555Desc pot1_desc("playtime", "Play Time", K_OHM(970.0), K_OHM(470.0), K_OHM(1470.0), n9a_555_desc);

static VIDEO_DESC( sharkjaws )
    VIDEO_RESISTANCE(1, OHM(330))
    VIDEO_RESISTANCE(2, OHM(330))
    VIDEO_RESISTANCE(3, OHM(330))
    VIDEO_RESISTANCE(4, OHM(330))
    //VIDEO_RESISTANCE(5, K_OHM(1.5)) // Use this?
    VIDEO_CONTRAST(4.0)

    // Values guessed based on screenshots. TODO: Make more accurate
    //             X,   Y,   W,    H,    R,    G,    B
    VIDEO_OVERLAY( 0.0, 0.0, -1.0, -1.0, 0.20, 0.75, 0.95 ) // Blue Overlay

    VIDEO_RETRO_V_SIZE(258)
VIDEO_DESC_END

static INPUT_DESC( sharkjaws )
    INPUT_INFO(JOYSTICK1_INPUT, "Move Diver")
    INPUT_INFO(COIN_INPUT, {{ 1 }}, "Insert Coin")
    INPUT_INFO(START_INPUT, {{ 1 }}, "Start Game")
INPUT_DESC_END

#define SPEED_HACK

#ifdef SPEED_HACK
static CHIP_LOGIC( 3OR ) { pin[4] = pin[1] | pin[2] | pin[3]; }
CHIP_DESC( 3OR ) = { CHIP_START( 3OR ) INPUT_PINS( 1, 2, 3 ) OUTPUT_PIN( 4 ) OUTPUT_DELAY_NS( 1.0, 1.0 ), CHIP_DESC_END };
#endif

//**************************************************************


CIRCUIT_LAYOUT( sharkjaws )

/* chips */

CHIP("1A", 9322)
CHIP("1B", 9322)
CHIP("1C", 9314)
CHIP("1DA", 74S287, &d1a_desc)  //shark and fish
CHIP("1DB", 74S287, &d1b_desc)  //diver
CHIP("1E", 74174)
CHIP("1F", 7486)
CHIP("1H", 9322)
CHIP("1J", 7430)
CHIP("1K", 9322)
CHIP("1L", 9316)
CHIP("1M", 9316)
CHIP("1N", 9316)
CHIP("2A", 74165)
CHIP("2B", 74165)
CHIP("2C", 74165)
CHIP("2D", 74165)
CHIP("2E", 74165)
CHIP("2F", 74165)
CHIP("2H", 74165)
CHIP("2J", 9316)
CHIP("2K", 9316)
CHIP("2L", 7404)
CHIP("2M", 7400)
CHIP("2N", 9316)
CHIP("3A", 9322)
CHIP("3B", 74164)
CHIP("3C", 7402)
CHIP("3D", 7408)
CHIP("3E", 7402)
CHIP("3F", 7474)
CHIP("3H", 7420)
CHIP("3J", 7485)
CHIP("3K", 7485)
CHIP("3L", 9314)
CHIP("3M", 7408)
CHIP("3N", 74107)
CHIP("4A", 7400)
CHIP("4B", 7404)
CHIP("4C", 7420)
CHIP("4D", 74107)
CHIP("4E", 7474)
CHIP("4F", 7410)
CHIP("4H", 7427)
CHIP("4J", 9316)
CHIP("4K", 9316)
CHIP("4L", 7485)
CHIP("4M", 9316)
CHIP("4N", 9316)
CHIP("5A", 7474)
CHIP("5B", 7430)
CHIP("5C", 7493)
CHIP("5D", 7493)
CHIP("5E", 7493)
CHIP("5F", 7493)
CHIP("5H", 9316)
CHIP("5J", 9316)
CHIP("5K", 7400)
CHIP("5L", 74153)
CHIP("5M", 7402)
CHIP("5N", 7402)
CHIP("6A", 9312)
CHIP("6B", 9312)
CHIP("6C", 7448)
CHIP("6D", 9322)
CHIP("6E", 7490)
CHIP("6F", 7490)
CHIP("6H", 7474)
CHIP("6J", 7410)
CHIP("6K", 74107)
CHIP("6L", 74153)
CHIP("6M", 7474)
CHIP("6N", 7474)
CHIP("7A", 7493)
CHIP("7B", 7410)
CHIP("7C", 7474)
CHIP("7D", 7408)
CHIP("7E", 7402)
CHIP("7F", 7474)
CHIP("7H", 7408)
CHIP("7J", 9310)
CHIP("7K", 7474)
CHIP("7L", 7486)
CHIP("7M", 7474)
CHIP("7N", 7400)
CHIP("8A", 7402)
CHIP("8B", 7404)
CHIP("8C", 7474)
CHIP("8D", 7474)
CHIP("8E", 7474)
CHIP("8F", 7404)
CHIP("8H", 7410)
CHIP("8J", 7404)
CHIP("8K", 7400)
CHIP("8L", 7402)
CHIP("8M", 9314)

CHIP("C9A", 555_Mono, &c9a_555_desc) // Actually a 556
CHIP("C9B", 555_Astable, &c9b_555_desc)  //actually a 556
CHIP("N8", 555_Mono, &n8_555_desc)
CHIP("N9A", 555_Mono, &n9a_555_desc) // Actually a 556
CHIP("N9B", 555_Astable, &n9b_555_desc)  //actually a 556

//CHIP("C10A", 555_Astable, &c10a_555_desc)  //actually a 556
//CHIP("C10B", 555_Astable, &c10b_555_desc)  //actually a 556

CHIP("XA", 9322) // =1A temp fix for 2 ROM outputs tied together
CHIP("XB", 9322) // =1B temp fix for 2 ROM outputs tied together
CHIP("XC", 9314) // =1C temp fix for 2 ROM outputs tied together
CHIP("XF", 7404) // use to invert joystick buttons so that press=HI

OPTIMIZATION_HINT("1A", 16, 64)
OPTIMIZATION_HINT("1B", 16, 64)
OPTIMIZATION_HINT("1C", 16, 64)
OPTIMIZATION_HINT("1DA", 256, 64)
OPTIMIZATION_HINT("1DB", 256, 64)

OPTIMIZATION_HINT("XA", 32, 64)
OPTIMIZATION_HINT("XB", 32, 64)
OPTIMIZATION_HINT("XC", 32, 64)

#ifdef SPEED_HACK
    CHIP("XE", 74174) // =1E speed hack for rom gfx addressing
    CHIP("3OR", 3OR)
    DISABLE_OPTIMIZATION("3OR", 1)
#endif


/* 555 556
    1   7   ground
    2  6/8  trigger
    3  5/9  output
    4  4/10 reset
    5  3/11 control voltage
    6  2/12 threshold
    7  1/13 discharge
    8   14  Vcc   */

CHIP("CAP35", CAPACITOR, &cap35_desc)
CHIP("CRYSTAL", CLOCK_14_318_MHZ)
CHIP("LATCH", LATCH)
CHIP("COIN", COIN_INPUT)
CHIP("START", START_INPUT)
CHIP("JOYSTICK", JOYSTICK1_INPUT)
CHIP("DSW1", DIPSWITCH, &dipswitch1_desc)
CHIP("POT1", POT_555_MONO, &pot1_desc)
POTENTIOMETER_CONNECTION("POT1", "N9A")

VIDEO(sharkjaws)
INPUT(sharkjaws)

#ifdef DEBUG
	CHIP("LOG1", VCD_LOG, &vcd_log_desc)
#endif

/* signals */

//sync generator
 #define _CLOCKn  "4E", 6

 #define _1H "5D", 12
 #define _2H "5D", 9
 #define _4H "5D", 8
 #define _8H "5D", 11
 #define _16H "5C", 12
 #define _32H "5C", 9
 #define _64H "5C", 8
 #define _128H "5C", 11
 #define _256H "4D", 3

 #define _1Hn "4B", 4
 #define _4Hn "4B", 2
 #define _256Hn "4D", 2

 #define _HRESETn "5A", 9
 #define _HRESET "5A", 8

 #define _HSYNC "5A", 6
 #define _HSYNCn "5A", 5
 #define _HSYNC1 "4B", 6

 #define _1V "5F", 12
 #define _2V "5F", 9
 #define _4V "5F", 8
 #define _8V "5F", 11
 #define _16V "5E", 12
 #define _32V "5E", 9
 #define _64V "5E", 8
 #define _128V "5E", 11
 #define _256V "4D", 5
 #define _256Vn "4D", 6

 #define _VRESET "4E", 8
 #define _VRESETn "4E", 9

 #define _VSYNCn "4A", 6

 #define _HBLANK "7C", 6
 #define _HBLANKn "7C", 5

 #define _VBLANK "7C", 8
 #define _VBLANKn "7C", 9

 #define _COMPBLANK "8K", 8

//Score
 #define _SCOREWIN "7E", 4
 #define _FISHSCORE "C9A", 3  //555:3 = 556:5
 #define _SCORE "2L", 2
 #define _SCOREn "1E", 15

//Half second clock
 #define _HALFSEC "8B", 8
 #define _HALFSECn "4B", 8

//Coin/Start/Timer
 #define _ENDGAMEn "N9A", 3  //556 pin 5 = 555 pin 3

 #define _START "8E", 6
 #define _STARTn "8E", 5

 #define _ATTRACT "8E", 9
 #define _ATTRACTn "8E", 8

 #define _Q "8F", 8

 #define _CREDITn "8D", 9

//Small fish motion
 #define _SMLFISHDIR "8J", 2

 #define _CV1 "6N", 9
 #define _CV2 "1L", 14
 #define _CV3 "1L", 13
 #define _CV4 "1L", 12

 #define _SV1 "1M", 14
 #define _SV2 "1M", 13
 #define _SV3 "1M", 12
 #define _SV4 "1M", 11

 #define _CH3 "2N", 12
 #define _CH4 "2N", 11
 #define _SH1 "1N", 14
 #define _SH2 "1N", 13
 #define _SH3 "1N", 12
 #define _SH4 "1N", 11

 #define _CVWIN "3M", 8
 #define _CHWIN "1N", 15

//Diver motion
 #define _STOPH  "7F", 6
 #define _STOPHn "7F", 5

 #define _STOPV  "7F", 8
 #define _STOPVn "7F", 9

 #define _AV1 "5H", 14
 #define _AV2 "5H", 13
 #define _AV3 "5H", 12
 #define _AV4 "5H", 11

 #define _MV1 "5J", 14
 #define _MV2 "5J", 13
 #define _MV3 "5J", 12
 #define _MV4 "5J", 11
 #define _MV5 "6K", 5
 #define _MV5n "6K", 6

 #define _AH3 "4J", 12
 #define _AH4 "4J", 11

 #define _MH1 "4K", 14
 #define _MH2 "4K", 13
 #define _MH3 "4K", 12
 #define _MH4 "4K", 11

 #define _AVWIN "5L", 7
 #define _AHWIN "4K", 15

 #define _SWLEFTn "8J", 10

 #define _JOYLEFT  "XF", 2
 #define _JOYRIGHT "XF", 4
 #define _JOYUP    "XF", 6
 #define _JOYDOWN  "XF", 8


//Large fish motion
 #define _LRGFISHDIR "8J", 12

 #define _BV1 "2K", 14
 #define _BV2 "2K", 13
 #define _BV3 "2K", 12
 #define _BV4 "2K", 11
 #define _BV5 "4N", 12

 #define _LV0 "2J", 14
 #define _LV1 "2J", 13
 #define _LV2 "2J", 12
 #define _LV3 "2J", 11
 #define _LV4 "3N", 5
 #define _LV4n "3N", 6

 #define _LH1 "4M", 13
 #define _LH2 "4M", 12
 #define _LH3 "4M", 11
 #define _LH4 "3N", 3

 #define _LVWIN "3M", 11
 #define _LHWIN "3N", 2

 #define _VAEQB "3J", 6

//Image generation
 #define _D1 "1DA", 12
 #define _D2 "1DA", 11 
 #define _D3 "1DA", 10
 #define _D4 "1DA", 9 
 #define _D5 "1C", 15
 #define _D6 "1C", 13
 #define _D7 "1C", 12
 #define _D8 "1C", 10

 #define _XD1 "1DB", 12  //temp fix for 2 roms joined
 #define _XD2 "1DB", 11  //temp fix for 2 roms joined 
 #define _XD3 "1DB", 10  //temp fix for 2 roms joined
 #define _XD4 "1DB", 9   //temp fix for 2 roms joined
 #define _XD5 "XC", 15   //temp fix for 2 roms joined
 #define _XD6 "XC", 13   //temp fix for 2 roms joined
 #define _XD7 "XC", 12   //temp fix for 2 roms joined
 #define _XD8 "XC", 10   //temp fix for 2 roms joined

 #define _LD1An "3B", 3
 #define _LD1Bn "3B", 4
 #define _LD1Cn "3B", 5
 #define _LD2An "3B", 10
 #define _LD2Bn "3B", 11
 #define _LD2Cn "3B", 12

 #define _SHARKENABLEn "7N", 8
 #define _DIVERENABLEn "5N", 10

 #define _MEDFISH "3C", 10
 #define _DIVERVID "3D", 8
 #define _LRGFISH "3E", 10
 #define _LRGFISHVID "3D", 6
 #define _SMLFISH "3C", 13
 #define _SMLFISHVID "3D", 11

 #define _V4 "1H", 4
 #define _V3 "1F", 8
 #define _V2 "1F", 6
 #define _V1 "1H", 9

//Catch
 #define _CATCH "8L", 10

 #define _RESET "6H", 9
 #define _RESETn "6H", 8

//#define _RESETn VCC  //test

//#define _D1 "Z1", 4   //join 2 rom outputs
//#define _D2 "Z1", 7 
//#define _D3 "Z1", 9 
//#define _D4 "Z1", 12 



//*****circuit layout  *****
//from (output pins) - to (input pins)

/* page 1 */

/* sync generator (page 1, D-7) */

 CONNECTION(_VRESETn,  "4A", 2)
 CONNECTION(_VSYNCn,   "4A", 1)
 CONNECTION("4A", 3,   "4A", 4)
 CONNECTION("4B", 10,  "4A", 5)

 CONNECTION(_1H,       "4B", 3)
 CONNECTION(_HSYNCn,   "4B", 5)
 CONNECTION(_4V,       "4B", 11)

 CONNECTION(_16V,      "4C", 2)
 CONNECTION(_32V,      "4C", 1)
 CONNECTION(_64V,      "4C", 4)
 CONNECTION(_128V,     "4C", 5)

 CONNECTION(VCC,       "4D", 1)
 CONNECTION(_128H,     "4D", 12)
 CONNECTION(VCC,       "4D", 4)
 CONNECTION(_HRESETn,  "4D", 13)
 CONNECTION(VCC,       "4D", 8)
 CONNECTION(_128V,     "4D", 9)
 CONNECTION(VCC,       "4D", 11)
 CONNECTION(_VRESETn,  "4D", 10)

 CONNECTION(VCC,       "4E", 4)
 CONNECTION("4E", 6,   "4E", 2)
 CONNECTION("8F", 12,  "4E", 3)
 CONNECTION(VCC,       "4E", 1)
 CONNECTION(VCC,       "4E", 10)
 CONNECTION("4F", 12,  "4E", 12)
 CONNECTION(_HRESET,   "4E", 11)
 CONNECTION(VCC,       "4E", 13)
 
 CONNECTION(_256V,     "4F", 13)
 CONNECTION(_4V,       "4F", 2)
 CONNECTION(_1V,       "4F", 1)

 CONNECTION(VCC,       "5A", 4)
 CONNECTION(VCC,       "5A", 2)
 CONNECTION(_16H,      "5A", 3)
 CONNECTION(_HRESETn,  "5A", 1)
 CONNECTION(VCC,       "5A", 10)
 CONNECTION("5B", 8,   "5A", 12)
 CONNECTION("4E", 5,   "5A", 11)
 CONNECTION(VCC,       "5A", 13)

 CONNECTION(_256H,     "5B", 11)
 CONNECTION(_128H,     "5B", 3)
 CONNECTION(_64H,      "5B", 6)
 CONNECTION(_4H,       "5B", 5)
 CONNECTION(_2H,       "5B", 4)
 CONNECTION(VCC,       "5B", 2)
 CONNECTION(VCC,       "5B", 1)
 CONNECTION(VCC,       "5B", 12)

 CONNECTION(_16H,      "5C", 1)
 CONNECTION(_8H,       "5C", 14)
 //notneededCONNECTION(VCC,   "5C", 5)
 //notneededCONNECTION(GND,   "5C", 10)
 CONNECTION(_HRESET,   "5C", 2)
 CONNECTION(_HRESET,   "5C", 3)

 CONNECTION(_1H,       "5D", 1)
 CONNECTION("4E", 5,   "5D", 14)
 //notneededCONNECTION(VCC,   "5D", 5)
 //notneededCONNECTION(GND,   "5D", 10)
 CONNECTION(_HRESET,   "5D", 2)
 CONNECTION(_HRESET,   "5D", 3)

 CONNECTION(_16V,      "5E", 1)
 CONNECTION(_8V,       "5E", 14)
 //notneededCONNECTION(VCC,   "5E", 5)
 //notneededCONNECTION(GND,   "5E", 10)
 CONNECTION(_VRESET,   "5E", 2)
 CONNECTION(_VRESET,   "5E", 3)

 CONNECTION(_1V,       "5F", 1)
 CONNECTION(_HRESET,   "5F", 14)
 //notneededCONNECTION(VCC,   "5F", 5)
 //notneededCONNECTION(GND,   "5F", 10)
 CONNECTION(_VRESET,   "5F", 2)
 CONNECTION(_VRESET,   "5F", 3)

 CONNECTION(_32H,      "7B", 2)
 CONNECTION(_128H,     "7B", 1)
 CONNECTION(_256H,     "7B", 13)

 CONNECTION(VCC,       "7C", 4)
 CONNECTION(VCC,       "7C", 2)
 CONNECTION("7D", 11,  "7C", 3)
 CONNECTION("7B", 12,  "7C", 1)
 CONNECTION(VCC,       "7C", 10)
 CONNECTION(VCC,       "7C", 12)
 CONNECTION(_32V,      "7C", 11)
 CONNECTION("4C", 6,   "7C", 13)

 CONNECTION(_64H,      "7D", 12)
 CONNECTION(_16H,      "7D", 13)  //guess!  missing on diagram

 CONNECTION(_HSYNC,    "7L", 9)
 CONNECTION("4A", 3,   "7L", 10)

 CONNECTION("CRYSTAL", 1, "8F", 13)

 CONNECTION(_HBLANKn,  "8K", 9)
 CONNECTION(_VBLANKn,  "8K", 10)

 CONNECTION("7L", 8,   "8L", 11)
 CONNECTION("7L", 8,   "8L", 12)


/* score (page 1, C-7) */

 CONNECTION("1E", 15,  "2L", 1)

 CONNECTION("4H", 8,   "4A", 12)
 CONNECTION("4B", 12,  "4A", 13)

 CONNECTION(_16H,      "4B", 13)

 CONNECTION(_16H,      "4C", 13)
 CONNECTION(_32H,      "4C", 9)
 CONNECTION(_64H,      "4C", 10)
 CONNECTION(_128H,     "4C", 12)

 CONNECTION("7E", 10,  "1E", 14)
 CONNECTION(_1Hn,      "1E", 9)
 CONNECTION(VCC,       "1E", 1)  //not shown

 CONNECTION(_16V,      "4F", 11)
 CONNECTION(_32V,      "4F", 10)
 CONNECTION("7E", 1,   "4F", 9)

 CONNECTION(_32H,      "4H", 11)
 CONNECTION(_64H,      "4H", 10)
 CONNECTION(_128H,     "4H", 9)

 CONNECTION("6C", 11,  "6A", 9)
 CONNECTION(GND,       "6A", 7)
 CONNECTION(GND,       "6A", 6)
 CONNECTION("6C", 9,   "6A", 5)
 CONNECTION("6C", 12,  "6A", 4)
 CONNECTION(GND,       "6A", 3)
 CONNECTION(GND,       "6A", 2)
 CONNECTION("6C", 15,  "6A", 1)
 CONNECTION(_2H,       "6A", 11)
 CONNECTION(_4H,       "6A", 12)
 CONNECTION(_8V,       "6A", 13)
 CONNECTION(_8H,       "6A", 10)

 CONNECTION("6C", 10,  "6B", 9)
 CONNECTION(GND,       "6B", 7)
 CONNECTION(GND,       "6B", 6)
 CONNECTION(GND,       "6B", 5)
 CONNECTION("6C", 14,  "6B", 4)
 CONNECTION(GND,       "6B", 3)
 CONNECTION(GND,       "6B", 2)
 CONNECTION("6C", 13,  "6B", 1)
 CONNECTION(_2V,       "6B", 11)
 CONNECTION(_4V,       "6B", 12)
 CONNECTION(_8V,       "6B", 13)
 CONNECTION(_8H,       "6B", 10)

 CONNECTION(_SCOREWIN, "6C", 4)
 CONNECTION("6D", 4,   "6C", 7)
 CONNECTION("6D", 7,   "6C", 1)
 CONNECTION("6D", 12,  "6C", 2)
 CONNECTION("6D", 9,   "6C", 6)
 CONNECTION(VCC,       "6C", 3)  //not shown
 CONNECTION(VCC,       "6C", 5)  //not shown

 CONNECTION("6F", 12,  "6D", 2)
 CONNECTION("6E", 12,  "6D", 3)
 CONNECTION("6F", 9,   "6D", 5)
 CONNECTION("6E", 9,   "6D", 6)
 CONNECTION("6F", 8,   "6D", 14)
 CONNECTION("6E", 8,   "6D", 13)
 CONNECTION("6F", 11,  "6D", 11)
 CONNECTION("6E", 11,  "6D", 10)
 CONNECTION(_256Hn,    "6D", 1)
 CONNECTION(GND,       "6D", 15)

 CONNECTION("6F", 11,  "6E", 14)
 CONNECTION("6E", 12,  "6E", 1)
 CONNECTION(_START,    "6E", 2)
 CONNECTION(_START,    "6E", 3)
 CONNECTION(GND,       "6E", 6)
 CONNECTION(GND,       "6E", 7)

 CONNECTION("7D", 3,   "6F", 14)
 CONNECTION("6F", 12,  "6F", 1)
 CONNECTION(_START,    "6F", 2)
 CONNECTION(_START,    "6F", 3)
 CONNECTION(GND,       "6F", 6)
 CONNECTION(GND,       "6F", 7)

 CONNECTION(_FISHSCORE, "7D", 2)
 CONNECTION(_ATTRACTn, "7D", 1)
 CONNECTION("4A", 11,  "7D", 5)
 CONNECTION("4C", 8,   "7D", 4)

 CONNECTION(_64V,      "7E", 3)
 CONNECTION(_128V,     "7E", 2)
 CONNECTION("7D", 6,   "7E", 6)
 CONNECTION("4F", 8,   "7E", 5)
 CONNECTION("6A", 15,  "7E", 9)
 CONNECTION("6B", 15,  "7E", 8)

 CONNECTION(_MEDFISH,  "8K", 12)
 CONNECTION(_SMLFISH,  "8K", 13)

 CONNECTION("8K", 11,  "C9A", 2) //556:6 = 555:2
 CONNECTION(VCC,       "C9A", 4) 


/* coin, start, game timer (page 1, B-5) */

 CONNECTION("START", i1, "7B", 4)  //off=lo
 CONNECTION("START", i1, "7B", 5)  //off=lo
 CONNECTION(_ATTRACT,    "7B", 3)

 CONNECTION("COIN", i1,  "7E", 11)  //off=lo
 CONNECTION(_CREDITn,    "7E", 12)

 CONNECTION(VCC,         "8C", 10)
 CONNECTION("COIN", i1,  "8C", 12)  //off=lo
 CONNECTION(_64V,        "8C", 11)
 CONNECTION("COIN", i1,  "8C", 13)  //off=lo
 CONNECTION(VCC,         "8C", 4)
 CONNECTION("8C", 9,     "8C", 2)
 CONNECTION(_64V,        "8C", 3)
 CONNECTION("COIN", i1,  "8C", 1)

 CONNECTION(GND,          "DSW1", 1)  // 1 play per quarter
 CONNECTION(VCC,          "DSW1", 2)  // 2 play per quarter
 CONNECTION("DSW1", 3,    "8D", 4)
 //CONNECTION(VCC, "8D", 4)  // replaced by dipswitch
 CONNECTION(VCC,         "8D", 2)
 CONNECTION(_ATTRACT,    "8D", 3)
 CONNECTION("8C", 6,     "8D", 1)
 CONNECTION(_Q,          "8D", 10)
 CONNECTION("8D", 5,     "8D", 12)
 CONNECTION(_ATTRACT,    "8D", 11)
 CONNECTION("8C", 6,     "8D", 13)

 CONNECTION(_Q,          "8E", 10)
 CONNECTION(VCC,         "8E", 12)
 CONNECTION("8F", 10,    "8E", 11)
 CONNECTION(_STARTn,     "8E", 13)
 CONNECTION("7E", 13,    "8E", 4)
 CONNECTION("7B", 6,     "8E", 2)
 CONNECTION(_256V,       "8E", 3)
 CONNECTION(VCC,         "8E", 1)

 CONNECTION(_ENDGAMEn,   "8F", 11)

 CONNECTION("8D", 8,     "LATCH", 1)   
 CONNECTION("8C", 6,     "LATCH", 2) 
 CONNECTION("LATCH", 3,  "8F", 9)

 CONNECTION(VCC,         "N9A", 4)
 CONNECTION(_STARTn,     "N9A", 2) // 556 pin 6


/* half second clock (page 1 A-8) */

 CONNECTION("C9B", 3,    "4B", 9)  //556:9 = 555:3

 CONNECTION(_HALFSEC,    "7A", 14)
 CONNECTION("7A", 12,    "7A", 1)
 CONNECTION(_START,      "7A", 2)
 CONNECTION(_START,      "7A", 3)

 CONNECTION("7A", 11,    "8A", 12)
 CONNECTION("8A", 10,    "8A", 11)
 CONNECTION("8A", 13,    "8A", 9)
 CONNECTION(_START,      "8A", 8)

 CONNECTION("4B", 8,     "8B", 9)

 CONNECTION(VCC,          "C9B", 4)  //not shown.  556:10 = 555:4 


/* page 2 */

/* small fish motion (page 2 top left) */

  CONNECTION(VCC,      "1L", 7)
  CONNECTION(_CV1,     "1L", 10)
  CONNECTION(_HSYNC1,  "1L", 2)
  CONNECTION("8M", 13, "1L", 3)
  CONNECTION("7L", 6,  "1L", 4)
  CONNECTION(VCC,      "1L", 5)
  CONNECTION(VCC,      "1L", 6)
  CONNECTION("2M", 6,  "1L", 9)
  CONNECTION(VCC,      "1L", 1)  //not shown

  CONNECTION("1L", 15, "1M", 7)
  CONNECTION(VCC,      "1M", 10)
  CONNECTION(_HSYNC1,  "1M", 2)
  CONNECTION(VCC,      "1M", 3)
  CONNECTION(VCC,      "1M", 4)
  CONNECTION(VCC,      "1M", 5)
  CONNECTION(GND,      "1M", 6)
  CONNECTION("2M", 6,  "1M", 9)
  CONNECTION(VCC,      "1M", 1)  //not shown

  CONNECTION("2N", 15, "1N", 7)
  CONNECTION(VCC,      "1N", 10)
  CONNECTION(_1Hn,     "1N", 2)
  CONNECTION(VCC,      "1N", 3)
  CONNECTION(GND,      "1N", 4)
  CONNECTION(GND,      "1N", 5)
  CONNECTION(GND,      "1N", 6)
  CONNECTION("2M", 3,  "1N", 9)
  CONNECTION(VCC,      "1N", 1)  //not shown

  CONNECTION("2N", 15, "2M", 1)
  CONNECTION("1N", 15, "2M", 2)
  CONNECTION("1L", 15, "2M", 5)
  CONNECTION("1M", 15, "2M", 4)

  CONNECTION(VCC,      "2N", 7)
  CONNECTION(VCC,      "2N", 10)
  CONNECTION(_1Hn,     "2N", 2)
  CONNECTION(_VRESETn, "2N", 3)
  CONNECTION("8L", 4,  "2N", 4)
  CONNECTION(VCC,      "2N", 5)
  CONNECTION(VCC,      "2N", 6)
  CONNECTION("2M", 3,  "2N", 9)
  CONNECTION(VCC,      "2N", 1)  //not shown

  CONNECTION("1M", 15, "3M", 10)
  CONNECTION("1L", 11, "3M", 9)

  CONNECTION(VCC,      "6N", 10)
  CONNECTION("6N", 8,  "6N", 12)
  CONNECTION(_HSYNC1,  "6N", 11)
  CONNECTION(VCC,      "6N", 13)

  CONNECTION("8M", 15, "7L", 1)
  CONNECTION("7M", 5,  "7L", 2)
  CONNECTION("8L", 1,  "7L", 4)
  CONNECTION("7M", 9,  "7L", 5)

  CONNECTION(VCC,      "7M", 4)
  CONNECTION(VCC,      "7M", 2)
  CONNECTION("7N", 3,  "7M", 3)
  CONNECTION(_HALFSEC, "7M", 1)
  CONNECTION(VCC,      "7M", 10)
  CONNECTION(VCC,      "7M", 12)
  CONNECTION("7N", 11, "7M", 11)
  CONNECTION(_HALFSEC, "7M", 13)

  CONNECTION(_SMLFISH, "7N", 2)
  CONNECTION(_HBLANK,  "7N", 1)
  CONNECTION(_VBLANK,  "7N", 12)
  CONNECTION(_SMLFISH, "7N", 13)

  CONNECTION("7L", 3,  "8J", 1)

  CONNECTION("8M", 13, "8L", 2)
  CONNECTION("8M", 12, "8L", 3)
  CONNECTION(_VRESETn, "8L", 6)
  CONNECTION("7L", 3,  "8L", 5)

  CONNECTION(_HALFSEC, "8M", 1)
  CONNECTION(_CLOCKn,  "8M", 3)
  CONNECTION(GND,      "8M", 2)
  CONNECTION(_1H,      "8M", 4)
  CONNECTION(GND,      "8M", 14)
  CONNECTION(_2H,      "8M", 6)
  CONNECTION(GND,      "8M", 5)
  CONNECTION(VCC,      "8M", 7)
  CONNECTION(GND,      "8M", 11)
  CONNECTION(VCC,      "8M", 9)  //not shown


/* diver motion (page 2 middle left) */

  CONNECTION("8K", 6,    "3M", 2)
  CONNECTION("8K", 3,    "3M", 1)

  CONNECTION(_SWLEFTn,   "4H", 1)
  CONNECTION(_VRESETn,   "4H", 2)
  CONNECTION(_STOPH,     "4H", 13)

  CONNECTION(VCC,        "4J", 7)
  CONNECTION(VCC,        "4J", 10)
  CONNECTION(_1H,        "4J", 2)
  CONNECTION("6J", 6,    "4J", 3)
  CONNECTION("4H", 12,   "4J", 4)
  CONNECTION(VCC,        "4J", 5)
  CONNECTION(VCC,        "4J", 6)
  CONNECTION("5K", 8,    "4J", 9)
  CONNECTION(VCC,        "4J", 1)  //not shown

  CONNECTION("4J", 15,   "4K", 7)
  CONNECTION(VCC,        "4K", 10)
  CONNECTION(_1H,        "4K", 2)
  CONNECTION(VCC,        "4K", 3)
  CONNECTION(GND,        "4K", 4)
  CONNECTION(GND,        "4K", 5)
  CONNECTION(GND,        "4K", 6)
  CONNECTION("5K", 8,    "4K", 9)
  CONNECTION(_RESETn,    "4K", 1)

  CONNECTION(VCC,        "5H", 7)
  CONNECTION(VCC,        "5H", 10)
  CONNECTION(_HSYNC,     "5H", 2)
  CONNECTION(GND,        "5H", 3)
  CONNECTION("3M", 3,    "5H", 4)
  CONNECTION("8J", 8,    "5H", 5)
  CONNECTION(VCC,        "5H", 6)
  CONNECTION("5K", 11,   "5H", 9)
  CONNECTION(VCC,        "5H", 1)  //not shown

  CONNECTION(VCC,        "5J", 7)
  CONNECTION("5H", 15,   "5J", 10)
  CONNECTION(_HSYNC,     "5J", 2)
  CONNECTION(VCC,        "5J", 3)
  CONNECTION(VCC,        "5J", 4)
  CONNECTION(VCC,        "5J", 5)
  CONNECTION(VCC,        "5J", 6)
  CONNECTION("5K", 11,   "5J", 9)
  CONNECTION(_RESETn,    "5J", 1)

  CONNECTION(_MV4,       "5K", 2)
  CONNECTION(_MV3,       "5K", 1)
  CONNECTION("4J", 15,   "5K", 10)
  CONNECTION("4K", 15,   "5K", 9)
  CONNECTION("CAP35", 2, "5K", 13)
  CONNECTION("6K", 5,    "5K", 12)

  CONNECTION(VCC,        "5L", 5)
  CONNECTION(GND,        "5L", 4)
  CONNECTION(GND,        "5L", 6)
  CONNECTION(GND,        "5L", 3)
  CONNECTION(_MV1,       "5L", 2)
  CONNECTION(_MV2,       "5L", 14)
  CONNECTION("5K", 3,    "5L", 1)

  CONNECTION("7H", 6,    "6J", 2)
  CONNECTION(_256Hn,     "6J", 13)
  CONNECTION(_JOYLEFT,   "6J", 1)
  CONNECTION(_STOPHn,    "6J", 4)
  CONNECTION(_VRESET,    "6J", 5)
  CONNECTION("7L", 11,   "6J", 3)

  CONNECTION(VCC,        "6K", 8)
  CONNECTION("CAP35", 2, "6K", 9)
  CONNECTION(VCC,        "6K", 11)
  CONNECTION(VCC,        "6K", 10)

  CONNECTION(VCC,        "7F", 4)
  CONNECTION(_ATTRACTn,  "7F", 2)
  CONNECTION(_VRESETn,   "7F", 3)
  CONNECTION("7H", 3,    "7F", 1)
  CONNECTION(VCC,        "7F", 10)
  CONNECTION(_ATTRACTn,  "7F", 12)
  CONNECTION(_VRESETn,   "7F", 11)
  CONNECTION("7H", 11,   "7F", 13)

  CONNECTION("6J", 12,   "7H", 2)
  CONNECTION("8H", 6,    "7H", 1)
  CONNECTION(_MEDFISH,   "7H", 4)
  CONNECTION(_HBLANK,    "7H", 5)
  CONNECTION(_VBLANK,    "7H", 9)
  CONNECTION(_MEDFISH,   "7H", 10)
  CONNECTION("8H", 8,    "7H", 13)
  CONNECTION("8H", 12,   "7H", 12)

  CONNECTION(_JOYRIGHT,  "7L", 12)
  CONNECTION(_JOYLEFT,   "7L", 13)

  CONNECTION(_128V,      "8F", 5)

  CONNECTION("7H", 6,    "8H", 3)
  CONNECTION(_256H,      "8H", 5)
  CONNECTION(_JOYRIGHT,  "8H", 4)
  CONNECTION("7H", 8,    "8H", 10)
  CONNECTION("8F", 6,    "8H", 9)
  CONNECTION(_JOYUP,     "8H", 11)
  CONNECTION("7H", 8,    "8H", 13)
  CONNECTION(_128V,      "8H", 2)
  CONNECTION(_JOYDOWN,   "8H", 1)
   
  CONNECTION("8K", 6,    "8J", 9)
  CONNECTION(_JOYLEFT,   "8J", 11)

  CONNECTION(_JOYUP,     "8K", 5)
  CONNECTION(_STOPVn,    "8K", 4)
  CONNECTION(_JOYDOWN,   "8K", 1)
  CONNECTION(_STOPVn,    "8K", 2)

  CONNECTION("5J", 15,   "CAP35", 1)


/* large fish motion (Page 2 lower left) */

  CONNECTION("2K", 15,   "2J", 7)
  CONNECTION(VCC,        "2J", 10)
  CONNECTION(_HSYNC,     "2J", 2)
  CONNECTION(VCC,        "2J", 3)
  CONNECTION(VCC,        "2J", 4)
  CONNECTION(VCC,        "2J", 5)
  CONNECTION(VCC,        "2J", 6)
  CONNECTION("2M", 8,    "2J", 9)
  CONNECTION(VCC,        "2J", 1)  //not shown

  CONNECTION(VCC,        "2K", 7)
  CONNECTION(VCC,        "2K", 10)
  CONNECTION(_HSYNC,     "2K", 2)
  CONNECTION("2L", 4,    "2K", 3)
  CONNECTION("2M", 11,   "2K", 4)
  CONNECTION(GND,        "2K", 5)
  CONNECTION(VCC,        "2K", 6)
  CONNECTION("2M", 8,    "2K", 9)
  CONNECTION(VCC,        "2K", 1)  //not shown

  CONNECTION("3L", 12,   "2L", 3)
  CONNECTION("3H", 6,    "2L", 5)
  CONNECTION(_LV0,       "2L", 13)

  CONNECTION("3M", 6,    "2M", 10)
  CONNECTION("3N", 5,    "2M", 9)
  CONNECTION("2L", 4,    "2M", 13)
  CONNECTION("3L", 10,   "2M", 12)

  CONNECTION(_LV3,       "3H", 1)
  CONNECTION(_LV2,       "3H", 2)
  CONNECTION(_LV1,       "3H", 4)
  CONNECTION("2L", 12,   "3H", 5)

  CONNECTION("3K", 6,    "3J", 3)
  CONNECTION(VCC,        "3J", 4)
  CONNECTION("3K", 7,    "3J", 2)
  CONNECTION(_MV2,       "3J", 10)
  CONNECTION(_MV3,       "3J", 12)
  CONNECTION(_MV4,       "3J", 13)
  CONNECTION(_MV5,       "3J", 15)
  CONNECTION(_LV1,       "3J", 9)
  CONNECTION(_LV2,       "3J", 11)
  CONNECTION(_LV3,       "3J", 14)
  CONNECTION(_LV4,       "3J", 1)

  CONNECTION(VCC,        "3K", 2)
  CONNECTION(VCC,        "3K", 3)
  CONNECTION(VCC,        "3K", 4)
  CONNECTION(VCC,        "3K", 9)
  CONNECTION(VCC,        "3K", 11)
  CONNECTION(VCC,        "3K", 10)
  CONNECTION(VCC,        "3K", 12)
  CONNECTION(_AV4,       "3K", 13)
  CONNECTION(_MV1,       "3K", 15)
  CONNECTION(_BV4,       "3K", 14)
  CONNECTION(_LV0,       "3K", 1)

  CONNECTION("5K", 6,    "3L", 1)
  CONNECTION("4L", 7,    "3L", 3)
  CONNECTION(GND,        "3L", 2)
  CONNECTION(GND,        "3L", 14)
  CONNECTION(GND,        "3L", 5)
  CONNECTION("3J", 6,    "3L", 6)
  CONNECTION(GND,        "3L", 11)
  CONNECTION("3J", 7,    "3L", 7)
  CONNECTION(VCC,        "3L", 9)  //not shown

  CONNECTION("2K", 15,   "3M", 5)
  CONNECTION("2J", 15,   "3M", 4)
  CONNECTION("3N", 5,    "3M", 12)
  CONNECTION("2L", 6,    "3M", 13)

  CONNECTION(VCC,        "3N", 8)
  CONNECTION("3M", 6,    "3N", 9)
  CONNECTION(VCC,        "3N", 11)
  CONNECTION(VCC,        "3N", 10)
  CONNECTION(VCC,        "3N", 1)
  CONNECTION("4M", 15,   "3N", 12)
  CONNECTION(VCC,        "3N", 4)
  CONNECTION(VCC,        "3N", 13)

  CONNECTION("4N", 15,   "4F", 3)
  CONNECTION("4M", 15,   "4F", 4)
  CONNECTION("3N", 3,    "4F", 5)

  CONNECTION(_MH1,       "4L", 10)
  CONNECTION(_MH2,       "4L", 12)
  CONNECTION(_MH3,       "4L", 13)
  CONNECTION(_MH4,       "4L", 15)
  CONNECTION(_LH1,       "4L", 9)
  CONNECTION(_LH2,       "4L", 11)
  CONNECTION(_LH3,       "4L", 14)
  CONNECTION(_LH4,       "4L", 1)
  CONNECTION(VCC,        "4L", 3)  //not shown
  CONNECTION(VCC,        "4L", 4)  //not shown

  CONNECTION("4N", 15,   "4M", 7)
  CONNECTION(VCC,        "4M", 10)
  CONNECTION(_CLOCKn,    "4M", 2)
  CONNECTION(VCC,        "4M", 3)
  CONNECTION(VCC,        "4M", 4)
  CONNECTION(GND,        "4M", 5)
  CONNECTION(GND,        "4M", 6)
  CONNECTION("4F", 6,    "4M", 9)
  CONNECTION(VCC,        "4M", 1)  //not shown

  CONNECTION(VCC,        "4N", 7)
  CONNECTION(VCC,        "4N", 10)
  CONNECTION(_CLOCKn,    "4N", 2)
  CONNECTION("5N", 4,    "4N", 3)
  CONNECTION("5N", 1,    "4N", 4)
  CONNECTION(GND,        "4N", 5)
  CONNECTION(VCC,        "4N", 6)
  CONNECTION("4F", 6,    "4N", 9)
  CONNECTION(VCC,        "4N", 1)  //not shown

  CONNECTION(_HALFSECn,  "5K", 4)
  CONNECTION(_VRESET,    "5K", 5)

  CONNECTION("3L", 15,   "5N", 2)
  CONNECTION("5N", 4,    "5N", 3)
  CONNECTION(_VRESET,    "5N", 5)
  CONNECTION("6N", 5,    "5N", 6)

  CONNECTION(VCC,        "6N", 4)
  CONNECTION(_VRESET,    "6N", 2)
  CONNECTION(_HSYNC,     "6N", 3)
  CONNECTION("7N", 6,    "6N", 1)

  CONNECTION("N8", 3,    "7N", 4)
  CONNECTION("N8", 3,    "7N", 5)

  CONNECTION("3L", 15,   "8J", 13)

  CONNECTION(_STARTn,    "N8", 2)
  CONNECTION(VCC,        "N8", 4)  //not shown


/* Reset (Page 2 F-5) */

 CONNECTION("2L", 10,   "1J", 3)
 CONNECTION(_AV3,       "1J", 5)
 CONNECTION(_AV2,       "1J", 2)
 CONNECTION(_AV1,       "1J", 6)
 CONNECTION(_MEDFISH,   "1J", 11)
 CONNECTION("2L", 8,    "1J", 4)
 CONNECTION(_COMPBLANK, "1J", 12)
 CONNECTION(_AH3,       "1J", 1)

 CONNECTION(_AH4,       "2L", 9)
 CONNECTION(_AV4,       "2L", 11)

 CONNECTION("1J", 8,    "6H", 10)
 CONNECTION(_CATCH,     "6H", 12)
 CONNECTION(_HALFSEC,   "6H", 11)
 CONNECTION(VCC,        "6H", 13)


/* Catch (page 2 F-4) */

 CONNECTION(VCC,        "6H", 4)
 CONNECTION("7J", 11,   "6H", 2)
 CONNECTION(_HALFSEC,   "6H", 3)
 CONNECTION(VCC,        "6H", 1)

 CONNECTION(_LRGFISH,   "6J", 11)
 CONNECTION(_MEDFISH,   "6J", 9)
 CONNECTION("6H", 5,    "6J", 10)

 CONNECTION("8J", 4,    "7J", 7)
 CONNECTION(VCC,        "7J", 10)
 CONNECTION(_HALFSEC,   "7J", 2)
 CONNECTION(VCC,        "7J", 3)
 CONNECTION(VCC,        "7J", 4)
 CONNECTION(VCC,        "7J", 5)
 CONNECTION(VCC,        "7J", 6)
 CONNECTION("6J", 8,    "7J", 1)
 CONNECTION(VCC,        "7J", 9)  //not shown

 CONNECTION("7J", 15,   "8J", 3)

 CONNECTION("7J", 11,   "8L", 8)
 CONNECTION("7J", 12,   "8L", 9)


/* catch connection (page 2 G-6) */

 CONNECTION("4H", 6,    "1F", 10)
 CONNECTION("1H", 7,    "1F", 9)
 CONNECTION("1H", 12,   "1F", 4)
 CONNECTION("4H", 6,    "1F", 5)

 CONNECTION("1K", 4,    "1H", 3)
 CONNECTION(_AV4,       "1H", 2)
 CONNECTION("1K", 7,    "1H", 6)
 CONNECTION(_AV3,       "1H", 5)
 CONNECTION("1K", 12,   "1H", 13)
 CONNECTION(_AV2,       "1H", 14)
 CONNECTION("1K", 9,    "1H", 10)
 CONNECTION(_AV1,       "1H", 11)
 CONNECTION(GND,        "1H", 15)
 CONNECTION(_LD1Cn,     "1H", 1)

 CONNECTION(_CV4,       "1K", 3)
 CONNECTION(_BV4,       "1K", 2)
 CONNECTION(_CV3,       "1K", 6)
 CONNECTION(_BV3,       "1K", 5)
 CONNECTION(_CV2,       "1K", 13)
 CONNECTION(_BV2,       "1K", 14)
 CONNECTION(_CV1,       "1K", 10)
 CONNECTION(_BV1,       "1K", 11)
 CONNECTION(GND,        "1K", 15)
 CONNECTION(_LD2Cn,     "1K", 1)

 CONNECTION("8J", 6,    "4H", 4)
 CONNECTION(_LD1Cn,     "4H", 5)
 CONNECTION("6K", 3,    "4H", 3)

 CONNECTION(VCC,        "6K", 1)
 CONNECTION(_256V,      "6K", 12)
 CONNECTION(VCC,        "6K", 4)
 CONNECTION(VCC,        "6K", 13)

 CONNECTION(_CATCH,     "8J", 5)


/* image generation (page 2, top right)  */

 CONNECTION(_D1,        "1A", 3)
 CONNECTION(_D8,        "1A", 2)
 CONNECTION(_D2,        "1A", 6)
 CONNECTION(_D7,        "1A", 5)
 CONNECTION(_D3,        "1A", 13)
 CONNECTION(_D6,        "1A", 14)
 CONNECTION(_D4,        "1A", 10)
 CONNECTION(_D5,        "1A", 11)
 CONNECTION("6L", 9,    "1A", 1)
 CONNECTION(GND,        "1A", 15)

 CONNECTION(_D5,        "1B", 3)
 CONNECTION(_D4,        "1B", 2)
 CONNECTION(_D6,        "1B", 6)
 CONNECTION(_D3,        "1B", 5)
 CONNECTION(_D7,        "1B", 13)
 CONNECTION(_D2,        "1B", 14)
 CONNECTION(_D8,        "1B", 10)
 CONNECTION(_D1,        "1B", 11)
 CONNECTION("6L", 9,    "1B", 1)
 CONNECTION(GND,        "1B", 15) 

 CONNECTION(GND,        "1C", 11)
 CONNECTION(_D4,        "1C", 7)
 CONNECTION(GND,        "1C", 5)
 CONNECTION(_D3,        "1C", 6)
 CONNECTION(GND,        "1C", 14)
 CONNECTION(_D2,        "1C", 4)
 CONNECTION(GND,        "1C", 2)
 CONNECTION(_D1,        "1C", 3)
 CONNECTION("4A", 8,    "1C", 1)
 CONNECTION(VCC,        "1C", 9)  //not shown 

 CONNECTION(_XD1,       "XA", 3)  //temp fix
 CONNECTION(_XD8,       "XA", 2)  //temp fix
 CONNECTION(_XD2,       "XA", 6)  //temp fix
 CONNECTION(_XD7,       "XA", 5)  //temp fix
 CONNECTION(_XD3,       "XA", 13) //temp fix
 CONNECTION(_XD6,       "XA", 14) //temp fix
 CONNECTION(_XD4,       "XA", 10) //temp fix
 CONNECTION(_XD5,       "XA", 11) //temp fix
 CONNECTION("6L", 9,    "XA", 1)  //temp fix
 CONNECTION(GND,        "XA", 15) //temp fix

 CONNECTION(_XD5,       "XB", 3)  //temp fix
 CONNECTION(_XD4,       "XB", 2)  //temp fix
 CONNECTION(_XD6,       "XB", 6)  //temp fix
 CONNECTION(_XD3,       "XB", 5)  //temp fix
 CONNECTION(_XD7,       "XB", 13) //temp fix
 CONNECTION(_XD2,       "XB", 14) //temp fix
 CONNECTION(_XD8,       "XB", 10) //temp fix
 CONNECTION(_XD1,       "XB", 11) //temp fix
 CONNECTION("6L", 9,    "XB", 1)  //temp fix
 CONNECTION(GND,        "XB", 15) //temp fix

 CONNECTION(GND,        "XC", 11) //temp fix
 CONNECTION(_XD4,       "XC", 7)  //temp fix
 CONNECTION(GND,        "XC", 5)  //temp fix
 CONNECTION(_XD3,       "XC", 6)  //temp fix
 CONNECTION(GND,        "XC", 14) //temp fix
 CONNECTION(_XD2,       "XC", 4)  //temp fix
 CONNECTION(GND,        "XC", 2)  //temp fix
 CONNECTION(_XD1,       "XC", 3)  //temp fix
 CONNECTION("4A", 8,    "XC", 1)  //temp fix
 CONNECTION(VCC,        "XC", 9)  //not shown

 CONNECTION(_V4,           "1DA", 3)
 CONNECTION(_V3,           "1DA", 4)
 CONNECTION(_V2,           "1DA", 7)
 CONNECTION(_V1,           "1DA", 6)

 CONNECTION(_V4,           "1DB", 3)
 CONNECTION(_V3,           "1DB", 4)
 CONNECTION(_V2,           "1DB", 7)
 CONNECTION(_V1,           "1DB", 6)

#ifndef SPEED_HACK
 CONNECTION("1E", 12,      "1DA", 15)
 CONNECTION("1E", 2,       "1DA", 1)
 CONNECTION("1E", 5,       "1DA", 2)

 CONNECTION("1E", 7,       "1DA", 5)
 CONNECTION(_SHARKENABLEn, "1DA", 14)
 CONNECTION(_SHARKENABLEn, "1DA", 13)

 CONNECTION("N9B", 3,      "1DB", 15)  //556:9 = 555:3
 CONNECTION("1E", 2,       "1DB", 1)
 CONNECTION("1E", 5,       "1DB", 2)

 CONNECTION("1E", 7,       "1DB", 5)
 CONNECTION(_DIVERENABLEn, "1DB", 14)
 CONNECTION(_DIVERENABLEn, "1DB", 13)
#else
 CONNECTION("XE", 12,      "1DA", 15)
 CONNECTION("XE", 2,       "1DA", 1)
 CONNECTION("XE", 5,       "1DA", 2)

 CONNECTION("XE", 7,       "1DA", 5)
 CONNECTION(_SHARKENABLEn, "1DA", 14)
 // Speed Hack - Enable ROM only when LVWIN or CVWIN are high
 CONNECTION(_LVWIN,        "3E", 2)
 CONNECTION(_CVWIN,        "3E", 3)
 CONNECTION("3E", 1,       "1DA", 13)

 CONNECTION("N9B", 3,      "1DB", 15)  //556:9 = 555:3
 CONNECTION("XE", 2,       "1DB", 1)
 CONNECTION("XE", 5,       "1DB", 2)

 CONNECTION("XE", 7,       "1DB", 5)
 CONNECTION(_DIVERENABLEn, "1DB", 14)
 // Speed Hack - Enable ROM only when AVWIN is high
 CONNECTION(_AVWIN, "XF", 11)
 CONNECTION("XF", 10, "1DB", 13)

 CONNECTION(_AVWIN, "3OR", 1)
 CONNECTION(_CVWIN, "3OR", 2)
 CONNECTION(_LVWIN, "3OR", 3)

 CONNECTION("3OR", 4,      "XE", 1)
 CONNECTION(_16H,          "XE", 3)
 CONNECTION(_8H,           "XE", 4)
 CONNECTION(_4H,           "XE", 6)
 CONNECTION("1F", 11,      "XE", 13)
 CONNECTION(_1Hn,          "XE", 9)
#endif

 CONNECTION(_16H,          "1E", 3)
 CONNECTION(_8H,           "1E", 4)
 CONNECTION(_4H,           "1E", 6)
 CONNECTION("1F", 11,      "1E", 13)
 //CONNECTION(_1Hn,        "1E", 9)  connected on page 1

 CONNECTION("3D", 3,       "1F", 12)
 CONNECTION("7K", 5,       "1F", 13)

 CONNECTION(GND,           "2A", 10)
 CONNECTION("XB", 9,       "2A", 11)
 CONNECTION("XB", 12,      "2A", 12)
 CONNECTION("XB", 7,       "2A", 13)
 CONNECTION("XB", 4,       "2A", 14)
 CONNECTION("XA", 9,       "2A", 3)
 CONNECTION("XA", 12,      "2A", 4)
 CONNECTION("XA", 7,       "2A", 5)
 CONNECTION("XA", 4,       "2A", 6)
 CONNECTION(_CLOCKn,       "2A", 2)
 CONNECTION("3A", 4,       "2A", 1)
 CONNECTION("7K", 8,       "2A", 15)

 CONNECTION("2A", 9,       "2B", 10)
 CONNECTION("XB", 9,       "2B", 11)
 CONNECTION("XB", 12,      "2B", 12)
 CONNECTION("XB", 7,       "2B", 13)
 CONNECTION("XB", 4,       "2B", 14)
 CONNECTION("XA", 9,       "2B", 3)
 CONNECTION("XA", 12,      "2B", 4)
 CONNECTION("XA", 7,       "2B", 5)
 CONNECTION("XA", 4,       "2B", 6)
 CONNECTION(_CLOCKn,       "2B", 2)
 CONNECTION("3B", 4,       "2B", 1)
 CONNECTION("7K", 8,       "2B", 15)

 CONNECTION("2B", 9,       "2C", 10)
 CONNECTION("XB", 9,       "2C", 11)
 CONNECTION("XB", 12,      "2C", 12)
 CONNECTION("XB", 7,       "2C", 13)
 CONNECTION("XB", 4,       "2C", 14)
 CONNECTION("XA", 9,       "2C", 3)
 CONNECTION("XA", 12,      "2C", 4)
 CONNECTION("XA", 7,       "2C", 5)
 CONNECTION("XA", 4,       "2C", 6)
 CONNECTION(_CLOCKn,       "2C", 2)
 CONNECTION("3A", 7,       "2C", 1)
 CONNECTION("7K", 8,       "2C", 15) 
 
 CONNECTION(GND,          "2D", 10)
 CONNECTION("1B", 9,      "2D", 11)
 CONNECTION("1B", 12,     "2D", 12)
 CONNECTION("1B", 7,      "2D", 13)
 CONNECTION("1B", 4,      "2D", 14)
 CONNECTION("1A", 9,      "2D", 3)
 CONNECTION("1A", 12,     "2D", 4)
 CONNECTION("1A", 7,      "2D", 5)
 CONNECTION("1A", 4,      "2D", 6)
 CONNECTION(_CLOCKn,      "2D", 2)
 CONNECTION("3B", 13,     "2D", 1)
 CONNECTION("3H", 8,      "2D", 15)

 CONNECTION("2F", 9,      "2E", 10)
 CONNECTION("1B", 9,      "2E", 11)
 CONNECTION("1B", 12,     "2E", 12)
 CONNECTION("1B", 7,      "2E", 13)
 CONNECTION("1B", 4,      "2E", 14)
 CONNECTION("1A", 9,      "2E", 3)
 CONNECTION("1A", 12,     "2E", 4)
 CONNECTION("1A", 7,      "2E", 5)
 CONNECTION("1A", 4,      "2E", 6)
 CONNECTION("3F", 5,      "2E", 2)
 CONNECTION("3A", 9,      "2E", 1)
 CONNECTION("3F", 8,      "2E", 15)

 CONNECTION("2H", 9,      "2F", 10)
 CONNECTION("1B", 9,      "2F", 11)
 CONNECTION("1B", 12,     "2F", 12)
 CONNECTION("1B", 7,      "2F", 13)
 CONNECTION("1B", 4,      "2F", 14)
 CONNECTION("1A", 9,      "2F", 3)
 CONNECTION("1A", 12,     "2F", 4)
 CONNECTION("1A", 7,      "2F", 5)
 CONNECTION("1A", 4,      "2F", 6)
 CONNECTION("3F", 5,      "2F", 2)
 CONNECTION(_LD2Bn,       "2F", 1)
 CONNECTION("3F", 8,      "2F", 15)

 CONNECTION(GND,          "2H", 10)
 CONNECTION("1B", 9,      "2H", 11)
 CONNECTION("1B", 12,     "2H", 12)
 CONNECTION("1B", 7,      "2H", 13)
 CONNECTION("1B", 4,      "2H", 14)
 CONNECTION("1A", 9,      "2H", 3)
 CONNECTION("1A", 12,     "2H", 4)
 CONNECTION("1A", 7,      "2H", 5)
 CONNECTION("1A", 4,      "2H", 6)
 CONNECTION("3F", 5,      "2H", 2)
 CONNECTION("3A", 12,     "2H", 1)
 CONNECTION("3F", 8,      "2H", 15)

 CONNECTION("6L", 9,      "3A", 1)
 CONNECTION("3B", 3,      "3A", 3)
 CONNECTION("3B", 5,      "3A", 2)
 CONNECTION("3B", 5,      "3A", 6)
 CONNECTION("3B", 3,      "3A", 5)
 CONNECTION("3B", 10,     "3A", 13)
 CONNECTION("3B", 12,     "3A", 14)
 CONNECTION("3B", 12,     "3A", 10)
 CONNECTION("3B", 10,     "3A", 11)
 CONNECTION(GND,          "3A", 15)

 CONNECTION(_HRESETn,     "3B", 9)
 CONNECTION(VCC,          "3B", 1)
 CONNECTION(VCC,          "3B", 2)
 CONNECTION("4B", 2,      "3B", 8)

 CONNECTION("2C", 7,      "3C", 9)
 CONNECTION("7K", 8,      "3C", 8)
 CONNECTION(_HSYNC1,      "3C", 5)
 CONNECTION(_RESET,       "3C", 6)
 CONNECTION(_HSYNC1,      "3C", 3)
 CONNECTION(_FISHSCORE,   "3C", 2)
 CONNECTION("2D", 7,      "3C", 12)
 CONNECTION("3H", 8,      "3C", 11)

 CONNECTION("3E", 4,      "3D", 2)
 CONNECTION(_BV5,         "3D", 1)
 CONNECTION("3E", 10,     "3D", 5)
 CONNECTION(_HBLANKn,     "3D", 4)
 CONNECTION("3C", 10,     "3D", 9)
 CONNECTION("3C", 4,      "3D", 10)
 CONNECTION("3C", 13,     "3D", 12)
 CONNECTION("3C", 1,      "3D", 13)

 CONNECTION(_8H,         "3E", 6)
 CONNECTION(_16H,        "3E", 5)
 CONNECTION("2E", 7,     "3E", 9)
 CONNECTION("3F", 8,     "3E", 8)

 CONNECTION("3F", 9,     "3F", 4)
 CONNECTION("3F", 6,     "3F", 2)
 CONNECTION(_CLOCKn,     "3F", 3)
 CONNECTION(VCC,         "3F", 1)
 CONNECTION(VCC,         "3F", 10)
 CONNECTION(_LVWIN,      "3F", 12)
 CONNECTION(_LHWIN,      "3F", 11)
 CONNECTION(_HRESETn,    "3F", 13)

 CONNECTION(_CH3,        "3H", 13)
 CONNECTION(_CH4,        "3H", 12)
 CONNECTION(_CVWIN,      "3H", 9)
 CONNECTION(_CHWIN,      "3H", 10)

 CONNECTION(_2H,         "4A", 10)
 CONNECTION(_4Hn,        "4A", 9)

 CONNECTION(_4H,         "4B", 1)

 CONNECTION("7N", 8,     "5N", 8)
 CONNECTION("7N", 8,     "5N", 9)

 CONNECTION(_VAEQB,      "6L", 3)
 CONNECTION(_VAEQB,      "6L", 4)
 CONNECTION(_VAEQB,      "6L", 5)
 CONNECTION(VCC,         "6L", 6)
 CONNECTION(_SMLFISHDIR, "6L", 13)
 CONNECTION(VCC,         "6L", 12)
 CONNECTION("6M", 9,     "6L", 11)
 CONNECTION("6M", 6,     "6L", 10)
 CONNECTION(_LD1Cn,      "6L", 14)
 CONNECTION(_LD2Cn,      "6L", 2)
 CONNECTION(GND,         "6L", 15)
 CONNECTION(GND,         "6L", 1)

 CONNECTION(VCC,         "6M", 4)
 CONNECTION(_ATTRACTn,   "6M", 2)
 CONNECTION(_JOYRIGHT,   "6M", 3)
 CONNECTION(_SWLEFTn,    "6M", 1)
 CONNECTION(VCC,         "6M", 10)
 CONNECTION(_LRGFISHDIR, "6M", 12)
 CONNECTION(_HALFSEC,    "6M", 11)
 CONNECTION(VCC,         "6M", 13)

 CONNECTION(VCC,         "7K", 4)
 CONNECTION(_LH3,        "7K", 2)
 CONNECTION("6L", 7,     "7K", 3)
 CONNECTION(_HALFSEC,    "7K", 1)
 CONNECTION(VCC,         "7K", 10)
 CONNECTION(_AVWIN,      "7K", 12)
 CONNECTION(_AHWIN,      "7K", 11)
 CONNECTION(_MH3,        "7K", 13)

 CONNECTION("3A", 4,     "7N", 9)
 CONNECTION("3A", 7,     "7N", 10)

 CONNECTION(VCC,         "N9B", 4)  //not shown.  556:10 = 555:4 


/* video */

CONNECTION("VIDEO", 1, _SCORE) 
CONNECTION("VIDEO", 2, _DIVERVID)  //medium fish=diver=player 
CONNECTION("VIDEO", 3, _LRGFISHVID)  //large fish=shark
CONNECTION("VIDEO", 4, _SMLFISHVID) 
CONNECTION("VIDEO", 5, VCC) 
CONNECTION("VIDEO", Video::VBLANK_PIN, "4A", 3)
CONNECTION("VIDEO", Video::HBLANK_PIN, "5A", 6) 

//CONNECTION("VIDEO", 2, _MEDFISH)  //medium fish=diver=player 
//CONNECTION("VIDEO", 3, _LRGFISH)  //large fish=shark
//CONNECTION("VIDEO", 4, _SMLFISH)
//CONNECTION("VIDEO", Video::VBLANK_PIN, _VBLANK)
//CONNECTION("VIDEO", Video::HBLANK_PIN, _HBLANK) 


/* Invert joystick so that pressed=HI and unpressed=LO */
CONNECTION("JOYSTICK", Joystick::LEFT,    "XF", 1)
CONNECTION("JOYSTICK", Joystick::RIGHT,   "XF", 3)
CONNECTION("JOYSTICK", Joystick::UP,      "XF", 5)
CONNECTION("JOYSTICK", Joystick::DOWN,    "XF", 9)

/* Audio */
/*  dissapointing without the analog part
CONNECTION("7A", 9,      "7B", 9)
CONNECTION("7A", 12,     "7B", 11)
CONNECTION(_HALFSECn,    "7B", 10)

CONNECTION(_CATCH,       "C10A", 4)

CONNECTION("7A", 12,     "C10B", 5)
CONNECTION(_FISHSCORE,   "C10B", 4)

CONNECTION("AUDIO", 1,   "7B", 8)
CONNECTION("AUDIO", 2,   "C10A", 3)
CONNECTION("AUDIO", 3,   "C10B", 3)
*/


#ifdef DEBUG

//CONNECTION(_HBLANK, "LOG1", 1)
//CONNECTION(_VBLANK, "LOG1", 2)
//CONNECTION(_DIVERENABLEn, "LOG1", 3)

#endif


CIRCUIT_LAYOUT_END

