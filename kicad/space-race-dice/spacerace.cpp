#include "../circuit_desc.h"

#define DEBUG
#undef DEBUG

#define USE_CLK_GATES

// TODO: Fix start/coin to reset game time properly?

#ifdef DEBUG
static VcdLogDesc vcd_log_desc
(
    "output_space.vcd",
    1, "a",
    2, "b",
    3, "c",
    4, "d",
    5, "e",
    6, "f",
    7, "g",
    8, "h",
    9, "i",
    10, "j",
    11, "k",
    12, "l",
    13, "m",
    14, "n",
    15, "o"
);
#endif

static Mono555Desc a3_555_desc(K_OHM(6.8) + K_OHM(6.8), U_FARAD(4.7));
static Mono555Desc a6_555_desc(K_OHM(330.0), U_FARAD(4.7));
static Mono555Desc a9_555_desc(K_OHM(100.0), U_FARAD(0.1));
static Mono555Desc b6_555_desc(K_OHM(330.0), U_FARAD(4.7));
static Mono555Desc c9_555_desc(K_OHM(1000.0), U_FARAD(100.0));
static PWM555Desc d9_555_desc(K_OHM(151.0), U_FARAD(0.1));

static Mono9602Desc l4_desc(K_OHM(10.0), P_FARAD(100.0), K_OHM(10.0), P_FARAD(100.0));

static DipswitchDesc dipswitch1_desc("coinage", "dice_dipswitch_1", "Coinage", 0, "1 Coin / 1 Credit", "1 Coin / 2 Credits");
static PotentimeterMono555Desc pot1_desc("playtime", "Play Time", K_OHM(970.0), K_OHM(470.0), K_OHM(1470.0), c9_555_desc);

static SeriesRCDesc coin_cap_desc(K_OHM(1.0), U_FARAD(0.1)); // Not shown, but needed to make coin work? TODO: Investigate

RCFilterDesc c25_filter_desc(K_OHM(470.0), K_OHM(470.0), U_FARAD(0.1));
RCFilterDesc c19_filter_desc(K_OHM(470.0), K_OHM(470.0), U_FARAD(0.1));
RCFilterDesc c32_filter_desc(K_OHM(25.2), K_OHM(25.2), U_FARAD(4.7)); // TODO: Include C33? Fix resistance values

NE566Desc a4_566_desc(K_OHM(6.8), U_FARAD(0.1)); // TODO: Extra capacitance from C42?
NE566Desc b4_566_desc(K_OHM(10.0), U_FARAD(0.1));
NE566Desc c4_566_desc(K_OHM(10.0), U_FARAD(0.1));

MixerDesc mixer_desc({K_OHM(10.0), K_OHM(10.0), K_OHM(4.7)}, 0.0, U_FARAD(0.1));

static DIODE_LAYOUT rocket_gfx =
{
	{ 0, 0, 0, 0, 0, 0, 0, 1 },
	{ 0, 0, 0, 0, 0, 0, 1, 0 },
	{ 0, 0, 0, 0, 0, 1, 0, 0 },
	{ 0, 0, 0, 0, 1, 0, 0, 0 },
	{ 0, 0, 0, 1, 1, 1, 0, 0 },
	{ 0, 0, 0, 0, 0, 1, 0, 0 },
	{ 0, 0, 0, 0, 0, 1, 0, 0 },
	{ 0, 0, 0, 0, 0, 1, 0, 0 },
	{ 0, 0, 0, 0, 0, 1, 0, 0 },
	{ 0, 0, 0, 0, 1, 0, 0, 0 },
	{ 0, 0, 0, 1, 0, 0, 0, 0 },
	{ 0, 0, 1, 0, 0, 0, 0, 0 },
	{ 0, 1, 0, 0, 0, 0, 0, 0 },
	{ 1, 1, 1, 1, 0, 1, 1, 1 },
	{ 0, 0, 0, 1, 0, 1, 0, 0 },
	{ 0, 0, 0, 1, 1, 1, 0, 0 }
};

static AUDIO_DESC( spacerace )
    AUDIO_GAIN(50.0)
    AUDIO_SPEAKER_CONFIG(MONO)
AUDIO_DESC_END

static INPUT_DESC( spacerace )
    INPUT_INFO(JOYSTICK1_INPUT, {{ Joystick::UP, Joystick::DOWN }}, "Move Left Rocket")
    INPUT_INFO(JOYSTICK2_INPUT, {{ Joystick::UP, Joystick::DOWN }}, "Move Right Rocket")

    INPUT_INFO(COIN_INPUT, {{ 1 }}, "Insert Coin")
    INPUT_INFO(START_INPUT, {{ 1 }}, "Start Game")
INPUT_DESC_END

static VIDEO_DESC ( spacerace )
    VIDEO_RETRO_V_SIZE(246)
VIDEO_DESC_END

// Transistor used to enable/disable 566 outputs
// TODO: Figure out how to simulate more accurately
static CHIP_DESC( SPACERACE_PNP )
{
    CUSTOM_CHIP_START([](Chip* chip, int mask) {
        double sw = chip->analog_input(1);
        if(sw > 2.0)
            chip->analog_output = 0.0;
        else
            chip->analog_output = chip->analog_input(0) + 2.30;
    })
    INPUT_PINS( 1, 2 )
    OUTPUT_PIN( i1 ),
    
    CHIP_DESC_END
};

CIRCUIT_LAYOUT( spacerace )
	/**************************************************************************
		Chips
	**************************************************************************/
	CHIP("CLOCK", CLOCK_14_318_MHZ)
    
    CHIP("DIODES", DIODE_MATRIX, &rocket_gfx)

	CHIP("A1", 7402)
	CHIP("A2", 9316)
    CHIP("A3", 555_Mono, &a3_555_desc)
    CHIP("A4", 566, &a4_566_desc)
    CHIP("A6", 555_Mono, &a6_555_desc)
	CHIP("A7", 7400)
    CHIP("A8", 7474)
    CHIP("A9", 555_Mono, &a9_555_desc)

	CHIP("B1", 7400)
	CHIP("B2", 9316)
    CHIP("B3", 7474)
    CHIP("B4", 566, &b4_566_desc)
    CHIP("B6", 555_Mono, &b6_555_desc)
	CHIP("B7", 7402)
	CHIP("B8", 7474)
	CHIP("B9", 7404)

	CHIP("C1", 7427)
	CHIP("C2", 74107)
    CHIP("C3", 7493)
    CHIP("C4", 566, &c4_566_desc)
	CHIP("C6", 7420)
	CHIP("C7", 7474)
	CHIP("C8", 7410)
    CHIP("C9", 555_Mono, &c9_555_desc)

	CHIP("D1", 7493)
	CHIP("D2", 9316)
	CHIP("D3", 7400)
	CHIP("D4", 7400)
	CHIP("D5", 7404)
	CHIP("D6", 7400)
	CHIP("D7", 7404)
    CHIP("D8", 7400)
    CHIP("D9", 555_PWM, &d9_555_desc)

	CHIP("E1", 7474)
	CHIP("E2", 9316)
	CHIP("E3", 7404)
	CHIP("E4", 7402)
	CHIP("E5", 9316)
	CHIP("E6", 7410)
    CHIP("E7", 7427)
    CHIP("E8", 7410)
	CHIP("E9", 7404)

    CHIP("F2", 7400)
	CHIP("F3", 7402)
	CHIP("F4", 74107)
	CHIP("F5", 9316)
	CHIP("F6", 7493)
	CHIP("F7", 7474)
    CHIP("F8", 7410)
    CHIP("F9", 7430)

	CHIP("H1", 7410)
	CHIP("H2", 7474)
	CHIP("H3", 9316)
	CHIP("H4", 9322)
	CHIP("H6", 7493)
	CHIP("H7", 74107)
    CHIP("H8", 7410)
	CHIP("H9", 7490)

	CHIP("J2", 7400)
	CHIP("J3", 9316)
	CHIP("J6", 7427)
	CHIP("J7", 7430)
    CHIP("J8", 7448)
    CHIP("J9", 7490)

	CHIP("K2", 7474)
	CHIP("K3", 9316)
	CHIP("K4", 9311)
	CHIP("K6", 7410)
	CHIP("K7", 7493)
    CHIP("K8", 74153)
    CHIP("K9", 7490) // Woof

	CHIP("L2", 7400)
	CHIP("L3", 9316)
	CHIP("L4", 9602, &l4_desc)
	CHIP("L5", 9312)
	CHIP("L6", 7486)
	CHIP("L7", 7493)
    CHIP("L8", 74153)
    CHIP("L9", 7490)

    CHIP("LATCH", LATCH)

    CHIP("COIN", COIN_INPUT)
    CHIP("START", START_INPUT)

    CHIP("STICK1", JOYSTICK1_INPUT)
    CHIP("STICK2", JOYSTICK2_INPUT)

    CHIP("DSW1", DIPSWITCH, &dipswitch1_desc)
    CHIP("POT1", POT_555_MONO, &pot1_desc)
    POTENTIOMETER_CONNECTION("POT1", "C9") 

    CHIP("CAP?", SERIES_RC, &coin_cap_desc)

    CHIP("C25", RC_FILTER, &c25_filter_desc)
    CHIP("C19", RC_FILTER, &c19_filter_desc)
    CHIP("C32", RC_FILTER, &c32_filter_desc)

    CHIP("Q3", SPACERACE_PNP)
    CHIP("Q6", SPACERACE_PNP)
    CHIP("Q9", SPACERACE_PNP)

    CHIP("MIXER", MIXER, &mixer_desc)

    AUDIO(spacerace)
    VIDEO(spacerace)
    INPUT(spacerace)

#ifdef DEBUG
	CHIP("LOG1", VCD_LOG, &vcd_log_desc)
#endif

    // Speed hack
    OPTIMIZATION_HINT("F5", 64, 64)
    OPTIMIZATION_HINT("E5", 64, 64)

#ifdef USE_CLK_GATES
    CHIP("CLK_GATE1", CLK_GATE)
    CHIP("CLK_GATE2", CLK_GATE)
    CHIP("CLK_GATE3", CLK_GATE)
    CHIP("CLK_GATE4", CLK_GATE)
#endif

	/**************************************************************************
		Defines
	**************************************************************************/
	#define CLK "C7", 8
    #define CLK_n "C7", 9

	#define H1 "L7", 12
	#define H2 "L7", 9
	#define H4 "L7", 8
	#define H8 "L7", 11

	#define H16 "K7", 12
	#define H32 "K7", 9
	#define H64 "K7", 8
	#define H128 "K7", 11

	#define H256 "H7", 5
	#define H256_n "H7", 6

	#define HRESET "F7", 6
	#define HRESET_n "F7", 5

	#define V1 "F6", 12
	#define V2 "F6", 9
	#define V4 "F6", 8
	#define V8 "F6", 11

	#define V16 "H6", 12
	#define V32 "H6", 9
	#define V64 "H6", 8
	#define V128 "H6", 11

	#define V256 "H7", 3
	#define V256_n "H7", 2

	#define VRESET "F7", 8
	#define VRESET_n "F7", 9

	#define VBLANK "B7", 1
	#define VBLANK_n "B7", 4
	#define VSYNC_n "C8", 12

	#define HBLANK "A7", 11
	#define HBLANK_n "A7", 8
	#define HSYNC "B8", 5
	#define HSYNC_n "B8", 6

    #define RESET_n "COIN", 1
    #define GAME_ON "C9", 3
    #define CRASH1_n "D5", 8
    #define CRASH2_n "D5", 10

	#define STAR_BLANK "E3", 12

	#define ROCKET_WINDOW "D6", 8

	#define RRESET "F3", 4

	#define QA1 "J3", 14
	#define QB1 "J3", 13
	#define QC1 "J3", 12
	#define QD1 "J3", 11

	#define SCORE1 "H2", 8
	#define STOP1 "D3", 11

	#define QA2 "L3", 14
	#define QB2 "L3", 13
	#define QC2 "L3", 12
	#define QD2 "L3", 11

	#define SCORE2 "K2", 8

	#define STARS_n "L4", 9
	#define ROCKETS_n "C7", 6


	/**************************************************************************
		Layout
	**************************************************************************/
	// HRESET Circuit
	CONNECTION("CLOCK", 1, "C7", 11)
    CONNECTION("C7", 8, "C7", 12)
    CONNECTION(VCC, "C7", 10)
    CONNECTION(VCC, "C7", 13)

	CONNECTION(CLK, "L7", 14)
	CONNECTION("L7", 12, "L7", 1)
	CONNECTION("F7", 6, "L7", 2)
	CONNECTION("F7", 6, "L7", 3)

	CONNECTION("L7", 11, "K7", 14)
	CONNECTION("K7", 12, "K7", 1)
	CONNECTION("F7", 6, "K7", 2)
	CONNECTION("F7", 6, "K7", 3)

	CONNECTION("K7", 11, "H7", 9)
	CONNECTION(VCC, "H7", 8)
	CONNECTION(VCC, "H7", 11)
	CONNECTION("F7", 5, "H7", 10)

	CONNECTION(VCC, "J7", 1)
	CONNECTION(VCC, "J7", 2)
	CONNECTION(VCC, "J7", 12)
	CONNECTION("H7", 5, "J7", 11)
	CONNECTION("K7", 11, "J7", 4)
	CONNECTION("K7", 8, "J7", 6)
	CONNECTION("L7", 8, "J7", 5)
	CONNECTION("L7", 9, "J7", 3)

	CONNECTION("J7", 8, "F7", 2)
	CONNECTION(VCC, "F7", 4)
	CONNECTION(RESET_n, "F7", 1)
	CONNECTION(CLK, "F7", 3)



	// VRESET Circuit
	CONNECTION("F7", 6, "F6", 14)
	CONNECTION("F6", 12, "F6", 1)
	CONNECTION("F7", 8, "F6", 2)
	CONNECTION("F7", 8, "F6", 3)

	CONNECTION("F6", 11, "H6", 14)
	CONNECTION("H6", 12, "H6", 1)
	CONNECTION("F7", 8, "H6", 2)
	CONNECTION("F7", 8, "H6", 3)

	CONNECTION("H6", 11, "H7", 12)
	CONNECTION(VCC, "H7", 1)
	CONNECTION(VCC, "H7", 4)
	CONNECTION("F7", 9, "H7", 13)

	CONNECTION("H7", 3, "E6", 3)
	CONNECTION("F6", 8, "E6", 4)
	CONNECTION("F6", 12, "E6", 5)

	CONNECTION("E6", 6, "F7", 12)
	CONNECTION(VCC, "F7", 10)
	CONNECTION(RESET_n, "F7", 13)
	CONNECTION("F7", 6, "F7", 11)



	// V/H BLANK Circuits
	CONNECTION(VRESET, "B7", 6)
	CONNECTION("B7", 1, "B7", 5)

	CONNECTION(V16, "B7", 2)
	CONNECTION("B7", 4, "B7", 3)

	CONNECTION(V8, "D7", 13)

	CONNECTION("B7", 1, "C8", 2)
	CONNECTION(V4, "C8", 13)
	CONNECTION("D7", 12, "C8", 1)

	CONNECTION(HRESET_n, "A7", 13)
	CONNECTION("A7", 8, "A7", 12)

	CONNECTION(H16, "A7", 5)
	CONNECTION(H64, "A7", 4)

	CONNECTION("A7", 11, "A7", 10)
	CONNECTION("A7", 6, "A7", 9)

	CONNECTION(H64, "D7", 11)

	CONNECTION(H32, "A7", 1)
	CONNECTION("D7", 10, "A7", 2)

	CONNECTION("A7", 8, "B7", 12)
	CONNECTION(H64, "B7", 11)

	CONNECTION(VCC, "B8", 4)
	CONNECTION("A7", 3, "B8", 2)
	CONNECTION("B7", 13, "B8", 1)
	CONNECTION(H16, "B8", 3)


	// R Reset Circuit
	CONNECTION(V32, "K6", 4)
	CONNECTION(V64, "K6", 5)
	CONNECTION(V128, "K6", 3)

	CONNECTION("K6", 6, "E3", 13)

	CONNECTION("K6", 6, "D6", 5)
	CONNECTION("D6", 3, "D6", 4)

	CONNECTION("D6", 6, "D6", 2)
	CONNECTION(VRESET_n, "D6", 1) // Schematic says vreset???

	CONNECTION("D6", 6, "E6", 9)
	CONNECTION(V16, "E6", 10)
	CONNECTION(V8, "E6", 11)

	CONNECTION(VCC, "E1", 4)
	CONNECTION("E6", 8, "E1", 2)
	CONNECTION(HSYNC, "E1", 3)
	CONNECTION(VCC, "E1", 1)

	CONNECTION("E6", 8, "F3", 5)
	CONNECTION("E1", 6, "F3", 6)


	// Rocket 1 Circuit
	CONNECTION(STOP1, "F3", 8)
	CONNECTION("STICK1", Joystick::DOWN, "F3", 9)

	CONNECTION("F3", 10, "E3", 5)

	CONNECTION("STICK1", Joystick::UP, "J2", 1)
	CONNECTION("E3", 6, "J2", 2)

	CONNECTION(CRASH1_n, "J2", 5)
	CONNECTION(GAME_ON, "J2", 4)

	CONNECTION("J2", 6, "J2", 12)
	CONNECTION(RRESET, "J2", 13)

	CONNECTION(VCC, "J3", 7)
	CONNECTION(VBLANK_n, "J3", 10)
	CONNECTION("J2", 11, "J3", 1)
	CONNECTION("J2", 8, "J3", 9)
	CONNECTION("J2", 3, "J3", 3)
	CONNECTION("E3", 6, "J3", 4)
	CONNECTION(GND, "J3", 5)
	CONNECTION(VCC, "J3", 6)
	CONNECTION(HSYNC_n, "J3", 2)

	CONNECTION("J3", 15, "H3", 7)
	CONNECTION(VCC, "H3", 10)
	CONNECTION("J2", 11, "H3", 1)
	CONNECTION("J2", 8, "H3", 9)
	CONNECTION(GND, "H3", 3)
	CONNECTION(GND, "H3", 4)
	CONNECTION(GND, "H3", 5)
	CONNECTION(GND, "H3", 6)
	CONNECTION(HSYNC_n, "H3", 2)

	CONNECTION("H3", 15, "J2", 9)
	CONNECTION("J3", 15, "J2", 10)

	CONNECTION(VCC, "H2", 10)
	CONNECTION("H3", 15, "H2", 12)
	CONNECTION(VBLANK, "H2", 11)
	CONNECTION(VCC, "H2", 13)

	CONNECTION(VCC, "H2", 4)
	CONNECTION("H3", 15, "H2", 2)
	CONNECTION("E1", 6, "H2", 3)
	CONNECTION(VCC, "H2", 1)

	CONNECTION("H2", 8, "D3", 12)
	CONNECTION("H2", 6, "D3", 13)



	// Rocket 2 Circuit
	CONNECTION("B1", 8, "F3", 11)
	CONNECTION("STICK2", Joystick::DOWN, "F3", 12)

	CONNECTION("F3", 13, "E3", 3)

	CONNECTION("STICK2", Joystick::UP, "L2", 1)
	CONNECTION("E3", 4, "L2", 2)

	CONNECTION(CRASH2_n, "L2", 5)
	CONNECTION(GAME_ON, "L2", 4)

	CONNECTION("L2", 6, "L2", 12)
	CONNECTION(RRESET, "L2", 13)

	CONNECTION(VCC, "L3", 7)
	CONNECTION(VBLANK_n, "L3", 10)
	CONNECTION("L2", 11, "L3", 1)
	CONNECTION("L2", 8, "L3", 9)
	CONNECTION("L2", 3, "L3", 3)
	CONNECTION("E3", 4, "L3", 4)
	CONNECTION(GND, "L3", 5)
	CONNECTION(VCC, "L3", 6)
	CONNECTION(HSYNC_n, "L3", 2)

	CONNECTION("L3", 15, "K3", 7)
	CONNECTION(VCC, "K3", 10)
	CONNECTION("L2", 11, "K3", 1)
	CONNECTION("L2", 8, "K3", 9)
	CONNECTION(GND, "K3", 3)
	CONNECTION(GND, "K3", 4)
	CONNECTION(GND, "K3", 5)
	CONNECTION(GND, "K3", 6)
	CONNECTION(HSYNC_n, "K3", 2)

	CONNECTION("L3", 15, "L2", 9)
	CONNECTION("K3", 15, "L2", 10)

	CONNECTION(VCC, "K2", 10)
	CONNECTION("K3", 15, "K2", 12)
	CONNECTION(VBLANK_n, "K2", 11)
	CONNECTION(VCC, "K2", 13)

	CONNECTION(VCC, "K2", 4)
	CONNECTION("K3", 15, "K2", 2)
	CONNECTION("E1", 6, "K2", 3)
	CONNECTION(VCC, "K2", 1)

	CONNECTION("K2", 8, "B1", 9)
	CONNECTION("K2", 6, "B1", 10)



	// Rocket Window Circuit
    CONNECTION(H256_n, "K6", 9)
	CONNECTION(H128, "K6", 10)
	CONNECTION(H64, "K6", 11)

	CONNECTION(H32, "J6", 1)
	CONNECTION(H16, "J6", 2)
	CONNECTION("K6", 8, "J6", 13)

	CONNECTION(VRESET_n, "C6", 13)
	CONNECTION(CRASH1_n, "C6", 10)
	CONNECTION("J6", 12, "C6", 9)
	CONNECTION("H3", 15, "C6", 12)

	CONNECTION(H32, "K6", 1)
	CONNECTION(H16, "K6", 2)
	CONNECTION(H256, "K6", 13)

	CONNECTION(H128, "J6", 5)
	CONNECTION(H64, "J6", 4)
	CONNECTION("K6", 12, "J6", 3)

	CONNECTION(VRESET_n, "C6", 1)
	CONNECTION(CRASH2_n, "C6", 4)
	CONNECTION("J6", 6, "C6", 5) // Wrong pin # on schematics again
	CONNECTION("K3", 15, "C6", 2)

	CONNECTION("C6", 6, "D6", 9)
	CONNECTION("C6", 8, "D6", 10)



	// Rocket GFX Circuit
	CONNECTION(QA1, "H4", 2)
	CONNECTION(QB1, "H4", 5)
	CONNECTION(QC1, "H4", 14)
	CONNECTION(QD1, "H4", 11)
	CONNECTION(QA2, "H4", 3)
	CONNECTION(QB2, "H4", 6)
	CONNECTION(QC2, "H4", 13)
	CONNECTION(QD2, "H4", 10)
	CONNECTION(GND, "H4", 15)
	CONNECTION(H256, "H4", 1)

	CONNECTION("H4", 4, "K4", 23)
	CONNECTION("H4", 7, "K4", 22)
	CONNECTION("H4", 12, "K4", 21)
	CONNECTION("H4", 9, "K4", 20)
	CONNECTION(GND, "K4", 18)
	CONNECTION(GND, "K4", 19)

	CONNECTION("K4", 1, "DIODES", ROW0)
	CONNECTION("K4", 2, "DIODES", ROW1)
	CONNECTION("K4", 3, "DIODES", ROW2)
	CONNECTION("K4", 4, "DIODES", ROW3)
	CONNECTION("K4", 5, "DIODES", ROW4)
	CONNECTION("K4", 6, "DIODES", ROW5)
	CONNECTION("K4", 7, "DIODES", ROW6)
	CONNECTION("K4", 8, "DIODES", ROW7)
	CONNECTION("K4", 9, "DIODES", ROW8)
	CONNECTION("K4", 10, "DIODES", ROW9)
	CONNECTION("K4", 11, "DIODES", ROW10)
	CONNECTION("K4", 13, "DIODES", ROW11)
	CONNECTION("K4", 14, "DIODES", ROW12)
	CONNECTION("K4", 15, "DIODES", ROW13)
	CONNECTION("K4", 16, "DIODES", ROW14)
	CONNECTION("K4", 17, "DIODES", ROW15)

	CONNECTION(H8, "L6", 5)
	CONNECTION(H1, "L6", 4)

	CONNECTION(H8, "L6", 9)
	CONNECTION(H2, "L6", 10)

	CONNECTION(H8, "L6", 12)
	CONNECTION(H4, "L6", 13)

    CONNECTION("DIODES", COL0, "L5", 1)
	CONNECTION("DIODES", COL1, "L5", 2)
	CONNECTION("DIODES", COL2, "L5", 3)
	CONNECTION("DIODES", COL3, "L5", 4)
	CONNECTION("DIODES", COL4, "L5", 5)
	CONNECTION("DIODES", COL5, "L5", 6)
	CONNECTION("DIODES", COL6, "L5", 7)
	CONNECTION("DIODES", COL7, "L5", 9)
	CONNECTION(GND, "L5", 10)
#ifdef USE_CLK_GATES
	CONNECTION(ROCKET_WINDOW, "CLK_GATE2", 1)
    CONNECTION("L6", 6, "CLK_GATE2", 2)
    CONNECTION("CLK_GATE2", 3, "L5", 11)
    
    CONNECTION(ROCKET_WINDOW, "CLK_GATE3", 1)
    CONNECTION("L6", 8, "CLK_GATE3", 2)
    CONNECTION("CLK_GATE3", 3, "L5", 12)

    CONNECTION(ROCKET_WINDOW, "CLK_GATE4", 1)
    CONNECTION("L6", 11, "CLK_GATE4", 2)
    CONNECTION("CLK_GATE4", 3, "L5", 13)
#else
	CONNECTION("L6", 6, "L5", 11)
    CONNECTION("L6", 8, "L5", 12)
    CONNECTION("L6", 11, "L5", 13)
#endif

    CONNECTION("L5", 14, "C7", 2)
	CONNECTION(VCC, "C7", 4)

#ifdef USE_CLK_GATES
	CONNECTION(ROCKET_WINDOW, "CLK_GATE1", 1)
    CONNECTION(CLK_n, "CLK_GATE1", 2)
    CONNECTION("CLK_GATE1", 3, "C7", 3)
#else
    CONNECTION(CLK_n, "C7", 3)
#endif
    CONNECTION(ROCKET_WINDOW, "C7", 1)



	// Stars Circuit
    CONNECTION(VCC, "E2", 10)
	CONNECTION(VCC, "E2", 7)
	CONNECTION("B1", 3, "E2", 9)
	CONNECTION(VRESET_n, "E2", 3)
	CONNECTION(GND, "E2", 4)
	CONNECTION(GND, "E2", 5)
	CONNECTION(VCC, "E2", 6)
	CONNECTION(CLK, "E2", 2)
	CONNECTION(RESET_n, "E2", 1)

	CONNECTION("E2", 15, "D2", 10)
	CONNECTION(VCC, "D2", 7)
	CONNECTION("B1", 3, "D2", 9)
	CONNECTION(VCC, "D2", 3)
	CONNECTION(VCC, "D2", 4)
	CONNECTION(GND, "D2", 5)
	CONNECTION(GND, "D2", 6)
	CONNECTION(CLK, "D2", 2)
	CONNECTION(RESET_n, "D2", 1)

	CONNECTION(VCC, "C2", 1)
	CONNECTION("D2", 15, "C2", 12)
	CONNECTION(VCC, "C2", 4)
	CONNECTION(RESET_n, "C2", 13)

	CONNECTION("C2", 3, "B1", 2)
	CONNECTION("D2", 15, "B1", 1)

	CONNECTION(VCC, "A2", 10)
	CONNECTION(VCC, "A2", 7)
	CONNECTION("B1", 6, "A2", 9)
	CONNECTION(VRESET_n, "A2", 3)
	CONNECTION(VRESET, "A2", 4)
	CONNECTION(GND, "A2", 5)
	CONNECTION(VCC, "A2", 6)
	CONNECTION(CLK, "A2", 2)
	CONNECTION(VCC, "A2", 1)

	CONNECTION("A2", 15, "B2", 10)
	CONNECTION(VCC, "B2", 7)
	CONNECTION("B1", 6, "B2", 9)
	CONNECTION(VCC, "B2", 3)
	CONNECTION(VCC, "B2", 4)
	CONNECTION(GND, "B2", 5)
	CONNECTION(GND, "B2", 6)
	CONNECTION(CLK, "B2", 2)
	CONNECTION(VCC, "B2", 1)

	CONNECTION(VCC, "C2", 8)
	CONNECTION("B2", 15, "C2", 9)
	CONNECTION(VCC, "C2", 11)
	CONNECTION(VCC, "C2", 10)

	CONNECTION("C2", 5, "B1", 4)
	CONNECTION("B2", 15, "B1", 5)

	CONNECTION(HRESET_n, "A1", 8)
	CONNECTION(HRESET_n, "A1", 9)

	CONNECTION(VBLANK_n, "B1", 13)
	CONNECTION("E1", 8, "B1", 12)

	CONNECTION("A1", 10, "D1", 14)
	CONNECTION("D1", 12, "D1", 1)
	CONNECTION("B1", 11, "D1", 2)
	CONNECTION("B1", 11, "D1", 3)

	CONNECTION("D1", 11, "E1", 12)
	CONNECTION(VCC, "E1", 10)
	CONNECTION(VCC, "E1", 13)
	CONNECTION("A1", 10, "E1", 11)

	CONNECTION("D1", 8, "E3", 11)

	CONNECTION("E3", 10, "C1", 4)
	CONNECTION("D1", 9, "C1", 5)
	CONNECTION("D1", 12, "C1", 3)

	CONNECTION("C1", 6, "E3", 9) // schematic says e2...

	CONNECTION("E3", 8, "F4", 1)
	CONNECTION("A1", 10, "F4", 12)
	CONNECTION("C1", 6, "F4", 4)
	CONNECTION(VCC, "F4", 13) // not shown on schematics

	CONNECTION("B1", 3, "C1", 13)
	CONNECTION("E1", 8, "C1", 2)
	CONNECTION("A1", 10, "C1", 1)

	CONNECTION("A1", 10, "C1", 11)
	CONNECTION("F4", 3, "C1", 10)
	CONNECTION("B1", 6, "C1", 9)

	CONNECTION("C1", 12, "A1", 5)
	CONNECTION("C1", 8, "A1", 6)



	CONNECTION(VCC, "F5", 7)
	CONNECTION(VCC, "F5", 10)
	CONNECTION("A1", 4, "F5", 9)
	CONNECTION(GND, "F5", 3)
	CONNECTION(V128, "F5", 4)
	CONNECTION(V64, "F5", 5)
	CONNECTION(V32, "F5", 6)
	CONNECTION("H1", 8, "F5", 2)
	CONNECTION("D6", 3, "F5", 1)

	CONNECTION(VCC, "E5", 7)
	CONNECTION("F5", 15, "E5", 10)
	CONNECTION("A1", 4, "E5", 9)
	CONNECTION(V16, "E5", 3)
	CONNECTION(V8, "E5", 4)
	CONNECTION(V4, "E5", 5)
	CONNECTION(V2, "E5", 6)
	CONNECTION("H1", 8, "E5", 2)
	CONNECTION("D6", 3, "E5", 1)

	CONNECTION("A1", 4, "D5", 5)

	CONNECTION("D5", 6, "D4", 2)
	CONNECTION(V1, "D4", 1)

	CONNECTION("D5", 6, "D4", 5)
	CONNECTION("D4", 3, "D4", 4)

	CONNECTION("E5", 15, "F3", 2) //not shown???
	CONNECTION("E5", 15, "F3", 3)

	CONNECTION("E5", 15, "D4", 9)
	CONNECTION("F4", 5, "D4", 10)

	CONNECTION("F4", 5, "H1", 2)
	CONNECTION("E5", 15, "H1", 1)
	CONNECTION("A1", 4, "H1", 13)

	CONNECTION(CLK, "E4", 11)
	CONNECTION(CLK, "E4", 12)

	CONNECTION("E4", 13, "H1", 9)
	CONNECTION("E4", 13, "H1", 10)
    CONNECTION("H1", 12, "H1", 11)

    CONNECTION("H1", 8, "E4", 5)
	CONNECTION("A1", 4, "E4", 6)

	CONNECTION("F3", 1, "E4", 2)
	CONNECTION("E4", 4, "E4", 3)

	CONNECTION("D4", 6, "F4", 8)
	CONNECTION("E4", 1, "F4", 9)
	CONNECTION("D4", 3, "F4", 11)
	CONNECTION("D6", 3, "F4", 10)

	CONNECTION("D4", 8, "L4", 11)
	CONNECTION(GND, "L4", 12)
	CONNECTION(VCC, "L4", 13) //not shown on schematics


    // Video Summing / Collision Detection
    CONNECTION(ROCKETS_n, "A1", 12)
    CONNECTION(STARS_n, "A1", 11)

    CONNECTION(ROCKETS_n, "D3", 1)
    CONNECTION(STARS_n, "D3", 2)

    CONNECTION(H256_n, "D3", 9) // Schematic says 256H
    CONNECTION("A1", 13, "D3", 10)

    CONNECTION("A1", 13, "D3", 4)
    CONNECTION(H256, "D3", 5)

    CONNECTION("D3", 8, "A6", 2)
    CONNECTION(VCC, "A6", 4)
    CONNECTION("A6", 3, "D5", 9) // Schematic says E5

    CONNECTION("D3", 6, "B6", 2)
    CONNECTION(VCC, "B6", 4)
    CONNECTION("B6", 3, "D5", 11)




	// Credit / Start Circuit //
    CONNECTION("COIN", 1, "B9", 13)

    // Not shown, but needed to make coin work? TODO: Investigate
    CONNECTION("COIN", 1, "CAP?", 1)
    CONNECTION(VCC, "CAP?", 2)

    //CONNECTION("COIN", 1, "A9", 2)
    CONNECTION("CAP?", 3, "A9", 2)
    CONNECTION(VCC, "A9", 4)    
    CONNECTION("A9", 3, "B9", 9)

    CONNECTION(VCC, "B8", 10)
    CONNECTION("B9", 8, "B8", 11)
    CONNECTION("B9", 12, "B8", 12)
    CONNECTION("B9", 12, "B8", 13)

    CONNECTION(GND, "DSW1", 1)
    CONNECTION(VCC, "DSW1", 2)

    CONNECTION(VCC, "DSW1", 4)
    CONNECTION("B8", 8, "DSW1", 5)

    CONNECTION("DSW1", 3, "A8", 10)
    CONNECTION("B9", 2, "A8", 11)
    CONNECTION(VCC, "A8", 12)
    CONNECTION("DSW1", 6, "A8", 13)

    CONNECTION(VCC, "A8", 4)
    CONNECTION("B9", 2, "A8", 3)
    CONNECTION("A8", 9, "A8", 2)
    CONNECTION("B8", 8, "A8", 1)
    
    CONNECTION("START", 1, "B9", 5)
    
    CONNECTION("B9", 2, "C8", 11)
    CONNECTION("B9", 6, "C8", 10)
    CONNECTION("A8", 6, "C8", 9)

    CONNECTION("LATCH", 3, "C9", 4)
    CONNECTION("C8", 8, "C9", 2)

    CONNECTION("C9", 3, "B9", 1)
    
    CONNECTION("C8", 8, "E9", 3)
    
    CONNECTION("B9", 2, "D8", 12)
    CONNECTION("A8", 5, "D8", 13)

    CONNECTION("D8", 11, "LATCH", 2)
    CONNECTION("B8", 8, "LATCH", 1)



    // Score Counters
    CONNECTION("E9", 4, "H9", 2)
    CONNECTION("E9", 4, "H9", 3)
    CONNECTION(GND, "H9", 6)
    CONNECTION(GND, "H9", 7)
    CONNECTION("H9", 12, "H9", 1)
    CONNECTION("J9", 11, "H9", 14)

    CONNECTION("E9", 4, "J9", 2)
    CONNECTION("E9", 4, "J9", 3)
    CONNECTION(GND, "J9", 6)
    CONNECTION(GND, "J9", 7)
    CONNECTION("J9", 12, "J9", 1)
    CONNECTION(SCORE1, "J9", 14)

    CONNECTION("E9", 4, "K9", 2)
    CONNECTION("E9", 4, "K9", 3)
    CONNECTION(GND, "K9", 6)
    CONNECTION(GND, "K9", 7)
    CONNECTION("K9", 12, "K9", 1)
    CONNECTION("L9", 11, "K9", 14)

    CONNECTION("E9", 4, "L9", 2)
    CONNECTION("E9", 4, "L9", 3)
    CONNECTION(GND, "L9", 6)
    CONNECTION(GND, "L9", 7)
    CONNECTION("L9", 12, "L9", 1)
    CONNECTION(SCORE2, "L9", 14)

    CONNECTION("H9", 12, "L8", 6)
    CONNECTION("H9", 9, "L8", 10)
    CONNECTION("J9", 12, "L8", 5)
    CONNECTION("J9", 9, "L8", 11)
    CONNECTION("K9", 12, "L8", 4)
    CONNECTION("K9", 9, "L8", 12)
    CONNECTION("L9", 12, "L8", 3)
    CONNECTION("L9", 9, "L8", 13)
    CONNECTION(H32, "L8", 14)
    CONNECTION(H64, "L8", 2)
    CONNECTION(GND, "L8", 1)
    CONNECTION(GND, "L8", 15)

    CONNECTION("H9", 8, "K8", 6)
    CONNECTION("H9", 11, "K8", 10)
    CONNECTION("J9", 8, "K8", 5)
    CONNECTION("J9", 11, "K8", 11)
    CONNECTION("K9", 8, "K8", 4)
    CONNECTION("K9", 11, "K8", 12)
    CONNECTION("L9", 8, "K8", 3)
    CONNECTION("L9", 11, "K8", 13)
    CONNECTION(H32, "K8", 14)
    CONNECTION(H64, "K8", 2)
    CONNECTION(GND, "K8", 1)
    CONNECTION(GND, "K8", 15)

    CONNECTION("L8", 7, "J8", 7)
    CONNECTION("L8", 9, "J8", 1)
    CONNECTION("K8", 7, "J8", 2)
    CONNECTION("K8", 9, "J8", 6)
    CONNECTION(VCC, "J8", 3)
    CONNECTION(VCC, "J8", 4)
    CONNECTION(H32, "J8", 5)


    // Score Display
    CONNECTION(H4, "D6", 13)
    CONNECTION(H8, "D6", 12)

    CONNECTION(H16, "D7", 1)

    CONNECTION("D6", 11, "B7", 8)
    CONNECTION("D7", 2, "B7", 9)

    CONNECTION("D7", 2, "E7", 13)
    CONNECTION(V8, "E7", 1)
    CONNECTION(V4, "E7", 2)

    CONNECTION(V4, "E6", 1)
    CONNECTION(V8, "E6", 2)
    CONNECTION(H16, "E6", 13)

    CONNECTION(H8, "E7", 5)
    CONNECTION(H4, "E7", 4)
    CONNECTION("D7", 2, "E7", 3)

    CONNECTION("E6", 12, "D7", 9)

    CONNECTION(H64, "D7", 3)

    CONNECTION(V16, "E9", 5)

    CONNECTION(H256_n, "E7", 11)
    CONNECTION("D7", 4, "E7", 9)
    CONNECTION(H128, "E7", 10)

    CONNECTION(H128, "E8", 10)
    CONNECTION("D7", 4, "E8", 11)
    CONNECTION(H256_n, "E8", 9)

    CONNECTION("J8", 15, "H8", 2)
    CONNECTION("E7", 6, "H8", 13)
    CONNECTION("E9", 6, "H8", 1)

    CONNECTION("J8", 9, "H8", 9)
    CONNECTION(V16, "H8", 11)
    CONNECTION("E7", 6, "H8", 10)

    CONNECTION("J8", 12, "F8", 5)
    CONNECTION("B7", 10, "F8", 4)
    CONNECTION("E9", 6, "F8", 3)

    CONNECTION("J8", 11, "H8", 5)
    CONNECTION("B7", 10, "H8", 3)
    CONNECTION(V16, "H8", 4)

    CONNECTION("J8", 13, "E8", 5)
    CONNECTION("E9", 6, "E8", 4)
    CONNECTION("E7", 12, "E8", 3)

    CONNECTION("J8", 14, "F8", 2)
    CONNECTION("E9", 6, "F8", 1)
    CONNECTION("D7", 8, "F8", 13)

    CONNECTION("J8", 10, "F8", 9)
    CONNECTION(V16, "F8", 10)
    CONNECTION("D7", 8, "F8", 11)

    CONNECTION("E7", 8, "D7", 5)

    CONNECTION("D7", 6, "D8", 5)
    CONNECTION("E8", 8, "D8", 4)

    CONNECTION("H8", 12, "F9", 4)
    CONNECTION("H8", 8, "F9", 3)
    CONNECTION("F8", 6, "F9", 5)
    CONNECTION(VCC, "F9", 1)
    CONNECTION("H8", 6, "F9", 2)
    CONNECTION("E8", 6, "F9", 11)
    CONNECTION("F8", 12, "F9", 12)
    CONNECTION("F8", 8, "F9", 6)

    CONNECTION("E3", 12, "E8", 2)
    CONNECTION("D8", 6, "E8", 13)
    CONNECTION("F9", 8, "E8", 1)

    CONNECTION("C8", 6, "D8", 1)
    CONNECTION("E8", 12, "D8", 2)


    // Fuel
    CONNECTION(V256_n, "D9", 2)
    //CONNECTION(VCC, "D9", 4)
    CONNECTION("C9", 3, "D9", 5)
    
    CONNECTION("D9", 3, "E9", 1)
    
    CONNECTION(GND, "L4", 4)
    CONNECTION(H256_n, "L4", 5)
    CONNECTION(VBLANK_n, "L4", 3)

    CONNECTION("C9", 3, "C8", 3)
    CONNECTION("E9", 2, "C8", 4)
    CONNECTION("L4", 6, "C8", 5)



    // Video
    CONNECTION("VIDEO", 1, "D3", 3)
    CONNECTION("VIDEO", 2, "D8", 3)

    CONNECTION("VIDEO", Video::HBLANK_PIN, HBLANK)
    CONNECTION("VIDEO", Video::VBLANK_PIN, VBLANK)




    // Sound
    CONNECTION(VCC, "B3", 10)
    CONNECTION(VCC, "B3", 12)
    CONNECTION("K3", 15, "B3", 11)
    CONNECTION(VRESET_n, "B3", 13)

    CONNECTION(VCC, "B3", 4)
    CONNECTION(VCC, "B3", 2)
    CONNECTION("H3", 15, "B3", 3)
    CONNECTION(VRESET_n, "B3", 1)

    CONNECTION(VRESET_n, "C3", 14)
    CONNECTION("C3", 12, "C3", 1)
    CONNECTION(GND, "C3", 2)
    CONNECTION(GND, "C3", 3)

    CONNECTION("L2", 6, "E3", 1)

    CONNECTION("E3", 2, "F2", 12)
    CONNECTION("C3", 11, "F2", 13)

    CONNECTION("J2", 6, "D5", 1)

    CONNECTION("D5", 2, "D4", 13)
    CONNECTION("C3", 8, "D4", 12)

    CONNECTION("A1", 13, "A1", 2)
    CONNECTION("A1", 13, "A1", 3)

    CONNECTION(VCC, "A3", 4)
    CONNECTION("A1", 1, "A3", 2)
    
    CONNECTION("A3", 3, "D5", 13)



    // Analog Sound
    CONNECTION("B3", 8, "AUDIO", 1)
    CONNECTION("F2", 11, "AUDIO", 2)

    CONNECTION("AUDIO", i1, "C25", 1)
    CONNECTION("C25", i1, "B4", 5)

    CONNECTION("B4", 4, "Q6", 1)
    CONNECTION("AUDIO", i2, "Q6", 2)


    CONNECTION("B3", 6, "AUDIO", 3)
    CONNECTION("D4", 11, "AUDIO", 4)

    CONNECTION("AUDIO", i3, "C19", 1)
    CONNECTION("C19", i1, "C4", 5)

    CONNECTION("C4", 4, "Q3", 1)
    CONNECTION("AUDIO", i4, "Q3", 2)


    CONNECTION("A3", 3, "AUDIO", 5)
    CONNECTION("D5", 12, "AUDIO", 6)

    CONNECTION("AUDIO", i5, "C32", 1)
    CONNECTION("C32", i1, "A4", 5)

    CONNECTION("A4", 4, "Q9", 1)
    CONNECTION("AUDIO", i6, "Q9", 2)


    CONNECTION("Q6", i1, "MIXER", 1)
    CONNECTION("Q3", i1, "MIXER", 2)
    CONNECTION("Q9", i1, "MIXER", 3)

    CONNECTION("MIXER", i1, "AUDIO", Audio::OUTPUT_MONO)

#ifdef DEBUG
    /*CONNECTION("LOG1", 1, CLK)
    CONNECTION("LOG1", 2, "A2", 15)
    CONNECTION("LOG1", 3, "B2", 15)
    CONNECTION("LOG1", 4, "C2", 5)
    CONNECTION("LOG1", 5, "B1", 6)
    CONNECTION("LOG1", 6, VRESET)
    CONNECTION("LOG1", 7, VRESET_n)
    CONNECTION("LOG1", 8, "A2", 14)
    CONNECTION("LOG1", 9, "A2", 13)
    CONNECTION("LOG1", 10, "A2", 12)
    CONNECTION("LOG1", 11, "A2", 11)*/
    CONNECTION("LOG1", 1, "D8", 11)
    CONNECTION("LOG1", 2, "B8", 8)
    CONNECTION("LOG1", 3, "LATCH", 3)
    CONNECTION("LOG1", 4, "C8", 8)
    CONNECTION("LOG1", 5, "C9", 3)
    CONNECTION("LOG1", 6, VBLANK)
    CONNECTION("LOG1", 7, "B9", 2)
    CONNECTION("LOG1", 8, "A8", 6)
    CONNECTION("LOG1", 9, "A8", 9)
    CONNECTION("LOG1", 10, "B9", 8)
    CONNECTION("LOG1", 11, "B9", 12)
    CONNECTION("LOG1", 12, "A8", 5)
#endif

CIRCUIT_LAYOUT_END

