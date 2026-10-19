#include "../circuit_desc.h"

#define DEBUG
#undef DEBUG

#ifdef DEBUG
static VcdLogDesc vcd_log_desc
(
    "pinpong.vcd",
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

// TODO: Adjustable resistance based on flipper mux?
static Mono9602Desc a5_desc(K_OHM(4.7), P_FARAD(220.0), K_OHM(15.0), U_FARAD(5.0));

static CapacitorDesc cap1_desc(P_FARAD(220.0));
static CapacitorDesc cap2_desc(P_FARAD(220.0));
static CapacitorDesc cap3_desc(P_FARAD(220.0));
static CapacitorDesc cap4_desc(P_FARAD(110.0)); // 220 too much? messes up ball horizontal count. TODO: adjust all capacitor delay times?
static CapacitorDesc cap5_desc(P_FARAD(220.0));

static DipswitchDesc dipswitch1_desc("coinage", "dice_dipswitch_1", "Coinage", 0, "1 Coin / 1 Credit", "1 Coin / 2 Credits");
static DipswitchDesc dipswitch2_desc("free_ball", "dice_dipswitch_2", "Free Ball", 0, "Enabled", "Disabled");
static DipswitchDesc dipswitch3_desc("ball_count", "dice_dipswitch_3", "Ball Count", 0, "3", "5");

static VIDEO_DESC( pinpong )
    VIDEO_RESISTANCE(1, OHM(330))
    VIDEO_RESISTANCE(2, OHM(330))
    VIDEO_RESISTANCE(3, K_OHM(4.7))
    VIDEO_RESISTANCE(4, OHM(330))
    VIDEO_RESISTANCE(5, OHM(330))
    VIDEO_RESISTANCE(6, OHM(330))
    VIDEO_ORIENTATION(ROTATE_90)
    VIDEO_BRIGHTNESS(-0.35)
    VIDEO_CONTRAST(2.5)
    VIDEO_RETRO_V_SIZE(255) // Also 248
VIDEO_DESC_END

static INPUT_DESC( pinpong )
    INPUT_INFO(BUTTONS1_INPUT, {{ 1 }}, "Flip Left Flipper")
    INPUT_INFO(BUTTONS1_INPUT, {{ 2 }}, "Flip Right Flipper")

    INPUT_INFO(COIN_INPUT, {{ 1 }}, "Insert Coin")
    INPUT_INFO(START_INPUT, {{ 1 }}, "Start Game / Serve Ball")
INPUT_DESC_END


CIRCUIT_LAYOUT( pinpong )
	/**************************************************************************
		Chips
	**************************************************************************/
    CHIP("CLOCK", CLOCK_14_318_MHZ)
    
    CHIP("A1", 7474)
    CHIP("A2", 7474)
    CHIP("A3", 7486)
    CHIP("A4", 9314)
    CHIP("A5", 9602, &a5_desc)
    CHIP("A6", 7400)
    CHIP("A7", 7410)
    CHIP("A8", 7402)
    CHIP("A9", 7408)

    CHIP("B1", 7420)
    CHIP("B2", 74193)
    CHIP("B3", 74193)
    CHIP("B4", 9322)
    CHIP("B5", 7474)
    CHIP("B8", 7410)
    CHIP("B9", 7402)

    CHIP("C1", 7474)
    CHIP("C2", 74193)
    CHIP("C3", 74193)
    CHIP("C4", 9322)
    CHIP("C5", 7400)
    CHIP("C6", 7490)
    CHIP("C7", 7490)
    CHIP("C8", 7400)
    CHIP("C9", 7432)

    CHIP("D1", 7408)
    CHIP("D2", 7474)
    CHIP("D3", 7408)
    CHIP("D4", 7493)
    CHIP("D5", 7486)
    CHIP("D6", 7490)
    CHIP("D7", 7490)
    CHIP("D8", 7420)
    CHIP("D9-1", 7474)
    CHIP("D9-2", 7474)
    
    CHIP("E1", 7474)
    CHIP("E2", 7402)
    CHIP("E3", 7486)
    CHIP("E4", 74193)
    CHIP("E5", 9312)
    CHIP("E6", 74153)
    CHIP("E7", 74153)
    CHIP("E8", 74107)

    CHIP("F1", 7474)
    CHIP("F2", 7400)
    CHIP("F3", 9316)
	CHIP("F4", 7400)
    CHIP("F5", 9312)
    CHIP("F6", 7448)
	CHIP("F7", 7402)
    CHIP("F8", 9322)
    CHIP("F9", 7474)

    CHIP("H2", 7404)
    CHIP("H3", 7410)
	CHIP("H4", 7402)
	CHIP("H5", 7474)
	CHIP("H6", 7486)
	CHIP("H7", 7474)
    CHIP("H8", 74107)
    CHIP("H9", 7408)
    CHIP("H10",7400)

    CHIP("J1", 9321)
    CHIP("J2", 7420)
    CHIP("J3", 7430)
	CHIP("J4", 7404)
	CHIP("J5", 7408)
	CHIP("J6", 7410)
	CHIP("J7", 7474)
    CHIP("J8", 7427)
    CHIP("J9", 7474)
    CHIP("J10", 7410)

    CHIP("K1", 9314)
	CHIP("K3", 7486)
	CHIP("K4", 7404)
	CHIP("K5", 7420)
	CHIP("K6", 9316)
	CHIP("K7", 7485)
	CHIP("K8", 7404)
    CHIP("K9", 7474)
    CHIP("K10", 7474)

    CHIP("L1", 9314)
    CHIP("L2", 7400)
    CHIP("L3", 7402)
    CHIP("L4", 7400)
    CHIP("L5", 7427)
	CHIP("L6", 9316)
	CHIP("L7", 7485)
	CHIP("L8", 74107)
 	CHIP("L9", 7410)
    CHIP("L10", 7402)

    CHIP("M1", 7430)
    CHIP("M2", 74157)
    CHIP("M3", 7474)
	CHIP("M4", 7408)
    CHIP("M5", 7474)
	CHIP("M6", 7474)
	CHIP("M7", 7486)
	CHIP("M8", 7493)
	CHIP("M9", 7408)
    CHIP("M10", 9312)

    CHIP("N1", 9312)
	CHIP("N2", 7400)
    CHIP("N3", 7408)
	CHIP("N4", 7474)
	CHIP("N5", 7410)
	CHIP("N6", 7486)
	CHIP("N7", 7486)
	CHIP("N8", 7493)
	CHIP("N9", 7420)
    CHIP("N10", 74164)

    CHIP("CAP1", CAPACITOR, &cap1_desc)
    CHIP("CAP2", CAPACITOR, &cap2_desc)
    CHIP("CAP3", CAPACITOR, &cap3_desc)
    CHIP("CAP4", CAPACITOR, &cap4_desc)
    CHIP("CAP5", CAPACITOR, &cap5_desc)

    CHIP("FLIPPERS", BUTTONS1_INPUT)
    CHIP("COIN", COIN_INPUT)
    CHIP("START", START_INPUT)
    CHIP("LATCH", LATCH)

    CHIP("S1", DIPSWITCH, &dipswitch1_desc)
	CHIP("S2", DIPSWITCH, &dipswitch2_desc)
	CHIP("S3", DIPSWITCH, &dipswitch3_desc)
    CHIP("WIRE_OR", 7432)

    VIDEO(pinpong)
    INPUT(pinpong)

    OPTIMIZATION_HINT("L7", 8192, 512)
    OPTIMIZATION_HINT("K7", 8192, 768)
    OPTIMIZATION_HINT("K3", 2048, 512)
    OPTIMIZATION_HINT("M4", 4096, 384)
    OPTIMIZATION_HINT("N4", 16384, 192)
    OPTIMIZATION_HINT("N5", 2048, 64)

    OPTIMIZATION_HINT("CAP1", 512, 256)
    OPTIMIZATION_HINT("H6", 1024, 256)
    OPTIMIZATION_HINT("L5", 8192, 128)
    OPTIMIZATION_HINT("M5", 8192, 64)

    //OPTIMIZATION_HINT("A8", 16, 64)
    OPTIMIZATION_HINT("J3", 256, 64)
    
    OPTIMIZATION_HINT("H3", 16, 64)
    OPTIMIZATION_HINT("B8", 8, 64)
    OPTIMIZATION_HINT("N2", 32, 64)

    DISABLE_OPTIMIZATION("A8", 2)
    DISABLE_OPTIMIZATION("A8", 5)
    DISABLE_OPTIMIZATION("CAP2", 1)
    OPTIMIZATION_HINT("A5", 8, 64)
    
    //OPTIMIZATION_HINT("L4", 16384, 512)

#ifdef DEBUG
	CHIP("LOG1", VCD_LOG, &vcd_log_desc)
#endif

	/**************************************************************************
		Signals
	**************************************************************************/	
    #define _2CLOCK "CLOCK", 1
    #define CLK "H7", 5
    #define CLK_n "H7", 6
	#define H1 "L6", 14
	#define H2 "L6", 13
    #define H2_n "K8", 4
	#define H4 "L6", 12
	#define H8 "L6", 11
	#define H16 "K6", 14
	#define H32 "K6", 13
    #define H32_n "K8", 6
	#define H64 "K6", 12
	#define H128 "K6", 11
	#define H256 "L8", 5
	#define H256_n "L8", 6
	#define HRESET "J7", 6
	#define HRESET_n "J7", 5

	#define V1 "M8", 12
	#define V2 "M8", 9
	#define V4 "M8", 8
	#define V8 "M8", 11
    #define V8_n "K8", 2
	#define V16 "N8", 12
	#define V32 "N8", 9
	#define V64 "N8", 8
	#define V128 "N8", 11
    #define V128_n "J8", 8
	#define V256 "L8", 3
	#define V256_n "L8", 2
	#define V240 "N9", 8
	#define VRESET "J7", 8
	#define VRESET_n "J7", 9
	#define HBLANK "F7", 1
	#define HBLANK_n "F7", 4
	#define HSYNC "H7", 8
	#define HSYNC_n "H7", 9
	#define VSYNC "F7", 10

	#define ZONEH "H5", 9
	#define ZONEH_n "H5", 8
	#define ZONEV "N6", 6
	#define ZONEV_n "K4", 8

	#define H32H64 "J5", 3
    #define H32_xor_H64_n "J4", 4
	#define HFIELD "H5", 5
	#define HFIELD_n "H5", 6
	#define VFIELD "M6", 9
	#define VFIELD_n "M6", 8

    #define V32_xor_V128 "N7", 11
    #define V16_xor_V128 "N7", 6
    #define V16_xor_V32 "N6", 8

    #define ATTRACT "J9", 5
    #define ATTRACT_n "J9", 6
    #define START "J9", 9
    #define START_n "J9", 8
    
    #define FREE_BALL_SWITCHED_n "S2", 3
    #define BALLS_REMAINING_n "L9", 12
    #define FREE_BALL_INDICATOR "K10", 6
        
    #define SERVE "H10", 6
    #define SERVE_n "J10", 8
    #define SERVE_BUFF_n "J4", 2
    #define SERVE_RESET "K10", 9
    #define SERVE_RESET_n "K10", 8
    #define BALL_BLANKING "J10", 12
    #define BALL_BLANKING_n "H10", 3

    #define HIT "H2", 8

    #define MISS_n "F4", 3
    #define MISS_nor_ATTRACT "N3", 6

    #define SLINGSHOTS "M4", 6
	#define PLAYFIELD_n "N5", 6

    #define THUMPER_BUMPERS_n "N5", 8
    #define CROSS_ZONE "K4", 2
    #define CROSS_ZONE_n "K5", 6
    #define VCROSS "N6", 11
    #define VCROSS_n "L4", 11
    #define CROSS "L4", 8
    #define CROSS_n "K4", 6
    #define CROSS_CENTER_FLASHING "J5", 8

    #define FLIPPER "A5", 6
    #define FLIPPER_n "A5", 7
    #define FLIPPER_MOTION "F8", 4
    #define FLIPPER_MOTION_n "H10", 11
    #define FLIP_UP_n "A7", 12
    #define FLIPPER_WINDOW "H2", 2
    #define FLIPPER_WINDOW_n "A7", 8
    #define FLIPPER_HIT_WINDOW "B5", 9
    #define FLIPPER_HIT_WINDOW_n "B5", 8

    #define R0 "D4", 12
    #define R1 "D4", 9
    #define R2 "D4", 8
    #define R3 "D4", 11

    #define FLIPPER_MOTION_CLOCK "F3", 13
    #define GRAVITY "H2", 12
    #define GRAVITY_n "F3", 15
   
    #define H_UP "M3", 5
    #define H_UP_n "M3", 6
    #define V_UP "M3", 9
    #define V_UP_n "M3", 8

    #define BALL "E1", 9
    #define BALL_n "E1", 8

    #define KNOCKDOWNS_n "F2", 6
    #define _100_POINT_OBJECTS "H3", 6
    #define INCREMENT_1000 "A9", 6

    #define HSCORE_WINDOW "H3", 12
    #define SCORE_WINDOW "H4", 10
    #define SCORE_WINDOW_n "J4", 8
    #define SCORE_OUT "C9", 8


	/**************************************************************************
		Layout - Page 1
	**************************************************************************/
    CONNECTION("CLOCK", 1, "H7", 3)
    CONNECTION("H7", 6, "H7", 2)
    CONNECTION(VCC, "H7", 1)
    CONNECTION(VCC, "H7", 4)
    
    /* Horizontal Sync */
    CONNECTION(CLK,"L6", 2)
    CONNECTION(CLK,"K6", 2)
	CONNECTION(VCC,"L6", 7)
	CONNECTION(VCC,"L6", 10)
	CONNECTION(VCC,"L6", 9)
	CONNECTION("L6", 15,"K6", 7)
	CONNECTION(VCC,"L8", 8)
	CONNECTION(VCC,"L8", 11)
	CONNECTION(VCC,"K6", 10)
	CONNECTION(VCC,"K6", 9)
	CONNECTION("K6", 15,"L8", 9)
	CONNECTION("L6", 14,"K5", 10)
	CONNECTION("K6", 12,"K5", 12)
	CONNECTION("K6", 11,"K5", 13)
	CONNECTION(H256,"K5", 9)
	CONNECTION("K5", 8,"J7", 2)
	CONNECTION(CLK_n,"J7", 3)
	CONNECTION(VCC,"J7", 4)
	CONNECTION(VCC,"J7", 1)
	CONNECTION(HRESET_n,"L8", 10)
	CONNECTION(HRESET_n,"K6", 1)
	CONNECTION(HRESET_n,"L6", 1)
	CONNECTION(HRESET,"F7", 6)
	CONNECTION("F7", 4,"F7", 3)
	CONNECTION(H64,"F7", 2)
	CONNECTION("F7", 1,"F7", 5)
	CONNECTION(H32,"H7", 12)
	CONNECTION(H16,"H7", 11)
	CONNECTION(HBLANK,"H7", 10)
	CONNECTION(VCC,"H7", 13)



	/* Vertical Sync */
	CONNECTION(HRESET,"M9", 10)
	CONNECTION(VCC,"M9", 9) // Unimplemented - Clock Stop, 50 Hz mode
	CONNECTION("M9", 8,"M8", 14)
	CONNECTION("M9", 8,"J7", 11)
	CONNECTION("M8", 12,"M8", 1)
	CONNECTION("M8", 11,"N8", 14)
	CONNECTION("N8", 11,"L8", 12)
	CONNECTION("N8", 12,"N8", 1)
	CONNECTION(VCC,"L8", 1)
	CONNECTION(VCC,"L8", 4)
	CONNECTION("L8", 3,"L9", 5)
	CONNECTION("M8", 9,"L9", 4)
	CONNECTION("M8", 8,"L9", 3)
	CONNECTION("L9", 6,"J7", 12)
	CONNECTION(VCC,"J7", 10)
	CONNECTION(VCC,"J7", 13)
	CONNECTION("J7", 9,"L8", 13)
	CONNECTION(VRESET,"M8", 2)
	CONNECTION(VRESET,"M8", 3)
	CONNECTION(VRESET,"N8", 2)
	CONNECTION(VRESET,"N8", 3)
	CONNECTION(V16,"N9", 9)
	CONNECTION(V32,"N9", 12)
	CONNECTION(V64,"N9", 13)
	CONNECTION(V128,"N9", 10)
	CONNECTION("N9", 8,"F7", 8)
	CONNECTION(V8,"K8", 1)
	CONNECTION("K8", 2,"F7", 9)

	/* Zones */
	CONNECTION(H16,"J5", 5)
	CONNECTION(H128,"J5", 4)
	CONNECTION("J5", 6,"H5", 11)
	CONNECTION(H256_n,"H5", 12)
	CONNECTION(H16,"J6", 1)
	CONNECTION(H32,"J6", 2)
	CONNECTION(H256,"J6", 13)
	CONNECTION("J6", 12,"H5", 13)
	CONNECTION(VCC,"H5", 10)
	CONNECTION(V64,"N6", 5)
	CONNECTION(V128,"N6", 4)
	CONNECTION("N6", 6,"K4", 9)

	/* Background */
	CONNECTION(V16,"N7", 1)
	CONNECTION(ZONEH,"N7", 2)
	CONNECTION("N7", 3,"N6", 1)
	CONNECTION(H16,"N6", 2)
	CONNECTION("N6", 3,"M7", 2)
	CONNECTION("N6", 3,"M7", 12)
	CONNECTION("N6", 3,"M7", 5)
	CONNECTION("N6", 3,"M7", 9)
	CONNECTION(V8,"M7", 1)
	CONNECTION(V4,"M7", 13)
	CONNECTION(V2,"M7", 4)
	CONNECTION(V1,"M7", 10)
	CONNECTION("M7", 3,"L7", 15)
	CONNECTION("M7", 11,"L7", 13)
	CONNECTION("M7", 6,"L7", 12)
	CONNECTION("M7", 8,"L7", 10)
	CONNECTION(CLK_n,"L7", 3)
	CONNECTION(GND,"L7", 2)
	CONNECTION(GND,"L7", 4)
	CONNECTION(H1,"L7", 9)
	CONNECTION(H2,"L7", 11)
	CONNECTION(H4,"L7", 14)
	CONNECTION(H8,"L7", 1)

	/* Field logic */
	CONNECTION(H32,"J5", 1)
	CONNECTION(H64,"J5", 2)
	//CONNECTION("J5", 3,"J4", 1) Not connected anywhere, and J4.2 also used elsewhere!
	CONNECTION("J5", 3,"J5", 12)
	CONNECTION(H2,"J5", 13)
	CONNECTION("J5", 11,"H5", 3)
	CONNECTION(VCC,"H5", 2)
	CONNECTION(VCC,"H5", 4)
	CONNECTION(H256,"J6", 5)
	CONNECTION(H128,"J6", 4)
	CONNECTION(H32,"J6", 3)
	CONNECTION("J6", 6,"H5", 1)
	CONNECTION(VCC,"M6", 12)
	CONNECTION(VCC,"M6", 10)
	CONNECTION(V16,"M6", 11)
	CONNECTION(V240,"M6", 13)
    CONNECTION("J6", 6, "H4", 2)
    CONNECTION(SERVE, "H4", 3)
    CONNECTION("H4", 1, "F4", 2)
    CONNECTION(BALL, "F4", 1)



	/* Playfield */
	CONNECTION(H32,"K8", 5)
	CONNECTION(V128,"N7", 10)
	CONNECTION(H256_n,"N7", 9)
	CONNECTION("N7", 8,"N7", 12)
	CONNECTION("N7", 8,"N7", 5)
	CONNECTION(V32,"N7", 13)
	CONNECTION(V16,"N7", 4)
	CONNECTION("L7", 7,"K7", 2)
	CONNECTION("L7", 5,"K7", 4)
	CONNECTION(GND,"K7", 3)
	CONNECTION("N7", 6,"K7", 10)
	CONNECTION("N7", 11,"K7", 12)
	CONNECTION(GND,"K7", 13)
	CONNECTION(GND,"K7", 15)
	CONNECTION(H16,"K7", 9)
	CONNECTION("K8", 6,"K7", 11)
	CONNECTION(GND,"K7", 14)
	CONNECTION(GND,"K7", 1)
	CONNECTION("K7", 5,"K3", 1)
	CONNECTION(H256_n,"K3", 2)
	CONNECTION("K3", 3,"M4", 2)
	CONNECTION(H32,"H6", 9)
	CONNECTION(H64,"H6", 10)
	CONNECTION("H6", 8,"J4", 3)
	CONNECTION("J4", 4,"F4", 4)
	CONNECTION(H256,"F4", 5)
	CONNECTION("F4", 6,"M4", 1)
	CONNECTION("M4", 3,"N4", 2)
	CONNECTION(VCC,"N4", 1)
	CONNECTION(CLK,"N4", 3)
	CONNECTION(ZONEH_n,"M4", 5)
	CONNECTION(ZONEV_n,"M4", 4)
	CONNECTION("M4", 6,"N4", 4)
	CONNECTION("N4", 5,"N5", 4)
	CONNECTION(HFIELD,"N5", 5)
	CONNECTION(VFIELD,"N5", 3)


    // Objects
    CONNECTION(H16, "H6", 1)
    CONNECTION(H32, "H6", 2)

    CONNECTION(V16, "N6", 10)
    CONNECTION(V32, "N6", 9)

    CONNECTION("L7", 7, "CAP1", 1)

    CONNECTION("CAP1", 2, "H6", 12)
    CONNECTION(H16, "H6", 13)

    CONNECTION("H6", 3, "J6", 11)
    CONNECTION(ZONEV, "J6", 9)
    CONNECTION("N6", 8, "J6", 10)

    CONNECTION("H6", 11, "L5", 1)
    CONNECTION(H64, "L5", 13)
    CONNECTION("J6", 8, "L5", 2)

    CONNECTION(VCC, "M5", 10)
    CONNECTION("L5", 12, "M5", 12)
    CONNECTION(CLK, "M5", 11)
    CONNECTION(VCC, "M5", 13)

    CONNECTION(VCC, "M5", 4)
    CONNECTION("M5", 6, "M5", 2)
    CONNECTION(INCREMENT_1000, "M5", 3)
    CONNECTION(MISS_nor_ATTRACT, "M5", 1)

    CONNECTION(H256, "N5", 1)
    CONNECTION(V32_xor_V128, "N5", 13)
    CONNECTION("M5", 6, "N5", 2)

    CONNECTION("M5", 9, "N5", 10)
    CONNECTION(ZONEH, "N5", 9)
    CONNECTION("N5", 12, "N5",11)

    CONNECTION(V32_xor_V128, "K4", 3)

    CONNECTION("K4", 4, "K5", 5)
    CONNECTION(H64, "K5", 1)
    CONNECTION(H128, "K5", 2)
    CONNECTION(ZONEV, "K5", 4)

    CONNECTION("K5", 6, "K4", 1)

    CONNECTION(VCC, "M6", 4)
    CONNECTION(V128, "M6", 2)
    CONNECTION(V2, "M6", 3)
    CONNECTION(VCC, "M6", 1)

    CONNECTION(V128, "N6", 13)
    CONNECTION("M6", 5, "N6", 12)

    CONNECTION("N6", 11, "L4", 12)
    CONNECTION("K4", 2, "L4", 13)

    CONNECTION(H4, "L5", 10)
    CONNECTION(H8, "L5", 11)
    CONNECTION(H16, "L5", 9)

    CONNECTION(H2, "K8", 3)

    CONNECTION("L5", 8, "D8", 4)
    CONNECTION("K8", 4, "D8", 1)
    CONNECTION(H32, "D8", 5)
    CONNECTION("K4", 2, "D8", 2)

    CONNECTION("L4", 11, "L4", 10)
    CONNECTION("D8", 6, "L4", 9)

    CONNECTION("L4", 11, "L3", 12)
    CONNECTION("D8", 6, "L3", 11)

    CONNECTION("L4", 8, "K4", 5)

    CONNECTION("L3", 13, "J5", 9)
    CONNECTION(GRAVITY_n, "J5", 10)



    // Flippers
    CONNECTION("H8", 6, "H8", 1)
    CONNECTION(FLIPPER_MOTION_CLOCK, "H8", 12)
    CONNECTION("H8", 5, "H8", 4)
    CONNECTION("FLIPPERS", 1_NC, "H8", 13) 
    
    CONNECTION("H8", 3, "H8", 8)
    CONNECTION(FLIPPER_MOTION_CLOCK, "H8", 9)
    CONNECTION("H8", 6, "H8", 11)
    CONNECTION("FLIPPERS", 1_NC, "H8", 10) 

    CONNECTION("E8", 6, "E8", 1)
    CONNECTION(FLIPPER_MOTION_CLOCK, "E8", 12)
    CONNECTION("E8", 5, "E8", 4)
    CONNECTION("FLIPPERS", 2_NC, "E8", 13) 
    
    CONNECTION("E8", 3, "E8", 8)
    CONNECTION(FLIPPER_MOTION_CLOCK, "E8", 9)
    CONNECTION("E8", 6, "E8", 11)
    CONNECTION("FLIPPERS", 2_NC, "E8", 10) 

    CONNECTION(V128, "J8", 9)
    CONNECTION(V128, "J8", 10)
    CONNECTION(V128, "J8", 11)

    CONNECTION("J8", 8, "F8", 1)
    CONNECTION("H8", 3, "F8", 2)
    CONNECTION("E8", 3, "F8", 3)
    CONNECTION("H8", 5, "F8", 5)
    CONNECTION("E8", 5, "F8", 6)
    CONNECTION("FLIPPERS", 1_NC, "F8", 14)
    CONNECTION("FLIPPERS", 2_NC, "F8", 13)
    CONNECTION("H8", 2, "F8", 11)
    CONNECTION("E8", 2, "F8", 10)
    CONNECTION(ATTRACT, "F8", 15)

    CONNECTION("F8", 4, "H10", 12)
    CONNECTION("F8", 4, "H10", 13)

    CONNECTION("K7", 7, "A8", 5)
    CONNECTION("F8", 12, "A8", 6)

    CONNECTION("F8", 7, "A7", 2)
    CONNECTION("F8", 9, "A7", 1)
    CONNECTION("H2", 2, "A7", 13)

    CONNECTION(V32_xor_V128, "M9", 5)
    CONNECTION(V16_xor_V128, "M9", 4)

    CONNECTION("M9", 6, "A8", 12)
    CONNECTION(ZONEV_n, "A8", 11)

    CONNECTION("F4", 6, "A8", 9)
    CONNECTION(H128, "A8", 8)

    CONNECTION("A8", 13, "A7", 10)
    CONNECTION(H64, "A7", 9)
    CONNECTION("A8", 10, "A7", 11)

    CONNECTION("A7", 8, "H2", 1)

    CONNECTION("A7", 8, "A8", 2)
    CONNECTION("A8", 4, "A8", 3)

    CONNECTION("A8", 1, "CAP2", 1)

    CONNECTION(VCC, "A5", 5)
    CONNECTION("CAP2", 2, "A5", 4)
    CONNECTION("B5", 9, "A5", 3)

    CONNECTION(H16, "C5", 13)
    CONNECTION("A7", 8, "C5", 12)

    CONNECTION(VCC, "B5", 10)
    CONNECTION(VCC, "B5", 12)
    CONNECTION("H2", 2, "B5", 11)
    CONNECTION("C5", 11, "B5", 13)




    /**************************************************************************
		Layout - Page 2
	**************************************************************************/
    // Ball Direction And Speed
    CONNECTION(V1, "L2", 12)
    CONNECTION(V2, "L2", 13)
    
    CONNECTION("L2", 11, "D4", 14)
    CONNECTION("D4", 12, "D4", 1)
    CONNECTION(GND, "D4", 2)
    CONNECTION(GND, "D4", 3)

    CONNECTION(VCC, "F3", 7)
    CONNECTION(SERVE_BUFF_n, "F3", 10)
    CONNECTION(VSYNC, "F3", 2)
    CONNECTION(H_UP, "F3", 3)
    CONNECTION(GND, "F3", 4)
    CONNECTION(GND, "F3", 5)
    CONNECTION(VCC, "F3", 6)
    CONNECTION("H2", 12, "F3", 9)
    CONNECTION(VCC, "F3", 1) // Not Shown

    CONNECTION("F3", 15, "H2", 13)

    CONNECTION(FLIPPER_WINDOW_n, "D1", 2)
    CONNECTION(SERVE_n, "D1", 1)

    CONNECTION(SERVE_n, "B4", 1)
    CONNECTION(VCC, "B4", 2)
    CONNECTION(FLIPPER_MOTION, "B4", 3)
    CONNECTION(VCC, "B4", 5)
    CONNECTION(V32_xor_V128, "B4", 6)
    CONNECTION(VCC, "B4", 14)
    CONNECTION(GND, "B4", 13)
    CONNECTION(VCC, "B4", 11)
    CONNECTION(FLIPPER_MOTION, "B4", 10)
    CONNECTION(GND, "B4", 15)

    CONNECTION("D1", 3, "C4", 1)
    CONNECTION("B4", 4, "C4", 2)
    CONNECTION(GND, "C4", 3)
    CONNECTION("B4", 7, "C4", 5)
    CONNECTION(R3, "C4", 6)
    CONNECTION("B4", 12, "C4", 14)
    CONNECTION(R0, "C4", 13)
    CONNECTION("B4", 9, "C4", 11)
    CONNECTION(R2, "C4", 10)
    CONNECTION(GND, "C4", 15)
    
    CONNECTION(GRAVITY_n, "F2", 2)
    CONNECTION(H_UP_n, "F2", 1)

    CONNECTION(GRAVITY, "H3", 10)
    CONNECTION(H_UP, "H3", 11)
    CONNECTION("H2", 10, "H3", 9)

    CONNECTION("E4", 7, "H2", 11)

    CONNECTION("F2", 3, "E4", 4)
    CONNECTION("H3", 8, "E4", 5)
    CONNECTION("C4", 4, "E4", 9)
    CONNECTION("C4", 7, "E4", 10)
    CONNECTION(R3, "E4", 1)
    CONNECTION(R0, "E4", 15)
    CONNECTION("N3", 11, "E4", 11)
    CONNECTION("N4", 9, "E4", 14)

    CONNECTION("E4", 13, "N4", 10)
    CONNECTION(GND, "N4", 12)
    CONNECTION(GRAVITY, "N4", 11)
    CONNECTION(VCC, "N4", 13)

    CONNECTION(VCROSS, "L3", 9)
    CONNECTION(CROSS_ZONE_n, "L3", 8)

    CONNECTION("L3", 10, "J4", 5)

    CONNECTION(HSCORE_WINDOW, "N3", 2)
    CONNECTION(HFIELD, "N3", 1)

    CONNECTION("N3", 3, "N2", 13)
    CONNECTION(H32_xor_H64_n, "N2", 12)

    CONNECTION("J4", 6, "N3", 10)
    CONNECTION("N3", 3, "N3", 9)

    CONNECTION(SERVE_n, "CAP3", 1) // C1

    CONNECTION(ZONEH, "N2", 4)
    CONNECTION("CAP3", 2, "N2", 5) // TODO: Add capacitance to all SERVE_n locations?

    CONNECTION(V32, "L2", 9)
    CONNECTION(ZONEH, "L2", 10)

    CONNECTION(V128_n, "L2", 2)
    CONNECTION(ZONEH_n, "L2", 1)

    CONNECTION("L2", 8, "L2", 5)
    CONNECTION("L2", 3, "L2", 4)

    CONNECTION(VCC, "J2", 5)
    CONNECTION(CROSS_ZONE_n, "J2", 4)
    CONNECTION(H256_n, "J2", 2)
    CONNECTION(H32H64, "J2", 1)

    CONNECTION("J2", 6, "J2", 9)
    CONNECTION(HIT, "J2", 10)
    CONNECTION(VCROSS_n, "J2", 12)
    CONNECTION(FLIP_UP_n, "J2", 13)

    CONNECTION("J2", 8, "H2", 5)

    CONNECTION(CROSS_ZONE, "L4", 5)
    CONNECTION(BALL, "L4", 4)

    CONNECTION("L4", 6, "L3", 5)
    CONNECTION(R3, "L3", 6)

    CONNECTION(CROSS_ZONE_n, "L3", 2)
    CONNECTION(VCROSS, "L3", 3)

    CONNECTION(ZONEH, "M4", 12)
    CONNECTION(ZONEV_n, "M4", 13) // Positive ZONEV makes no sense here? TODO: investigate
    
    CONNECTION("L3", 4, "L5", 3)
    CONNECTION("L3", 1, "L5", 4)
    CONNECTION("M4", 11, "L5", 5)

    CONNECTION("L5", 6, "M4", 10)
    CONNECTION(HIT, "M4", 9)

    CONNECTION(ZONEV_n, "M2", 1)
    CONNECTION("N2", 11, "M2", 2)
    CONNECTION(H256_n, "M2", 3)
    CONNECTION("N3", 8, "M2", 5)
    CONNECTION("N2", 6, "M2", 6)
    CONNECTION("L2", 6, "M2", 14)
    CONNECTION(V128_n, "M2", 13)
    CONNECTION("H2", 6, "M2", 11)
    CONNECTION(HIT, "M2", 10)
    CONNECTION("L3", 4, "M2", 15)

    CONNECTION(HIT, "N2", 10)
    CONNECTION("M2", 7, "N2", 9)

    CONNECTION(SERVE_n, "N3", 13)
    CONNECTION("N2", 8, "N3", 12)

    CONNECTION("N2", 8, "A4", 1)
    CONNECTION("C4", 12, "A4", 6)
    CONNECTION("C4", 9, "A4", 4)
    CONNECTION(R1, "A4", 3)
    CONNECTION(SERVE_n, "A4", 9)
    CONNECTION(GND, "A4", 2)
    CONNECTION(GND, "A4", 5)
    CONNECTION(GND, "A4", 7)
    CONNECTION(GND, "A4", 11)
    CONNECTION(GND, "A4", 14)

    CONNECTION(VCC, "M3", 10)
    CONNECTION("M2", 12, "M3", 12)
    CONNECTION("M2", 9, "M3", 11)
    CONNECTION(SERVE_n, "M3", 13)

    CONNECTION("E4", 13, "M3", 4)
    CONNECTION("M2", 4, "M3", 2)
    CONNECTION("M4", 8, "M3", 3)
    CONNECTION(SERVE_n, "M3", 1)



    // Ball Generation
    CONNECTION(H_UP, "E3", 5)
    CONNECTION("E4", 7, "E3", 4)

    CONNECTION(H_UP, "E3", 9)
    CONNECTION("E4", 6, "E3", 10)

    CONNECTION(H_UP, "E3", 12)
    CONNECTION("E4", 2, "E3", 13)

    CONNECTION(H_UP, "E3", 2)
    CONNECTION("E4", 3, "E3", 1)

    CONNECTION(H_UP, "F2", 12)
    CONNECTION(VRESET, "F2", 13)

    CONNECTION(VRESET, "D3", 10)
    CONNECTION("E3", 6, "D3", 9)

    CONNECTION(VRESET, "D3", 4)
    CONNECTION("E3", 8, "D3", 5)

    CONNECTION(VRESET, "D3", 1)
    CONNECTION("E3", 11, "D3", 2)

    CONNECTION(VRESET, "D3", 13)
    CONNECTION("E3", 3, "D3", 12)

    CONNECTION("D3", 11, "C3", 15)
    CONNECTION("D3", 3, "C3", 1)
    CONNECTION("D3", 6, "C3", 10)
    CONNECTION("D3", 8, "C3", 9)
    CONNECTION("CAP4", 2, "C3", 11)
    CONNECTION("D2", 6, "C3", 14)
    CONNECTION(_2CLOCK, "C3", 5)
    CONNECTION(VCC, "C3", 4)

    CONNECTION("F2", 11, "C2", 15)
    CONNECTION(GND, "C2", 1)
    CONNECTION(GND, "C2", 10)
    CONNECTION(GND, "C2", 9)
    CONNECTION("CAP4", 2, "C2", 11)
    CONNECTION("D2", 6, "C2", 14)
    CONNECTION("C3", 12, "C2", 5)
    CONNECTION(VCC, "C2", 4)
    
    CONNECTION("D2", 5, "C1", 10)
    CONNECTION("C1", 8, "C1", 12)
    CONNECTION("C2", 12, "C1", 11)
    CONNECTION("CAP4", 2, "C1", 13)

    CONNECTION("D2", 5, "C1", 4)
    CONNECTION("C1", 6, "C1", 2)
    CONNECTION("C1", 8, "C1", 3)
    CONNECTION("CAP4", 2, "C1", 1)

    CONNECTION(VCC, "D2", 4)
    CONNECTION(VCC, "D2", 2)
    CONNECTION(H256, "D2", 3)
    CONNECTION(SERVE_RESET_n, "D2", 1)

    CONNECTION("C2", 3, "D1", 9)
    CONNECTION("C3", 2, "D1", 10)

    CONNECTION("C1", 5, "B1", 4)
    CONNECTION("C1", 9, "B1", 5)
    CONNECTION("C2", 7, "B1", 1)
    CONNECTION("D1", 8, "B1", 2)

    CONNECTION(VCC, "D2", 10)
    CONNECTION("B1", 6, "D2", 12)
    CONNECTION(_2CLOCK, "D2", 11)
    CONNECTION("D2", 5, "D2", 13)

    CONNECTION("D2", 9, "CAP4", 1)


    CONNECTION(V_UP, "A3", 9)
    CONNECTION("A4", 10, "A3", 10)

    CONNECTION(V_UP, "A3", 5)
    CONNECTION("A4", 12, "A3", 4)

    CONNECTION(V_UP, "A3", 2)
    CONNECTION("A4", 13, "A3", 1)

    CONNECTION(V_UP, "A3", 12)
    CONNECTION("A4", 15, "A3", 13)
    
    CONNECTION(H128, "D1", 12)
    CONNECTION(VCC, "D1", 13) // TODO: CLOCK_STOP ?

    CONNECTION("A3", 11, "B3", 15)
    CONNECTION("A3", 3, "B3", 1)
    CONNECTION("A3", 6, "B3", 10)
    CONNECTION("A3", 8, "B3", 9)
    CONNECTION("CAP5", 2, "B3", 11)
    CONNECTION(GND, "B3", 14)
    CONNECTION("D1", 11, "B3", 5)
    CONNECTION(VCC, "B3", 4)

    CONNECTION(V_UP_n, "B2", 15)
    CONNECTION(GND, "B2", 1)
    CONNECTION(GND, "B2", 10)
    CONNECTION(GND, "B2", 9)
    CONNECTION("CAP5", 2, "B2", 11)
    CONNECTION(GND, "B2", 14)
    CONNECTION("B3", 12, "B2", 5)
    CONNECTION(VCC, "B2", 4)

    CONNECTION(VCC, "A2", 4)
    CONNECTION("A2", 6, "A2", 2)
    CONNECTION("B2", 12, "A2", 3)
    CONNECTION("CAP5", 2, "A2", 1)

    CONNECTION(VCC, "A2", 10)
    CONNECTION("A2", 8, "A2", 12)
    CONNECTION("A2", 6, "A2", 11)
    CONNECTION("CAP5", 2, "A2", 13)

    CONNECTION("A2", 9, "B1", 9)
    CONNECTION("B2", 3, "B1", 10)
    CONNECTION("B3", 7, "B1", 12)
    CONNECTION("B3", 6, "B1", 13)

    CONNECTION(VCC, "A1", 4)
    CONNECTION("B1", 8, "A1", 2)
    CONNECTION("D1", 11, "A1", 3)
    CONNECTION("A1", 9, "A1", 1)

    CONNECTION("A1", 5, "CAP5", 1)

    CONNECTION(VCC, "A1", 10)
    CONNECTION(VCC, "A1", 12)
    CONNECTION(VFIELD, "A1", 11)
    CONNECTION(SERVE_RESET_n, "A1", 13)

    CONNECTION(BALL_BLANKING_n, "F2", 10)
    CONNECTION(VCC, "F2", 9) // TODO : ALTERNATE_BLANK ?
    
    CONNECTION("B3", 7, "E2", 5)
    CONNECTION("F2", 8, "E2", 6)

    CONNECTION("E2", 4, "E1", 4)
    CONNECTION(GND, "E1", 2)
    CONNECTION("A2", 9, "E1", 3)
    CONNECTION(VCC, "E1", 1)

    CONNECTION("C3", 7, "E2", 9)
    CONNECTION("E1", 5, "E2", 8)

    CONNECTION(VCC, "E1", 10)
    CONNECTION(VCC, "E1", 12)
    CONNECTION("C1", 5, "E1", 11)
    CONNECTION("E2", 10, "E1", 13)
   


    // Knockdowns
    CONNECTION(H32, "J1", 2)
    CONNECTION(H64, "J1", 3)
    CONNECTION("F2", 6, "J1", 1)
    CONNECTION(CLK_n, "J1", 14)
    CONNECTION(V128_n, "J1", 13)
    CONNECTION(BALL_n, "J1", 15)

    CONNECTION(MISS_n, "N3", 5)
    CONNECTION(ATTRACT_n, "N3", 4)

    CONNECTION(VCC, "L1", 3)
    CONNECTION("J1", 4, "L1", 2)
    CONNECTION(VCC, "L1", 4)
    CONNECTION("J1", 5, "L1", 14)
    CONNECTION(VCC, "L1", 6)
    CONNECTION("J1", 6, "L1", 5)
    CONNECTION(VCC, "L1", 7)
    CONNECTION("J1", 7, "L1", 11)
    CONNECTION("J1", 9, "L1", 1)
    CONNECTION("N3", 6, "L1", 9)

    CONNECTION(VCC, "K1", 3)
    CONNECTION("J1", 4, "K1", 2)
    CONNECTION(VCC, "K1", 4)
    CONNECTION("J1", 5, "K1", 14)
    CONNECTION(VCC, "K1", 6)
    CONNECTION("J1", 6, "K1", 5)
    CONNECTION(VCC, "K1", 7)
    CONNECTION("J1", 7, "K1", 11)
    CONNECTION("J1", 11, "K1", 1)
    CONNECTION("N3", 6, "K1", 9)

    CONNECTION("K1", 10, "N1", 9)
    CONNECTION("K1", 12, "N1", 7)
    CONNECTION("K1", 13, "N1", 6)
    CONNECTION("K1", 15, "N1", 5)
    CONNECTION("L1", 10, "N1", 4)
    CONNECTION("L1", 12, "N1", 3)
    CONNECTION("L1", 13, "N1", 2)
    CONNECTION("L1", 15, "N1", 1)
    CONNECTION(GND, "N1", 10)
    CONNECTION(H32, "N1", 11)
    CONNECTION(H64, "N1", 12)
    CONNECTION(V128, "N1", 13)

    CONNECTION("K1", 10, "M1", 11)
    CONNECTION("K1", 12, "M1", 12)
    CONNECTION("K1", 13, "M1", 6)
    CONNECTION("K1", 15, "M1", 5)
    CONNECTION("L1", 10, "M1", 4)
    CONNECTION("L1", 12, "M1", 3)
    CONNECTION("L1", 13, "M1", 2)
    CONNECTION("L1", 15, "M1", 1)

    CONNECTION("M1", 8, "S2", 1)
    CONNECTION(VCC, "S2", 2)

    CONNECTION(VCC, "F1", 4)
    CONNECTION("N1", 14, "F1", 2)
    CONNECTION(H8, "F1", 3)
    CONNECTION(VCC, "F1", 1)

    CONNECTION("F1", 5, "F2", 5)
    CONNECTION("H2", 4, "F2", 4)

    CONNECTION("J3", 8, "H2", 3)

    CONNECTION(H16, "J3", 2)
    CONNECTION(V4, "J3", 6)
    CONNECTION(V8, "J3", 5)
    CONNECTION(V16, "J3", 4)
    CONNECTION(V16_xor_V32, "J3", 3)
    CONNECTION(H128, "J3", 1)
    CONNECTION(ZONEH, "J3", 11)
    CONNECTION(ZONEV_n, "J3", 12)



    // Coin / Start
    // N.O. Input + Inverter = N.C.
    CONNECTION("START", 1_NC, "B9", 11)
    CONNECTION("START", 1_NC, "B9", 12)

    CONNECTION("B9", 13, "L10", 12)
    CONNECTION("H10", 3, "L10", 11)

    CONNECTION(VCC, "K10", 10)
    CONNECTION("L10", 13, "K10", 12)
    CONNECTION(V256, "K10", 11)
    CONNECTION("B9", 10, "K10", 13)

    CONNECTION(MISS_n, "J10", 2)
    CONNECTION(ATTRACT_n, "J10", 1)
    CONNECTION("H10", 3, "J10", 13)

    CONNECTION("J10", 12, "H10", 2)
    CONNECTION("K10", 8, "H10", 1)

    CONNECTION(BALL, "J10", 5)
    CONNECTION(ZONEH, "J10", 4)
    CONNECTION(H256_n, "J10", 3)

    CONNECTION("J10", 6, "J10", 10)
    CONNECTION(ATTRACT_n, "J10", 11)
    CONNECTION("H10", 6, "J10", 9)

    CONNECTION("J10", 8, "H10", 5)
    CONNECTION("K10", 8, "H10", 4)

    CONNECTION("H10", 6, "J4", 1)


    CONNECTION("J9", 5, "H9", 4)
    CONNECTION("START", 1_NC, "H9", 5)

    CONNECTION(VCC, "J9", 10)
    CONNECTION("H9", 6, "J9", 12)
    CONNECTION(H256, "J9", 11)
    CONNECTION("K8", 10, "J9", 13)

    CONNECTION("H9", 3, "J9", 4)
    CONNECTION(VCC, "J9", 2)
    CONNECTION("M9", 11, "J9", 3)
    CONNECTION("J9", 8, "J9", 1)

    CONNECTION("B5", 5, "J8", 2)
    CONNECTION("J9", 9, "J8", 13)
    CONNECTION("J9", 6, "J8", 1)

    CONNECTION("COIN", 1_NO, "H9", 1)
    CONNECTION("K8", 10, "H9", 2)

    CONNECTION("F9", 8, "B9", 8)
    CONNECTION("J9", 5, "B9", 9)


    CONNECTION("COIN", 1_NO, "K8", 9)

    // TODO: Optional Coin Counter?
    CONNECTION("K8", 8, "H9", 9) // H9 pin # not shown
    CONNECTION(VCC, "H9", 10) // H9 pin # not shown

    CONNECTION("H9", 8, "F9", 4)
    CONNECTION("COIN", 1_NO, "F9", 2)
    CONNECTION(V128, "F9", 3)
    CONNECTION(VCC, "F9", 1)

    CONNECTION("H9", 8, "F9", 10)
    CONNECTION("F9", 5, "F9", 12)
    CONNECTION(V128, "F9", 11)
    CONNECTION(VCC, "F9", 13)

    CONNECTION(GND, "L10", 8)
    CONNECTION("F9", 8, "L10", 9)

    CONNECTION(GND, "S1", 1)
    CONNECTION(VCC, "S1", 2)

    CONNECTION("S1", 3, "K9", 4)
    CONNECTION(VCC, "K9", 2)
    CONNECTION("J8", 12, "K9", 3)
    CONNECTION("L10", 10, "K9", 1)

    CONNECTION("K8", 10, "K9", 10)
    CONNECTION("K9", 5, "K9", 12)
    CONNECTION("J8", 12, "K9", 11)
    CONNECTION("L10", 10, "K9", 13)

    CONNECTION("K9", 8, "LATCH", 1)
    CONNECTION("L10", 10, "LATCH", 2)

    CONNECTION("LATCH", 3, "K8", 11)



    // Balls Remaining
    CONNECTION(START_n, "K10", 4)
    CONNECTION(VCC, "K10", 2)
    CONNECTION(SERVE_n, "K10", 3)
    CONNECTION(FREE_BALL_SWITCHED_n, "K10", 1)

    CONNECTION(SERVE_RESET, "M9", 2)
    CONNECTION("K10", 5, "M9", 1)

    CONNECTION(VCC, "N10", 1)
    CONNECTION(VCC, "N10", 2)
    CONNECTION("M9", 3, "N10", 8)
    CONNECTION(START_n, "N10", 9)

    CONNECTION("K10", 6, "L10", 6)
    CONNECTION(MISS_n, "L10", 5)

    CONNECTION(VCC, "S3", 1)
    CONNECTION(GND, "S3", 2)

    // Diodes used to pull bits 4+5 high when ball count is set to 3. 
    // Diodes disabled when ball count set to 5. Use OR gate to handle this
    CONNECTION("WIRE_OR", 1, "S3", 3)
    CONNECTION("WIRE_OR", 2, "N10", 6)

    CONNECTION("WIRE_OR", 4, "S3", 3)
    CONNECTION("WIRE_OR", 5, "N10", 10)

    CONNECTION("N10", 5, "S3", 4)
    CONNECTION("WIRE_OR", 6, "S3", 5)

    CONNECTION("S3", 6, "M9", 13)
    CONNECTION("L10", 4, "M9", 12)

    CONNECTION(VCC, "M10", 9)
    CONNECTION(VCC, "M10", 7)
    CONNECTION(VCC, "M10", 6)
    CONNECTION("WIRE_OR", 6, "M10", 5)
    CONNECTION("WIRE_OR", 3, "M10", 4)
    CONNECTION("N10", 5, "M10", 3)
    CONNECTION("N10", 4, "M10", 2)
    CONNECTION("N10", 3, "M10", 1)
    CONNECTION(H8, "M10", 11)
    CONNECTION(H16, "M10", 12)
    CONNECTION(H32_n, "M10", 13)
    CONNECTION(GND, "M10", 10)

    CONNECTION(V128_n, "L9", 9)
    CONNECTION(V4, "L9", 10)
    CONNECTION(VFIELD_n, "L9", 11)

    CONNECTION("L9", 8, "J8", 3)
    CONNECTION(H4, "J8", 5)
    CONNECTION(V8_n, "J8", 4)

    CONNECTION("F4", 6, "L10", 3)
    CONNECTION(ZONEH, "L10", 2)

    CONNECTION("J8", 6, "L9", 2)
    CONNECTION("L10", 1, "L9", 13)
    CONNECTION("M10", 14, "L9", 1)



    // Video Summing
	CONNECTION(PLAYFIELD_n,"N2", 2)
	CONNECTION(BALLS_REMAINING_n,"N2", 1)

    CONNECTION(THUMPER_BUMPERS_n, "H3", 4)
    CONNECTION(CROSS_n, "H3", 5)
    CONNECTION(KNOCKDOWNS_n, "H3", 3)

    CONNECTION(FLIPPER, "H4", 5)
    CONNECTION("H3", 6, "H4", 6)


	/*Video Output*/
    //CONNECTION("VIDEO", Video::HBLANK_PIN, "H7", 8)
    //CONNECTION("VIDEO", Video::VBLANK_PIN, "F7", 10)
    CONNECTION("VIDEO", Video::HBLANK_PIN, "F7", 1)
    CONNECTION("VIDEO", Video::VBLANK_PIN, "F7", 10)
	CONNECTION("VIDEO", 1, "H4", 4)
	CONNECTION("VIDEO", 2, "N2", 3)
    CONNECTION("VIDEO", 3, "L7", 6)
    CONNECTION("VIDEO", 4, CROSS_CENTER_FLASHING)
    CONNECTION("VIDEO", 5, BALL)
    CONNECTION("VIDEO", 6, SCORE_OUT)



    /**************************************************************************
		Layout - Page 3
	**************************************************************************/
    // Hit / Sound
    CONNECTION("C5", 3, "B9", 2)
    CONNECTION(FREE_BALL_SWITCHED_n, "B9", 3)

    CONNECTION(FLIPPER_MOTION_n, "B9", 5)
    CONNECTION(FLIPPER_HIT_WINDOW_n, "B9", 6)

    CONNECTION(CROSS_CENTER_FLASHING, "C9", 2)
    CONNECTION("B9", 1, "C9", 1)

    CONNECTION(FLIPPER, "C9", 5)
    CONNECTION("B9", 4, "C9", 4)

    CONNECTION(BALL, "A9", 12)
    CONNECTION(CROSS_CENTER_FLASHING, "A9", 13)

    CONNECTION(BALL, "B8", 5)
    CONNECTION(PLAYFIELD_n, "B8", 3)
    CONNECTION(SLINGSHOTS, "B8", 4)

    CONNECTION(BALL, "C8", 10)
    CONNECTION(_100_POINT_OBJECTS, "C8", 9)

    CONNECTION(BALL, "C8", 4)
    CONNECTION("C9", 3, "C8", 5)

    CONNECTION(BALL, "C8", 2)
    CONNECTION("C9", 6, "C8", 1)

    CONNECTION(BALL, "H9", 13)
    CONNECTION(PLAYFIELD_n, "H9", 12)

    CONNECTION("B8", 6, "B8", 10)
    CONNECTION("C8", 8, "B8", 9)
    CONNECTION("C8", 3, "B8", 11)

    CONNECTION("B8", 8, "E2", 11)
    CONNECTION("H9", 11, "E2", 12)

    CONNECTION("E2", 13, "H2", 9)

    CONNECTION("A5", 10, "L4", 2)
    CONNECTION("A9", 11, "L4", 1)

    CONNECTION("B8", 6, "D8", 10)
    CONNECTION("C8", 8, "D8", 9)
    CONNECTION("C8", 6, "D8", 13)
    CONNECTION("C8", 3, "D8", 12)

    CONNECTION("D8", 8, "A5", 12)
    CONNECTION(VCC, "A5", 11)
    CONNECTION("L4", 3, "A5", 13)

    CONNECTION(VCC, "F1", 10)
    CONNECTION(SERVE_n, "F1", 12)
    CONNECTION("A5", 10, "F1", 11)
    CONNECTION(VRESET_n, "F1", 13)

    CONNECTION("B8", 6, "D9-2", 10)
    CONNECTION(GND,     "D9-2", 12)
    CONNECTION("D8", 8, "D9-2", 11)
    CONNECTION(VCC,     "D9-2", 13)

    CONNECTION("C8", 8, "D9-2", 4)
    CONNECTION(GND,     "D9-2", 2)
    CONNECTION("D8", 8, "D9-2", 3)
    CONNECTION(VCC,     "D9-2", 1)

    CONNECTION("C8", 6, "D9-1", 4)
    CONNECTION(GND,     "D9-1", 2)
    CONNECTION("D8", 8, "D9-1", 3)
    CONNECTION(VCC,     "D9-1", 1)

    CONNECTION("C8", 3, "D9-1", 10)
    CONNECTION(GND,     "D9-1", 12)
    CONNECTION("D8", 8, "D9-1", 11)
    CONNECTION(VCC,     "D9-1", 13)

    CONNECTION("F1", 9, "A9", 1)
    CONNECTION("D9-2", 9, "A9", 2)

    CONNECTION("F1", 9, "A9", 10)
    CONNECTION("D9-2", 5, "A9", 9)

    CONNECTION("F1", 9, "A9", 4)
    CONNECTION("D9-1", 5, "A9", 5)

    // TODO: Finish Sound


    
    // Score
    CONNECTION(START, "C7", 2)
    CONNECTION(START, "C7", 3)
    CONNECTION(GND, "C7", 6)
    CONNECTION(GND, "C7", 7)
    CONNECTION("A9", 3, "C7", 14)
    CONNECTION("C7", 12, "C7", 1)

    CONNECTION("C7", 11, "D5", 13)
    CONNECTION("A9", 8, "D5", 12)

    CONNECTION(START, "D7", 2)
    CONNECTION(START, "D7", 3)
    CONNECTION(GND, "D7", 6)
    CONNECTION(GND, "D7", 7)
    CONNECTION("D5", 11, "D7", 14)
    CONNECTION("D7", 12, "D7", 1)

    CONNECTION("D7", 11, "D5", 10)
    CONNECTION("A9", 6, "D5", 9)

    CONNECTION(START, "D6", 2)
    CONNECTION(START, "D6", 3)
    CONNECTION(GND, "D6", 6)
    CONNECTION(GND, "D6", 7)
    CONNECTION("D5", 8, "D6", 14)
    CONNECTION("D6", 12, "D6", 1)

    CONNECTION(START, "C6", 2)
    CONNECTION(START, "C6", 3)
    CONNECTION(GND, "C6", 6)
    CONNECTION(GND, "C6", 7)
    CONNECTION("D6", 11, "C6", 14)
    CONNECTION("C6", 12, "C6", 1)

    // TODO: FREE GAME SELECT
    CONNECTION(VCC, "B5", 4)
    CONNECTION(GND, "B5", 2)
    CONNECTION(START_n, "B5", 3)
    CONNECTION(VCC, "B5", 1)


    CONNECTION("D7", 12, "E7", 3)
    CONNECTION("C7", 12, "E7", 4)
    CONNECTION("C6", 12, "E7", 5)
    CONNECTION("D6", 12, "E7", 6)
    CONNECTION("D7", 9, "E7", 13)
    CONNECTION("C7", 9, "E7", 12)
    CONNECTION("C6", 9, "E7", 11)
    CONNECTION("D6", 9, "E7", 10)
    CONNECTION(V16, "E7", 14)
    CONNECTION(V32, "E7", 2)
    CONNECTION("F7", 13, "E7", 1)
    CONNECTION("F7", 13, "E7", 15)
    
    CONNECTION(V16, "A6", 12)
    CONNECTION(V64, "A6", 13)

    CONNECTION(V32, "F7", 12)
    CONNECTION("A6", 11, "F7", 11)

    CONNECTION("D7", 8, "E6", 3)
    CONNECTION("C7", 8, "E6", 4)
    CONNECTION("C6", 8, "E6", 5)
    CONNECTION("D6", 8, "E6", 6)
    CONNECTION("D7", 11, "E6", 13)
    CONNECTION("C7", 11, "E6", 12)
    CONNECTION("C6", 11, "E6", 11)
    CONNECTION("D6", 11, "E6", 10)
    CONNECTION(V16, "E6", 14)
    CONNECTION(V32, "E6", 2)
    CONNECTION("F7", 13, "E6", 1)
    CONNECTION("F7", 13, "E6", 15)

    CONNECTION(VCC, "F6", 3)
    CONNECTION(VCC, "F6", 5)
    CONNECTION("E7", 7, "F6", 7)
    CONNECTION("E7", 9, "F6", 1)
    CONNECTION("E6", 7, "F6", 2)
    CONNECTION("E6", 9, "F6", 6)
    CONNECTION(SCORE_WINDOW, "F6", 4)

    CONNECTION("F7", 13, "J4", 11)

    CONNECTION(V32_xor_V128, "F4", 13)
    CONNECTION("J4", 10, "F4", 12)

    CONNECTION(ZONEV, "F4", 9)
    CONNECTION("F4", 11, "F4", 10)

    CONNECTION(H32H64, "H3", 2)
    CONNECTION(H256_n, "H3", 13)
    CONNECTION(ZONEH_n, "H3", 1)

    CONNECTION("H3", 12, "H4", 8)
    CONNECTION("F4", 8, "H4", 9)

    CONNECTION("H4", 10, "J4", 9)

    CONNECTION("F6", 12, "F5", 1)
    CONNECTION("F6", 11, "F5", 3)
    CONNECTION("F6", 15, "F5", 6)
    CONNECTION("F6", 9, "F5", 9)
    CONNECTION(GND, "F5", 2)
    CONNECTION(GND, "F5", 4)
    CONNECTION(GND, "F5", 5)
    CONNECTION(GND, "F5", 7)
    CONNECTION(V2, "F5", 11)
    CONNECTION(H8, "F5", 12)
    CONNECTION(V4, "F5", 13)
    CONNECTION(V8_n, "F5", 10)

    CONNECTION("F6", 13, "E5", 1)
    CONNECTION(GND, "E5", 3)
    CONNECTION(GND, "E5", 6)
    CONNECTION("F6", 10, "E5", 9)
    CONNECTION(GND, "E5", 2)
    CONNECTION("F6", 14, "E5", 4)
    CONNECTION(GND, "E5", 5)
    CONNECTION(GND, "E5", 7)
    CONNECTION(H2, "E5", 11)
    CONNECTION(H4, "E5", 12)
    CONNECTION(H8, "E5", 13)
    CONNECTION(V8_n, "E5", 10)

    CONNECTION("F5", 14, "C5", 5)
    CONNECTION("E5", 14, "C5", 4)

    CONNECTION("C5", 6, "C5", 2)
    CONNECTION(H16, "C5", 1)

    CONNECTION("C5", 3, "D5", 2)
    CONNECTION(FREE_BALL_INDICATOR, "D5", 1)

    CONNECTION("B5", 6, "H4", 12)
    CONNECTION(GRAVITY, "H4", 11)

    CONNECTION("D5", 3, "D5", 4)
    CONNECTION("H4", 13, "D5", 5)

    CONNECTION("D5", 6, "C9", 10)
    CONNECTION(SCORE_WINDOW_n, "C9", 9)




#ifdef DEBUG
    CONNECTION("LOG1", 1,START_n)
	CONNECTION("LOG1", 2,SERVE_n)
    CONNECTION("LOG1", 3,"N2",6)
    CONNECTION("LOG1", 4, "M2", 12)
    CONNECTION("LOG1", 5, "A4", 15)
    CONNECTION("LOG1", 6, "A4", 13)
    CONNECTION("LOG1", 7, "A4", 12)
    CONNECTION("LOG1", 8, "A4", 10)
    CONNECTION("LOG1", 9, "J10", 6)
    CONNECTION("LOG1", 10, BALL)
    CONNECTION("LOG1", 11, ZONEH)
    CONNECTION("LOG1", 12, H256_n)
    /*CONNECTION("LOG1", 1,"H4",4)
	CONNECTION("LOG1", 2,"N2",3)
    CONNECTION("LOG1", 3,"L7",6)
    CONNECTION("LOG1", 4,CROSS_CENTER_FLASHING)
    CONNECTION("LOG1", 5,BALL)
    CONNECTION("LOG1", 6,SCORE_OUT)*/

    /*CONNECTION(HIT, "LOG1", 1)
	CONNECTION(ZONEV_n,"LOG1", 2)
	CONNECTION("M2", 12,"LOG1", 3)
	CONNECTION("M2", 9,"LOG1", 4)
	CONNECTION(V_UP,"LOG1", 5)
	CONNECTION("L3", 4,"LOG1", 6)
	CONNECTION("H2", 6,"LOG1", 7)
	CONNECTION("L2", 6,"LOG1", 8)*/
    /*CONNECTION(HIT, "LOG1", 1)
	CONNECTION("M4", 8,"LOG1", 2)
	CONNECTION("N2", 8,"LOG1", 3)
	CONNECTION("N3", 11,"LOG1", 4)
	CONNECTION("M2", 4,"LOG1", 5)
	CONNECTION("E4", 13,"LOG1", 6)
	CONNECTION("L3", 4,"LOG1", 7)
	CONNECTION("L3", 1,"LOG1", 8)
	CONNECTION("M4", 11,"LOG1", 9)
	CONNECTION(H_UP,"LOG1", 10)
	CONNECTION("E4", 3,"LOG1", 11)
	CONNECTION("E4", 2,"LOG1", 12)
	CONNECTION("E4", 6,"LOG1", 13)
	CONNECTION("E4", 7,"LOG1", 14)
	CONNECTION(R0,"LOG1", 15)
	CONNECTION(R3,"LOG1", 16)*/
    /*CONNECTION("B3", 3,"LOG1", 1)
	CONNECTION("B3", 2,"LOG1", 2)
	CONNECTION("B3", 6,"LOG1", 3)
	CONNECTION("B3", 7,"LOG1", 4)
	CONNECTION("B2", 3,"LOG1", 5)*/
    /*CONNECTION("A3", 11,"LOG1", 1)
	CONNECTION("A3", 3,"LOG1", 2)
	CONNECTION("A3", 6,"LOG1", 3)
	CONNECTION("A3", 8,"LOG1", 4)
	CONNECTION(V_UP_n,"LOG1", 5)*/
    /*CONNECTION(ZONEV_n,"LOG1", 1)
	CONNECTION("M2", 12,"LOG1", 2)
	CONNECTION("M2", 9,"LOG1", 3)
	CONNECTION(SERVE_n,"LOG1", 4)
	CONNECTION(V_UP,"LOG1", 5)*/
    /*CONNECTION("N2", 8,"LOG1", 1)
	CONNECTION("C4", 12,"LOG1", 2)
	CONNECTION("C4", 9,"LOG1", 3)
	CONNECTION(SERVE_n,"LOG1", 4)
	CONNECTION("A4", 13,"LOG1", 5)
	CONNECTION("B2", 2,"LOG1", 6)
	CONNECTION("B2", 6,"LOG1", 7)
	CONNECTION("B2", 7,"LOG1", 8)
	CONNECTION("A2", 5,"LOG1", 9)
	CONNECTION("A2", 9,"LOG1", 10)
	CONNECTION("D1",11,"LOG1", 11)
	CONNECTION(SERVE_RESET_n,"LOG1", 12)
	CONNECTION("A1", 9,"LOG1", 13)
	CONNECTION("A1", 5,"LOG1", 14)
	CONNECTION(VRESET,"LOG1", 15)*/
    // Add signals to be logged here
	/*CONNECTION("M7", 3,"LOG1", 1)
	CONNECTION("M7",11,"LOG1", 2)
	CONNECTION("M7", 6,"LOG1", 3)
	CONNECTION("M7", 8,"LOG1", 4)
	CONNECTION(H1,"LOG1", 5)
	CONNECTION(H2,"LOG1", 6)
	CONNECTION(H4,"LOG1", 7)
	CONNECTION(H8,"LOG1", 8)
	CONNECTION("L7", 7,"LOG1", 9)
	CONNECTION("L7", 5,"LOG1", 10)
	CONNECTION("F7", 10,"LOG1", 11)
	CONNECTION(HRESET, "LOG1", 12)*/

#endif

CIRCUIT_LAYOUT_END

