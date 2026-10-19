/* Highway by Atari (1975) - REV C*/

//Last Update 03/01/2014

#include "../circuit_desc.h"
#include "../circuit.h"
#include "highway.h"

#define DEBUG
#undef DEBUG

#ifdef DEBUG
static VcdLogDesc vcd_log_desc
(
    "output_highway.vcd",
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
    16, "P",
    17, "Q",
    18, "R",
    19, "S",
    20, "T",
    21, "U",
    22, "V",
    23, "W",
    24, "X",
    25, "Y",
    26, "Z"
);
#endif

//static Astable555Desc d9_555_desc(K_OHM(50.0), K_OHM(3.3), U_FARAD(0.1));

static Astable555Desc e9_555_desc(K_OHM(510.0), K_OHM(470.0), U_FARAD(10.0));
static PotentimeterAstable555Desc e9pot_desc("playtime", "Play Time", K_OHM(510.0), K_OHM(10.0), K_OHM(1010.0), e9_555_desc);

static CapacitorDesc capa28_desc(P_FARAD(470));
static CapacitorDesc capc36_desc(P_FARAD(100));
static CapacitorDesc capd34_desc(P_FARAD(100));
static CapacitorDesc capd63_desc(N_FARAD(10));
static CapacitorDesc capf68_desc(P_FARAD(100));
static CapacitorDesc capf77_desc(P_FARAD(100));
static CapacitorDesc capf96_desc(N_FARAD(1));
static CapacitorDesc cap10_desc(N_FARAD(1));
static CapacitorDesc cap11_desc(N_FARAD(1));
static CapacitorDesc cap12_desc(P_FARAD(100));
static CapacitorDesc cap14_desc(N_FARAD(1), OHM(180));  //RC

static Dipswitch4SP4TDesc sw_ext_play("ext_play", "dice_dipswitch16_1", "Extended Play Score", 6, "None",
                                      "10", "20", "30", "40", "50", "60", "70", "80",
                                      "90", "100", "110", "120", "130", "140", "150");
static DipswitchDesc sw_k4l4("concurrent_traffic", "dice_dipswitch_1", "Concurrent Traffic", 0, "Regular", "Double");
static DipswitchDesc sw_h6n4("opposing_traffic", "dice_dipswitch_2", "Opposing Traffic", 0, "Regular", "Double");

static Ram2533Desc e1_desc;

static Wheel1Desc wheel1_desc;

static BufferDesc buf1_desc(DELAY_NS(40.0), DELAY_NS(40.0));
static BufferDesc buf2_desc(DELAY_NS(25.0), DELAY_NS(25.0));
static BufferDesc buf3_desc(DELAY_NS(25.0), DELAY_NS(25.0));

static VIDEO_DESC( highway )
    VIDEO_RESISTANCE(1, OHM(470))  
    VIDEO_RESISTANCE(2, OHM(800)) 
    VIDEO_CONTRAST(1.0)
    VIDEO_RETRO_V_SIZE(252)
VIDEO_DESC_END

static MixerDesc mixer_desc({OHM(220.0)}, 0, 0, U_FARAD(0.1)); 

static HighwaySpeedDesc speed_desc;

static AUDIO_DESC( highway )
    AUDIO_GAIN(20.0)
    AUDIO_SPEAKER_CONFIG(MONO) 
AUDIO_DESC_END

static INPUT_DESC( highway )
    INPUT_INFO(WHEEL1_INPUT, "Steer Car")
    INPUT_INFO(BUTTONS1_INPUT, {{ 1 }}, "Accelerate")
    INPUT_INFO(COIN_INPUT, {{ 1 }}, "Insert Coin and Start Game")
INPUT_DESC_END

//**************************************************************


CIRCUIT_LAYOUT( hiway )

/* * * CHIPS * * */

//some capacitors are named on the diagram and some are not
CHIP("CAP_A2_8",  CAPACITOR, &capa28_desc)
CHIP("CAP_C3_6",  CAPACITOR, &capc36_desc)
CHIP("CAP_D3_4",  CAPACITOR, &capd34_desc)
CHIP("CAP_D6_3",  CAPACITOR, &capd63_desc)
CHIP("CAP_F6_8",  CAPACITOR, &capf68_desc)
CHIP("CAP_F7_7",  CAPACITOR, &capf77_desc)
CHIP("CAP_F9_6",  CAPACITOR, &capf96_desc)
CHIP("CAP10",     CAPACITOR, &cap10_desc)
CHIP("CAP11",     CAPACITOR, &cap11_desc)
CHIP("CAP12",     CAPACITOR, &cap12_desc)
CHIP("CAP14",     CAPACITOR, &cap14_desc)

CHIP("A1", 7400)
CHIP("A2", 7404)
CHIP("A3", 7405)  //unused a3.13->12
CHIP("A4", 7400)
CHIP("A5", 7427)
CHIP("A6", 7410)
CHIP("A7", 7493)
CHIP("A8", 7493)
//CHIP("A9", LM380)

CHIP("B1", 7420)
CHIP("B2", 7493)
CHIP("B3", 7486)
CHIP("B4", 74193) //unused 12,13
CHIP("B5", 74193)
CHIP("B6", 7420)
CHIP("B7", 7402) //unused 11,12->13
CHIP("B8", 7400)
CHIP("B9", 7406) //unused 3->4,13->12

CHIP("C1", 74107) 
CHIP("C2", 7493)
CHIP("C3", 7486)
CHIP("C4", 74193)
CHIP("C5", 74193)
CHIP("C6", 7493)
CHIP("C7", 74145) //unused 1, 10, 11
CHIP("C8", 7474)
CHIP("C9", 7492) //unused 8 - sound

CHIP("D1", 7402) //unused 2,3->1
CHIP("D2", 7404) //unused 12 =1H_n ?
CHIP("D3", 7405) 
CHIP("D4", 7400)
CHIP("D5", 7410)
CHIP("D6", 7400)
CHIP("D7", 7404)
CHIP("D8", 7420)
//CHIP("D9", 555_Astable , &d9_555_desc)

CHIP("E1", 2533, &e1_desc)
CHIP("E2", 7410)
CHIP("E3", 7404)
CHIP("E4", 7474) //unused 6
CHIP("E5", 7404)
CHIP("E6", 7486) //unused 6
CHIP("E7", 74193)
CHIP("E8", 7493)
CHIP("E9", 555_Astable , &e9_555_desc)

CHIP("F1", 7402)
CHIP("F2", 7486)
CHIP("F3", 7493)
CHIP("F4", 7400)
CHIP("F5", 74164)
CHIP("F6", 7400)
CHIP("F7", 74279)
CHIP("F8", 7400) //unused 8
CHIP("F9", 74132) 

CHIP("H1", 7420)
CHIP("H2", 7430)
CHIP("H3", 7493)
CHIP("H4", 7410) //unused 1,2,13->12
CHIP("H5", 74165) //unused 7
CHIP("H6", 7474) //unused 6, 8
CHIP("H7", 7402)
CHIP("H8", 7404)
CHIP("H9", 7474) //unused 5

CHIP("J1", 7474)
//CHIP("J2", none)
CHIP("J3", 7404)
CHIP("J4", 7493)
CHIP("J5", 7486) //unused 4,5->6
CHIP("J6", 7404)
CHIP("J7", 9316) //unused 14=_2M?
CHIP("J8", 74193)
CHIP("J9", 7405) //unused 1->2, skipped 5->6, 9->8, 

CHIP("K1", 7420)
//CHIP("K2", none)  this spot is used for dipswitches
CHIP("K3", 7493)
CHIP("K4", 7493)
CHIP("K5", 7420)
CHIP("K6", 7400)
CHIP("K7", 9316) //unused 15
CHIP("K8", 7486)
CHIP("K9", 7400)

CHIP("L1", 9312) //unused 15
CHIP("L2", 7493)
CHIP("L3", 7400)
CHIP("L4", 7420)
CHIP("L5", 7404)
CHIP("L6", 74107)
CHIP("L7", 7410)
CHIP("L8", 7400)
CHIP("L9", 7404)  //skipped 1->2, 3->4, 13->12

CHIP("M1", 7448)
CHIP("M2", 9322)
CHIP("M3", 7493)
CHIP("M4", 7493)
CHIP("M5", 7420)
CHIP("M6", 7486) //unused 4,5->6
CHIP("M7", 7493)
CHIP("M8", 74107) //unused 1,4,12,13->2,3
CHIP("M9", 74145) //unused 10, 11

CHIP("N1", 9312) //unused 15
CHIP("N2", 7490)
CHIP("N3", 7410) //unused 1,2,13->12
CHIP("N4", 7400)
CHIP("N5", 7410)
CHIP("N6", 7408) //unused 3,11
CHIP("N7", 7493) //unused 12
CHIP("N8", 74107) //unused 6
CHIP("N9", 7493)

CHIP("P1", 7427) //unused 6,12
//CHIP("P2", none)
CHIP("P3", 74279) //unused 1,2,3->4
CHIP("P4", 7404) //unused 3->4, 5->6
//CHIP("P5", none)
//CHIP("P6", none)
//CHIP("P7", none)
//CHIP("P8", none)
//CHIP("P9", none)

//CHIP("LATCH",      LATCH)

CHIP("CRYSTAL",         CLOCK_12_096_MHZ)
CHIP("COIN_IN",         COIN_INPUT)
CHIP("STEERINGWHEEL",   WHEEL1_INPUT, &wheel1_desc)  
CHIP("ACCELERATOR",     BUTTONS1_INPUT)

CHIP("E9POT",           POT_555_ASTABLE, &e9pot_desc)
POTENTIOMETER_CONNECTION("E9POT", "E9")

CHIP("SPEED1", HIGHWAY_SPEED_CONTROL, &speed_desc)

//CHIP("MIXER", MIXER, &mixer_desc)

CHIP("SW_EXT_PLAY",  DIPSWITCH_4SPST, &sw_ext_play)
CHIP("SW_K4L4",         DIPSWITCH, &sw_k4l4)
CHIP("SW_H6N4",         DIPSWITCH, &sw_h6n4)

//these chips simulate open collector connections - essentially an "AND"
//CHIP("CR1_CONNECT",     WIRED_AND, 9)
CHIP("CR1_CONNECT_A",   WIRED_AND, 3)
CHIP("CR1_CONNECT_B",   WIRED_AND, 3)
CHIP("CR1_CONNECT_C",   WIRED_AND, 3)
CHIP("CR1_CONNECT",     WIRED_AND, 3)
CHIP("C7_CONNECT1",     WIRED_AND, 4)
CHIP("C7_CONNECT2",     WIRED_AND, 2)
CHIP("M9_CONNECT1",     WIRED_AND, 5)
CHIP("M9_CONNECT2",     WIRED_AND, 2)

CHIP("BUF1", BUFFER, &buf1_desc) // Delay road reset. TODO: Why is this needed?
CHIP("BUF2", BUFFER, &buf2_desc) // Prevent glitches on F6.3 from setting latch F7.
CHIP("BUF3", BUFFER, &buf3_desc) // Prevent glitches on SP_n from clocking C6.

OPTIMIZATION_HINT("CR1_CONNECT", 64, 64)
OPTIMIZATION_HINT("CR1_CONNECT_C", 32, 64)
OPTIMIZATION_HINT("M7", 8, 64)
OPTIMIZATION_HINT("N7", 8, 64)
OPTIMIZATION_HINT("K9", 8, 64)
OPTIMIZATION_HINT("J9", 8, 64)
OPTIMIZATION_HINT("P1", 16, 64)
OPTIMIZATION_HINT("E4", 8, 64)
OPTIMIZATION_HINT("B1", 32, 64)
OPTIMIZATION_HINT("M5", 32, 64)
OPTIMIZATION_HINT("N3", 32, 64)
OPTIMIZATION_HINT("N4", 32, 64)
OPTIMIZATION_HINT("L8", 16, 64)
OPTIMIZATION_HINT("M6", 32, 64)


VIDEO(highway)
AUDIO(highway)
INPUT(highway)

#ifdef DEBUG
	CHIP("LOG1", VCD_LOG, &vcd_log_desc)
#endif

/* * * SIGNALS * * */

//page1
//timing (DD 6)
 #define _1H                 "C2", 12
 #define _2H                 "C2", 9
 #define _4H                 "C2", 8
 #define _8H                 "C2", 11
 #define _16H                "B2", 12
 #define _32H                "B2", 9
 #define _64H                "B2", 8
 #define _128H               "B2", 11
 #define _1H_n               "D2", 12
 #define _2H_n               "D2", 8
 #define _4H_n               "P4", 8
 #define _8H_n               "P4", 10
 #define _16H_n              "A2", 2
 #define _32H_n              "A2", 6
 #define _64H_n              "CAP_A2_8", 2
 #define _128H_n             "A2", 4
 #define _A1                 "C1", 2
 #define _A1_n               "C1", 3
 #define _A0_n               "A1", 6
 #define _A0                 "A2", 12
 #define _A2                 "C1", 6
 #define _HSYNC              "E3", 8
 #define _HBLANK             "P4", 2
 #define _1V                 "F3", 12
 #define _2V                 "F3", 9
 #define _4V                 "F3", 8
 #define _8V                 "F3", 11
 #define _16V                "H3", 12
 #define _32V                "H3", 9
 #define _64V                "H3", 8
 #define _128V               "H3", 11
 #define _2F                 "J4", 9
 #define _4F                 "J4", 8
 #define _8F                 "J4", 11
 #define _1V_n               "E3", 2
 #define _2V_n               "E3", 4
 #define _4V_n               "E3", 6
 #define _16V_n              "J3", 12
 #define _32V_n              "J3", 6
 #define _64V_n              "J3", 8
 #define _128V_n             "J3", 10
//video & sync (DD 3)
 #define _VSYNC              "F1", 4
 #define _VSYNC_n            "E3", 12
 #define _VBLANK             "F7", 13
 #define _XPP                "D2", 2
//1024 bit S.R. entry control (DD 7)
 #define _2XV                "E3", 10
 #define _AFT                "D2", 4
// (CC 3)
 #define _CR1                "CR1_CONNECT", 10 
//Road H functions (CC 2)
 #define _ROAD_n             "M8", 5
 #define _ROAD               "M8", 6
 #define _4HR                "M7", 8
 #define _4HR_n              "P4", 12
 #define _8HR                "M7", 11
 #define _8HR_n              "L5", 2
 #define _16HR               "N7", 9
 #define _32HR               "N7", 8
 #define _64HR               "N7", 11
 #define _64HR_n             "L5", 12
 #define _DIVIDER_n          "N3", 6
// speed pulse sync lock (BB 8)
 //#define _SP_n               "CAP_F6_8", 2  //"F6", 8  //BB7
 #define _SP_n               "BUF3", 2   //BB7
 #define _SR                 "F1", 1
// motor sounds (BB 2)
 #define _RFX                "N9", 12
 #define _RFD                "C9", 12
 #define _GO                 "H9", 6
// road shaping (AA 4)
 #define _LorR               "E7", 7
 #define _LorR_n             "E5", 2

//page2
// score counters (HH 7)
 #define _Fx                 "C6", 12    //HH8
 #define _Fy                 "A8", 9     //HH8 
// traffic v and motion functions (HH 7)
 #define _DOTS               "K4", 12    //HH7
// me car and score video (HH 5)
 #define _SCORE_AND_ME_VIDEO "K1", 6
 #define _CAR_BODY           "J6", 6     //GG4
// coin and play time (HH 3)
 #define _GT                 "CAP_F9_6", 2
 #define _GT_n               "F9", 8
 #define _FLASH              "D8", 6
// traffic h shape (GG 6)
 #define _TRAFFIC_n          "J3", 4     //GG6
// off road and crash (GG 5)
 #define _OFR                "F7", 9     //GG5
 #define _CRASH              "CAP_F7_7", 2  //GG5
// steering (EE 6)
 #define _MCW                "A4", 11    //EE7
// h me car motion (FF 2)
 #define _2M                 "J7", 14
 #define _4M_n               "J6", 10
 #define _8M_n               "J6", 12
 #define _16M                "J7", 11
 #define _32M                "K7", 14
 #define _64M                "K7", 13
 #define _128M               "K7", 12
 #define _A2M_n              "L6", 5
 #define _A2M                "L6", 6
 #define _AOM_n              "K6", 8

/* * * CONNECTIONS * * */

//from (output pins) - to (input pins)

//**PAGE 1**

 //timing circuits (DD 6)

CONNECTION("CRYSTAL", 1,       "C2", 14)
CONNECTION(_1H,                "C2", 1)
CONNECTION(GND,                "C2", 2)
CONNECTION(GND,                "C2", 3)
//nn 5, 10

   //H 
CONNECTION(_8H,                "B2", 14)
CONNECTION(_16H,               "B2", 1)
CONNECTION(GND,                "B2", 2)
CONNECTION(GND,                "B2", 3)
// nn 5, 10
 
CONNECTION(VCC,                "C1", 1)
CONNECTION(_128H,              "C1", 12)
CONNECTION(_A0_n,              "C1", 4)
CONNECTION(VCC,                "C1", 13)

CONNECTION(_A1_n,              "C1", 8)
CONNECTION(_128H,              "C1", 9)
CONNECTION(_A1_n,              "C1", 11)
CONNECTION(VCC,                "C1", 10)
 
CONNECTION(_A1_n,              "A1", 5)
CONNECTION("C1",           5,  "A1", 4)
 
CONNECTION(_A0_n,              "A2", 13)
 
CONNECTION(_1H,                "D2", 13)

CONNECTION(_2H,                "D2", 9)
 
CONNECTION(_4H,                "P4", 9)

CONNECTION(_8H,                "P4", 11)
 
CONNECTION(_16H,               "A2", 1)

CONNECTION(_32H,               "A2", 5)

CONNECTION(_64H,               "A2", 9)
 
CONNECTION("A2",           8,  "CAP_A2_8", 1)
 
CONNECTION(_128H,              "A2", 3)
 
CONNECTION(_128H,              "H1", 5)
CONNECTION(_128H,              "H1", 4)
CONNECTION(_A0,                "H1", 2)
CONNECTION(_64H_n,             "H1", 1)
 
CONNECTION("H1",           6,  "E3", 9)
 
CONNECTION("H1",           6,  "P3", 5)
CONNECTION(_128H,              "P3", 6)
 
CONNECTION("P3",           7,  "P4", 1)
  
   //V
CONNECTION("H1",           6,  "F3", 14)
CONNECTION(_1V,                "F3", 1)
CONNECTION(GND,                "F3", 2)
CONNECTION(GND,                "F3", 3)
 
CONNECTION(_8V,                "H3", 14)
CONNECTION(_16V,               "H3", 1)
CONNECTION(GND,                "H3", 2)
CONNECTION(GND,                "H3", 3)
 
CONNECTION(_128V,              "J4", 14)
CONNECTION("J4",          12,  "J4", 1)
CONNECTION(GND,                "J4", 2)
CONNECTION(GND,                "J4", 3)
 
CONNECTION(_1V,                "E3", 1)

CONNECTION(_2V,                "E3", 3)

CONNECTION(_4V,                "E3", 5)
 
CONNECTION(_16V,               "J3", 13)

CONNECTION(_32V,               "J3", 5)

CONNECTION(_64V,               "J3", 9)

CONNECTION(_128V,              "J3", 11)
 

 //video & sync (DD 3)

CONNECTION(_128V,              "H4", 3)
CONNECTION(_64V,               "H4", 5)
CONNECTION(_32V,               "H4", 4)

CONNECTION(_16V,               "H4", 10)
CONNECTION(_8V,                "H4", 9)
CONNECTION(_4V,                "H4", 11)
 
CONNECTION("H4",           6,  "F1", 5)
CONNECTION("H4",           8,  "F1", 6)
 
CONNECTION("H4",           8,  "D2", 1)
 
CONNECTION(_VSYNC,             "E3", 13)
 
CONNECTION(_2XV,               "F7", 15)
CONNECTION(_16V_n,             "F7", 14)
 
CONNECTION(_VBLANK,            "H7", 3)
CONNECTION(_HBLANK,            "H7", 2)
 
CONNECTION(_TRAFFIC_n,         "N3", 11)
CONNECTION(_ROAD,              "N3", 10)
CONNECTION(_DIVIDER_n,         "N3", 9)
 
CONNECTION("N3",           8,  "K9", 5)
CONNECTION("H7",           1,  "K9", 4)

CONNECTION(_SCORE_AND_ME_VIDEO , "K9", 13)
CONNECTION("H7",           1,  "K9", 12)

CONNECTION("K9",           6,  "K9", 9)
CONNECTION("K9",          11,  "K9", 10)
 
CONNECTION("K9",          11,  "J9", 13)

CONNECTION("K9",           8,  "J9", 11)

CONNECTION("J9",          10,  "J9", 3)

CONNECTION(_HSYNC,             "J9", 5)

CONNECTION(_VSYNC,             "J9", 9)
 

 //1024 bit s.r. entry control (DD 7)

CONNECTION(_VSYNC_n,           "P3", 11)
CONNECTION(_VSYNC_n,           "P3", 12)
CONNECTION(_4V_n,              "P3", 10)
 
CONNECTION("P3",           9,  "E3", 11)
 
CONNECTION("P3",           9,  "H1", 9)
CONNECTION(_1V,                "H1", 12)
CONNECTION(_2V,                "H1", 13)
CONNECTION(_4V_n,              "H1", 10)
 
CONNECTION("H1",           8,  "J1", 4)
CONNECTION("J1",           6,  "J1", 2)
CONNECTION(_SP_n,              "J1", 3)
CONNECTION(VCC,                "J1", 1)

CONNECTION("H1",           8,  "J1", 10)
CONNECTION("J1",           8,  "J1", 12)
CONNECTION("J1",           6,  "J1", 11)
CONNECTION(VCC,                "J1", 13)
 
CONNECTION("J1",           9,  "A1", 9)
CONNECTION("J1",           5,  "A1", 10)
 
CONNECTION("J1",           9,  "A4", 10)
CONNECTION("J1",           6,  "A4", 9)
 
CONNECTION(_4V,                "F2", 13)
CONNECTION(_2V,                "F2", 12)

CONNECTION(_4V,                "F2", 2)
CONNECTION(_1V,                "F2", 1)

CONNECTION("J1",           9,  "F2", 9)
CONNECTION("F2",          11,  "F2", 10)

CONNECTION("J1",           5,  "F2", 5)
CONNECTION("F2",           3,  "F2", 4)
 
CONNECTION("F2",           8,  "F1", 12)
CONNECTION("F2",           6,  "F1", 11)

CONNECTION("F1",          13,  "CAP10", 1)
 
CONNECTION(_4V,                "E2", 2)
CONNECTION("P3",           9,  "E2", 13)
CONNECTION("CAP10",        2,  "E2", 1)
 
CONNECTION("CAP10",        2,  "F4", 9)
CONNECTION(_4V_n,              "F4", 10)
 
CONNECTION("E2",          12,  "E4", 4)
CONNECTION(GND,                "E4", 2)
CONNECTION("F4",           8,  "E4", 3)
CONNECTION("P3",           9,  "E4", 1)
 
CONNECTION(_4V,                "E2", 3)
CONNECTION("E4",           5,  "E2", 4)
CONNECTION("A1",           8,  "E2", 5)

CONNECTION("A1",           8,  "E2", 9)
CONNECTION("E4",           5,  "E2", 11)
CONNECTION(_4V_n,              "E2", 10)
 
CONNECTION("E2",           8,  "B1", 10)
CONNECTION(_A0,                "B1", 9)
CONNECTION(_128H_n,            "B1", 12)
CONNECTION(_16H,               "B1", 13)


 //1024 bit S.R. road memory (DD 6)

//nn CONNECTION(VCC,                "E1", 8)
CONNECTION("H5",           9,  "E1", 5)
CONNECTION("E2",           6,  "E1", 3)
CONNECTION("B1",           8,  "E1", 6)
CONNECTION("E1",           1,  "E1", 7)
//nn CONNECTION(GND,                "E1", 4)


 //S.R. read ckts

CONNECTION(_32H_n,             "A1", 1)
CONNECTION(_64H_n,             "A1", 2)
 
CONNECTION("B1",           8,  "A2", 11)

CONNECTION("A1",           3,  "B1", 4)
CONNECTION("E1",           1,  "B1", 5)
CONNECTION(_64H_n,             "B1", 1)
CONNECTION("A2",          10,  "B1", 2)
 
CONNECTION(_4H_n,              "P1", 10)
CONNECTION("B1",           6,  "P1", 9)
CONNECTION(_8H_n,              "P1", 11)
 
CONNECTION(VCC,                "E4", 10)
CONNECTION("E1",           1,  "E4", 12)
CONNECTION("A1",           3,  "E4", 11)
CONNECTION(VCC,                "E4", 13)
 
CONNECTION("E4",           9,  "D4", 5)
CONNECTION("P1",           8,  "D4", 4)

CONNECTION("E4",           8,  "D4", 1)
CONNECTION("P1",           8,  "D4", 2)


 //data in register (CC 5)
 
CONNECTION("E2",           8,  "D2", 3)
 
CONNECTION("A2",          10,  "A1", 12)
CONNECTION(_64H_n,             "A1", 13)
 
CONNECTION("A1",          11,  "F1", 8)
CONNECTION("E2",           6,  "F1", 9)
 
CONNECTION(_MCW,               "H5", 1)
CONNECTION("F1",          10,  "H5", 2)
CONNECTION(GND,                "H5", 15)
CONNECTION("F5",          13,  "H5", 11)
CONNECTION("F5",          12,  "H5", 12)
CONNECTION("F5",          11,  "H5", 13)
CONNECTION("F5",          10,  "H5", 14)
CONNECTION("F5",           6,  "H5", 3)
CONNECTION("F5",           5,  "H5", 4)
CONNECTION("F5",           4,  "H5", 5)
CONNECTION("F5",           3,  "H5", 6)
CONNECTION(GND,                "H5", 10)  //not shown
 


 //speed pulse sync lock (BB 8)
 
CONNECTION(_XPP,               "D5", 3)
CONNECTION(_128V_n,            "D5", 5)
CONNECTION(_GO,                "D5", 4)
 
CONNECTION("J6",           4,  "F6", 4)
CONNECTION("D5",           6,  "F6", 5)
 
CONNECTION("F6",           6,  "H6", 10)
CONNECTION(GND,                "H6", 12)
CONNECTION("D5",           6,  "H6", 11)
CONNECTION("A4",           8,  "H6", 13)
 
CONNECTION("D5",           6,  "J6", 9)
 
CONNECTION("J6",           8,  "F6", 10)
CONNECTION("H6",           9,  "F6", 9)
 
CONNECTION("F6",           8,  "CAP_F6_8", 1)

CONNECTION("CAP_F6_8",     2,  "BUF3", 1) // Needs extra delay?


 //data accumulator
 
CONNECTION(_2V_n,              "F4", 2)
CONNECTION(_LorR,              "F4", 1)

CONNECTION(_2V,                "F4", 12)
CONNECTION("D5",          12,  "F4", 13)

CONNECTION("F4",           3,  "F4", 4)
CONNECTION("F4",          11,  "F4", 5)
 
CONNECTION(_1V_n,              "F1", 3)
CONNECTION(_SP_n,              "F1", 2)
 
CONNECTION(_SR,                "F5", 8)
CONNECTION("F4",           6,  "F5", 1)
CONNECTION("F4",           6,  "F5", 2)
CONNECTION(VCC,                "F5", 9) //not shown


 //road write functions (CC 4)
 
CONNECTION("C5",           3,  "C4", 15)
CONNECTION("C5",           2,  "C4", 1)
CONNECTION("C5",           6,  "C4", 10)
CONNECTION("C5",           7,  "C4", 9)
CONNECTION("D4",           6,  "C4", 5)
CONNECTION("D4",           3,  "C4", 4)
CONNECTION(_VSYNC_n,           "C4", 11)
CONNECTION(GND,                "C4", 14)
 
CONNECTION("B5",           3,  "B4", 15)
CONNECTION("B5",           2,  "B4", 1)
CONNECTION("B5",           6,  "B4", 10)
CONNECTION("B5",           7,  "B4", 9)
CONNECTION("C4",          12,  "B4", 5)
CONNECTION("C4",          13,  "B4", 4)
CONNECTION(_VSYNC_n,           "B4", 11)
CONNECTION(GND,                "B4", 14)
 
CONNECTION(_2H,                "D3", 1)

CONNECTION("D3",           2,  "D3", 3)
CONNECTION("D3",           4,  "CAP_D3_4", 1)

CONNECTION("B4",           7,  "B3", 13)
CONNECTION(_A1,                "B3", 12)

CONNECTION("B4",           6,  "B3", 10)
CONNECTION(_128H,              "B3", 9)

CONNECTION("B4",           2,  "B3", 1)
CONNECTION(_64H,               "B3", 2)

CONNECTION("B4",           3,  "B3", 4)
CONNECTION(_32H,               "B3", 5)
 
CONNECTION("C4",           7,  "C3", 13)
CONNECTION(_16H,               "C3", 12)

CONNECTION("C4",           6,  "C3", 10)
CONNECTION(_8H,                "C3", 9)

CONNECTION("C4",           2,  "C3", 1)
CONNECTION(_4H,                "C3", 2)

CONNECTION("C4",           3,  "C3", 4)
CONNECTION("CAP_D3_4",     2,  "C3", 5)
 
CONNECTION("C3",           6,  "CAP_C3_6", 1)

CONNECTION(_A0,                "A3", 11)

CONNECTION("B3",          11,  "A3", 3)

CONNECTION("B3",           8,  "A3", 9)

CONNECTION("B3",           3,  "A3", 1)

CONNECTION("B3",           6,  "A3", 5)
 
CONNECTION("C3",          11,  "D3", 11)

CONNECTION("C3",           8,  "D3", 9)

CONNECTION("C3",           3,  "D3", 13)

CONNECTION("CAP_C3_6",     2,  "D3", 5)
 
/*CONNECTION("A3",          10,  "CR1_CONNECT", 1)
CONNECTION("A3",           4,  "CR1_CONNECT", 2)
CONNECTION("A3",           8,  "CR1_CONNECT", 3)
CONNECTION("A3",           2,  "CR1_CONNECT", 4)
CONNECTION("A3",           6,  "CR1_CONNECT", 5)
CONNECTION("D3",          10,  "CR1_CONNECT", 6)
CONNECTION("D3",           8,  "CR1_CONNECT", 7)
CONNECTION("D3",          12,  "CR1_CONNECT", 8)
CONNECTION("D3",           6,  "CR1_CONNECT", 9)*/
// Split up for improved performance
CONNECTION("A3",          10,  "CR1_CONNECT_A", 1)
CONNECTION("A3",           4,  "CR1_CONNECT_A", 2)
CONNECTION("A3",           8,  "CR1_CONNECT_A", 3)
CONNECTION("A3",           2,  "CR1_CONNECT_B", 1)
CONNECTION("A3",           6,  "CR1_CONNECT_B", 2)
CONNECTION("D3",          10,  "CR1_CONNECT_B", 3)
CONNECTION("D3",           8,  "CR1_CONNECT_C", 1)
CONNECTION("D3",          12,  "CR1_CONNECT_C", 2)
CONNECTION("D3",           6,  "CR1_CONNECT_C", 3)

CONNECTION("CR1_CONNECT_A",10, "CR1_CONNECT", 1)
CONNECTION("CR1_CONNECT_B",10, "CR1_CONNECT", 2)
CONNECTION("CR1_CONNECT_C",10, "CR1_CONNECT", 3)


 //road H functions (CC 2)
 
CONNECTION(_CR1,               "D2", 11)
CONNECTION("D2", 10, "BUF1", 1)

CONNECTION(VCC,                "M8", 8)
CONNECTION(_64HR,              "M8", 9)
CONNECTION(VCC,                "M8", 11)
CONNECTION("BUF1", 2, "M8", 10)
//CONNECTION("D2",          10,  "M8", 10)
 
CONNECTION(_1H,                "L8", 4)
CONNECTION(_ROAD,              "L8", 5)
 
CONNECTION("L8",           6,  "M7", 1)
CONNECTION(GND,                "M7", 2)
CONNECTION(GND,                "M7", 3)
 
CONNECTION(_8HR,               "N7", 1)
CONNECTION(GND,                "N7", 2)
CONNECTION(GND,                "N7", 3)
CONNECTION(VCC,                "N7", 14) //not shown
 
CONNECTION(_4HR,               "P4", 13)
 
CONNECTION(_8HR,               "L5", 1)

CONNECTION(_64HR,              "L5", 13)
 
CONNECTION(_64HR,              "P3", 15)
CONNECTION(_1H,                "P3", 14)
 
CONNECTION("P3",          13,  "CAP11", 1)

CONNECTION(_64HR,              "N3", 3)
CONNECTION("CAP11",        2,  "N3", 4)
CONNECTION(_DOTS,              "N3", 5)


 //road shaping (BB 4)
 
CONNECTION(_LorR_n,            "B6", 13)
CONNECTION("B5",           2,  "B6", 9)
CONNECTION("B5",           6,  "B6", 10)
CONNECTION("B5",           7,  "B6", 12)
 
CONNECTION("B5",           7,  "A5", 5)
CONNECTION("B5",           6,  "A5", 4)
CONNECTION("B5",           2,  "A5", 3)
 
CONNECTION("A5",           6,  "B8", 13)
CONNECTION(_LorR,              "B8", 12)
 
CONNECTION("B6",           8,  "C8", 10)
CONNECTION(_RFD,               "C8", 12)
CONNECTION("C8",           5,  "C8", 11)
CONNECTION("B8",          11,  "C8", 13)

CONNECTION(VCC,                "C8", 4)
CONNECTION(_RFX,               "C8", 2)
CONNECTION("B8",           6,  "C8", 3)
CONNECTION(VCC,                "C8", 1)
 
CONNECTION(_Fy,                "B8", 1)
CONNECTION("C8",           5,  "B8", 2)

CONNECTION("C8",           6,  "B8", 10)
CONNECTION(_Fx,                "B8", 9)

CONNECTION("B8",           3,  "B8", 4)
CONNECTION("B8",           8,  "B8", 5)
 
CONNECTION("C8",           8,  "B7", 5)
CONNECTION("B6",           6,  "B7", 6)

CONNECTION("B6",           6,  "B7", 3)
CONNECTION("C8",           9,  "B7", 2)
 
CONNECTION("B7",           4,  "D7", 9)

CONNECTION("B7",           1,  "D7", 3)
 
CONNECTION(VCC,                "E7", 15)
CONNECTION(VCC,                "E7", 1)
CONNECTION(VCC,                "E7", 10)
CONNECTION(VCC,                "E7", 9)
CONNECTION("D7",           8,  "E7", 5)
CONNECTION("D7",           4,  "E7", 4)
CONNECTION("E7",          12,  "E7", 11)
CONNECTION("D7",           2,  "E7", 14)
 
CONNECTION("E7",          13,  "D7", 1)
 
CONNECTION(_LorR,              "E5", 1)
 
CONNECTION(_LorR_n,            "E6", 2)
CONNECTION("E7",           6,  "E6", 1)

CONNECTION(_LorR_n,            "E6", 12)
CONNECTION("E7",           2,  "E6", 13)

CONNECTION(_LorR_n,            "E6", 9)
CONNECTION("E7",           3,  "E6", 10)
 
CONNECTION("B6",           8,  "A6", 5)
CONNECTION("B8",          11,  "A6", 3)
CONNECTION("C8",           6,  "A6", 4)
 
CONNECTION(_A1_n,              "A5", 2)
CONNECTION(_1V,                "A5", 13)
CONNECTION(_SP_n,              "A5", 1)
 
CONNECTION("A6",           6,  "A6", 9)
CONNECTION(_2V_n,              "A6", 11)
CONNECTION("A5",          12,  "A6", 10)
 
CONNECTION("A6",           8,  "E5", 13)
 
CONNECTION(_SP_n,              "C6", 1)
CONNECTION(GND,                "C6", 2)
CONNECTION(GND,                "C6", 3)
 
CONNECTION("C6",          11,  "B6", 2)
CONNECTION("C6",           8,  "B6", 5)
CONNECTION("C6",           9,  "B6", 4)
CONNECTION("E5",          12,  "B6", 1)
 
CONNECTION("C6",           9,  "C7", 15)
CONNECTION("C6",           8,  "C7", 14)
CONNECTION("C6",          11,  "C7", 13)
CONNECTION(GND,                "C7", 12)

CONNECTION("C7",           2,  "C7_CONNECT1", 1)
CONNECTION("C7",           4,  "C7_CONNECT1", 2)
CONNECTION("C7",           6,  "C7_CONNECT1", 3)
CONNECTION("C7",           9,  "C7_CONNECT1", 4)

CONNECTION("C7",           3,  "C7_CONNECT2", 1)
CONNECTION("C7",           7,  "C7_CONNECT2", 2)

CONNECTION("C7_CONNECT1", 10,  "D7", 13)

CONNECTION("C7_CONNECT2", 10,  "D7", 11)

CONNECTION("C7",           5,  "D7", 5)
 
CONNECTION("D7",          12,  "D6", 10)
CONNECTION("E6",           3,  "D6", 9)

CONNECTION("D7",          10,  "D6", 13)
CONNECTION("E6",          11,  "D6", 12)

CONNECTION("D7",           6,  "D6", 4)
CONNECTION("E6",           8,  "D6", 5)
 
CONNECTION("D6",           8,  "D5", 2)
CONNECTION("D6",          11,  "D5", 13)
CONNECTION("D6",           6,  "D5", 1)

CONNECTION("D5",          12,  "D5", 11)
CONNECTION(_2V,                "D5", 9)
CONNECTION("A5",          12,  "D5", 10)
 
CONNECTION("D5",           8,  "E5", 9)
 
CONNECTION(_LorR_n,            "D4", 10)
CONNECTION("E5",           8,  "D4", 9)

CONNECTION("E5",           8,  "D4", 12)
CONNECTION(_LorR,              "D4", 13)
 
CONNECTION(VCC,                "C5", 15)
CONNECTION(VCC,                "C5", 1)
CONNECTION(VCC,                "C5", 10)
CONNECTION(VCC,                "C5", 9)
CONNECTION("D4",           8,  "C5", 5)
CONNECTION("D4",          11,  "C5", 4)
CONNECTION("B5",          12,  "C5", 11)
CONNECTION("E5",          10,  "C5", 14)
 
CONNECTION(VCC,                "B5", 15)
CONNECTION(VCC,                "B5", 1)
CONNECTION(VCC,                "B5", 10)
CONNECTION(VCC,                "B5", 9)
CONNECTION("C5",          12,  "B5", 5)
CONNECTION("C5",          13,  "B5", 4)
CONNECTION("B5",          12,  "B5", 11)
CONNECTION("E5",          10,  "B5", 14)
 
CONNECTION("B5",          13,  "E5", 11)
 

 //analog speed (BB 3)
 
CONNECTION(_CRASH,             "B9", 9)

CONNECTION(_OFR,               "B9", 5)

CONNECTION(_GT_n,              "B9", 11)
 
//D9 - Modeled in SPEED CONTROL
//CONNECTION(VCC,                "D9", 4a

CONNECTION("ACCELERATOR", 1,   "SPEED1", 1)
CONNECTION(_CRASH,             "SPEED1", 2)
CONNECTION(_OFR,               "SPEED1", 3)
CONNECTION(_GT_n,              "SPEED1", 4)

CONNECTION("SPEED1",       5,  "J6", 3)
 
CONNECTION(VCC,                "N8", 8)
CONNECTION("SPEED1",       5,  "N8", 9)
CONNECTION("N8",           2,  "N8", 11)
CONNECTION(_VSYNC_n,           "N8", 10)

CONNECTION("N8",           5,  "N8", 1)
CONNECTION(GND,                "N8", 4)
CONNECTION("SPEED1",       5,  "N8", 12)
CONNECTION(_VSYNC_n,           "N8", 13)
 
CONNECTION("N8",           5,  "K9", 1)
CONNECTION("N8",           3,  "K9", 2)
 
CONNECTION("SPEED1",       7,  "H9", 4) 
CONNECTION("K9",           3,  "H9", 2)
CONNECTION(_VSYNC,             "H9", 3)
CONNECTION(VCC,                "H9", 1)

CONNECTION(_GO,                "D8", 13)
CONNECTION(_8F,                "D8", 9)
CONNECTION(_4V,                "D8", 10)
CONNECTION(_OFR,               "D8", 12)


 //motor sounds (BB 2)

CONNECTION("SPEED1",       5,  "N9", 14)
 
CONNECTION(_RFX,               "C9", 14)

CONNECTION("SPEED1",       5,  "C9", 1)
CONNECTION(GND,                "C9", 6)
CONNECTION(GND,                "C9", 7)
 

//**PAGE 2**

 //score counters (distance) (HH 7)
 
CONNECTION(_SP_n,              "C6", 14)
 
CONNECTION(_Fx,                "A8", 14)
CONNECTION("A8",          12,  "A8", 1)
CONNECTION(GND,                "A8", 2)
CONNECTION(GND,                "A8", 3)
 
CONNECTION("A8",          11,  "A7", 14)
CONNECTION("A7",          12,  "A7", 1)
CONNECTION(_GT_n,              "A7", 2)
CONNECTION(VCC,                "A7", 3)
 
CONNECTION("A7",          11,  "N2", 14)
CONNECTION("N2",          12,  "N2", 1)
CONNECTION(GND,                "N2", 6)
CONNECTION(GND,                "N2", 7)
CONNECTION("E5",           4,  "N2", 2)
CONNECTION("E5",           4,  "N2", 3)

CONNECTION("N2",          11,  "L2", 14)
CONNECTION("L2",          12,  "L2", 1)
CONNECTION("E5",           4,  "L2", 2)
CONNECTION("E5",           4,  "L2", 3)

 
 //ext play # decode (HH 6)
 
CONNECTION(VCC,                "SW_EXT_PLAY", 1)
CONNECTION("L2",          12,  "SW_EXT_PLAY", 2)

CONNECTION(VCC,                "SW_EXT_PLAY", 3)
CONNECTION("L2",           9,  "SW_EXT_PLAY", 4)

CONNECTION(VCC,                "SW_EXT_PLAY", 5)
CONNECTION("L2",           8,  "SW_EXT_PLAY", 6)

CONNECTION(VCC,                "SW_EXT_PLAY", 7)
CONNECTION("L2",          11,  "SW_EXT_PLAY", 8)

CONNECTION("SW_EXT_PLAY",  9,  "K1", 9)
CONNECTION("SW_EXT_PLAY", 10,  "K1", 12)
CONNECTION("SW_EXT_PLAY", 11,  "K1", 13)
CONNECTION("SW_EXT_PLAY", 12,  "K1", 10)
 

 //traffic v and motion functions (HH 8)
 
CONNECTION(_2V,                "L3", 2)
CONNECTION(_VSYNC,             "L3", 1)
 
CONNECTION(_AFT,               "D1", 12)
CONNECTION(_A1_n,              "D1", 11)
 
CONNECTION("D1",          13,  "K4", 14)
 
CONNECTION("L3",           3,  "L5", 11)
 
CONNECTION("L5",          10,  "L3", 13)
CONNECTION(_A2,                "L3", 12)

CONNECTION(_DOTS,              "L3", 5)
CONNECTION("L3",           3,  "L3", 4)

CONNECTION("L3",          11,  "L3", 10)
CONNECTION(_DOTS,              "L3", 9)
 
CONNECTION("L3",           8,  "K3", 14)
CONNECTION("K3",          12,  "K3", 1)
CONNECTION(GND,                "K3", 2)
CONNECTION(GND,                "K3", 3)
 
CONNECTION("K3",          11,  "K4", 1)
CONNECTION(GND,                "K4", 2)
CONNECTION(GND,                "K4", 3)

CONNECTION("K4",          11,  "SW_K4L4", 1)
CONNECTION(VCC,                "SW_K4L4", 2)

CONNECTION("SW_K4L4",      3,  "L4", 12) 
CONNECTION("K4",           8,  "L4", 9)
CONNECTION("K4",           9,  "L4", 10)
CONNECTION("K3",          11,  "L4", 13)
 
CONNECTION("L3",           6,  "M3", 14)
CONNECTION("M3",          12,  "M3", 1)
CONNECTION(GND,                "M3", 2)
CONNECTION(GND,                "M3", 3)
 
CONNECTION("M3",          11,  "M4", 1)
CONNECTION(GND,                "M4", 2)
CONNECTION(GND,                "M4", 3)
 
CONNECTION("M4",          11,  "L4", 2)
CONNECTION("M4",           8,  "L4", 5)
CONNECTION("M4",           9,  "L4", 4)
CONNECTION("M3",          11,  "L4", 1)
 
CONNECTION("M3",           9,  "L5", 5)
 

 //hr functions (FF 8)
 
CONNECTION(_4HR_n,             "M6", 2)
CONNECTION(_32HR,              "M6", 1)

CONNECTION(_32HR,              "M6", 13)
CONNECTION(_16HR,              "M6", 12)

CONNECTION(_16HR,              "M6", 10)
CONNECTION(_8HR_n,             "M6", 9)
 
CONNECTION("L4",           8,  "L5", 9)
 
CONNECTION("L5",           8,  "N6", 4)
CONNECTION(_64HR,              "N6", 5)
 
CONNECTION("K3",           9,  "M5", 5)
CONNECTION("M6",           3,  "M5", 2)
CONNECTION("N6",           6,  "M5", 4)
CONNECTION("M6",          11,  "M5", 1)
 
CONNECTION("M6",          11,  "N5", 3)
CONNECTION("M6",           8,  "N5", 4)
CONNECTION("N6",           6,  "N5", 5)
 
CONNECTION("M5",           6,  "N4", 1) //wheels
CONNECTION("N5",           6,  "N4", 2) //body
 
CONNECTION("N6",           8,  "M5", 10)
CONNECTION("L5",           6,  "M5", 9)
CONNECTION("M6",           3,  "M5", 12)
CONNECTION("M6",          11,  "M5", 13)
 
CONNECTION("M6",          11,  "N5", 11)
CONNECTION("M6",           8,  "N5", 10)
CONNECTION("N6",           8,  "N5", 9)
 
CONNECTION("M5",           8,  "N4", 12)
CONNECTION("N5",           8,  "N4", 13)
 
 //traffic H shape (GG 6)
 
CONNECTION("L4",           6,  "L5", 3)
 
CONNECTION("L5",           4,  "N6", 10)
CONNECTION(_64HR_n,            "N6", 9)
 
CONNECTION("L5",           4,  "M4", 14)
 
CONNECTION(VCC,                "H6", 4)
CONNECTION("M4",          12,  "H6", 2)
CONNECTION(_2F,                "H6", 3)
CONNECTION(VCC,                "H6", 1)
 
CONNECTION("H6",           5,  "SW_H6N4", 1)
CONNECTION(VCC,                "SW_H6N4", 2)

CONNECTION("SW_H6N4",      3,  "N4", 9) 
CONNECTION("N4",          11,  "N4", 10)
 
CONNECTION("N4",           3,  "J3", 1)

CONNECTION("J3",           2,  "CAP12", 1)
 
CONNECTION("N4",           8,  "N4", 5) //dwn car
CONNECTION("CAP12",        2,  "N4", 4) //up car
 
CONNECTION("N4",           6,  "J3", 3)
 

 //steering circuits (EE 6) 

CONNECTION("STEERINGWHEEL", Wheel::A,  "F9", 1)
CONNECTION("STEERINGWHEEL", Wheel::A,  "F9", 2)

CONNECTION("STEERINGWHEEL", Wheel::B,  "F9", 12)
CONNECTION("STEERINGWHEEL", Wheel::B,  "F9", 13)
 
CONNECTION("F9",           3,  "M7", 14)

CONNECTION(VCC,                "H9", 10)
CONNECTION("F9",           3,  "H9", 12)
CONNECTION("F9",          11,  "H9", 11)
CONNECTION(VCC,                "H9", 13)
 
CONNECTION("M7",          12,  "H7", 8)
CONNECTION("H9",           9,  "H7", 9)

CONNECTION("M7",          12,  "H7", 11)
CONNECTION("H9",           8,  "H7", 12)
 
CONNECTION("H7",          10,  "H8", 3)

CONNECTION("H7",          13,  "H8", 1)
 
CONNECTION(VCC,                "J8", 15)
CONNECTION(VCC,                "J8", 1)
CONNECTION(VCC,                "J8", 10)
CONNECTION(VCC,                "J8", 9)
CONNECTION("H8",           4,  "J8", 5)
CONNECTION("H8",           2,  "J8", 4)
CONNECTION("J8",          12,  "J8", 11)
CONNECTION("CAP_D6_3",     2,  "J8", 14) 
 
CONNECTION(_GT,                "D6", 1)
CONNECTION("J8",          13,  "D6", 2)

CONNECTION("D6",           3,  "CAP_D6_3", 1)
 
CONNECTION("J8",           7,  "H8", 5)
 
CONNECTION("H8",           6,  "K8", 5)
CONNECTION("J8",           6,  "K8", 4)

CONNECTION("H8",           6,  "K8", 12)
CONNECTION("J8",           2,  "K8", 13)

CONNECTION("H8",           6,  "K8", 9)
CONNECTION("J8",           3,  "K8", 10)
 
CONNECTION(_128V_n,            "A5", 9)
CONNECTION(_64V,               "A5", 10)
CONNECTION(_32V_n,             "A5", 11)
 
CONNECTION("A5",           8,  "A4", 1)
CONNECTION(_1V,                "A4", 2)

CONNECTION("A5",           8,  "A4", 13)
CONNECTION(_16V,               "A4", 12)

CONNECTION(_SP_n,              "A4", 5)
CONNECTION("A4",           3,  "A4", 4)
 
CONNECTION("A4",           6,  "N9", 1)
CONNECTION(GND,                "N9", 2)
CONNECTION(GND,                "N9", 3)
 
CONNECTION("N9",          11,  "M9", 13)
CONNECTION("N9",           8,  "M9", 14)
CONNECTION("N9",           9,  "M9", 15)
CONNECTION(GND,                "M9", 12)

CONNECTION("M9",          1,  "M9_CONNECT1", 1)
CONNECTION("M9",          2,  "M9_CONNECT1", 2)
CONNECTION("M9",          4,  "M9_CONNECT1", 3)
CONNECTION("M9",          6,  "M9_CONNECT1", 4)
CONNECTION("M9",          9,  "M9_CONNECT1", 5)

CONNECTION("M9",          3,  "M9_CONNECT2", 1)
CONNECTION("M9",          7,  "M9_CONNECT2", 2)

CONNECTION("M9_CONNECT1", 10, "L9", 5)

CONNECTION("M9_CONNECT2", 10, "L9", 11)

CONNECTION("M9",          5,  "L9", 9)

CONNECTION("K8",           6,  "L8", 2)
CONNECTION("L9",           6,  "L8", 1)

CONNECTION("K8",          11,  "L8", 12)
CONNECTION("L9",          10,  "L8", 13)

CONNECTION("K8",           8,  "L8", 9)
CONNECTION("L9",           8,  "L8", 10)
 
CONNECTION("L8",           3,  "L7", 1)
CONNECTION("L8",          11,  "L7", 13)
CONNECTION("L8",           8,  "L7", 2)
 
CONNECTION(_MCW,               "E5", 5)
 

 //off road and crash (GG 4)
 
CONNECTION(_ROAD_n,            "F6", 13)
CONNECTION(_CAR_BODY,          "F6", 12)

CONNECTION(_CAR_BODY,          "F6", 2)
CONNECTION("N4",           6,  "F6", 1)

CONNECTION("F6",           3,  "BUF2", 1)

CONNECTION(_16V_n,             "A6", 13)
CONNECTION(_A1,                "A6", 1)
CONNECTION("A5",           8,  "A6", 2)
 
CONNECTION("F6",          11,  "F7", 11)
CONNECTION("F6",          11,  "F7", 12)
CONNECTION("A6",          12,  "F7", 10)

//CONNECTION("F6",           3,  "F7", 6)
CONNECTION("BUF2",         2,  "F7", 6)
CONNECTION("A6",          12,  "F7", 5)

CONNECTION("F7",           7,  "CAP_F7_7", 1)
 

 //H ME motion circuits (FF 3)
 
CONNECTION(_CRASH,             "K6", 4)
CONNECTION(_VSYNC,             "K6", 5)
 
CONNECTION(_SR,                "L7", 5)
CONNECTION(_2V,                "L7", 4)
CONNECTION("L7",          12,  "L7", 3)
 
CONNECTION("L7",          12,  "K6", 2)
CONNECTION("A5",           8,  "K6", 1)
 
CONNECTION("H8",           6,  "K8", 2)
CONNECTION("E5",           6,  "K8", 1)
 
CONNECTION("K6",           6,  "L7", 10)
CONNECTION("L7",           6,  "L7", 9)
CONNECTION("K6",           3,  "L7", 11)
 
CONNECTION("L7",           8,  "J6", 1)
 
CONNECTION("J6",           2,  "H7", 5)
CONNECTION("K8",           3,  "H7", 6)
 
CONNECTION("J6",           2,  "J7", 3)
CONNECTION("H7",           4,  "J7", 4)
CONNECTION(GND,                "J7", 5)
CONNECTION(GND,                "J7", 6)
CONNECTION(VCC,                "J7", 1) // not shown
CONNECTION(_1H,                "J7", 2)
CONNECTION("K6",          11,  "J7", 9)
CONNECTION(VCC,                "J7", 7)
CONNECTION(VCC,                "J7", 10)

CONNECTION(VCC,                "K7", 1) // not shown
CONNECTION(_1H,                "K7", 2)
CONNECTION("K6",          11,  "K7", 9)
CONNECTION(GND,                "K7", 3)
CONNECTION(GND,                "K7", 4)
CONNECTION(GND,                "K7", 5)
CONNECTION(GND,                "K7", 6)
CONNECTION("J7",          15,  "K7", 7)
CONNECTION("J7",          15,  "K7", 10)
 
CONNECTION("J7",          13,  "J6", 11)

CONNECTION("J7",          12,  "J6", 13)
 
CONNECTION("K7",          11,  "K6", 13)
CONNECTION("L6",           2,  "K6", 12)
 
CONNECTION(VCC,                "L6", 1)
CONNECTION(_128M,              "L6", 12)
CONNECTION(_AOM_n,             "L6", 4)
CONNECTION(VCC,                "L6", 13)

CONNECTION("L6",           3,  "L6", 8)
CONNECTION(_128M,              "L6", 9)
CONNECTION("L6",           3,  "L6", 11)
CONNECTION(VCC,                "L6", 10)
 
CONNECTION(_A2M_n,             "K6", 9)
CONNECTION("L6",           3,  "K6", 10)
 

 //score shaping functions (GG 6)
 
CONNECTION(_32H_n,             "M2", 1)
CONNECTION(GND,                "M2", 15)
CONNECTION("N2",          12,  "M2", 2)
CONNECTION("N2",           9,  "M2", 5)
CONNECTION("N2",           8,  "M2", 14)
CONNECTION("N2",          11,  "M2", 11)
CONNECTION("L2",          12,  "M2", 3)
CONNECTION("L2",           9,  "M2", 6)
CONNECTION("L2",           8,  "M2", 13)
CONNECTION("L2",          11,  "M2", 10)
 
CONNECTION("M2",           4,  "M1", 7)
CONNECTION("M2",           7,  "M1", 1)
CONNECTION("M2",          12,  "M1", 2)
CONNECTION("M2",           9,  "M1", 6)
CONNECTION(VCC,  "M1", 3)  //not shown
CONNECTION(VCC,  "M1", 4)  //not shown
CONNECTION(VCC,  "M1", 5)  //not shown
 
CONNECTION("M1",          15,  "L1", 1)
CONNECTION("M1",           9,  "L1", 3)
CONNECTION("M1",          12,  "L1", 6)
CONNECTION("M1",          11,  "L1", 9) 
CONNECTION(GND,                "L1", 2)
CONNECTION(GND,                "L1", 4)
CONNECTION(GND,                "L1", 5)
CONNECTION(GND,                "L1", 7)
CONNECTION("D2",           6,  "L1", 10)
CONNECTION(_4H,                "L1", 11)
CONNECTION(_8V,                "L1", 12)
CONNECTION(_8H,                "L1", 13)
 
CONNECTION("M1",          13,  "N1", 1)
CONNECTION("M1",          14,  "N1", 4)
CONNECTION("M1",          10,  "N1", 9)
CONNECTION(GND,                "N1", 2)
CONNECTION(GND,                "N1", 3)
CONNECTION(GND,                "N1", 5)
CONNECTION(GND,                "N1", 6)
CONNECTION(GND,                "N1", 7)
CONNECTION("H2",           8,  "N1", 10)
CONNECTION(_2V,                "N1", 11)
CONNECTION(_4V,                "N1", 12)
CONNECTION(_8V,                "N1", 13)


 //me car and score video (HH 5)
 
CONNECTION(_FLASH,             "H2", 2)
CONNECTION(_128V_n,            "H2", 3)
CONNECTION(_64V_n,             "H2", 4)
CONNECTION(_32V,               "H2", 12)
CONNECTION(_16V,               "H2", 11)
CONNECTION(_A1,                "H2", 5)
CONNECTION(_128H,              "H2", 6)
CONNECTION("D1",           4,  "H2", 1)
 
CONNECTION(_64H,               "D1", 6)
CONNECTION(_16H_n,             "D1", 5)

CONNECTION(_2H_n,              "D1", 9)
CONNECTION("H2",           8,  "D1", 8)
 
CONNECTION("D1",          10,  "D2", 5)
 
CONNECTION("L1",          14,  "K1", 2)
CONNECTION("N1",          14,  "K1", 1)
CONNECTION("K5",           6,  "K1", 4)
CONNECTION("N5",          12,  "K1", 5)
 
CONNECTION(_128M,              "K5", 10)
CONNECTION(_128M,              "K5", 9)
CONNECTION(_A2M,               "K5", 12)
CONNECTION(_64M,               "K5", 13)
 
CONNECTION("K5",           8,  "B7", 8)
CONNECTION(_MCW,               "B7", 9)
 
CONNECTION(_4M_n,              "J5", 1)
CONNECTION(_32M,               "J5", 2)

CONNECTION(_32M,               "J5", 9)
CONNECTION(_16M,               "J5", 10)

CONNECTION(_16M,               "J5", 12)
CONNECTION(_8M_n,              "J5", 13)
 
CONNECTION("J5",           3,  "K5", 2)
CONNECTION(_4V,                "K5", 5)
CONNECTION("J5",           8,  "K5", 4)
CONNECTION("B7",          10,  "K5", 1)
 
CONNECTION("B7",          10,  "N5", 1)
CONNECTION("J5",           8,  "N5", 2)
CONNECTION("J5",          11,  "N5", 13)
 
CONNECTION("N5",          12,  "J6", 5)
 

 //coin, start, timer (HH 3)

CONNECTION("COIN_IN",      1,  "F7", 1) //guess
CONNECTION("K1",           8,  "F7", 2)
CONNECTION("K1",           8,  "F7", 3)
 
CONNECTION("F7",           4,  "H8", 9)

CONNECTION("H8",           8,  "CAP14", 1)
 
CONNECTION("F7",           4,  "F8", 4)
CONNECTION("CAP14",        2,  "F8", 5) 

CONNECTION("F8",           6,  "F8", 12)
CONNECTION(_GT,                "F8", 13)

CONNECTION("E9",           3,  "E8", 1)
CONNECTION("F8",          11,  "E8", 2)
CONNECTION("F8",          11,  "E8", 3)
CONNECTION("E8",          11,  "E8", 14)
 
CONNECTION("E8",          11,  "D8", 1)
CONNECTION("E8",           8,  "D8", 4)
CONNECTION("E8",           9,  "D8", 2)
CONNECTION(_8F,                "D8", 5)

//skip power-on-reset transistor circuit
CONNECTION(VCC,                "F8", 2) //guess
CONNECTION("H8",          12,  "F8", 1)
 
CONNECTION("F8",           3,  "H8", 11)

CONNECTION("E8",          12,  "H8", 13)

CONNECTION("COIN_IN",      1,  "F9", 4) //guess
CONNECTION("F9",           8,  "F9", 5)

CONNECTION("F9",           6,  "CAP_F9_6", 1)

CONNECTION(_GT,                "F9", 9)
CONNECTION("H8",          10,  "F9", 10)
 
CONNECTION("COIN_IN",      1,  "E5", 3) //guess

CONNECTION(_GT,                "E9", 4)


/* video hookup */

CONNECTION("VIDEO", Video::HBLANK_PIN, _HSYNC)
CONNECTION("VIDEO", Video::VBLANK_PIN, _VSYNC)

CONNECTION("J9", 4,          "VIDEO", 1)
CONNECTION("J9", 12,         "VIDEO", 2)  

/* audio hookup */

//todo: needs work

//CONNECTION("D8", 8,  "AUDIO", 1)
//CONNECTION(_SCORETONE,     "AUDIO", 2)  
//CONNECTION(_SKIDIn,        "AUDIO", 3) 
//CONNECTION(_SKIDIIn,       "AUDIO", 4) 

//CONNECTION("AUDIO", i1, "MIXER", 1)
//CONNECTION("AUDIO", i2, "MIXER", 2)
//CONNECTION("AUDIO", i3, "MIXER", 3)
//CONNECTION("AUDIO", i4, "MIXER", 4)

//CONNECTION("AUDIO", Audio::OUTPUT_MONO, "MIXER", i1)


#ifdef DEBUG

CONNECTION(_VSYNC_n, "LOG1", 1) // A
CONNECTION(_SP_n, "LOG1", 2) // B
CONNECTION("C5", 3, "LOG1", 3) // C
CONNECTION("C5", 2, "LOG1", 4) // D
CONNECTION("C5", 6, "LOG1", 5) // E
CONNECTION("C5", 7, "LOG1", 6) // F
CONNECTION("B5", 3, "LOG1", 7) // G
CONNECTION("B5", 2, "LOG1", 8) // H
CONNECTION("B5", 6, "LOG1", 9) // I
CONNECTION("B5", 7, "LOG1", 10) // J
CONNECTION("D4", 8, "LOG1", 11) // K
CONNECTION("D4", 11, "LOG1", 12) // L
CONNECTION("C6", 9, "LOG1", 13) // M
CONNECTION("C6", 8, "LOG1", 14) // N
CONNECTION("C6", 11, "LOG1", 15) // O
CONNECTION("D6", 8, "LOG1", 16) // P
CONNECTION("D6", 11, "LOG1", 17) // Q
CONNECTION("D6", 6, "LOG1", 18) // R
CONNECTION("D5", 12, "LOG1", 19) // S
CONNECTION("D5", 8, "LOG1", 20) // T
CONNECTION("A5", 12, "LOG1", 21) // U
CONNECTION(_2V, "LOG1", 22) // V
CONNECTION("E7", 3, "LOG1", 23) // W
CONNECTION("E7", 2, "LOG1", 24) // X
CONNECTION("E7", 6, "LOG1", 25) // Y
CONNECTION("E7", 7, "LOG1", 26) // Z

#endif


CIRCUIT_LAYOUT_END





