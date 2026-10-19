#include "../circuit_desc.h"
#include "../circuit.h"

#define DEBUG
#undef DEBUG

#ifdef DEBUG
static VcdLogDesc vcd_log_desc
(
    "output_air.vcd",
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
    15, "O"
);
#endif

static Mono9602Desc b1_desc(K_OHM(9.1), U_FARAD(100.0), K_OHM(9.1), U_FARAD(100.0));
static Mono9602Desc c1_desc(K_OHM(15.0), U_FARAD(5.0), K_OHM(15.0), U_FARAD(5.0));
static Mono9602Desc e1_desc(K_OHM(33.0), U_FARAD(47.0), K_OHM(27.0), P_FARAD(100.0));
static Mono555Desc d9_555_desc(K_OHM(610.0), U_FARAD(100.0));

static DipswitchDesc dipswitch1_desc("coinage", "dice_dipswitch_1", "Coinage", 0, "1 Coin / 1 Credit", "1 Coin / 2 Credits");
static DipswitchDesc dipswitch2_desc("plane_type", "dice_dipswitch_2", "Plane Type", 0, "Airplane", "UFO");
static PotentimeterMono555Desc pot1_desc("playtime", "Play Time", K_OHM(830.0), K_OHM(220.0), K_OHM(1220.0), d9_555_desc);

static RomDesc k1_desc("antiaircraft", "aa.k1", 0x9DE772D5);

// 100 ms period +/- 25% (Guess). TODO: Determine actual functionality
static CUSTOM_LOGIC( RANDOM_CLOCK_GEN )
{
    // Output should be high at start, so push event immediately
    if(chip->circuit->global_time == 0)
    {
        chip->pending_event = chip->circuit->queue_push(chip, 1);
    }
    else
    {
        double r = 1.0 + (double(rand()) / RAND_MAX - 0.5) / 2.0;
        uint64_t delay = uint64_t(100.0e-3 * r / Circuit::timescale);

        chip->pending_event = chip->circuit->queue_push(chip, delay);
    }
}

static CHIP_LOGIC( RANDOM_CLOCK_BUF )
{
    pin[i1] = pin[1];
}

static CHIP_DESC( RANDOM_CLOCK_GEN ) = 
{
	CUSTOM_CHIP_START( &RANDOM_CLOCK_GEN )
        INPUT_PINS( i1 )
        OUTPUT_PIN( 1 ),

    CHIP_START( RANDOM_CLOCK_BUF )
        INPUT_PINS( 1 )
        OUTPUT_PIN( i1 )
        OUTPUT_DELAY_NS( 1.0, 1.0 ),

    CHIP_DESC_END
};

static INPUT_DESC( antiaircraft )
    INPUT_INFO(BUTTONS1_INPUT, {{ 1, 2, 3 }}, "Fire Left Cannon")
    INPUT_INFO(BUTTONS2_INPUT, {{ 1, 2, 3 }}, "Fire Right Cannon")
    INPUT_INFO(COIN_INPUT, {{ 1 }}, "Insert Coin")
    INPUT_INFO(START_INPUT, {{ 1 }}, "Start Game")
INPUT_DESC_END

static VIDEO_DESC ( antiaircraft )
    VIDEO_RETRO_V_SIZE(252)
VIDEO_DESC_END

CIRCUIT_LAYOUT( antiaircraft )
	/**************************************************************************
	* Chips                                                                   *
	**************************************************************************/
    CHIP("CLOCK", CLOCK_14_318_MHZ)
    CHIP("RANDOM_CLOCK", RANDOM_CLOCK_GEN)
    
    CHIP("A1", 7402)
    CHIP("A2", 7408)
    CHIP("A3", 7493)
    CHIP("A4", 74153)
    CHIP("A5", 74153)
    CHIP("A6", 7448)
    CHIP("A7", 9312)

    CHIP("B1", 9602, &b1_desc)
    CHIP("B2", 7400)
    CHIP("B3", 7474)
    CHIP("B4", 7490)
    CHIP("B5", 7490)
    CHIP("B6", 9312)
    CHIP("B7", 7402)
    CHIP("B8", 7400)

    CHIP("C1", 9602, &c1_desc)
    CHIP("C2", 7400)
    CHIP("C3", 7402)
    CHIP("C4", 7490)
    CHIP("C5", 7490)
    CHIP("C6", 7486)
    CHIP("C7", 7410)
    CHIP("C8", 7404)

    CHIP("D1", 7474)
    CHIP("D2", 7427)
    CHIP("D3", 7420) // Actually a 7413
    CHIP("D4", 7420)
    CHIP("D5", 7402)
    CHIP("D6", 9316)
    CHIP("D7", 9316)
    CHIP("D8", 7474)
    CHIP("D9", 555_Mono, &d9_555_desc) // Actually a 556

    CHIP("E1", 9602, &e1_desc)
    CHIP("E2", 7404)
    CHIP("E3", 9316)
    CHIP("E5", 7486)
    CHIP("E6", 9316)
    CHIP("E7", 9316)
    CHIP("E8", 7408)
    CHIP("E9", 7474)

    CHIP("F1", 9316)
    CHIP("F2", 74107)
    CHIP("F3", 7402)
    CHIP("F4", 7408)
    CHIP("F5", 7474)
    CHIP("F6", 7400)
    CHIP("F7", 74107)
    CHIP("F8", 7474)
    CHIP("F9", 7404)

    CHIP("H1", 9316)
    CHIP("H2", 7408)
    CHIP("H3", 7400)
    CHIP("H4", 9316)
    CHIP("H5", 9316)
    CHIP("H6", 7420)
    CHIP("H7", 7402)
    CHIP("H8", 7432)
    CHIP("H9", 7400)

    CHIP("J1", 7486)
    CHIP("J2", 7486)
    CHIP("J3", 7402)
    CHIP("J4", 7474)
    CHIP("J5", 7474)
    CHIP("J6", 74107)
    CHIP("J7", 7400)
    CHIP("J8", 7474)
    CHIP("J9", 74153)

    CHIP("K1", 82S123, &k1_desc)
    CHIP("K2", 7474)
    CHIP("K3", 7404)
    CHIP("K4", 7493)
    CHIP("K5", 7493)
    CHIP("K6", 7410)
    CHIP("K7", 7486)
    CHIP("K8", 7474)
    CHIP("K9", 7474)

    CHIP("L1", 9312)
    CHIP("L3", 74153)
    CHIP("L4", 74153)
    CHIP("L5", 74153)
    CHIP("L6", 7402)
    CHIP("L7", 9316)
    CHIP("L8", 9316)
    CHIP("L9", 7400)

    CHIP("M3", 7485)
    CHIP("M4", 7485)
    CHIP("M5", 74153)
    CHIP("M6", 7400)
    CHIP("M7", 9316)
    CHIP("M8", 9316)
    CHIP("M9", 7408)

    CHIP("N4", 7404)
    CHIP("N5", 7450)
    CHIP("N6", 7402)
    CHIP("N7", 7408)
    CHIP("N8", 7400)
    CHIP("N9", 7402)

    CHIP("LATCH", LATCH)
    CHIP("COIN", COIN_INPUT)
    CHIP("START", START_INPUT)

    CHIP("BUTTONS1", BUTTONS1_INPUT) // Buttons are normally closed (active high)
    CHIP("BUTTONS2", BUTTONS2_INPUT)

    CHIP("DSW1", DIPSWITCH, &dipswitch1_desc)
    CHIP("DSW2", DIPSWITCH, &dipswitch2_desc)
    CHIP("POT1", POT_555_MONO, &pot1_desc)
    POTENTIOMETER_CONNECTION("POT1", "D9")

    VIDEO(antiaircraft)
    INPUT(antiaircraft)

    OPTIMIZATION_HINT("M3", 64, 64)
    OPTIMIZATION_HINT("M4", 64, 64)
    OPTIMIZATION_HINT("L1", 256, 64)

#ifdef DEBUG
	CHIP("LOG1", VCD_LOG, &vcd_log_desc)
#endif
	
    /**************************************************************************
    * Signals                                                                 *
	**************************************************************************/
	#define CLOCK  "J4", 9
	#define CLOCK_n  "J4", 8

    #define H1 "H4", 14
    #define H2 "H4", 13
    #define H4 "H4", 12
    #define H8 "H4", 11
    #define H16 "H5", 14
    #define H16_n "K3", 6
    #define H32 "H5", 13
    #define H64 "H5", 12
    #define H64_n "K3", 4
    #define H128 "H5", 11
    #define H256 "J6", 3
    #define H256_n "J6", 2

    #define H256_xor_H32 "C6", 3
    #define H128_xor_H256 "C6", 8
    #define H128_xor_H256_n "C8", 12

    #define HRESET "J4", 6
    #define HRESET_n "J4", 5

    #define HSYNC "J3", 4
    #define HSYNC_n "J3", 1

    #define V1 "K4", 12
    #define V2 "K4", 9
    #define V4 "K4", 8
    #define V8 "K4", 11
    #define V16 "K5", 12
    #define V32 "K5", 9
    #define V64 "K5", 8
    #define V128 "K5", 11
    #define V256 "J6", 5
    #define V256_n "J6", 6

    #define V1_n "K3", 2
    #define V2_n "K3", 8
    #define V4_n "K3", 10
    #define V8_n "K3", 12

    #define VRESET "J5", 6
    #define VRESET_n "J5", 5

    #define VSYNC "J3", 10
    #define VSYNC_n "J3", 13

    #define COMP_SYNC "J2", 3

    #define SCOREV_n "C7", 6

    #define Q "F9", 10

    #define ATTRACT "D8", 9
    #define ATTRACT_n "D8", 8

    #define RA "K9", 5
    #define RB "K9", 9
    #define RA_n "K9", 6
    #define RB_n "K9", 8

    #define RA_nor_RB "N6", 10

    #define LA "K8", 5
    #define LB "K8", 9
    #define LA_n "K8", 6
    #define LB_n "K8", 8

    #define LA_or_LB "N4", 10

    #define FIRE_RIGHT "J8", 6
    #define FIRE_RIGHT_n "J8", 5

    #define FIRE_LEFT "J8", 8
    #define FIRE_LEFT_n "J8", 9

    #define RMH1 "M8", 14
    #define RMH2 "M8", 13
    #define RMH3 "M8", 12
    #define RMH4 "M8", 11

    #define RMV1 "L7", 14
    #define RMV2 "L7", 13
    #define RMV3 "L7", 12
    #define RMV4 "L7", 11

    #define LARGE_RIGHT_MISSILE "N9", 10
    #define RIGHT_MISSILE_n "M9", 11
    #define RIGHT_MISSILE_WIN "L6", 4

    #define LMH1 "E6", 14
    #define LMH2 "E6", 13
    #define LMH3 "E6", 12
    #define LMH4 "E6", 11

    #define LMV1 "D6", 14
    #define LMV2 "D6", 13
    #define LMV3 "D6", 12
    #define LMV4 "D6", 11

    #define LARGE_LEFT_MISSILE "C3", 4
    #define LEFT_MISSILE_n "F4", 8
    #define LEFT_MISSILE_WIN "F3", 13

    #define RT_HIT "B1", 6
    #define RT_HIT_n "B1", 7

    #define LT_HIT "B1", 10
    #define LT_HIT_n "B1", 9

    #define DELAY_R "C1", 6
    #define DELAY_L "C1", 10

    #define FLASH "A3", 8

    #define MISSILE_VRESET "F5", 8
    #define VCOUNT_n "F4", 11

    #define PLANE_RESET "K2", 8 
    #define PLANE_RESET_n "K2", 9

    #define PH1 "H1", 14
    #define PH2 "H1", 13
    #define PH3 "H1", 12
    #define PH4 "H1", 11

    #define DIR_SELECT_n "F2", 3

    #define RANDOM_CLOCK "D3", 8

    #define START "D8", 5
    #define START_n "D8", 6

    #define HIT_DETECT "B2", 6
    #define TARGET_HIT_n "B3", 8

    #define COMP_HIT_n "C2", 6

    #define VPLANE_ENABLE "E2", 4
    #define PLANE_EN "H2", 8



    
    /**************************************************************************
    * Layout - Page 1                                                         *
	**************************************************************************/
	
    // Clock generation
    CONNECTION("CLOCK", 1, "N4", 3)

    CONNECTION(VCC, "J4", 10)
    CONNECTION("J4", 8, "J4", 12)
    CONNECTION("N4", 4, "J4", 11)
    CONNECTION(VCC, "J4", 13)



    // HSYNC
    CONNECTION(CLOCK, "H4", 2)
	CONNECTION(VCC, "H4", 10)
	CONNECTION(VCC, "H4", 7)
	CONNECTION(VCC, "H4", 9)
	CONNECTION(VCC, "H4", 3) // No connections shown
	CONNECTION(VCC, "H4", 4)
	CONNECTION(VCC, "H4", 5)
	CONNECTION(VCC, "H4", 6)
	CONNECTION(HRESET_n, "H4", 1)

    CONNECTION(CLOCK, "H5", 2)
	CONNECTION(VCC, "H5", 10)
	CONNECTION("H4", 15, "H5", 7)
	CONNECTION(VCC, "H5", 9)
	CONNECTION(VCC, "H5", 3) // No connections shown
	CONNECTION(VCC, "H5", 4)
	CONNECTION(VCC, "H5", 5)
	CONNECTION(VCC, "H5", 6)
	CONNECTION(HRESET_n, "H5", 1)

    CONNECTION(VCC, "J6", 1)
    CONNECTION("H5", 15, "J6", 12)
    CONNECTION(VCC, "J6", 4)
    CONNECTION(HRESET_n, "J6", 13)

    CONNECTION("J6", 3, "H6", 13)
    CONNECTION("H5", 11, "H6", 12)
    CONNECTION("H5", 12, "H6", 10)
    CONNECTION("H4", 11, "H6", 9)

    CONNECTION(VCC, "J4", 4)
    CONNECTION("H6", 8, "J4", 2)
    CONNECTION(CLOCK_n, "J4", 3)
    CONNECTION(VCC, "J4", 1)

    CONNECTION(HRESET, "J3", 2)
    CONNECTION("J3", 4, "J3", 3)
    CONNECTION("J3", 1, "J3", 5)
    //CONNECTION(H32, "J3", 6)
    CONNECTION(H64, "J3", 6) // Schematic says H32, but causes gfx glitch on left launcher. TODO: Investigate



    // VSYNC
    CONNECTION(HRESET, "K4", 14)
	CONNECTION("K4", 12, "K4", 1)
	CONNECTION(VRESET, "K4", 2)
	CONNECTION(VRESET, "K4", 3)

    CONNECTION("K4", 11, "K5", 14)
	CONNECTION("K5", 12, "K5", 1)
	CONNECTION(VRESET, "K5", 2)
	CONNECTION(VRESET, "K5", 3)

    CONNECTION(VCC, "J6", 8)
    CONNECTION("K5", 11, "J6", 9)
    CONNECTION(VCC, "J6", 11)
    CONNECTION(VRESET_n, "J6", 10)

    CONNECTION("J6", 5, "K6", 11)
    CONNECTION("K4", 9, "K6", 10)
    CONNECTION("K4", 12, "K6", 9)

    CONNECTION(VCC, "J5", 4)
    CONNECTION("K6", 8, "J5", 2)
    CONNECTION(HRESET, "J5", 3)
    CONNECTION(VCC, "J5", 1)

    CONNECTION(VRESET, "J3", 12)
    CONNECTION("J3", 10, "J3", 11)
    CONNECTION("J3", 13, "J3", 8)
    CONNECTION(V8, "J3", 9)

    CONNECTION(HSYNC, "J2", 1)
    CONNECTION(VSYNC_n, "J2", 2)




    // Launcher Inputs
    CONNECTION("BUTTONS2", i2, "L9", 13)
    CONNECTION("BUTTONS2", i2, "L9", 12)

    CONNECTION("L9", 11, "H9", 1)
    CONNECTION(ATTRACT_n, "H9", 2)

    CONNECTION("BUTTONS1", i2, "N9", 2)
    CONNECTION("BUTTONS1", i2, "N9", 3)

    CONNECTION("N9", 1, "H9", 13)
    CONNECTION(ATTRACT_n, "H9", 12)

    CONNECTION(GND, "J9", 3)
    CONNECTION("BUTTONS2", i1, "J9", 4)
    CONNECTION("H9", 3, "J9", 5)
    CONNECTION("BUTTONS2", i3, "J9", 6)
    CONNECTION(GND, "J9", 13)
    CONNECTION("BUTTONS1", i3, "J9", 12)
    CONNECTION("H9", 11, "J9", 11)
    CONNECTION("BUTTONS1", i1, "J9", 10)
    CONNECTION(H1, "J9", 14)
    CONNECTION(H2, "J9", 2)
    CONNECTION("J8", 6, "J9", 1)
    CONNECTION("J8", 8, "J9", 15)

    CONNECTION(ATTRACT_n, "K9", 4)
    CONNECTION(H1, "K9", 2)
    CONNECTION("J9", 7, "K9", 3)
    CONNECTION(VCC, "K9", 1)
            
    CONNECTION(ATTRACT_n, "K8", 4)
    CONNECTION(H1, "K8", 2)
    CONNECTION("J9", 9, "K8", 3)
    CONNECTION(VCC, "K8", 1)

    CONNECTION(VCC, "K9", 10)
    CONNECTION(H2, "K9", 12)
    CONNECTION("J9", 7, "K9", 11)
    CONNECTION(ATTRACT_n, "K9", 13)

    CONNECTION(VCC, "K8", 10)
    CONNECTION(H2, "K8", 12)
    CONNECTION("J9", 9, "K8", 11)
    CONNECTION(ATTRACT_n, "K8", 13)

    CONNECTION(V256, "H9", 5)
    CONNECTION("J9", 7, "H9", 4)

    CONNECTION(V256, "H9", 10)
    CONNECTION("J9", 9, "H9", 9)

    CONNECTION(DELAY_R, "H8", 2)
    CONNECTION("H9", 6, "H8", 1)

    CONNECTION("H9", 8, "H8", 13)
    CONNECTION(DELAY_L, "H8", 12)

    CONNECTION("J7", 3, "J8", 4)
    CONNECTION(VCC, "J8", 2)
    CONNECTION(RT_HIT_n, "J8", 3)
    CONNECTION("H8", 3, "J8", 1)

    CONNECTION("J7", 11, "J8", 10)
    CONNECTION(VCC, "J8", 12)
    CONNECTION(LT_HIT_n, "J8", 11)
    CONNECTION("H8", 11, "J8", 13)
    
    CONNECTION(HSYNC_n, "J7", 5)
    CONNECTION(VRESET_n, "J7", 4)

    CONNECTION(LARGE_RIGHT_MISSILE, "J7", 1)
    CONNECTION("J7", 6, "J7", 2)
   
    CONNECTION("J7", 6, "J7", 12)
    CONNECTION(LARGE_LEFT_MISSILE, "J7", 13)

    CONNECTION(FIRE_RIGHT, "H7", 6)
    CONNECTION(FIRE_LEFT, "H7", 5)

    CONNECTION("H7", 4, "H7", 3)
    CONNECTION(ATTRACT, "H7", 2)





    // Right Launcher Graphics
    CONNECTION(H16, "K3", 5)

    CONNECTION(H64, "K3", 3)

    CONNECTION(RA, "M5", 14)
    CONNECTION(RB, "M5", 2)
    CONNECTION(H1, "M5", 6)
    CONNECTION(H2, "M5", 5)
    CONNECTION(H4, "M5", 4)
    CONNECTION(VCC, "M5", 3) // Not Shown
    CONNECTION(H2, "M5", 10)
    CONNECTION(H4, "M5", 11)
    CONNECTION(H8, "M5", 12)
    CONNECTION(VCC, "M5", 13) // Not Shown
    //CONNECTION(GND, "M5", 1)
    //CONNECTION(GND, "M5", 15)
    CONNECTION(SCOREV_n, "M5", 1) // HACK - improves performance
    CONNECTION(SCOREV_n, "M5", 15) // HACK - improves performance

    CONNECTION(RA, "L4", 14)
    CONNECTION(RB, "L4", 2)
    CONNECTION(H4, "L4", 6)
    CONNECTION(H8, "L4", 5)
    CONNECTION(H16_n, "L4", 4)
    CONNECTION(VCC, "L4", 3) // Not Shown
    CONNECTION(H8, "L4", 10)
    CONNECTION(H16_n, "L4", 11)
    CONNECTION(H64_n, "L4", 12)
    CONNECTION(VCC, "L4", 13) // Not Shown
    //CONNECTION(GND, "L4", 1)
    //CONNECTION(GND, "L4", 15)
    CONNECTION(SCOREV_n, "L4", 1) // HACK - improves performance
    CONNECTION(SCOREV_n, "L4", 15) // HACK - improves performance
    

    CONNECTION(RA, "N6", 8)
    CONNECTION(RB, "N6", 9)

    CONNECTION("N6", 10, "C8", 3)

    CONNECTION(H256_xor_H32, "N6", 6)
    CONNECTION("F9", 2, "N6", 5)

    CONNECTION(H16, "J2", 10)
    CONNECTION(H32, "J2", 9)

    CONNECTION("J2", 8, "M6", 2)
    CONNECTION(H128_xor_H256_n, "M6", 1)

    CONNECTION(SCOREV_n, "N6", 11)
    CONNECTION("M6", 3, "N6", 12)

    CONNECTION("N6", 13, "F9", 1)

    CONNECTION("N6", 10, "N5", 13)
    CONNECTION("N6", 4, "N5", 1)
    CONNECTION("C8", 4, "N5", 9)
    CONNECTION("N6", 13, "N5", 10)

    CONNECTION("N5", 8, "N4", 13)

    CONNECTION("N4", 12, "M4", 3)
    CONNECTION(GND, "M4", 2)
    CONNECTION(GND, "M4", 4)
    CONNECTION("M5", 7, "M4", 10)
    CONNECTION("M5", 9, "M4", 12)
    CONNECTION("L4", 7, "M4", 13)
    CONNECTION("L4", 9, "M4", 15)
    CONNECTION(V1, "M4", 9)
    CONNECTION(V2, "M4", 11)
    CONNECTION(V4, "M4", 14)
    CONNECTION(V8, "M4", 1)

    CONNECTION(H256, "N7", 9)
    CONNECTION(CLOCK_n, "N7", 10)

    CONNECTION("N7", 8, "N7", 5)
    CONNECTION("M4", 6, "N7", 4)




    // Left Launcher Graphics
    CONNECTION(LA, "L5", 14)
    CONNECTION(LB, "L5", 2)
    CONNECTION(H1, "L5", 6)
    CONNECTION(H2, "L5", 5)
    CONNECTION(H4, "L5", 4)
    CONNECTION(VCC, "L5", 3) // Not Shown
    CONNECTION(H2, "L5", 10)
    CONNECTION(H4, "L5", 11)
    CONNECTION(H8, "L5", 12)
    CONNECTION(VCC, "L5", 13) // Not Shown
    //CONNECTION(GND, "L5", 1)
    //CONNECTION(GND, "L5", 15)
    CONNECTION(SCOREV_n, "L5", 1) // HACK - improves performance
    CONNECTION(SCOREV_n, "L5", 15) // HACK - improves performance

    CONNECTION(LA, "L3", 14)
    CONNECTION(LB, "L3", 2)
    CONNECTION(H4, "L3", 6)
    CONNECTION(H8, "L3", 5)
    CONNECTION(H16_n, "L3", 4)
    CONNECTION(VCC, "L3", 3) // Not Shown
    CONNECTION(H8, "L3", 10)
    CONNECTION(H16_n, "L3", 11)
    CONNECTION(H64_n, "L3", 12)
    CONNECTION(VCC, "L3", 13) // Not Shown
    //CONNECTION(GND, "L3", 1)
    //CONNECTION(GND, "L3", 15)
    CONNECTION(SCOREV_n, "L3", 1) // HACK - improves performance
    CONNECTION(SCOREV_n, "L3", 15) // HACK - improves performance


    CONNECTION(LA, "N6", 2)
    CONNECTION(LB, "N6", 3)

    CONNECTION("N6", 1, "N4", 11)

    CONNECTION("N6", 1, "N5", 3)
    CONNECTION("N6", 4, "N5", 2)
    CONNECTION("N6", 13, "N5", 4)
    CONNECTION("N4", 10, "N5", 5)

    CONNECTION("N5", 6, "N4", 9)

    CONNECTION(V1, "K3", 1)
    CONNECTION(V2, "K3", 9)
    CONNECTION(V4, "K3", 11)
    CONNECTION(V8, "K3", 13)

    CONNECTION("N4", 8, "M3", 3)
    CONNECTION(GND, "M3", 2)
    CONNECTION(GND, "M3", 4)
    CONNECTION("L5", 7, "M3", 10)
    CONNECTION("L5", 9, "M3", 12)
    CONNECTION("L3", 7, "M3", 13)
    CONNECTION("L3", 9, "M3", 15)
    CONNECTION("K3", 2, "M3", 9)
    CONNECTION("K3", 8, "M3", 11)
    CONNECTION("K3", 10, "M3", 14)
    CONNECTION("K3", 12, "M3", 1)

    CONNECTION(CLOCK_n, "N7", 12)
    CONNECTION(H256_n, "N7", 13)

    CONNECTION("M3", 6, "N7", 1)
    CONNECTION("N7", 11, "N7", 2)

    CONNECTION("N7", 6, "N9", 5)
    CONNECTION("N7", 3, "N9", 6)

    CONNECTION(GND, "E1", 12)
    CONNECTION("N9", 4, "E1", 11)
    CONNECTION(COMP_SYNC, "E1", 13)




    // Coin / Start
    CONNECTION("COIN", i1, "F9", 3)

    CONNECTION("COIN", i1, "F8", 4)
    CONNECTION("F9", 4, "F8", 2)
    CONNECTION(V128, "F8", 3)
    CONNECTION(VCC, "F8", 1)

    CONNECTION(VCC, "F8", 10)
    CONNECTION("F8", 5, "F8", 12)
    CONNECTION(V128, "F8", 11)
    CONNECTION(VCC, "F8", 13)
    
    CONNECTION(GND, "DSW1", 1)
    CONNECTION(VCC, "DSW1", 2)

    CONNECTION("DSW1", 3, "E9", 4)
    CONNECTION(VCC, "E9", 2)
    CONNECTION(ATTRACT, "E9", 3)
    CONNECTION("F8", 9, "E9", 1)

    CONNECTION(Q, "E9", 10)
    CONNECTION("E9", 5, "E9", 12)
    CONNECTION(ATTRACT, "E9", 11)
    CONNECTION("F8", 9, "E9", 13)

    CONNECTION("E9", 8, "LATCH", 1)    
    CONNECTION("F8", 9, "LATCH", 2)

    CONNECTION("LATCH", 3, "F9", 11)


    CONNECTION(ATTRACT, "E8", 2)
    CONNECTION("START", i1, "E8", 1)

    CONNECTION(VCC, "D8", 4)
    CONNECTION("E8", 3, "D8", 2)
    CONNECTION(V256, "D8", 3)
    CONNECTION(Q, "D8", 1)

    CONNECTION("F9", 4, "E8", 12)
    CONNECTION(Q, "E8", 13)

    CONNECTION("E8", 11, "D9", 4)
    CONNECTION("D8", 6, "D9", 2) // 556 pin 6

    CONNECTION("D9", 3, "F9", 13) // 556 pin 5

    CONNECTION("E8", 11, "D8", 10)
    CONNECTION(VCC, "D8", 12)
    CONNECTION("F9", 12, "D8", 11)
    CONNECTION("D8", 6, "D8", 13)




    // Right Missile
    CONNECTION(VRESET, "M9", 4)
    CONNECTION(RT_HIT_n, "M9", 5)

    CONNECTION("M9", 6, "N8", 10)
    CONNECTION(RA_nor_RB, "N8", 9)

    CONNECTION("M9", 6, "N8", 12)
    CONNECTION(RA, "N8", 13)

    CONNECTION(VCC, "M8", 7)
    CONNECTION(VCC, "M8", 10)
    CONNECTION(CLOCK, "M8", 2)
    CONNECTION(VCC, "M8", 3)
    CONNECTION("N8", 11, "M8", 4)
    CONNECTION("N8", 8, "M8", 5)
    CONNECTION("M9", 6, "M8", 6)
    CONNECTION("N8", 3, "M8", 1)
    CONNECTION("L9", 6, "M8", 9)

    CONNECTION("M8", 15, "M7", 7)
    CONNECTION(VCC, "M7", 10)
    CONNECTION(CLOCK, "M7", 2)
    CONNECTION(VCC, "M7", 3)
    CONNECTION(VCC, "M7", 4)
    CONNECTION(GND, "M7", 5)
    CONNECTION(GND, "M7", 6)
    CONNECTION("N8", 3, "M7", 1)
    CONNECTION("L9", 6, "M7", 9)    

    CONNECTION(VCC, "F7", 8)
    CONNECTION("M7", 15, "F7", 9)
    CONNECTION(VCC, "F7", 11)
    CONNECTION("N8", 3, "F7", 10)

    CONNECTION("M7", 15, "M9", 9)
    CONNECTION("F7", 5, "M9", 10)

    CONNECTION("M8", 15, "L9", 4)
    CONNECTION("M9", 8, "L9", 5)

    CONNECTION(H256, "J5", 10)
    CONNECTION(H128, "J5", 12)
    CONNECTION(H4, "J5", 11)
    CONNECTION(VCC, "J5", 13)

    CONNECTION("J5", 8, "N8", 2)
    CONNECTION(FIRE_RIGHT_n, "N8", 1)


    CONNECTION(RT_HIT, "L6", 3)
    CONNECTION("L6", 13, "L6", 2)

    CONNECTION(RA_nor_RB, "L6", 11)
    CONNECTION(RT_HIT, "L6", 12)

    CONNECTION(RT_HIT, "L6", 9)
    CONNECTION(RA_n, "L6", 8)

    CONNECTION(MISSILE_VRESET, "M6", 5)
    CONNECTION(FIRE_RIGHT_n, "M6", 4)

    CONNECTION(VCC, "L7", 7)
    CONNECTION(VCOUNT_n, "L7", 10)
    CONNECTION(HSYNC, "L7", 2)
    CONNECTION("L6", 10, "L7", 3)
    CONNECTION("L6", 13, "L7", 4)
    CONNECTION("L6", 1, "L7", 5)
    CONNECTION(VCC, "L7", 6)
    CONNECTION("M6", 6, "L7", 1)
    CONNECTION("L9", 8, "L7", 9)

    CONNECTION("L7", 15, "L8", 7)
    CONNECTION(VCC, "L8", 10)
    CONNECTION(HSYNC, "L8", 2)
    CONNECTION(GND, "L8", 3)
    CONNECTION(GND, "L8", 4)
    CONNECTION(GND, "L8", 5)
    CONNECTION(GND, "L8", 6)
    CONNECTION("M6", 6, "L8", 1)
    CONNECTION("L9", 8, "L8", 9)    

    CONNECTION("L7", 15, "L9", 10)
    CONNECTION("L8", 15, "L9", 9)


    CONNECTION(RMH2, "K7", 1)
    CONNECTION(RMH3, "K7", 2)

    CONNECTION(RMV3, "K7", 5)
    CONNECTION(RMV2, "K7", 4)

    CONNECTION("K7", 3, "K7", 13)
    CONNECTION("K7", 6, "K7", 12)

    CONNECTION("K7", 3, "H7", 9)
    CONNECTION("K7", 6, "H7", 8)

    CONNECTION(RMH1, "J2", 4)
    CONNECTION(RMV1, "J2", 5)

    CONNECTION(RMV4, "M6", 13)
    CONNECTION("L8", 15, "M6", 12)

    CONNECTION(RMH4, "M6", 10)
    CONNECTION("M9", 8, "M6", 9)

    CONNECTION(FLASH, "K7", 9)
    CONNECTION("K7", 11, "K7", 10)
    
    CONNECTION("H7", 10, "H7", 11)
    CONNECTION("J2", 6, "H7", 12)

    CONNECTION("M6", 11, "L6", 5)
    CONNECTION("M6", 8, "L6", 6)

    CONNECTION(RT_HIT, "H6", 5)
    CONNECTION("K7", 8, "H6", 2)
    CONNECTION("H7", 13, "H6", 1)
    CONNECTION("L6", 4, "H6", 4)


    CONNECTION("L8", 15, "K6", 13)
    CONNECTION(RMV3, "K6", 1)
    CONNECTION(RMV4, "K6", 2)

    CONNECTION("L9", 6, "N9", 9)
    CONNECTION("K6", 12, "N9", 8)

    
    CONNECTION("L9", 6, "N9", 11)
    CONNECTION("L9", 8, "N9", 12)

    CONNECTION(RT_HIT_n, "L9", 1)
    CONNECTION("N9", 13, "L9", 2)

    CONNECTION("L9", 3, "M9", 12)
    CONNECTION("H6", 6, "M9", 13)




    /**************************************************************************
    * Layout - Page 2                                                         *
	**************************************************************************/
    
    // Left Missile
    CONNECTION(VRESET, "F4", 4)
    CONNECTION(LT_HIT_n, "F4", 5)

    CONNECTION("F4", 6, "H3", 12)
    CONNECTION(LA, "H3", 13)

    CONNECTION(LA_or_LB, "C2", 1)
    CONNECTION("F4", 6, "C2", 2)

    CONNECTION("F4", 6, "E2", 9)

    CONNECTION(VCC, "E6", 7)
    CONNECTION(VCC, "E6", 10)
    CONNECTION(CLOCK, "E6", 2)
    CONNECTION("H3", 11, "E6", 3)
    CONNECTION("C2", 3, "E6", 4)
    CONNECTION("E2", 8, "E6", 5)
    CONNECTION(GND, "E6", 6)
    CONNECTION("F5", 5, "E6", 1)
    CONNECTION("F6", 3, "E6", 9)

    CONNECTION("E6", 15, "E7", 7)
    CONNECTION(VCC, "E7", 10)
    CONNECTION(CLOCK, "E7", 2)
    CONNECTION(VCC, "E7", 3)
    CONNECTION(VCC, "E7", 4)
    CONNECTION(GND, "E7", 5)
    CONNECTION(GND, "E7", 6)
    CONNECTION("F5", 5, "E7", 1)
    CONNECTION("F6", 3, "E7", 9)   

    CONNECTION(VCC, "F7", 1)
    CONNECTION("E7", 15, "F7", 12)
    CONNECTION(VCC, "F7", 4)
    CONNECTION("F5", 5, "F7", 13)

    CONNECTION("F7", 3, "M9", 2)
    CONNECTION("E7", 15, "M9", 1)

    CONNECTION("E6", 15, "F6", 2)
    CONNECTION("M9", 3, "F6", 1)

    CONNECTION(H16, "F4", 1)
    CONNECTION(H8, "F4", 2)

    CONNECTION(VCC, "F5", 4)
    CONNECTION(VCC, "F5", 2)
    CONNECTION("F4", 3, "F5", 3)
    CONNECTION(FIRE_LEFT, "F5", 1)


    CONNECTION(LB_n, "D5", 6)
    CONNECTION(LT_HIT, "D5", 5)

    CONNECTION(LT_HIT, "B7", 11)
    CONNECTION(LA_or_LB, "B7", 12)

    CONNECTION("D5", 4, "D5", 3)
    CONNECTION(LT_HIT, "D5", 2)

    CONNECTION(VCC, "D6", 7)
    CONNECTION(VCOUNT_n, "D6", 10)
    CONNECTION(HSYNC, "D6", 2)
    CONNECTION("B7", 13, "D6", 3)
    CONNECTION("D5", 4, "D6", 4)
    CONNECTION("D5", 1, "D6", 5)
    CONNECTION(VCC, "D6", 6)
    CONNECTION("F6", 11, "D6", 1)
    CONNECTION("B8", 6, "D6", 9)

    CONNECTION("D6", 15, "D7", 7)
    CONNECTION(VCC, "D7", 10)
    CONNECTION(HSYNC, "D7", 2)
    CONNECTION(GND, "D7", 3)
    CONNECTION(GND, "D7", 4)
    CONNECTION(GND, "D7", 5)
    CONNECTION(GND, "D7", 6)
    CONNECTION("F6", 11, "D7", 1)
    CONNECTION("B8", 6, "D7", 9)    

    CONNECTION("D6", 15, "B8", 5)
    CONNECTION("D7", 15, "B8", 4)

    CONNECTION(FIRE_LEFT_n, "F6", 13)
    CONNECTION(MISSILE_VRESET, "F6", 12)


    CONNECTION("D7", 15, "K6", 3)
    CONNECTION(LMV4, "K6", 4)
    CONNECTION(LMV3, "K6", 5)

    CONNECTION("F6", 3, "C3", 5)
    CONNECTION("K6", 6, "C3", 6)

    CONNECTION("F6", 3, "C3", 3)
    CONNECTION("B8", 6, "C3", 2)


    CONNECTION(LMH2, "E5", 12)
    CONNECTION(LMH3, "E5", 13)

    CONNECTION(LMV2, "E5", 1)
    CONNECTION(LMV3, "E5", 2)

    CONNECTION("E5", 11, "E5", 10)
    CONNECTION("E5", 3, "E5", 9)

    CONNECTION("E5", 3, "D5", 8)
    CONNECTION("E5", 11, "D5", 9)

    CONNECTION(LMH1, "C6", 5)
    CONNECTION(LMV1, "C6", 4)

    CONNECTION(LMH4, "F6", 9)
    CONNECTION("M9", 3, "F6", 10)

    CONNECTION(LMV4, "J7", 10)
    CONNECTION("D7", 15, "J7", 9)

    CONNECTION(FLASH, "E5", 4)
    CONNECTION("E5", 8, "E5", 5)

    CONNECTION("D5", 10, "D5", 11)
    CONNECTION("C6", 6, "D5", 12)

    CONNECTION("F6", 8, "F3", 12)
    CONNECTION("J7", 8, "F3", 11)

    CONNECTION(LT_HIT, "D4", 4)
    CONNECTION("E5", 6, "D4", 2)
    CONNECTION("D5", 13, "D4", 1)
    CONNECTION("F3", 13, "D4", 5)

    CONNECTION("C3", 1, "F6", 5)
    CONNECTION(LT_HIT_n, "F6", 4)

    CONNECTION("D4", 6, "F4", 9)
    CONNECTION("F6", 6, "F4", 10)




    // Missile VRESET & VCOUNT
    CONNECTION(V8_n, "F5", 10)
    CONNECTION(SCOREV_n, "F5", 12)
    CONNECTION(V4, "F5", 11)
    CONNECTION(VCC, "F5", 13)

    CONNECTION(VSYNC_n, "F4", 13)
    CONNECTION(V256_n, "F4", 12)




    // Collision Detection
    CONNECTION(VPLANE_ENABLE, "A1", 12)
    CONNECTION("A1", 10, "A1", 11)

    CONNECTION("A1", 13, "A1", 9)
    CONNECTION(VRESET, "A1", 8)


    CONNECTION(RT_HIT_n, "A2", 9)
    CONNECTION("A1", 13, "A2", 10)

    CONNECTION(PLANE_EN, "B2", 12)
    CONNECTION(LARGE_RIGHT_MISSILE, "B2", 13)

    CONNECTION(RIGHT_MISSILE_WIN, "A2", 1)
    CONNECTION("A2", 8, "A2", 2)

    CONNECTION("B2", 11, "B1", 5)
    CONNECTION("A2", 3, "B1", 4)
    CONNECTION("C1", 7, "B1", 3)

    CONNECTION("B1", 6, "C1", 5)
    CONNECTION(GND, "C1", 4)
    CONNECTION(VCC, "C1", 3)


    CONNECTION(LT_HIT_n, "A2", 13)
    CONNECTION("A1", 13, "A2", 12)

    CONNECTION(PLANE_EN, "B2", 9)
    CONNECTION(LARGE_LEFT_MISSILE, "B2", 10)

    CONNECTION(LEFT_MISSILE_WIN, "A2", 5)
    CONNECTION("A2", 11, "A2", 4)

    CONNECTION("B2", 8, "B1", 11)
    CONNECTION("A2", 6, "B1", 12)
    CONNECTION("C1", 9, "B1", 13)

    CONNECTION("B1", 10, "C1", 11)
    CONNECTION(GND, "C1", 12)
    CONNECTION(VCC, "C1", 13)

    
    CONNECTION("B2", 11, "B2", 4)
    CONNECTION("B2", 8, "B2", 5)

    CONNECTION("B2", 6, "B2", 1)
    CONNECTION("B2", 6, "B2", 2)

    CONNECTION("B2", 8, "C3", 8)
    CONNECTION(ATTRACT, "C3", 9)

    CONNECTION("B2", 11, "C3", 11)
    CONNECTION(ATTRACT, "C3", 12)

    CONNECTION(VCC, "B3", 10)
    CONNECTION(ATTRACT_n, "B3", 12)
    CONNECTION("B2", 3, "B3", 11)
    CONNECTION(VRESET_n, "B3", 13)
    

    CONNECTION(RT_HIT, "A1", 6)
    CONNECTION(LT_HIT, "A1", 5)

    CONNECTION(VRESET_n, "A3", 14)
    CONNECTION("A3", 12, "A3", 1)
    CONNECTION("A1", 4, "A3", 2)
    CONNECTION("A1", 4, "A3", 3)

    CONNECTION("A1", 4, "A1", 3)
    CONNECTION(ATTRACT, "A1", 2)

    CONNECTION("A1", 1, "C8", 1)




    // Score Counters
    CONNECTION("C3", 10, "C4", 14)
    CONNECTION("C4", 12, "C4", 1)
    CONNECTION(START, "C4", 2)
    CONNECTION(START, "C4", 3)
    CONNECTION(GND, "C4", 6)
    CONNECTION(GND, "C4", 7)

    CONNECTION("C4", 11, "C5", 14)
    CONNECTION("C5", 12, "C5", 1)
    CONNECTION(START, "C5", 2)
    CONNECTION(START, "C5", 3)
    CONNECTION(GND, "C5", 6)
    CONNECTION(GND, "C5", 7)

    CONNECTION("C3", 13, "B4", 14)
    CONNECTION("B4", 12, "B4", 1)
    CONNECTION(START, "B4", 2)
    CONNECTION(START, "B4", 3)
    CONNECTION(GND, "B4", 6)
    CONNECTION(GND, "B4", 7)

    CONNECTION("B4", 11, "B5", 14)
    CONNECTION("B5", 12, "B5", 1)
    CONNECTION(START, "B5", 2)
    CONNECTION(START, "B5", 3)
    CONNECTION(GND, "B5", 6)
    CONNECTION(GND, "B5", 7)





    // Score Window
    CONNECTION(V16, "C8", 5)

    CONNECTION(V32, "E8", 9)
    CONNECTION(V64, "E8", 10)

    CONNECTION(V128, "C7", 5)
    CONNECTION("C8", 6, "C7", 3)
    CONNECTION("E8", 8, "C7", 4)
    
    CONNECTION(H32, "C6", 1)
    CONNECTION(H256, "C6", 2)

    CONNECTION(H64, "C6", 13)
    CONNECTION(H256, "C6", 12)

    CONNECTION(H256, "C6", 10)
    CONNECTION(H128, "C6", 9)

    CONNECTION("C6", 3, "C8", 9)
    
    CONNECTION("C6", 8, "C8", 13)

    CONNECTION("C8", 8, "C7", 11)
    CONNECTION("C6", 11, "C7", 9)
    CONNECTION("C6", 8, "C7", 10)

    CONNECTION("C7", 6, "B7", 5)
    CONNECTION("C7", 8, "B7", 6)

    CONNECTION("E8", 8, "C7", 2)
    CONNECTION(V16, "C7", 1)
    CONNECTION(V128, "C7", 13)

    CONNECTION("C7", 12, "B7", 3)
    CONNECTION("C6", 3, "B7", 2)

    CONNECTION("B7", 1, "B8", 2)
    CONNECTION("C8", 12, "B8", 1)




    // Score Decoding
    CONNECTION("B4", 12, "A4", 3)
    CONNECTION("B5", 12, "A4", 4)
    CONNECTION("C4", 12, "A4", 5)
    CONNECTION("C5", 12, "A4", 6)
    CONNECTION("B4", 9, "A4", 13)
    CONNECTION("B5", 9, "A4", 12)
    CONNECTION("C4", 9, "A4", 11)
    CONNECTION("C5", 9, "A4", 10)
    CONNECTION(H16, "A4", 14)
    CONNECTION(H32, "A4", 2)
    CONNECTION(GND, "A4", 1)
    CONNECTION(GND, "A4", 15)

    CONNECTION("B4", 8, "A5", 3)
    CONNECTION("B5", 8, "A5", 4)
    CONNECTION("C4", 8, "A5", 5)
    CONNECTION("C5", 8, "A5", 6)
    CONNECTION("B4", 11, "A5", 13)
    CONNECTION("B5", 11, "A5", 12)
    CONNECTION("C4", 11, "A5", 11)
    CONNECTION("C5", 11, "A5", 10)
    CONNECTION(H16, "A5", 14)
    CONNECTION(H32, "A5", 2)
    CONNECTION(GND, "A5", 1)
    CONNECTION(GND, "A5", 15)

    CONNECTION(VCC, "A6", 3) // Not shown
    CONNECTION(H16, "A6", 5)
    CONNECTION("A4", 7, "A6", 7)
    CONNECTION("A4", 9, "A6", 1)
    CONNECTION("A5", 7, "A6", 2)
    CONNECTION("A5", 9, "A6", 6)
    CONNECTION("B7", 4, "A6", 4)




    // Score Display
    CONNECTION("A6", 11, "B6", 9)
    CONNECTION(GND, "B6", 7)
    CONNECTION(GND, "B6", 6)
    CONNECTION("A6", 9, "B6", 5)
    CONNECTION("A6", 12, "B6", 4)
    CONNECTION(GND, "B6", 3)
    CONNECTION(GND, "B6", 2)
    CONNECTION("A6", 15, "B6", 1)
    CONNECTION(H8, "B6", 10)
    CONNECTION(H2, "B6", 11)
    CONNECTION(H4, "B6", 12)
    CONNECTION(V8, "B6", 13)

    CONNECTION("A6", 10, "A7", 9)
    CONNECTION(GND, "A7", 7)
    CONNECTION(GND, "A7", 6)
    CONNECTION(GND, "A7", 5)
    CONNECTION("A6", 14, "A7", 4)
    CONNECTION(GND, "A7", 3)
    CONNECTION(GND, "A7", 2)
    CONNECTION("A6", 13, "A7", 1)
    CONNECTION(H8, "A7", 10)
    CONNECTION(V2, "A7", 11)
    CONNECTION(V4, "A7", 12)
    CONNECTION(V8, "A7", 13)

    CONNECTION("B6", 15, "B7", 8)
    CONNECTION("A7", 15, "B7", 9)

    CONNECTION("B7", 10, "B8", 12)
    CONNECTION("B8", 3, "B8", 13)

    CONNECTION(H1, "C8", 11)
    
    CONNECTION(VCC, "B3", 4)
    CONNECTION("B8", 11, "B3", 2)
    CONNECTION("C8", 10, "B3", 3)
    CONNECTION(COMP_SYNC, "B3", 1)




    // Plane Horizontal Counter
    CONNECTION(START, "E1", 4)
    CONNECTION(COMP_HIT_n, "E1", 5)
    CONNECTION(VCC, "E1", 3)

    CONNECTION(VCC, "K2", 10)
    CONNECTION(VCC, "K2", 12)
    CONNECTION(HSYNC, "K2", 11)
    CONNECTION("E1", 7, "K2", 13)

    CONNECTION(VCC, "H1", 7)
    CONNECTION(VCC, "H1", 10)
    CONNECTION(CLOCK_n, "H1", 2)
    CONNECTION(PLANE_RESET_n, "H1", 1)
    CONNECTION(VCC, "H1", 3)
    CONNECTION(VRESET_n, "H1", 4)
    CONNECTION("H3", 3, "H1", 5)
    CONNECTION("F3", 1, "H1", 6)
    CONNECTION("H3", 6, "H1", 9)

    CONNECTION("H1", 15, "F1", 7)
    CONNECTION(VCC, "F1", 10)
    CONNECTION(CLOCK_n, "F1", 2)
    CONNECTION(PLANE_RESET_n, "F1", 1)
    CONNECTION(VCC, "F1", 3)
    CONNECTION(VCC, "F1", 4)
    CONNECTION(GND, "F1", 5)
    CONNECTION(GND, "F1", 6)
    CONNECTION("H3", 6, "F1", 9)

    CONNECTION(VRESET, "H3", 1)
    CONNECTION("F2", 3, "H3", 2)

    CONNECTION(VRESET_n, "F3", 2)
    CONNECTION("F2", 2, "F3", 3)

    CONNECTION(VCC, "F2", 1)
    CONNECTION(RANDOM_CLOCK, "F2", 12)
    CONNECTION(VCC, "F2", 4)
    CONNECTION(VCC, "F2", 13)

    CONNECTION("RANDOM_CLOCK", 1, "D3", 10)
    CONNECTION("RANDOM_CLOCK", 1, "D3", 12)
    CONNECTION("RANDOM_CLOCK", 1, "D3", 13)
    CONNECTION(PLANE_RESET, "D3", 9)

    CONNECTION(VCC, "F2", 8)
    CONNECTION("F1", 15, "F2", 9)
    CONNECTION(VCC, "F2", 11)
    CONNECTION(PLANE_RESET_n, "F2", 10)

    CONNECTION("F1", 15, "H2", 2)
    CONNECTION("F2", 5, "H2", 1)

    CONNECTION("H1", 15, "H3", 4)
    CONNECTION("H2", 3, "H3", 5)




    // Plane Vertical Position
    CONNECTION(V64, "J2", 12)
    CONNECTION(V128, "J2", 13)

    CONNECTION("J2", 11, "H2", 13)
    CONNECTION(V8_n, "H2", 12)

    CONNECTION(VCC, "E3", 7)
    CONNECTION("J2", 11, "E3", 10)
    CONNECTION(V8_n, "E3", 2)
    CONNECTION(START_n, "E3", 1)
    CONNECTION("E2", 2, "E3", 3)
    CONNECTION(GND, "E3", 4)
    CONNECTION(GND, "E3", 5)
    CONNECTION(VCC, "E3", 6)
    CONNECTION("E2", 10, "E3", 9)

    CONNECTION("E3", 15, "E2", 11)

    CONNECTION(RANDOM_CLOCK, "E2", 1)

    CONNECTION("E3", 11, "D3", 5)
    CONNECTION("E3", 12, "D3", 4)
    CONNECTION("E3", 13, "D3", 2)
    CONNECTION("H2", 11, "D3", 1)

    CONNECTION("E3", 14, "E2", 13)

    CONNECTION(HIT_DETECT, "C2", 9)
    CONNECTION("E2", 12, "C2", 10)

    CONNECTION(VCC, "D1", 4)
    CONNECTION("D1", 6, "D1", 2)
    CONNECTION(RANDOM_CLOCK, "D1", 3)
    CONNECTION("C2", 8, "D1", 1)

    CONNECTION("E3", 14, "C2", 13)
    CONNECTION(HIT_DETECT, "C2", 12)

    CONNECTION(VCC, "D1", 10)
    CONNECTION(VCC, "D1", 12)
    CONNECTION(RANDOM_CLOCK, "D1", 11)
    CONNECTION("C2", 11, "D1", 13)

    CONNECTION("D1", 6, "D2", 5)
    CONNECTION("E3", 14, "D2", 4)
    CONNECTION("D3", 6, "D2", 3)

    CONNECTION("D1", 6, "C2", 4)
    CONNECTION("D1", 8, "C2", 5)

    CONNECTION("D1", 8, "D2", 9)
    CONNECTION("D3", 6, "D2", 11)
    CONNECTION("E2", 12, "D2", 10)

    CONNECTION("D2", 6, "F3", 8)
    CONNECTION("D2", 8, "F3", 9)

    CONNECTION("F3", 10, "E2", 3)

    CONNECTION("H2", 3, "H2", 10)
    CONNECTION("E2", 4, "H2", 9)




    // Plane Graphics
    CONNECTION(DIR_SELECT_n, "J1", 10)
    CONNECTION(PH4, "J1", 9)

    CONNECTION(DIR_SELECT_n, "J1", 2)
    CONNECTION(PH3, "J1", 1)

    CONNECTION(DIR_SELECT_n, "J1", 4)
    CONNECTION(PH2, "J1", 5)

    CONNECTION(DIR_SELECT_n, "J1", 12)
    CONNECTION(PH1, "J1", 13)

    CONNECTION(GND, "DSW2", 1)
    CONNECTION(VCC, "DSW2", 2)

    CONNECTION("DSW2", 3, "K1", 14) // Tied low on PCB
    CONNECTION("J1", 8, "K1", 13)
    CONNECTION("J1", 3, "K1", 12)
    CONNECTION("J1", 6, "K1", 11)
    CONNECTION("J1", 11, "K1", 10)
    CONNECTION(GND, "K1", 15)

    CONNECTION(PLANE_RESET_n, "H3", 10)
    CONNECTION(PLANE_EN, "H3", 9)

    CONNECTION("K1", 9, "L1", 9)
    CONNECTION("K1", 7, "L1", 7)
    CONNECTION("K1", 6, "L1", 6)
    CONNECTION("K1", 5, "L1", 5)
    CONNECTION("K1", 4, "L1", 4)
    CONNECTION("K1", 3, "L1", 3)
    CONNECTION("K1", 2, "L1", 2)
    CONNECTION("K1", 1, "L1", 1)
    CONNECTION(V1, "L1", 11)
    CONNECTION(V2, "L1", 12)
    CONNECTION(V4, "L1", 13)
    CONNECTION("H3", 8, "L1", 10)
    



    // Video Summing
    CONNECTION(RIGHT_MISSILE_n, "B8", 10)
    CONNECTION(LEFT_MISSILE_n, "B8", 9)
    
    CONNECTION("VIDEO", 1, "B3", 5)
    CONNECTION("VIDEO", 2, "B8", 8)
    CONNECTION("VIDEO", 3, "L1", 15)
    CONNECTION("VIDEO", 4, "E1", 10)

    CONNECTION("VIDEO", Video::HBLANK_PIN, HSYNC)
    CONNECTION("VIDEO", Video::VBLANK_PIN, VSYNC)


CIRCUIT_LAYOUT_END

