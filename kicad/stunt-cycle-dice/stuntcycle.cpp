#include "../circuit_desc.h"
#include "../circuit.h"

#define DEBUG
#undef DEBUG

#define USE_CLK_GATES

#ifdef DEBUG
static VcdLogDesc vcd_log_desc
(
    "output_stunt.vcd",
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

struct StuntCycleThrottleDesc
{
    double throttle_pos;
    double cap_voltage;
    uint64_t last_event_time;

    static CUSTOM_LOGIC( stuntcycle_throttle );

    enum INPUT_MASKS
    {
        ATTRACT_MASK      = 1 << 0,
        FLIP_OR_JUMP_MASK = 1 << 1,
        SPEED_KILL_MASK   = 1 << 2,
        R2_MASK           = 1 << 3,
        R3_MASK           = 1 << 4
    };

    enum OUTPUT_PINS
    {
        SPEED_PULSES_PIN = i2
    };
};

static StuntCycleThrottleDesc stunt_cycle_throttle_desc = { 0.0, 0.0, 0 };
static Throttle1Desc throttle_desc(&stunt_cycle_throttle_desc.throttle_pos);

static CapacitorDesc c57_desc(P_FARAD(220.0), OHM(330.0)); // 330 Ohm resistor in serires
static CapacitorDesc c58_desc(P_FARAD(220.0));

static Mono9602Desc n6_desc(K_OHM(47.0), U_FARAD(100.0), K_OHM(47.0), U_FARAD(1.0));
static SeriesRCDesc c13_desc(K_OHM(2.2), P_FARAD(470.0));

static RomDesc d7_desc("stuntcycle", "82s123.4d", 0x31A09EFB);
static RomDesc hf1_desc("stuntcycle", "82s115.1fh", 0x4ED5A99D);

static Dipswitch53137Desc f5_desc("misses", "dice_dipswitch16_1", "Number of Misses Allowed", 4,
                                  "0", "1", "2", "3",
                                  "4", "5", "6", "7");

static Dipswitch53137Desc f7_desc("free_game_control", "dice_dipswitch16_2", "Free Game Control", 9,
                                  "12", "13", "14", "15", "16", "17", "18", "19",
                                  "20", "21", "22", "23", "24", "25", "26", "27");

static DipswitchDesc dipswitch1_desc("coinage", "dice_dipswitch_1", "Coinage", 0,
                                     "1 Coin / 1 Credit", "1 Coin / 2 Credits");
static DipswitchDesc dipswitch2_desc("free_game_en", "dice_dipswitch_2", "Free Game", 0, "Enabled", "Disabled");

static VIDEO_DESC( stuntcycle )
    VIDEO_RESISTANCE(1, K_OHM(1.0))
    VIDEO_RESISTANCE(2, K_OHM(1.0))
    VIDEO_RESISTANCE(Video::HBLANK_PIN, K_OHM(1.0))
    VIDEO_CONTRAST(1.0)
    VIDEO_RETRO_V_SIZE(252)
VIDEO_DESC_END

static INPUT_DESC( stuntcycle )
    INPUT_INFO(THROTTLE1_INPUT, "Adjust Motorcycle Speed")

    INPUT_INFO(COIN_INPUT, {{ 1 }}, "Insert Coin")
    INPUT_INFO(START_INPUT, {{ 1 }}, "Start 1-Player Game")
    INPUT_INFO(START_INPUT, {{ 2 }}, "Start 2-Player Game")
INPUT_DESC_END

extern CHIP_DESC( STUNTCYCLE_THROTTLE );

CIRCUIT_LAYOUT( stuntcycle )
	/**************************************************************************
		Chips
	**************************************************************************/
    CHIP("CLOCK", CLOCK_14_318_MHZ)
    
    CHIP("A3", 7400)
    CHIP("A4", 7474)
	CHIP("A5", 7474)
	CHIP("A6", 9312)
	CHIP("A7", 9322)
    CHIP("A8", 7402)
    CHIP("A9", 7474)
	
    CHIP("B2", 7400)
	CHIP("B3", 9316)
    CHIP("B4", 74107)
	CHIP("B5", 7408)
	CHIP("B6", 9312)
	CHIP("B7", 9322)
    CHIP("B8", 74192)
    CHIP("B9", 74192)
	
    CHIP("C1", 7493)
    CHIP("C2", 7474)
	CHIP("C3", 9316)
    CHIP("C4", 7410)
    CHIP("C5", 7474)
	CHIP("C6", 7448)
	CHIP("C7", 9322)
	CHIP("C8", 7486)
	
	CHIP("D1", 7450)
    CHIP("D2", 7474)
	CHIP("D3", 7404)
	CHIP("D4", 7402)
	CHIP("D5", 7400)
	CHIP("D6", 7410)
	CHIP("D7", 82S123, &d7_desc)
	CHIP("D8", 7427)
    CHIP("D9", 7474)
	
    CHIP("E1", 74194)
    CHIP("E2", 74194)
	CHIP("E3", 7410)
    CHIP("E4", 7427)
    CHIP("E5", 74193)
	CHIP("E6", 7485)
    CHIP("E7", 7485)
    CHIP("E8", 74193)
	
    CHIP("F2", 74165)
    CHIP("F3", 7450)
    CHIP("F4", 7400)
    CHIP("F5", 53137, &f5_desc)
	CHIP("F6", 7474)
    CHIP("F7", 53137, &f7_desc)
    CHIP("F8", 7474)
    CHIP("F9", 7402)
	
    CHIP("HF1", 82S115, &hf1_desc)

	CHIP("H2", 7400)
	CHIP("H3", 7474)
	CHIP("H4", 7410)
	CHIP("H5", 7408)
	CHIP("H6", 7404)
	CHIP("H7", 9316)
    CHIP("H8", 7474)
    CHIP("H9", 7410)            
	
    CHIP("J1", 9322)
    CHIP("J2", 7474)
	CHIP("J3", 7402)
	CHIP("J4", 7486)
	CHIP("J5", 7402)
	CHIP("J6", 7420)
	CHIP("J7", 7474)
    CHIP("J8", 7400)
    CHIP("J9", 74107)
	
    CHIP("K1", 9316)
    CHIP("K2", 9316)
	CHIP("K3", 7493)
	CHIP("K4", 74107)
    CHIP("K5", 7427)
	CHIP("K6", 7402)
    CHIP("K7", 7474)
    CHIP("K8", 7404)
    CHIP("K9", 7450)
	
	CHIP("L1", 7402)
	CHIP("L2", 7400)
	CHIP("L3", 7493)
	CHIP("L4", 9316)
    CHIP("L5", 7493)
    CHIP("L6", 7408)
    CHIP("L7", 7402)
    CHIP("L8", 74193)
    CHIP("L9", 7400)
	
	CHIP("M1", 7474)
	CHIP("M2", 7486)
	CHIP("M3", 7474)
	CHIP("M4", 9316)
	CHIP("M5", 7410)
    CHIP("M6", 7400)
	CHIP("M7", 7400)
	CHIP("M8", 74193)
    CHIP("M9", 7420)

	CHIP("N1", 7493)
	CHIP("N2", 7485)
	CHIP("N3", 7404)
	CHIP("N4", 7474)
	CHIP("N5", 7400)
    CHIP("N6", 9602, &n6_desc)
    CHIP("N7", 7474)
    CHIP("N8", 7408)
    CHIP("N9", 7400)

	CHIP("C57", CAPACITOR, &c57_desc)
	CHIP("C58", CAPACITOR, &c58_desc)
    CHIP("C13", SERIES_RC, &c13_desc)
	
    CHIP("START", START_INPUT)
    CHIP("COIN", COIN_INPUT)
    CHIP("LATCH", LATCH)

    CHIP("DSW1", DIPSWITCH, &dipswitch1_desc)
    CHIP("DSW2", DIPSWITCH, &dipswitch2_desc)

    VIDEO(stuntcycle)
    INPUT(stuntcycle)

    // Throttle
    CHIP("THROTTLE", THROTTLE1_INPUT, &throttle_desc)
    CHIP("STUNT_THROTTLE", STUNTCYCLE_THROTTLE, &stunt_cycle_throttle_desc)
    THROTTLE_CONNECTION("THROTTLE", "STUNT_THROTTLE")

#ifdef DEBUG
	CHIP("LOG1", VCD_LOG, &vcd_log_desc)
#endif

    OPTIMIZATION_HINT("N2", 256, 64)
    OPTIMIZATION_HINT("M1", 256, 64)
    OPTIMIZATION_HINT("B3", 64, 64)
    OPTIMIZATION_HINT("C3", 64, 64)
    OPTIMIZATION_HINT("B4", 16, 64)
    OPTIMIZATION_HINT("C4", 16, 64)
    OPTIMIZATION_HINT("D2", 8, 64)

#ifdef USE_CLK_GATES
    CHIP("CLK_GATE1", CLK_GATE)
    CHIP("CLK_GATE2", CLK_GATE)
    CHIP("CLK_GATE3", CLK_GATE)
    CHIP("CLK_GATE4", CLK_GATE)

    DISABLE_OPTIMIZATION("F2", 1)
    DISABLE_OPTIMIZATION("F2", i8)
    DISABLE_OPTIMIZATION("E1", 11)
    DISABLE_OPTIMIZATION("E2", 11)
#endif

	/**************************************************************************
		Lines
	**************************************************************************/	
	#define HF_CLOCK  "CLOCK", 1
	#define CLOCK  "N4", 9
	#define CLOCK_n  "N4", 8
	
	#define _1H  "M4", 14
	#define _2H  "M4", 13
	#define _4H  "M4", 12
	#define _8H  "M4", 11

	#define _16H  "L4", 14
	#define _32H  "L4", 13
	#define _64H  "L4", 12
	#define _128H  "L4", 11
	
	#define _256H  "K4", 3
	#define _256H_n  "K4", 2
	
	#define HRESET_n  "J6", 6
	#define HRESET  "H6", 6

	#define _1V  "L3", 12
	#define _2V  "L3", 9
	#define _4V  "L3", 8
	#define _8V  "L3", 11
	
	#define _16V  "K3", 12
	#define _32V  "K3", 9
	#define _64V  "K3", 8
	#define _128V  "K3", 11
	
	#define _256V  "K4", 5
	#define _256V_n  "K4", 6
	
	#define VRESET_n  "M3", 9
	#define VRESET  "M3", 8
	
	#define HSYNC  "J5", 1
	#define HSYNC_n  "J5", 4
	
	#define VSYNC  "J5", 10
	#define VSYNC_n  "J5", 13
	
	#define _32H_xor_256H  "J4", 6
	#define _128H_xor_256H  "J4", 8
	
	#define HSCORE_n  "H4", 8
	#define VSCORE_n  "H4", 12
	#define SCORE_WINDOW  "J3", 1
	
    #define PLAYER_CONTROL "H6", 8
    #define PLAYER_CONTROL_n "D5", 11

    #define RETURN_THROTTLE GND // TEMP
    #define RETURN_THROTTLE_n "K8", 2
    #define FREE_PLAY "F8", 6
    #define FREE_PLAY_n "F8", 5
    #define ATTRACT "D9", 8
    #define ATTRACT_n "D9", 9

	#define COMP_SCORE_n  "A5", 5
	#define SCORE1_n  "M7", 6
	#define SCORE2  "K6", 1
	
	#define ROAD_n  "H4", 6
	
	//#define FIXED_RAMP_ZONE  "D8", 8
	#define FIXED_RAMP_ZONE  "C58", 2
	#define FIXED_RAMP_ZONE_n  "H6", 4
	#define OBJECT_ZONE  "J7", 9
	#define OBJECT_ZONE_n  "J7", 8
	#define VRAMP  "N3", 8
    #define VRAMP_n "E3", 8 // Is this correct? Name not shown
	#define RAMPS  "L1", 4
    #define RAMPS_n "L1", 10

	#define H1  "C3", 14
	#define H2  "C3", 13
	#define H3  "C3", 12
	#define H4  "C3", 11
	#define H5  "B3", 14
	#define H6  "B3", 13
	#define H7  "B3", 12
	#define H8  "B3", 11

	#define V1  "K1", 14
	#define V2  "K1", 13
	#define V3  "K1", 12
	#define V4  "K1", 11

    #define DIRECTION "M3", 5
    #define DIRECTION_n "M3", 6

    #define HWINDOW "E4", 12
    #define HWINDOW_DELAYED "A4", 5
    #define HCOUNTER_RESET_n "D5", 3

    #define VWINDOW "K2", 15
    #define VCOUNTER_RESET_n "L2", 6
				
    #define CYCLE_WINDOW "L6", 11

    #define CYCLE_RESET_n "N6", 9
    #define CYCLE_RESET "N6", 10
    #define CYCLE_RESET_A_n "K8", 4

    #define GRAVITY "L6", 8

    #define OBJECT_HIT_n "M7", 3

    #define JUMP "N9", 11
    #define JUMP_n "N9", 3

    #define FLIP "N7", 5
    #define FLIP_n "N7", 6

    #define GOOD_JUMP "K7", 5
    #define GOOD_JUMP_n "K7", 6
    #define BAD_JUMP "K7", 9
    #define BAD_JUMP_n "K7", 8

    #define MS1 "B2", 11
    #define MS2 "B2", 3
    #define MS3 "N7", 8

    #define CYCLE "D2", 8
    #define CYCLE_n "D2", 9

    #define R2 "M8", 2
    #define R3 "M8", 6
    #define R4 "C1", 11

    #define START "D9", 6
    #define START_n "D9", 5

	/**************************************************************************
		Layout
	**************************************************************************/
	/* Clock */
    CONNECTION(VCC, "N4", 10)
	CONNECTION("N4", 8, "N4", 12)
	CONNECTION(HF_CLOCK, "N4", 11)
	CONNECTION(VCC, "N4", 13)
	
	/* Horizontal Counter */
	CONNECTION(CLOCK, "M4", 2)
	CONNECTION(VCC, "M4", 7)
	CONNECTION(VCC, "M4", 10)
	CONNECTION(GND, "M4", 3)
	CONNECTION(GND, "M4", 4)
	CONNECTION(GND, "M4", 5)
	CONNECTION(GND, "M4", 6)
	CONNECTION("J6", 6, "M4", 9)
	CONNECTION(VCC, "M4", 1)

	CONNECTION(CLOCK, "L4", 2)
	CONNECTION("M4", 15, "L4", 7)
	CONNECTION(VCC, "L4", 10)
	CONNECTION(GND, "L4", 3)
	CONNECTION(GND, "L4", 4)
	CONNECTION(GND, "L4", 5)
	CONNECTION(GND, "L4", 6)
	CONNECTION("J6", 6, "L4", 9)
	CONNECTION(VCC, "L4", 1)
	
	CONNECTION(VCC, "K4", 1)
	CONNECTION("L4", 11, "K4", 12)
	CONNECTION(VCC, "K4", 4)
	CONNECTION(VCC, "K4", 13)
	
	CONNECTION("K4", 3, "J6", 5)
	CONNECTION("L4", 11, "J6", 4)
	CONNECTION("L4", 12, "J6", 2)
	CONNECTION("M4", 11, "J6", 1)
	
	CONNECTION("J6", 6, "H6", 5)
	
	
	
	/* Vertical Counter */
	CONNECTION("H6", 6, "L3", 14)
	CONNECTION("L3", 12, "L3", 1)
	CONNECTION("M3", 8, "L3", 2)
	CONNECTION("M3", 8, "L3", 3)
	
	CONNECTION("L3", 11, "K3", 14)
	CONNECTION("K3", 12, "K3", 1)
	CONNECTION("M3", 8, "K3", 2)
	CONNECTION("M3", 8, "K3", 3)
	
	CONNECTION("K3", 11, "K4", 9)
	CONNECTION(VCC, "K4", 8)
	CONNECTION(VCC, "K4", 11)
	CONNECTION("M3", 9, "K4", 10)
	
	CONNECTION("K4", 5, "M5", 9)
	CONNECTION("L3", 9, "M5", 10)
	CONNECTION("L3", 12, "M5", 11)
	
	CONNECTION("M5", 8, "M3", 12)
	CONNECTION(VCC, "M3", 10)
	CONNECTION(VCC, "M3", 13)
	CONNECTION("H6", 6, "M3", 11)
	
	
	
	/* H and V Sync */
	CONNECTION("H6", 6, "J5", 6)
	CONNECTION("J5", 1, "J5", 5)
	
	CONNECTION("J5", 4, "J5", 3)
	CONNECTION(_32H, "J5", 2)
		
	CONNECTION(_8V, "J5", 8)
	CONNECTION("J5", 13, "J5", 9)
	
	CONNECTION("J5", 10, "J5", 11)
	CONNECTION("M3", 8, "J5", 12)
		
	
	
	/* Score Window */
	CONNECTION(_64V, "L1", 11)
	CONNECTION(_128V, "L1", 12)
	
	CONNECTION(_32H, "J4", 4)
	CONNECTION(_256H, "J4", 5)

	CONNECTION(_128H, "J4", 10)
	CONNECTION(_256H, "J4", 9)
	
	CONNECTION(_64H, "J4", 13)
	CONNECTION(_256H_n, "J4", 12)
	
	CONNECTION("L1", 13, "H4", 2)
	CONNECTION(_16V, "H4", 1)
	CONNECTION(_32V, "H4", 13)
	
	CONNECTION("J4", 6, "H4", 10)
	CONNECTION("J4", 8, "H4", 9)
	CONNECTION("J4", 11, "H4", 11)
	
	CONNECTION("H4", 12, "J3", 2)
	CONNECTION("H4", 8, "J3", 3)

	
	
	/* Scores */
    CONNECTION(CYCLE_RESET_A_n, "A3", 2)
    CONNECTION("C4", 6, "A3", 1)

    CONNECTION("A3", 3, "C4", 3)
    CONNECTION(BAD_JUMP_n, "C4", 4)
    CONNECTION(FLIP_n, "C4", 5)

    CONNECTION(COMP_SCORE_n, "C5", 4)
    CONNECTION(GND, "C5", 2)
    CONNECTION("A3", 3, "C5", 3)
    CONNECTION("D6", 8, "C5", 1)

    CONNECTION("H8", 6, "D6", 11)
    CONNECTION(VRESET, "D6", 10)
    CONNECTION("E5", 3, "D6", 9)

    CONNECTION("D7", 6, "K6", 5)
    CONNECTION("H3", 8, "K6", 6)

    CONNECTION("C5", 6, "K6", 8)
    CONNECTION("K6", 4, "K6", 9)

    CONNECTION(ATTRACT_n, "H5", 12)
    CONNECTION(_128V, "H5", 13)

    CONNECTION(VCC, "C5", 10)
    CONNECTION("D7", 6, "C5", 12)
    CONNECTION(GOOD_JUMP_n, "C5", 11)
    CONNECTION("H5", 11, "C5", 13)

    CONNECTION("K6", 10, "D5", 10)
    CONNECTION("M6", 8, "D5", 9)

    CONNECTION(VCC, "F5", 1)
    CONNECTION(VCC, "F5", 4)
    CONNECTION(VCC, "F5", 12)
    CONNECTION(GND, "F5", 2)
    CONNECTION(GND, "F5", 3)
    CONNECTION(GND, "F5", 11)

    CONNECTION(GND, "E5", 15)
    CONNECTION("F5", 15, "E5", 1)
    CONNECTION("F5", 14, "E5", 10)
    CONNECTION("F5", 6, "E5", 9)
    CONNECTION(START_n, "E5", 11)
    CONNECTION(VCC, "E5", 5)
    CONNECTION("D5", 8, "E5", 4)
    CONNECTION(GND, "E5", 14)

    CONNECTION("E5", 3, "A8", 5)
    CONNECTION("C5", 8, "A8", 6)

    CONNECTION("C5", 9, "B5", 5)
    CONNECTION("E5", 3, "B5", 4)

    // SCORE 1
    CONNECTION(GND, "B8", 15)
    CONNECTION(GND, "B8", 1)
    CONNECTION(GND, "B8", 10)
    CONNECTION(VCC, "B8", 9)
    CONNECTION(START_n, "B8", 11)
    CONNECTION("A8", 4, "B8", 5)
    CONNECTION(VCC, "B8", 4)
    CONNECTION(GND, "B8", 14)

    CONNECTION(VCC, "A9", 10)
    CONNECTION("A9", 8, "A9", 12)
    CONNECTION("B8", 12, "A9", 11)
    CONNECTION(START_n, "A9", 13)
    
    CONNECTION("A9", 9, "A8", 8)
    CONNECTION("B8", 7, "A8", 9)

    // SCORE 2
    CONNECTION(GND, "B9", 15)
    CONNECTION(GND, "B9", 1)
    CONNECTION(GND, "B9", 10)
    CONNECTION(VCC, "B9", 9)
    CONNECTION(START_n, "B9", 11)
    CONNECTION("B5", 6, "B9", 5)
    CONNECTION(VCC, "B9", 4)
    CONNECTION(GND, "B9", 14)

    CONNECTION(VCC, "A9", 4)
    CONNECTION("A9", 6, "A9", 2)
    CONNECTION("B9", 12, "A9", 3)
    CONNECTION(START_n, "A9", 1)
    
    CONNECTION("A9", 5, "A8", 2)
    CONNECTION("B9", 7, "A8", 3)

    CONNECTION("H8", 5, "D5", 13)
    CONNECTION("E5", 3, "D5", 12)

    CONNECTION("D5", 11, "H6", 9)

	CONNECTION("D5", 11, "D1", 9)
	CONNECTION(_128V, "D1", 10)
	CONNECTION("D3", 4, "D1", 1)
	CONNECTION(_256H_n, "D1", 13)
	
	CONNECTION(_128V, "D3", 3)
	
	CONNECTION("D1", 8, "B7", 1)
	CONNECTION("B9", 3, "B7", 3)
	CONNECTION("B8", 3, "B7", 2)
	CONNECTION("B9", 2, "B7", 6)
	CONNECTION("B8", 2, "B7", 5)
	CONNECTION("B9", 6, "B7", 13)
	CONNECTION("B8", 6, "B7", 14)
	CONNECTION("B9", 7, "B7", 10)
	CONNECTION("B8", 7, "B7", 11)
	CONNECTION(GND, "B7", 15)
	
	CONNECTION("D1", 8, "A7", 1)
	CONNECTION("A9", 5, "A7", 3)
	CONNECTION("A9", 9, "A7", 2)
	CONNECTION("A8", 1, "A7", 6)
	CONNECTION("A8", 10, "A7", 5)
	CONNECTION(GND, "A7", 13)
	CONNECTION(GND, "A7", 14)
	CONNECTION(GND, "A7", 10)
	CONNECTION(GND, "A7", 11)
	CONNECTION(GND, "A7", 15)
	
	CONNECTION(_16H, "C7", 1)
	CONNECTION("B7", 4, "C7", 3)
	CONNECTION("A7", 4, "C7", 2)
	CONNECTION("B7", 7, "C7", 6)
	CONNECTION("A7", 7, "C7", 5)
	CONNECTION("B7", 12, "C7", 13)
	CONNECTION(GND, "C7", 14)
	CONNECTION("B7", 9, "C7", 10)
	CONNECTION(GND, "C7", 11)
	CONNECTION(GND, "C7", 15)
	
	CONNECTION(_16H, "C6", 5)
	CONNECTION("C7", 4, "C6", 7)
	CONNECTION("C7", 7, "C6", 1)
	CONNECTION("C7", 12, "C6", 2)
	CONNECTION("C7", 9, "C6", 6)
	CONNECTION(SCORE_WINDOW, "C6", 4)
	CONNECTION(VCC, "C6", 3)
	
	CONNECTION("C6", 11, "B6", 9)
	CONNECTION(GND, "B6", 7)
	CONNECTION(GND, "B6", 6)
	CONNECTION("C6", 9, "B6", 5)
	CONNECTION("C6", 12, "B6", 4)
	CONNECTION(GND, "B6", 3)
	CONNECTION(GND, "B6", 2)
	CONNECTION("C6", 15, "B6", 1)
	CONNECTION(_2H, "B6", 11)
	CONNECTION(_4H, "B6", 12)
	CONNECTION(_8V, "B6", 13)
	CONNECTION(_8H, "B6", 10)
	
	CONNECTION("C6", 10, "A6", 9)
	CONNECTION(GND, "A6", 7)
	CONNECTION(GND, "A6", 6)
	CONNECTION(GND, "A6", 5)
	CONNECTION("C6", 14, "A6", 4)
	CONNECTION(GND, "A6", 3)
	CONNECTION(GND, "A6", 2)
	CONNECTION("C6", 13, "A6", 1)
	CONNECTION(_2V, "A6", 11)
	CONNECTION(_4V, "A6", 12)
	CONNECTION(_8V, "A6", 13)
	CONNECTION(_8H, "A6", 10)
	
	CONNECTION("B6", 14, "B5", 13)
	CONNECTION("A6", 14, "B5", 12)
	
	CONNECTION(VCC, "A5", 4)
	CONNECTION("B5", 11, "A5", 2)
	CONNECTION(CLOCK, "A5", 3)
	CONNECTION(VCC, "A5", 1)
	
	CONNECTION("A5", 6, "M7", 5)
	CONNECTION(_128H, "M7", 4)
	
	CONNECTION("A5", 5, "K6", 2)
	CONNECTION(_128H, "K6", 3)
	
	
	
	/* Road Circuit */
	CONNECTION(VCC, "H3", 10)
	CONNECTION(VCC, "H3", 12)
	CONNECTION(VSYNC_n, "H3", 11)
	CONNECTION("H2", 11, "H3", 13)
	
	CONNECTION(_8V, "H2", 12)
	CONNECTION(_32V, "H2", 13)
	
	CONNECTION("H3", 8, "J3", 11)
	CONNECTION(HSYNC, "J3", 12)
	
	CONNECTION(_128H_xor_256H, "H2", 10)
	CONNECTION("J3", 13, "H2", 9)
	
	CONNECTION(_256H_n, "J3", 5)
	CONNECTION("H2", 8, "J3", 6)
	
	CONNECTION(_256H, "J3", 9)
	CONNECTION("H2", 8, "J3", 8)
	
    CONNECTION(_256H, "C8", 10)
    CONNECTION(PLAYER_CONTROL, "C8", 9)

	CONNECTION("H3", 8, "H3", 4)
	CONNECTION(_32V, "H3", 2)
	CONNECTION(_1V, "H3", 3)
	CONNECTION(VCC, "H3", 1)
	
	CONNECTION(_1H, "H4", 3)
	CONNECTION(_32V, "H4", 5)
	CONNECTION("H3", 6, "H4", 4)
	
	CONNECTION(RETURN_THROTTLE, "K8", 1)

    CONNECTION(ATTRACT, "F3", 2)
    CONNECTION("J3", 4, "F3", 3)
    CONNECTION("J3", 10, "F3", 4)
    CONNECTION(FREE_PLAY, "F3", 5)

    CONNECTION(ATTRACT_n, "F3", 1)
    CONNECTION("J3", 4, "F3", 13)
    CONNECTION("J3", 10, "F3", 10)
    CONNECTION(FREE_PLAY_n, "F3", 9)

    CONNECTION(PLAYER_CONTROL, "D4", 2)
    CONNECTION(CYCLE_n, "D4", 3)

    CONNECTION("F3", 6, "D3", 5)

    CONNECTION(VSCORE_n, "K5", 11)
    CONNECTION(_32H_xor_256H, "K5", 10)
    CONNECTION(_64H, "K5", 9)

    CONNECTION("K5", 8, "F4", 13)
    CONNECTION(_128H_xor_256H, "F4", 12)

    CONNECTION("F4", 11, "D4", 5)
    CONNECTION("C8", 8, "D4", 6)
    
    CONNECTION("F4", 11, "D3", 1)

    CONNECTION("C8", 8, "F4", 9)
    CONNECTION("D3", 2, "F4", 10)

    CONNECTION(CYCLE, "F4", 5)
    CONNECTION(PLAYER_CONTROL, "F4", 4)



	
	/* Ramps Circuit */
	CONNECTION("B7", 4, "D7", 10)
	CONNECTION("B7", 7, "D7", 11)
	CONNECTION("B7", 12, "D7", 12)
	CONNECTION("B7", 9, "D7", 13)
	CONNECTION("A7", 4, "D7", 14)
    CONNECTION(GND, "D7", 15)
	
	CONNECTION("D7", 5,  "C8", 5)
	CONNECTION("D6", 12, "C8", 4)
	
	CONNECTION("D7", 1, "E6", 10)
	CONNECTION("D7", 2, "E6", 12)
	CONNECTION("D7", 3, "E6", 13)
	CONNECTION("D7", 4, "E6", 15)
	CONNECTION(_8H, "E6", 9)
	CONNECTION(_16H, "E6", 11)
	CONNECTION(_32H, "E6", 14)
	CONNECTION(_64H, "E6", 1)
	CONNECTION("C8", 6, "E6", 3)
	CONNECTION(GND, "E6", 4)
	CONNECTION(GND, "E6", 2)

    CONNECTION("D7", 5, "K6", 11)
    CONNECTION(OBJECT_ZONE_n, "K6", 12)

    CONNECTION(VCC, "F7", 9)
    CONNECTION(VCC, "F7", 12)
    CONNECTION(VCC, "F7", 4)
    CONNECTION(VCC, "F7", 1)
    CONNECTION(GND, "F7", 10)
    CONNECTION(GND, "F7", 11)
    CONNECTION(GND, "F7", 3)
    CONNECTION(GND, "F7", 2)

	CONNECTION("D7", 1, "E7", 10)
	CONNECTION("D7", 2, "E7", 12)
	CONNECTION("D7", 3, "E7", 13)
	CONNECTION("D7", 4, "E7", 15)
	CONNECTION("F7", 15, "E7", 9)
	CONNECTION("F7", 14, "E7", 11)
	CONNECTION("F7", 6, "E7", 14)
	CONNECTION("F7", 7, "E7", 1)
	CONNECTION("K6", 13, "E7", 3)
	CONNECTION(GND, "E7", 4)
	CONNECTION(GND, "E7", 2)

	CONNECTION(_256H_n, "D6", 1)
	CONNECTION(_128H, "D6", 2)
	CONNECTION(_128H, "D6", 13)
	
	CONNECTION(_32H, "D8", 10)
	CONNECTION("D6", 12, "D8", 11)
	CONNECTION(_64H, "D8", 9)

	CONNECTION("D8", 8, "C58", 1)
	
	CONNECTION(VCC, "F6", 4)
	CONNECTION("E6", 6, "F6", 2)
	CONNECTION(CLOCK_n, "F6", 3)
	CONNECTION(_128H_xor_256H, "F6", 1)

	CONNECTION("H7", 15, "H6", 1)
	
	CONNECTION("F6", 6, "H7", 9)
	CONNECTION("H6", 2, "H7", 7)
	CONNECTION(VCC, "H7", 10)
	CONNECTION(_1H, "H7", 2)
	CONNECTION(VCC, "H7", 3)
	CONNECTION(VCC, "H7", 4)
	CONNECTION(GND, "H7", 5)
	CONNECTION(GND, "H7", 6)
	CONNECTION(VCC, "H7", 1)
	
	CONNECTION("H7", 15, "H5", 10)
	CONNECTION("F6", 6, "H5", 9)
	
	CONNECTION("H5", 8, "M2", 5)
	CONNECTION(_1V, "M2", 4)
	
	CONNECTION("H5", 8, "M2", 13)
	CONNECTION(_2V, "M2", 12)
	
	CONNECTION("H5", 8, "M2", 2)
	CONNECTION(_4V, "M2", 1)
	
	CONNECTION(_16V, "L2", 1)
	CONNECTION(_64V, "L2", 2)
	
	CONNECTION(_32V, "L1", 3)
	CONNECTION("L2", 3, "L1", 2)
	
	CONNECTION("L1", 1, "E3", 11)
	CONNECTION(_8V, "E3", 9)
	CONNECTION(_128V, "E3", 10)
	
	CONNECTION("E3", 8, "N3", 9)
	
	CONNECTION("H5", 3, "N1", 2)
	CONNECTION("H5", 3, "N1", 3)
	CONNECTION("N1", 12, "N1", 1)
	CONNECTION(_2H, "N1", 14)
	
	CONNECTION("N1", 12, "N2", 9)
	CONNECTION("N1", 9, "N2", 11)
	CONNECTION("N1", 8, "N2", 14)
	CONNECTION("N1", 11, "N2", 1)
	CONNECTION("M2", 6, "N2", 10)
	CONNECTION("M2", 11, "N2", 12)
	CONNECTION("M2", 3, "N2", 13)
	CONNECTION(GND, "N2", 15)
	CONNECTION(VCC, "N2", 2) //Not shown?
	CONNECTION(VCC, "N2", 3) //Not shown?
	CONNECTION(VCC, "N2", 4) //Not shown?
	
	CONNECTION("N2", 5, "M2", 9)
	CONNECTION("H5", 8, "M2", 10)
	
	CONNECTION(VCC, "M1", 10)
	CONNECTION("M2", 8, "M1", 12)
	CONNECTION(_1H, "M1", 11)
	CONNECTION("N3", 8, "M1", 13)


	CONNECTION(FIXED_RAMP_ZONE, "H6", 3)
	
	CONNECTION(VCC, "J7", 10)
	CONNECTION(VRAMP, "J7", 12)
	CONNECTION("H6", 4, "J7", 11)
	CONNECTION("H7", 15, "J7", 13)
	
	CONNECTION("H6", 4, "H5", 1)
	CONNECTION("H7", 15, "H5", 2)
	
	CONNECTION("H5", 3, "L1", 5)
	CONNECTION("M1", 8, "L1", 6)

    CONNECTION(RAMPS, "L1", 8)
    CONNECTION(RAMPS, "L1", 9)

    CONNECTION(VCC, "A5", 10)
    CONNECTION(VCC, "A5", 12)
    CONNECTION("H7", 15, "A5", 11)
    CONNECTION(HRESET_n, "A5", 13)

    CONNECTION(VCC, "J7", 4)
    CONNECTION("A5", 8, "J7", 2)
    CONNECTION(HWINDOW, "J7", 3)
    CONNECTION("K7", 8, "J7", 1)

    CONNECTION(VCC, "K7", 4)
    CONNECTION("J7", 5, "K7", 2)
    CONNECTION(JUMP_n, "K7", 3)
    CONNECTION(CYCLE_RESET_A_n, "K7", 1)

    CONNECTION(OBJECT_HIT_n, "K7", 10)
    CONNECTION("J7", 6, "K7", 12)
    CONNECTION(JUMP_n, "K7", 11)
    CONNECTION(CYCLE_RESET_A_n, "K7", 13)

    CONNECTION(CYCLE_RESET, "L2", 12)
    CONNECTION(VRESET, "L2", 13)

    CONNECTION("L1", 1, "M1", 2)
    CONNECTION("M1", 6, "M1", 4)
    CONNECTION(_8V, "M1", 3)
    CONNECTION("L2", 11, "M1", 1)

    CONNECTION("L1", 1, "L2", 5)
    CONNECTION("M1", 6, "L2", 4)





    /* Horizontal Cycle Counter */
    CONNECTION(VCC, "C2", 4)
    CONNECTION(VCC, "C2", 2)
    CONNECTION("STUNT_THROTTLE", StuntCycleThrottleDesc::SPEED_PULSES_PIN, "C2", 3)
    CONNECTION("C2", 8, "C2", 1)

    CONNECTION(VCC, "C2", 10)
    CONNECTION("C2", 5, "C2", 12)
    CONNECTION("A3", 6, "C2", 11)
    CONNECTION(VCC, "C2", 13)
    
    CONNECTION(DIRECTION_n, "B2", 4)
    CONNECTION("C2", 9, "B2", 5)

    CONNECTION("C2", 5, "C1", 14)
    CONNECTION("C1", 12, "C1", 1)
    CONNECTION(FLIP, "C1", 2)
    CONNECTION(FLIP, "C1", 3)

	CONNECTION(HF_CLOCK, "C3", 2)
	CONNECTION(VCC, "C3", 7)
	CONNECTION(VCC, "C3", 10)
	CONNECTION("C2", 9, "C3", 3)
	CONNECTION("B2", 6, "C3", 4)
	CONNECTION(VCC, "C3", 5)
	CONNECTION(VCC, "C3", 6)
	CONNECTION("A3", 6, "C3", 9)
	CONNECTION(HCOUNTER_RESET_n, "C3", 1)

	CONNECTION(HF_CLOCK, "B3", 2)
	CONNECTION("C3", 15, "B3", 7)
	CONNECTION(VCC, "B3", 10)
	CONNECTION(GND, "B3", 3)
	CONNECTION(VCC, "B3", 4)
	CONNECTION(VCC, "B3", 5)
	CONNECTION(GND, "B3", 6)
	CONNECTION("A3", 6, "B3", 9)
	CONNECTION(HCOUNTER_RESET_n, "B3", 1)

    CONNECTION("B3", 13, "B5", 10)
    CONNECTION("B3", 14, "B5", 9)
    
    CONNECTION(VCC, "B4", 8)
    CONNECTION("B3", 15, "B4", 9)
    CONNECTION(VCC, "B4", 11)
	CONNECTION(HCOUNTER_RESET_n, "B4", 10)
	
    CONNECTION(VCC, "B4", 1)
	CONNECTION("B4", 5, "B4", 12)
    CONNECTION(VCC, "B4", 4)
    CONNECTION(HCOUNTER_RESET_n, "B4", 13)

    CONNECTION("B3", 15, "C4", 2)
    CONNECTION("B4", 5, "C4", 13)
    CONNECTION("B4", 2, "C4", 1)

    CONNECTION("C4", 12, "D3", 13)
    
    CONNECTION("B4", 3, "C4", 11)
    CONNECTION("B4", 5, "C4", 9)
    CONNECTION("B3", 11, "C4", 10)

    CONNECTION("C4", 8, "E4", 13)
    CONNECTION("B3", 12, "E4", 2)
    CONNECTION("B5", 8, "E4", 1)

    CONNECTION("C3", 15, "A3", 5)
    CONNECTION("D3", 12, "A3", 4)

    CONNECTION(VCC, "A4", 4)
    CONNECTION("E4", 12, "A4", 2)
    CONNECTION(H4, "A4", 3)
    CONNECTION(VCC, "A4", 1)

    CONNECTION(VCC, "A4", 10)
    CONNECTION(H4, "A4", 12)
    CONNECTION(H2, "A4", 11)
    CONNECTION("A4", 5, "A4", 13)

    CONNECTION("A4", 8, "A8", 12)
    CONNECTION(H4, "A8", 11)

    CONNECTION("A8", 13, "D3", 9)

    CONNECTION(DIRECTION, "B2", 12)
    CONNECTION("D3", 8, "B2", 13)
    
    CONNECTION(DIRECTION_n, "B2", 1)
    CONNECTION("D3", 8, "B2", 2)

    CONNECTION(CYCLE_RESET_n, "D5", 5)
    CONNECTION("D5", 3, "D5", 4)
    CONNECTION(FIXED_RAMP_ZONE_n, "D5", 1)
    CONNECTION("D5", 6, "D5", 2)





    /* Vertical Cycle Counter */
    CONNECTION(HWINDOW, "N5", 5)
    CONNECTION(FIXED_RAMP_ZONE, "N5", 4)

    CONNECTION(HSYNC, "N4", 2)
    CONNECTION(HWINDOW, "N4", 3)
    CONNECTION("N4", 6, "N4", 4)
    CONNECTION("N5", 6, "N4", 1)

    CONNECTION(VCC, "M3", 4)
    CONNECTION("M3", 6, "M3", 2)
    CONNECTION("N4", 5, "M3", 3)
    CONNECTION(CYCLE_RESET_n, "M3", 1)

    CONNECTION(VCC, "J2", 4)
    CONNECTION(VCC, "J2", 2)
    CONNECTION("N4", 5, "J2", 3)
    CONNECTION("J2", 8, "J2", 1)

    CONNECTION(_32V, "N3", 5)

    CONNECTION(VCC, "J2", 10)
    CONNECTION("J2", 5, "J2", 12)
    CONNECTION("N3", 6, "J2", 11)
    CONNECTION(VCC, "J2", 13)

    CONNECTION(_256V_n, "H5", 4)
    CONNECTION(VSYNC_n, "H5", 5)

	CONNECTION(HSYNC, "K1", 2)
	CONNECTION(VCC, "K1", 7)
	CONNECTION("H5", 6, "K1", 10)
    CONNECTION("L8", 3, "K1", 3)
	CONNECTION("L8", 2, "K1", 4)
	CONNECTION("L8", 6, "K1", 5)
	CONNECTION("K8", 6, "K1", 6)
	CONNECTION("L2", 8, "K1", 9)
	CONNECTION(VCOUNTER_RESET_n, "K1", 1)

    CONNECTION(HSYNC, "K2", 2)
	CONNECTION("K1", 15, "K2", 7)
	CONNECTION("J2", 8, "K2", 10)
	CONNECTION(GND, "K2", 3)
	CONNECTION(GND, "K2", 4)
	CONNECTION(GND, "K2", 5)
	CONNECTION(GND, "K2", 6)
	CONNECTION("L2", 8, "K2", 9)
	CONNECTION(VCOUNTER_RESET_n, "K2", 1)

    CONNECTION("K1", 15, "L2", 9)
    CONNECTION("K2", 15, "L2", 10)





    /* Cycle Movement Logic */
    CONNECTION(RAMPS, "N8", 2)
    CONNECTION(CYCLE_WINDOW, "N8", 1)

    CONNECTION(VWINDOW, "L6", 13)
    CONNECTION(HWINDOW_DELAYED, "L6", 12)

    CONNECTION(CYCLE, "M7", 2)
    CONNECTION(OBJECT_ZONE, "M7", 1)

    CONNECTION(FIXED_RAMP_ZONE, "N9", 4)
    CONNECTION("N8", 3, "N9", 5)

    CONNECTION("M7", 3, "N8", 12)
    CONNECTION("N9", 6, "N8", 13)

    CONNECTION("N8", 11, "C57", 1)

    CONNECTION("C57", 2, "N9", 12)
    CONNECTION("N9", 3, "N9", 13)
    CONNECTION("N9", 11, "N9", 2)
    CONNECTION(MS3, "N9", 1)

    CONNECTION("N9", 11, "N9", 10)
    CONNECTION(BAD_JUMP_n, "N9", 9)

    CONNECTION("M8", 13, "M7", 13)
    CONNECTION(MS3, "M7", 12)

    CONNECTION(BAD_JUMP_n, "M7", 10)
    CONNECTION(MS3, "M7", 9)
    
    CONNECTION(BAD_JUMP_n, "L9", 12)
    CONNECTION("M7", 11, "L9", 13)

    CONNECTION(CYCLE_RESET_n, "L9", 9)
    CONNECTION("L9", 11, "L9", 10)

    CONNECTION(BAD_JUMP_n, "M9", 4)
    CONNECTION("STUNT_THROTTLE", 12, "M9", 1)
    CONNECTION(GRAVITY, "M9", 2)
    CONNECTION("M5", 6, "M9", 5)

    CONNECTION("STUNT_THROTTLE", 10, "L9", 1)
    CONNECTION(BAD_JUMP_n, "L9", 2)

    CONNECTION(_64V, "L9", 5)
    CONNECTION(BAD_JUMP, "L9", 4)

    CONNECTION("M5", 6, "M9", 10)
    CONNECTION(GRAVITY, "M9", 13)
    CONNECTION("L9", 3, "M9", 12)
    CONNECTION("L9", 6, "M9", 9)

    CONNECTION("M9", 6, "M8", 5)
    CONNECTION("M9", 8, "M8", 4)
    CONNECTION(VCC, "M8", 15)
    CONNECTION(VCC, "M8", 1)
    CONNECTION(GND, "M8", 10)
    CONNECTION(GND, "M8", 9)
    CONNECTION("N9", 8, "M8", 11)
    CONNECTION("L9", 8, "M8", 14)

    CONNECTION(CYCLE_RESET_A_n, "N7", 10)
    CONNECTION(VWINDOW, "N7", 12)
    CONNECTION(VRAMP_n, "N7", 11)
    CONNECTION(VCC, "N7", 13)

    CONNECTION(VCC, "L8", 5)
    CONNECTION(GRAVITY, "L8", 4)
    CONNECTION(FIXED_RAMP_ZONE_n, "L8", 15)
    //CONNECTION(VCC, "L8", 10)
    //CONNECTION(VCC, "L8", 9)
    CONNECTION(GND, "L8", 10) // Schematic says VCC ???
    CONNECTION(GND, "L8", 9) // Schematic says VCC ???
    CONNECTION(FIXED_RAMP_ZONE, "L8", 1)
    CONNECTION("N8", 11, "L8", 11)
    CONNECTION("N9", 3, "L8", 14)

    CONNECTION("L8", 7, "K8", 5)

    // Rev B
    /*CONNECTION(_128V, "K5", 5)
    CONNECTION(HSYNC, "K5", 4)
    CONNECTION(_16V, "K5", 3)

    CONNECTION("K5", 6, "M6", 10)
    CONNECTION(CYCLE, "M6", 9)*/

    // Rev D
    CONNECTION(JUMP, "M6", 10)
    CONNECTION("J2", 9, "M6", 9)

    CONNECTION(CYCLE, "M5", 13)
    CONNECTION(HRESET, "M5", 2)
    CONNECTION("M7", 8, "M5", 1)

    CONNECTION("M6", 8, "L6", 2)
    CONNECTION("M5", 12, "L6", 1)

    CONNECTION(JUMP, "M6", 13)
    CONNECTION("L7", 13, "M6", 12)

    CONNECTION(FLIP, "M6", 2)
    CONNECTION(JUMP_n, "M6", 1)

    CONNECTION("L6", 3, "L6", 4)
    CONNECTION("M6", 11, "L6", 5)

    CONNECTION("M6", 3, "N6", 5)
    CONNECTION(BAD_JUMP, "N6", 4)
    CONNECTION("N6", 9, "N6", 3)

    // Capacitor C13 used apparently to drive a ~1us low pulse
    // onto M6 pin 5 at the falling edge of FLIP TIMER.
    CONNECTION("N6", 6, "C13", 1)
    CONNECTION(VCC, "C13", 2)

    CONNECTION(START_n, "M6", 4)
    CONNECTION("C13", 3, "M6", 5)

    CONNECTION(VCC, "N6", 13)
    CONNECTION("M6", 6, "N6", 12)
    CONNECTION("L6", 6, "N6", 11)

    CONNECTION("N6", 10, "K8", 3)




    /* Gravity */
    CONNECTION(R2, "N8", 4)
    CONNECTION(R3, "N8", 5)

    CONNECTION("N7", 6, "N7", 4)
    CONNECTION("N8", 6, "N7", 2)
    CONNECTION(VRESET_n, "N7", 3)
    CONNECTION("N6", 9, "N7", 1)

    CONNECTION("N7", 6, "L7", 11)
    CONNECTION(BAD_JUMP, "L7", 12)

    CONNECTION("N8", 3, "L7", 6)
    CONNECTION("N7", 5, "L7", 5)

    CONNECTION("L7", 4, "L7", 3)
    CONNECTION(BAD_JUMP, "L7", 2)

    CONNECTION("N7", 5, "L7", 9)
    CONNECTION(JUMP, "L7", 8)

    CONNECTION("L7", 1, "L5", 2)
    CONNECTION("L7", 1, "L5", 3)
    CONNECTION(VRESET_n, "L5", 14)
    CONNECTION("L5", 12, "L5", 1)

    CONNECTION(VCC, "F6", 10)
    CONNECTION("L5", 11, "F6", 12)
    CONNECTION(HSYNC_n, "F6", 11)
    CONNECTION(BAD_JUMP_n, "F6", 13)

    CONNECTION("L5", 11, "L6", 9)
    CONNECTION("F6", 8, "L6", 10)




    /* GFX Rom Decode */
    CONNECTION(H6, "D4", 9)
    CONNECTION(DIRECTION_n, "D4", 8) // Schematic says DIRECTION?

    CONNECTION(DIRECTION_n, "B5", 1) // Schematic says DIRECTION?
    CONNECTION("B5", 8, "B5", 2)

    CONNECTION("D4", 10, "D4", 11)
    CONNECTION("B5", 3, "D4", 12)

    // Speed hack
#ifdef USE_CLK_GATES
    CONNECTION(VWINDOW, "CLK_GATE3", 1)
    CONNECTION(H5, "CLK_GATE3", 2)
    CONNECTION(VWINDOW, "CLK_GATE4", 1)
    CONNECTION("D4", 13, "CLK_GATE4", 2)
#endif

    
#ifdef USE_CLK_GATES    
    CONNECTION("CLK_GATE4", 3, "H2", 1)
#else
    CONNECTION("D4", 13, "H2", 1)
#endif
    CONNECTION(HSYNC_n, "H2", 2)

    CONNECTION(HSYNC_n, "H2", 4)
#ifdef USE_CLK_GATES
    CONNECTION("CLK_GATE3", 3, "H2", 5)
#else
    CONNECTION(H5, "H2", 5)
#endif
        
    CONNECTION(VCC, "J1", 3)
    CONNECTION(V4, "J1", 2)
    CONNECTION(_4V, "J1", 6)
    CONNECTION(V3, "J1", 5)
    CONNECTION(_2V, "J1", 13)
    CONNECTION(V2, "J1", 14)
    CONNECTION(_1V, "J1", 10)
    CONNECTION(V1, "J1", 11)
    CONNECTION(HSYNC, "J1", 1)
    CONNECTION(GND, "J1", 15)

    CONNECTION(R4, "HF1", 6)
    CONNECTION(R3, "HF1", 5)
    CONNECTION(R2, "HF1", 4)
    CONNECTION("H2", 3, "HF1", 3)
    CONNECTION("H2", 6, "HF1", 2)
    CONNECTION("J1", 4, "HF1", 1)
    CONNECTION("J1", 7, "HF1", 23)
    CONNECTION("J1", 12, "HF1", 22)
    CONNECTION("J1", 9, "HF1", 21)
    CONNECTION(VCC, "HF1", 18)

    // Speed hack
#ifdef USE_CLK_GATES
    CONNECTION(VWINDOW, "CLK_GATE2", 1)
    CONNECTION("D3", 10, "CLK_GATE2", 2)
#endif

    CONNECTION(H1, "D3", 11)

    CONNECTION("HF1", 7, "E1", 3)
    CONNECTION("HF1", 8, "E1", 4)
    CONNECTION("HF1", 9, "E1", 5)
    CONNECTION("HF1", 10, "E1", 6)
#ifdef USE_CLK_GATES
    CONNECTION("CLK_GATE2", 3, "E1", 11)
#else
    CONNECTION("D3", 10, "E1", 11)
#endif
    CONNECTION(CYCLE_RESET_A_n, "E1", 1)
    CONNECTION(MS1, "E1", 9)
    CONNECTION(MS2, "E1", 10)
    CONNECTION("E2", 15, "E1", 7)
    CONNECTION(GND, "E1", 2)

    CONNECTION("HF1", 14, "E2", 3)
    CONNECTION("HF1", 15, "E2", 4)
    CONNECTION("HF1", 16, "E2", 5)
    CONNECTION("HF1", 17, "E2", 6)
#ifdef USE_CLK_GATES
    CONNECTION("CLK_GATE2", 3, "E2", 11)
#else
    CONNECTION("D3", 10, "E2", 11)
#endif
    CONNECTION(CYCLE_RESET_A_n, "E2", 1)
    CONNECTION(MS1, "E2", 9)
    CONNECTION(MS2, "E2", 10)
    CONNECTION("E1", 12, "E2", 2)
    CONNECTION(GND, "E2", 7)

    CONNECTION("E2", 12, "D1", 4)
    CONNECTION(DIRECTION_n, "D1", 5)
    CONNECTION("E1", 15, "D1", 2)
    CONNECTION(DIRECTION, "D1", 3)

    CONNECTION(VWINDOW, "D2", 10)
    CONNECTION("D1", 6, "D2", 12)
#ifdef USE_CLK_GATES
    CONNECTION("CLK_GATE2", 3, "D2", 11)
#else
    CONNECTION(H1, "D2", 11)
#endif
    CONNECTION(VCC, "D2", 13)

    // Speed hack
#ifdef USE_CLK_GATES   
    CONNECTION(OBJECT_ZONE, "CLK_GATE1", 1)
    CONNECTION(CLOCK, "CLK_GATE1", 2)
#endif
    CONNECTION("HF1", 7, "F2", 11)
    CONNECTION("HF1", 8, "F2", 12)
    CONNECTION("HF1", 9, "F2", 13)
    CONNECTION("HF1", 10, "F2", 14)
    CONNECTION("HF1", 14, "F2", 3)
    CONNECTION("HF1", 15, "F2", 4)
    CONNECTION("HF1", 16, "F2", 5)
    CONNECTION("HF1", 17, "F2", 6)
#ifdef USE_CLK_GATES
    CONNECTION("CLK_GATE1", 3, "F2", 2)
#else
    CONNECTION(CLOCK, "F2", 2)
#endif
    CONNECTION(HSYNC_n, "F2", 1)
    CONNECTION("F2", 9, "F2", 10)
    CONNECTION(GND, "F2", 15)
    CONNECTION(VCC, "D2", 4)
    CONNECTION("F2", 9, "D2", 2)
#ifdef USE_CLK_GATES
    CONNECTION("CLK_GATE1", 3, "D2", 3)
#else
    CONNECTION(CLOCK, "D2", 3)
#endif
    CONNECTION(OBJECT_ZONE, "D2", 1)




    /* Coin / Start */
    CONNECTION("J9", 6, "LATCH", 1)
    CONNECTION(VCC, "LATCH", 2)

    CONNECTION(VCC, "C8", 13)
    CONNECTION("LATCH", 3, "C8", 12)

    CONNECTION("COIN", 1, "K8", 11)

    CONNECTION(VCC, "DSW1", 1)
    CONNECTION(GND, "DSW1", 2)

    CONNECTION("DSW1", 3, "K9", 1)
    CONNECTION("K8", 10, "K9", 13)
    CONNECTION("F8", 9, "K9", 9)
    CONNECTION("H8", 6, "K9", 10)

    CONNECTION(VCC, "H8", 10)
    CONNECTION("K8", 10, "H8", 12)
    CONNECTION(_64V, "H8", 11)
    CONNECTION("K8", 10, "H8", 13)

    CONNECTION("F8", 8, "J8", 4)
    CONNECTION("H8", 8, "J8", 5)

    CONNECTION("J8", 6, "J9", 8)
    CONNECTION(_64V, "J9", 9)
    CONNECTION("J9", 2, "J9", 11)
    CONNECTION("J8", 6, "J9", 10)

    CONNECTION("K9", 8, "J8", 1)
    CONNECTION("J9", 6, "J8", 2)
    
    CONNECTION("J8", 3, "J9", 1)
    CONNECTION(_64V, "J9", 12)
    CONNECTION(GND, "J9", 4)
    CONNECTION("J8", 6, "J9", 13)
    
    CONNECTION("J9", 6, "E8", 5)
    CONNECTION("J8", 8, "E8", 4)
    CONNECTION(VCC, "E8", 15)
    CONNECTION(VCC, "E8", 1)
    CONNECTION(VCC, "E8", 10)
    CONNECTION(VCC, "E8", 9)
    CONNECTION("E8", 12, "E8", 11)
    CONNECTION("C8", 11, "E8", 14)    
    
    CONNECTION("E8", 7, "D8", 5)
    CONNECTION("E8", 6, "D8", 4)
    CONNECTION("E8", 2, "D8", 3)
    
    CONNECTION("D8", 6, "K8", 9)
    
    CONNECTION("K8", 8, "F9", 9)
    CONNECTION("E8", 3, "F9", 8)

    CONNECTION("F9", 10, "F9", 5)
    CONNECTION("F9", 10, "F9", 6)

    CONNECTION(VCC, "DSW2", 1)
    CONNECTION(GND, "DSW2", 2)

    CONNECTION("E7", 6, "H9", 11)
    CONNECTION("DSW2", 3, "H9", 10)
    CONNECTION(ATTRACT_n, "H9", 9)

    CONNECTION("H8", 8, "F8", 4)
    CONNECTION("F8", 8, "F8", 2)
    CONNECTION(ATTRACT, "F8", 3)
    CONNECTION("H9", 8, "F8", 1)

    CONNECTION(VCC, "F8", 10)
    CONNECTION(VCC, "F8", 12)
    CONNECTION("F8", 6, "F8", 11)
    CONNECTION(ATTRACT_n, "F8", 13)

    CONNECTION("START", i2, "H9", 13) // Start 2 Inverted
    CONNECTION("K8", 8, "H9", 1)
    CONNECTION(START, "H9", 2)

    CONNECTION("H9", 12, "H9", 3)
    CONNECTION(START, "H9", 4)
    CONNECTION("START", i1, "H9", 5)

    CONNECTION("H9", 12, "H8", 4)
    CONNECTION(GND, "H8", 2)
    CONNECTION(ATTRACT, "H8", 3)
    CONNECTION("H9", 6, "H8", 1)

    CONNECTION("START", i2, "F9", 2)
    CONNECTION("START", i1, "F9", 3)

    CONNECTION(VRAMP, "J8", 13)
    CONNECTION("H8", 5, "J8", 12)

    CONNECTION("J8", 11, "J8", 10)
    CONNECTION(START, "J8", 9)

    CONNECTION("J8", 6, "D8", 1)
    CONNECTION("D9", 9, "D8", 13)
    CONNECTION("F9", 10, "D8", 2)

    CONNECTION("D8", 12, "D9", 4)
    CONNECTION("F9", 1, "D9", 2)
    CONNECTION(_256V, "D9", 3)
    CONNECTION(VCC, "D9", 1)

    CONNECTION("E5", 13, "H6", 13)

    CONNECTION("H6", 12, "F9", 11)
    CONNECTION("C8", 11, "F9", 12)

    CONNECTION("D9", 8, "D9", 10)
    CONNECTION("D9", 6, "D9", 12)
    CONNECTION(_256V, "D9", 11)
    CONNECTION("F9", 13, "D9", 13)    




    
    /* Throttle */
    CONNECTION(CYCLE_RESET_n, "N5", 13)
    CONNECTION("M5", 6, "N5", 12)

    CONNECTION("N5", 11, "M5", 5)
    CONNECTION(ATTRACT_n, "M5", 4)
    CONNECTION(GND, "M5", 3)

    CONNECTION("N5", 11, "N3", 11)

    CONNECTION("STUNT_THROTTLE", 1, ATTRACT_n)
    CONNECTION("STUNT_THROTTLE", 2, "L7", 10)
    CONNECTION("STUNT_THROTTLE", 3, "N3", 10)
    CONNECTION("STUNT_THROTTLE", 4, R2)
    CONNECTION("STUNT_THROTTLE", 5, R3)
    



    /* Video Summing */
    CONNECTION(RAMPS_n, "F4", 1)
    CONNECTION(ROAD_n, "F4", 2)

    CONNECTION("D4", 1, "E4", 11)
    CONNECTION("D3", 6, "E4", 9)
    CONNECTION("D4", 4, "E4", 10)

    CONNECTION("F4", 8, "E3", 4)
    CONNECTION("F3", 8, "E3", 5)
    CONNECTION("F4", 6, "E3", 3)

    CONNECTION("F4", 3, "E4", 3)
    CONNECTION(SCORE2, "E4", 4)
    CONNECTION("E3", 6, "E4", 5)

    CONNECTION("E4", 8, "E3", 13)
    CONNECTION("D2", 6, "E3", 2)
    CONNECTION(SCORE1_n, "E3", 1)

    CONNECTION("VIDEO", 1, "E3", 12)
    CONNECTION("VIDEO", 2, "E4", 6)
    
    CONNECTION("VIDEO", Video::HBLANK_PIN, HSYNC)
    CONNECTION("VIDEO", Video::VBLANK_PIN, VSYNC)

CIRCUIT_LAYOUT_END


CUSTOM_LOGIC( StuntCycleThrottleDesc::stuntcycle_throttle )
{
    StuntCycleThrottleDesc* desc = (StuntCycleThrottleDesc*)chip->custom_data;
    double pos;

    chip->inputs ^= mask;

    if(!(chip->inputs & SPEED_KILL_MASK))
    {
        desc->cap_voltage = 5.0; // Assume this happens instantly
        pos = 5.0;
        chip->output_links[0].chip->pending_event = 0; // Disable speed pulses
    }
    else 
    {
        if(!(chip->inputs & ATTRACT_MASK))
        {
            pos = (5.0-0.7)*(220.0)/(330.0+220.0); // R30, D43, R34 Voltage divider
            // TODO: Redo this to take into account voltage drop due to capacitor. 
        }
        else if(!(chip->inputs & FLIP_OR_JUMP_MASK)) // Q14 disabled
        {
            pos = 5.0;
        }
        else
        {
            pos = 5.0 - desc->throttle_pos/20.0; // 5 KOhm variable, 0 Ohm = max throttle
        }

        // Calculate R based on state of K11 switches
        double r_inv = 1.0 / 120.0e3; // R31
        if(chip->inputs & R2_MASK) r_inv += 1.0 / 150.0e3; // R35
        if(chip->inputs & R3_MASK) r_inv += 1.0 / 68.0e3; // R36, Variable?

        double tc = 22.0e-6 / r_inv; // C11, 22 uF
        double t = (chip->circuit->global_time - desc->last_event_time) * Circuit::timescale;

        desc->cap_voltage += (pos - desc->cap_voltage)*(1.0 - exp(-t/tc));

        // R = 47 kOhm at min throttle, 3.9 kOhm at max. Assume linear relationship?
        double R = (47.0e3 - 3.9e3)*(desc->cap_voltage / 5.0) + 3.9e3;
        double period = R*0.1e-6*5.0 / (2.0*(5.0-2.5)); // 566 timer frequency equation inverse, C10 = 0.1 uF

        //printf("t:%lld t:%g tc:%g exp:%g pos:%g cap:%g R:%g T:%g\n", 
        //         chip->circuit->global_time, t, tc, exp(-t/tc), pos, desc->cap_voltage, R, period);

        // Update speed pulse period
        Chip* c = chip->output_links[0].chip;
        uint64_t pend = c->pending_event;
        c->deactivate_outputs();
        c->pending_event = pend;
        c->state = ACTIVE;
        c->output_events.clear();
        c->activation_time = chip->circuit->global_time;
        c->end_time = ~0ull;

        uint64_t pulse_time = uint64_t(period / 2.0 / Circuit::timescale);
        c->output_events.push_back(Event(chip->activation_time, 0));
        c->output_events.push_back(Event(chip->activation_time + pulse_time, 0));
        c->cycle_time = 2*pulse_time;
        c->first_output_event = c->output_events.begin();
        c->current_output_event = c->output_events.begin();

        if(c->pending_event == 0) c->pending_event = c->circuit->queue_push(c, pulse_time);
    }

    // Calculate op-amp outputs. TODO: Determine correct behavior?
    int new_out = 0;
    Chip* c = chip->output_links[1].chip;

    if(desc->cap_voltage > pos + 1.5) 
        new_out = 1;

    if(c->output != new_out) 
        c->pending_event = c->circuit->queue_push(c, c->delay[c->output]);

    new_out = 0;
    c = chip->output_links[2].chip;

    if(desc->cap_voltage > pos + 0.75)
        new_out = 1;

    if(c->output != new_out) 
        c->pending_event = c->circuit->queue_push(c, c->delay[c->output]);

    desc->last_event_time = chip->circuit->global_time;
}

static CHIP_LOGIC( SPEED_PULSES )
{
    // Do nothing...
}

static CUSTOM_LOGIC( OP_AMP )
{
    // Do nothing...
}

CHIP_DESC( STUNTCYCLE_THROTTLE ) =
{
    CUSTOM_CHIP_START(&StuntCycleThrottleDesc::stuntcycle_throttle)
        INPUT_PINS( 
            1, // ATTRACT_n
            2, // FLIP_or_JUMP_n
            3, // SPEED KILL (N3 pin 10)
            4, // R2
            5, // R3
            i3 // Connection from throttle input
        )
        OUTPUT_PIN( i1 )
        OUTPUT_DELAY_NS( 1.0, 1.0 ),

    CHIP_START( SPEED_PULSES )
        INPUT_PINS( i1 )
        OUTPUT_PIN( i2 )
        OUTPUT_DELAY_NS( 1.0, 1.0 ),

    CUSTOM_CHIP_START( OP_AMP )
        INPUT_PINS( i1 )
        OUTPUT_PIN( 12 )
        OUTPUT_DELAY_NS( 10.0, 10.0 ),

    CUSTOM_CHIP_START( OP_AMP )
        INPUT_PINS( i1 )
        OUTPUT_PIN( 10 )
        OUTPUT_DELAY_NS( 10.0, 10.0 ),

	CHIP_DESC_END
};
