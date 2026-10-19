#include "../circuit_desc.h"

#define DEBUG
#undef DEBUG

#ifdef DEBUG
static VcdLogDesc vcd_log_desc
(
    "output_basket.vcd",
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

static DIODE_LAYOUT basket_layout =
{
	{ 1, 1, 0, 0, 0, 0, 0, 0 },	
	{ 0, 1, 1, 0, 0, 0, 0, 0 },
	{ 0, 0, 1, 1, 0, 0, 0, 0 },
	{ 0, 0, 0, 1, 1, 0, 0, 0 },
	{ 0, 0, 0, 0, 1, 1, 0, 0 },
	{ 0, 0, 0, 0, 0, 1, 1, 0 },
	{ 0, 0, 0, 0, 0, 0, 1, 1 },
	{ 0, 0, 0, 0, 0, 0, 1, 1 }
};

static DIODE_LAYOUT dummy_layout =
{
	{ 0, 1, 0, 0 },	
	{ 0, 1, 0, 0 },
	{ 0, 1, 1, 0 },
	{ 0, 0, 0, 0 },
	{ 1, 0, 0, 0 },
	{ 1, 1, 0, 0 },
	{ 1, 1, 0, 1 },
	{ 1, 0, 0, 1 }
};

static VIDEO_DESC( tvbasketball )
    VIDEO_RESISTANCE(1, K_OHM(2.7))
    VIDEO_RESISTANCE(2, K_OHM(2.2))
    VIDEO_RESISTANCE(3, K_OHM(1.8))
    VIDEO_RESISTANCE(4, K_OHM(1.0))
    VIDEO_RESISTANCE(Video::HBLANK_PIN, K_OHM(1.2))
    VIDEO_CONTRAST(1.5)
    VIDEO_RETRO_V_SIZE(246)
VIDEO_DESC_END

static INPUT_DESC( tvbasketball )
    INPUT_INFO(PADDLE1_VERTICAL_INPUT, "Move Left Striped Player")
    INPUT_INFO(PADDLE2_VERTICAL_INPUT, "Move Right Solid Player")
    INPUT_INFO(PADDLE3_VERTICAL_INPUT, "Move Right Striped Player")
    INPUT_INFO(PADDLE4_VERTICAL_INPUT, "Move Left Solid Player")
    INPUT_INFO(COIN_INPUT, {{ 1 }}, "Insert Coin")
    INPUT_INFO(START_INPUT, {{ 1 }}, "Start Game")
INPUT_DESC_END

static Mono555Desc _5h_555_desc(K_OHM(100.0), U_FARAD(0.1));
static Mono555Desc _5f_555_desc(K_OHM(100.0), U_FARAD(0.1));
static Mono555Desc _3h_555_desc(K_OHM(100.0), U_FARAD(0.1));
static Mono555Desc _3f_555_desc(K_OHM(100.0), U_FARAD(0.1));

static Mono555Desc _12a_555_desc(K_OHM(220.0), U_FARAD(3.3));
static Mono555Desc _3b_555_desc(K_OHM(100.0), U_FARAD(4.7));
static Mono555Desc _14g_555_desc(K_OHM(330.0), U_FARAD(0.22));
static Astable555Desc _9d_555_desc(K_OHM(40.0), K_OHM(15.0), U_FARAD(22.0));

static Paddle1VerticalDesc pad1_desc(4000.0, 94000.0, &_5h_555_desc);
static Paddle2VerticalDesc pad2_desc(4000.0, 94000.0, &_3f_555_desc);
static Paddle3VerticalDesc pad3_desc(4000.0, 94000.0, &_3h_555_desc);
static Paddle4VerticalDesc pad4_desc(4000.0, 94000.0, &_5f_555_desc);

static CapacitorDesc c1_desc(U_FARAD(0.001));
static CapacitorDesc c2_desc(U_FARAD(0.001));
static CapacitorDesc c3_desc(U_FARAD(0.001));
static CapacitorDesc c4_desc(U_FARAD(0.001));
static CapacitorDesc c5_desc(U_FARAD(0.001));
static CapacitorDesc c6_desc(P_FARAD(100.0));
static CapacitorDesc c7_desc(U_FARAD(0.01));

static BufferDesc buf1_desc(DELAY_NS(25.0), DELAY_NS(25.0)); // 25 ns buffer to prevent resonance in RC circuits
static BufferDesc buf2_desc(DELAY_NS(25.0), DELAY_NS(25.0)); // 25 ns buffer to prevent resonance in RC circuits

static SeriesRCDesc rc1_desc(OHM(220.0), U_FARAD(350.0));
static SeriesRCDesc rc2_desc(OHM(220.0), U_FARAD(470.0));

static PotentimeterAstable555Desc pot1_desc("playtime", "Play Time", K_OHM(35.0), K_OHM(10.0), K_OHM(60.0), _9d_555_desc);

// Hack to improve performance
static CHIP_LOGIC( diode_matrix_custom_n )
{
    DIODE_LAYOUT* d_l = (DIODE_LAYOUT*)custom_data;

    int y = 4*pin[i5] + 2*pin[i4] + pin[i3];
    int x = 2*pin[i2] + pin[i1];

    pin[6] = (*d_l)[y][x];
}

static CHIP_LOGIC( inv )
{
    pin[5] = pin[6] ^ 1;
}


static CHIP_DESC( DIODE_MATRIX_CUSTOM ) = 
{
    CHIP_START( diode_matrix_custom_n )
        INPUT_PINS( i1, i2, i3, i4, i5 )
        OUTPUT_PIN( 6 )
        OUTPUT_DELAY_NS( 35.0, 36.0 ),

	CHIP_START( inv )
        INPUT_PINS( 6 )
        OUTPUT_PIN( 5 )
        OUTPUT_DELAY_NS( 7.0, 7.0 ),

   	CHIP_DESC_END
};



CIRCUIT_LAYOUT( tvbasketball )
	/**************************************************************************
		Chips
	**************************************************************************/
	CHIP("CLOCK", CLOCK_14_318_MHZ)

	CHIP("BASKET", DIODE_MATRIX, &basket_layout)  
	CHIP("DUMMY", DIODE_MATRIX, &dummy_layout)
    
    CHIP("4A", 7408)
    CHIP("5A", 74151)
    CHIP("6A", 7490)
    CHIP("7A", 7448)
    CHIP("8A", 7410)
    CHIP("9A", 7430)
	CHIP("11A", 74154)
    CHIP("12A", 555_Mono, &_12a_555_desc)
	CHIP("13A", 7404)
    CHIP("14A", 74107)

    CHIP("3B", 555_Mono, &_3b_555_desc)
    CHIP("4B", 7404)
    CHIP("5B", 74151)
    CHIP("6B", 7490)
    CHIP("7B", 74192)
    CHIP("8B", 7410)
    CHIP("9B", 7402)
    CHIP("10B", 7402)
    CHIP("11B", 7427)
    CHIP("12B", 7427)
	CHIP("13B", 7402)
	CHIP("14B", 7400)
    CHIP("15B", 7425)

    CHIP("3C", 7402)
    CHIP("4C", 7454)
    CHIP("5C", 74151)
    CHIP("6C", 7490)
    CHIP("7C", 7425)
    CHIP("8C", 7410)
    CHIP("9C", 74107)
	CHIP("10C", 7410)
    CHIP("11C", 7408)
    CHIP("12C", 7432)
    CHIP("13C", 7400)
	CHIP("14C", 7425)
    CHIP("15C", 7400)

    CHIP("3D", 7427)
    CHIP("4D", 7454)
    CHIP("5D", 74151)
    CHIP("6D", 7490)
    CHIP("7D", 74192)
    CHIP("8D", 7427)
    CHIP("9D", 555_Astable, &_9d_555_desc)
    CHIP("10D", 7400)
    CHIP("11D", 7493)
    CHIP("12D", 7400)
    CHIP("13D", 7474)
    CHIP("14D", 7425)
    CHIP("15D", 7404)

    CHIP("1E", 74155)
    //CHIP("2E", 74151)
    CHIP("2E", DIODE_MATRIX_CUSTOM, &dummy_layout) 
    CHIP("3E", 7404)
    CHIP("4E", 7454)
    CHIP("6E", 7404)
    CHIP("7E", 7404)
    CHIP("8E", 7402)
    CHIP("9E", 7400)
    CHIP("10E", 7400)
	CHIP("11E", 7402)
    CHIP("12E", 74107)
    CHIP("13E", 7404)
    CHIP("14E", 7402)
    CHIP("15E", 7400)

    CHIP("1F", 74155)
	CHIP("2F", 74151)
    CHIP("3F", 555_Mono, &_3f_555_desc)
    CHIP("4F", 7493)
    CHIP("5F", 555_Mono, &_5f_555_desc)
    CHIP("6F", 7493)
    CHIP("7F", 7454)
	CHIP("8F", 7483)
    CHIP("9F", 74161)
    CHIP("10F", 74161)
    CHIP("11F", 7493)
	CHIP("12F", 7404)
    CHIP("13F", 7400)
    CHIP("14F", 7410)
    CHIP("15F", 74279)
    
    CHIP("3G", 7400)
    CHIP("4G", 7420)
    CHIP("5G", 7400)
    CHIP("6G", 7420)
    CHIP("7G", 7454)
    CHIP("8G", 7474)
    CHIP("9G", 7486)
    CHIP("10G", 7420)
    CHIP("11G", 7493)
	CHIP("12G", 7474)
    CHIP("13G", 7400)
    CHIP("14G", 555_Mono, &_14g_555_desc)
	
    CHIP("3H", 555_Mono, &_3h_555_desc)
    CHIP("4H", 7493)
    CHIP("5H", 555_Mono, &_5h_555_desc)
    CHIP("6H", 7493)
    CHIP("7H", 7454)
    CHIP("8H", 7474)
    CHIP("9H", 7486)
    CHIP("10H", 74161)
    CHIP("11H", 74161)
	CHIP("12H", 7410)
	CHIP("13H", 7400)
	CHIP("14H", 7493)
	CHIP("15H", 7493)
	
    CHIP("3J", 7474)
    CHIP("4J", 7474)
    CHIP("5J", 7486)
	CHIP("6J", 7402)
	CHIP("7J", 74107)
    CHIP("8J", 7451)
    CHIP("9J", 7402)
    CHIP("10J", 7402)
    CHIP("11J", 74107)
	CHIP("12J", 7404)
	CHIP("14J", 74107)
	CHIP("15J", 7404)
	CHIP("13J", 7430)

    CHIP("PAD1", PADDLE1_VERTICAL_INPUT, &pad1_desc)
    PADDLE_CONNECTION("PAD1", "5H")
    CHIP("PAD2", PADDLE4_VERTICAL_INPUT, &pad2_desc)
    PADDLE_CONNECTION("PAD2", "3F")
    CHIP("PAD3", PADDLE3_VERTICAL_INPUT, &pad3_desc)
    PADDLE_CONNECTION("PAD3", "3H")
    CHIP("PAD4", PADDLE2_VERTICAL_INPUT, &pad4_desc)
    PADDLE_CONNECTION("PAD4", "5F")

    CHIP("LATCH", LATCH)
    CHIP("COIN", COIN_INPUT)
    CHIP("START", START_INPUT)

    CHIP("POT1", POT_555_ASTABLE, &pot1_desc)
    POTENTIOMETER_CONNECTION("POT1", "9D") 

    CHIP("BUF1", BUFFER, &buf1_desc)
    CHIP("BUF2", BUFFER, &buf2_desc)

    CHIP("RC1", SERIES_RC, &rc1_desc)
    CHIP("RC2", SERIES_RC, &rc2_desc)

    // Misc. Capacitors
	CHIP("C1", CAPACITOR, &c1_desc)
	CHIP("C2", CAPACITOR, &c2_desc)
	CHIP("C3", CAPACITOR, &c3_desc)
	CHIP("C4", CAPACITOR, &c4_desc)
	CHIP("C5", CAPACITOR, &c5_desc)
	CHIP("C6", CAPACITOR, &c6_desc)
    CHIP("C7", CAPACITOR, &c7_desc)

    VIDEO(tvbasketball)
    INPUT(tvbasketball)

    OPTIMIZATION_HINT("8A", 256, 256)
    OPTIMIZATION_HINT("8B", 256, 256)
    OPTIMIZATION_HINT("8C", 256, 256)
    OPTIMIZATION_HINT("9A", 256, 384)

    OPTIMIZATION_HINT("7E", 16, 64)

    DISABLE_OPTIMIZATION("15D", 11)
    DISABLE_OPTIMIZATION("VIDEO", 4)
    DISABLE_OPTIMIZATION("14C", 9)

   

    //OPTIMIZATION_HINT("2E", 128, 128)

    /*CHIP("CLK_GATE1", CLK_GATE)
    CHIP("CLK_GATE2", CLK_GATE)
    CHIP("CLK_GATE3", CLK_GATE)*/

#ifdef DEBUG
	CHIP("LOG1", VCD_LOG, &vcd_log_desc)
#endif

	/**************************************************************************
		Lines
	**************************************************************************/	
	#define CLK "14J", 5

    #define A "4B", 6 // Not Really
    #define B "13A", 4

    #define H1  "15H", 12
	#define H2  "15H", 9
	#define H4  "15H", 8
	#define H8  "15H", 11
	#define H4_n  "15J", 6
	#define H8_n  "15J", 4

	#define H16  "14H", 12
	#define H32  "14H", 9
	#define H64  "14H", 8
	#define H128  "14H", 11
	#define H64_n  "10D", 11
	#define H16_n  "15J", 2
	
	#define H256  "14J", 3
	#define H256_n  "14J", 2
	
	#define HBLANK  "13H", 6
	#define HBLANK_n  "13H", 3
	#define HSYNC_n  "13H", 8
	
	#define V1  "11F", 12
	#define V2  "11F", 9
	#define V4  "11F", 8
	#define V8  "11F", 11
	#define V2_n  "12F", 8
	#define V4_n  "12J", 6
	#define V8_n  "12F", 12
	
	#define V16  "11G", 12
	#define V32  "11G", 9
	#define V64  "11G", 8
	#define V128  "11G", 11
	#define V256  "11J", 5
	#define V16_n  "12F", 6
	#define V64_n  "12F", 4
	#define V128_n  "12F", 10
	
    #define VRESET "12G", 8
	#define VBLANK  "11E", 4
	#define VSYNC_n  "12H", 6	
	
    #define BALL "10J", 1

    #define GAME_ON "10B", 10


	/**************************************************************************
		Layout
	**************************************************************************/
    /* Horizontal Divider */
	CONNECTION("CLOCK", 1, "14J", 9)
	CONNECTION(A, "14J", 8)
	CONNECTION(A, "14J", 11)
	CONNECTION(A, "14J", 10)
    
    CONNECTION(CLK, "15H", 14)
	CONNECTION("15H", 12, "15H", 1)
	CONNECTION("12G", 6, "15H", 2)
	CONNECTION("12G", 6, "15H", 3)
	
	CONNECTION("15H", 11, "15J", 3)
	
	CONNECTION("15H", 8, "15J", 5)
	
	CONNECTION("15H", 11, "14H", 14)
	CONNECTION("14H", 12, "14H", 1)
	CONNECTION("12G", 6, "14H", 2)
	CONNECTION("12G", 6, "14H", 3)
	
	CONNECTION(A, "14J", 1)
	CONNECTION("14H", 11, "14J", 12)
	CONNECTION(A, "14J", 4)
	CONNECTION("12G", 5, "14J", 13)
	
	CONNECTION("14J", 3, "13J", 4)
	CONNECTION("14H", 11, "13J", 11)
	CONNECTION("14H", 8, "13J", 1)
	CONNECTION("15H", 8, "13J", 5)
	CONNECTION("15H", 9, "13J", 6)
	CONNECTION(A, "13J", 3)
	CONNECTION(A, "13J", 2)
	CONNECTION(A, "13J", 12)
	
	CONNECTION(VCC, "12G", 4)
	CONNECTION("13J", 8, "12G", 2)
	CONNECTION(CLK, "12G", 3)
	CONNECTION(VCC, "12G", 1)

	CONNECTION(H64, "13H", 13)
	CONNECTION(H16, "13H", 12)
	
	CONNECTION(H16, "15J", 1)
	
	CONNECTION(H64, "10D", 12)
	CONNECTION(H64, "10D", 13)

	CONNECTION("13H", 11, "13H", 2)
	CONNECTION("13H", 6, "13H", 1)
		
	CONNECTION("13H", 3, "13H", 4)
	CONNECTION("12G", 5, "13H", 5)

	CONNECTION(H32, "13H", 10)
	CONNECTION("13H", 6, "13H", 9)
	
	

	
	/* Vertical Divider */
	CONNECTION("12G", 6, "11F", 14)
	CONNECTION("11F", 12, "11F", 1)
	CONNECTION("12G", 8, "11F", 2)
	CONNECTION("12G", 8, "11F", 3)
	
	CONNECTION("11F", 11, "12F", 13)
	
	CONNECTION("11F", 11, "12J", 3)
	
	CONNECTION("11F", 8, "12J", 5)

	CONNECTION("11F", 9, "12F", 9)
	
	CONNECTION("11F", 11, "11G", 14)
	CONNECTION("11G", 12, "11G", 1)
	CONNECTION("12G", 8, "11G", 2)
	CONNECTION("12G", 8, "11G", 3)
	
	CONNECTION(A, "11J", 8)
	CONNECTION("11G", 11, "11J", 9)
	CONNECTION(A, "11J", 11)
	CONNECTION("12G", 9, "11J", 10)

	CONNECTION("11G", 11, "12F", 11)
	
	CONNECTION("11G", 8, "12F", 3)

	CONNECTION("11G", 12, "12F", 5)
	
	CONNECTION("11J", 5, "12H", 9)
	CONNECTION("11F", 8, "12H", 10)
	CONNECTION("11F", 12, "12H", 11)

	CONNECTION(VCC, "12G", 10)
	CONNECTION("12H", 8, "12G", 12)
	CONNECTION("12G", 6, "12G", 11)
	CONNECTION(A, "12G", 13)
	
	CONNECTION("12G", 8, "11E", 2)
	CONNECTION("11E", 4, "11E", 3)
	
	CONNECTION("11E", 1, "11E", 5)
	CONNECTION("11G", 12, "11E", 6)
	
	CONNECTION("11F", 8, "12H", 5)
	CONNECTION("12J", 4, "12H", 4)
	CONNECTION("11E", 4, "12H", 3)
	


	
	/* Vertical Hit Direction*/
    CONNECTION("10B", 1, "4B", 9)

    CONNECTION("10B", 13, "3E", 5)

    CONNECTION("6H", 9, "7H", 10)
    CONNECTION("4B", 8, "7H", 9)
    CONNECTION("6F", 9, "7H", 13)
    CONNECTION("3E", 6, "7H", 1)
    CONNECTION("4H", 9, "7H", 3)
    CONNECTION("4A", 11, "7H", 2)
    CONNECTION("4F", 9, "7H", 5)
    CONNECTION("4A", 8, "7H", 4)

    CONNECTION("6H", 8, "7G", 10)
    CONNECTION("4B", 8, "7G", 9)
    CONNECTION("6F", 8, "7G", 13)
    CONNECTION("3E", 6, "7G", 1)
    CONNECTION("4H", 8, "7G", 3)
    CONNECTION("4A", 11, "7G", 2)
    CONNECTION("4F", 8, "7G", 5)
    CONNECTION("4A", 8, "7G", 4)

    CONNECTION("6H", 11, "7F", 10)
    CONNECTION("4B", 8, "7F", 9)
    CONNECTION("6F", 11, "7F", 13)
    CONNECTION("3E", 6, "7F", 1)
    CONNECTION("4H", 11, "7F", 3)
    CONNECTION("4A", 11, "7F", 2)
    CONNECTION("4F", 11, "7F", 5)
    CONNECTION("4A", 8, "7F", 4)

    CONNECTION("15D", 8, "10J", 9)
    CONNECTION("15F", 9, "10J", 8)

    CONNECTION("12G", 9, "13F", 10)
    CONNECTION("13F", 6, "13F", 9)

    CONNECTION(VCC, "8G", 4)
    CONNECTION("7H", 8, "8G", 2)
    CONNECTION("15C", 8, "8G", 3)
    CONNECTION("10J", 10, "8G", 1)

    CONNECTION(VCC, "8G", 10)
    CONNECTION("7G", 8, "8G", 12)
    CONNECTION("15C", 8, "8G", 11)
    CONNECTION("10J", 10, "8G", 13)

    CONNECTION(VCC, "8H", 4)
    CONNECTION("7F", 8, "8H", 2)
    CONNECTION("15C", 8, "8H", 3)
    CONNECTION("10J", 10, "8H", 1)

    //CONNECTION("13C", 8, "7J", 10)
    CONNECTION("C6", 2, "7J", 10)
    CONNECTION("10J", 13, "7J", 8)
    CONNECTION("13F", 8, "7J", 9)
    CONNECTION("10J", 13, "7J", 11)

    CONNECTION("7J", 5, "9G", 2)
    CONNECTION("8G", 5, "9G", 1)

    CONNECTION("7J", 5, "9G", 13)
    CONNECTION("8G", 9, "9G", 12)

    CONNECTION("7J", 5, "8J", 4)
    CONNECTION("8H", 5, "8J", 5)
    CONNECTION("8H", 6, "8J", 2)
    CONNECTION("7J", 6, "8J", 3)

    CONNECTION("9G", 3, "8F", 10)
    CONNECTION("9G", 11, "8F", 8)
    CONNECTION("8J", 6, "8F", 3)
    CONNECTION("8J", 6, "8F", 11)
    CONNECTION(VCC, "8F", 4)
    CONNECTION(VCC, "8F", 7)
    CONNECTION(GND, "8F", 1)
    CONNECTION(GND, "8F", 16)
    CONNECTION(GND, "8F", 13)




    /* Vertical Position */
    CONNECTION("8F", 15, "9F", 6)
    CONNECTION("8F", 2, "9F", 5)
    CONNECTION("8F", 6, "9F", 4)
    CONNECTION("8F", 9, "9F", 3)
    CONNECTION(VCC, "9F", 7)
    CONNECTION("11E", 1, "9F", 10)
    CONNECTION("13H", 8, "9F", 2)
    CONNECTION("9E", 8, "9F", 9)
    CONNECTION("10D", 6, "9F", 1)

    CONNECTION(GND, "10F", 6)
    CONNECTION(GND, "10F", 5)
    CONNECTION(GND, "10F", 4)
    CONNECTION(GND, "10F", 3)
    CONNECTION("9F", 15, "10F", 7)
    CONNECTION(VCC, "10F", 10)
    CONNECTION("13H", 8, "10F", 2)
    CONNECTION("9E", 8, "10F", 9)
    CONNECTION("10D", 6, "10F", 1)

    CONNECTION("10F", 15, "9E", 9)
    CONNECTION("9F", 15, "9E", 10)




    /* Horizontal Position */
    CONNECTION(A, "10H", 6)
    CONNECTION("10E", 8, "10H", 3)
    CONNECTION("10E", 11, "10H", 4)
    CONNECTION(GND, "10H", 5)
    CONNECTION(VCC, "10H", 7) // Not shown. ???
    CONNECTION(HBLANK_n, "10H", 10)
    CONNECTION(CLK, "10H", 2)
    CONNECTION("12H", 12, "10H", 9)
    CONNECTION("10D", 6, "10H", 1)

    CONNECTION(A, "11H", 6)
    CONNECTION(GND, "11H", 3)
    CONNECTION(GND, "11H", 4)
    CONNECTION(GND, "11H", 5)
    CONNECTION("10H", 15, "11H", 7)
    CONNECTION(A, "11H", 10)
    CONNECTION(CLK, "11H", 2)
    CONNECTION("12H", 12, "11H", 9)
    CONNECTION("10D", 6, "11H", 1)

    CONNECTION(VCC, "11J", 1)
    CONNECTION("11H", 15, "11J", 12)
    CONNECTION(A, "11J", 4)
    CONNECTION("10D", 6, "11J", 13)

    CONNECTION("11J", 3, "12H", 2)
    CONNECTION("10H", 15, "12H", 13)
    CONNECTION("11H", 15, "12H", 1)
    



    /* Ball Form */
    CONNECTION("11H", 15, "10G", 9)
    CONNECTION("10F", 15, "10G", 13)
    CONNECTION("9F", 11, "10G", 12)
    CONNECTION("10H", 11, "10G", 10)

    CONNECTION("9F", 13, "9H", 4)
    CONNECTION("9F", 12, "9H", 5)

    CONNECTION("9F", 12, "9H", 1)
    CONNECTION("9F", 14, "9H", 2)

    CONNECTION("10H", 13, "9H", 12)
    CONNECTION("10H", 12, "9H", 13)

    CONNECTION("10H", 12, "9H", 10)
    CONNECTION("10H", 14, "9H", 9)

    CONNECTION("11J", 2, "10J", 5)
    CONNECTION("10G", 8, "10J", 6)

    CONNECTION("10J", 4, "12J", 11)

    CONNECTION("9F", 12, "12J", 13)

    CONNECTION("9H", 6, "9J", 11)
    CONNECTION("9H", 3, "9J", 12)

    // Speed hack
    //CONNECTION("10J", 4, "CLK_GATE1", 1)
    //CONNECTION("9H", 11, "CLK_GATE1", 2)
    //CONNECTION("10J", 4, "CLK_GATE2", 1)
    //CONNECTION("9H", 8, "CLK_GATE2", 2)

    CONNECTION("9H", 11, "9J", 9)
    CONNECTION("9H", 8, "9J", 8)
    //CONNECTION("CLK_GATE1", 3, "9J", 9)
    //CONNECTION("CLK_GATE2", 3, "9J", 8)


    CONNECTION("9H", 6, "8J", 10)
    CONNECTION("9H", 3, "8J", 9)
    CONNECTION("9H", 11, "8J", 1)
    CONNECTION("9H", 8, "8J", 13)
    //CONNECTION("CLK_GATE1", 3, "8J", 1)
    //CONNECTION("CLK_GATE2", 3, "8J", 13)
    
    CONNECTION("12J", 10, "10J", 12)
    CONNECTION("12J", 12, "10J", 11)

    CONNECTION("9J", 13, "9J", 2)
    CONNECTION("9J", 10, "9J", 3)

    CONNECTION("8J", 8, "12J", 9)

    CONNECTION("12J", 10, "10J", 3)
    CONNECTION("9J", 4, "10J", 2)

    CONNECTION("9J", 1, "9J", 5)
    CONNECTION("12J", 8, "9J", 6)





	/* Basket Generation */
	CONNECTION("12F", 10, "10C", 3)
	CONNECTION("11G", 8, "10C", 5)
	CONNECTION("11G", 9, "10C", 4)
	
	CONNECTION("11F", 8, "1F", 13)
	CONNECTION("11F", 11, "1F", 3)
	CONNECTION("11G", 12, "1F", 1)
	CONNECTION("11G", 12, "1F", 15)
	CONNECTION("10C", 6, "1F", 2)
	CONNECTION("10C", 6, "1F", 14)
	
	CONNECTION("1F", 9, "BASKET", ROW0)
	CONNECTION("1F", 10, "BASKET", ROW1)
	CONNECTION("1F", 11, "BASKET", ROW2)
	CONNECTION("1F", 12, "BASKET", ROW3)
	CONNECTION("1F", 7, "BASKET", ROW4)
	CONNECTION("1F", 6, "BASKET", ROW5)
	CONNECTION("1F", 5, "BASKET", ROW6)
	CONNECTION("1F", 4, "BASKET", ROW7)
	
	CONNECTION("BASKET", COL0, "2F", 4)
	CONNECTION("BASKET", COL1, "2F", 3)
	CONNECTION("BASKET", COL2, "2F", 2)
	CONNECTION("BASKET", COL3, "2F", 1)
	CONNECTION("BASKET", COL4, "2F", 15)
	CONNECTION("BASKET", COL5, "2F", 14)
	CONNECTION("BASKET", COL6, "2F", 13)
	CONNECTION("BASKET", COL7, "2F", 12)
	CONNECTION("5J", 3, "2F", 11)
	CONNECTION("5J", 11, "2F", 10)
	CONNECTION("5J", 8, "2F", 9)
	CONNECTION(GND, "2F", 7)
	
    // TODO: Other side of cap is connected to VCC,
    // and there is a 470 Ohm parallel resistor.
	CONNECTION("2F", 5, "C2", 1)
	
	CONNECTION("15H", 12, "5J", 1)
	CONNECTION("15H", 11, "5J", 2)
	
	CONNECTION("15H", 11, "5J", 13)
	CONNECTION("15H", 9, "5J", 12)
	
	CONNECTION("15H", 8, "5J", 9)
	CONNECTION("15H", 11, "5J", 10)
	
	CONNECTION("15H", 11, "5J", 5)
	CONNECTION("14H", 12, "5J", 4)
	
	CONNECTION("11A", 4, "8H", 12)
	CONNECTION(H16, "8H", 11)
	CONNECTION(VCC, "8H", 10)
	CONNECTION(VCC, "8H", 13)
	
	CONNECTION("5J", 6, "6E", 13)
	
	CONNECTION("6E", 12, "6J", 11)
	CONNECTION("8H", 9, "6J", 12)
	
	CONNECTION("5J", 6, "6J", 5)
	CONNECTION("11A", 14, "6J", 6)
	
	CONNECTION("6J", 13, "6J", 2)
	CONNECTION("6J", 4, "6J", 3)
	
	//CONNECTION("2F", 5, "6J", 9)
	CONNECTION("C2", 2, "6J", 9)
	CONNECTION("6J", 1, "6J", 8)
	
	CONNECTION("6J", 10, "C1", 1)
		
	CONNECTION(VCC, "7J", 1)
	//CONNECTION("6J", 10, "7J", 12)
	CONNECTION("C1", 2, "7J", 12)
	CONNECTION(VCC, "7J", 4)
	CONNECTION(HBLANK_n, "7J", 13)
	
	CONNECTION(V2, "14B", 2)
	CONNECTION(V1, "14B", 1)
	
	CONNECTION("14B", 3, "13B", 6)
	CONNECTION("7J", 2, "13B", 5)
	
	CONNECTION(H2, "14B", 5)
	CONNECTION(H1, "14B", 4)
	
	CONNECTION("7J", 2, "13B", 2)
	CONNECTION("14B", 6, "13B", 3)
	
    CONNECTION(V16, "15B", 5)
    CONNECTION(V8, "15B", 4)
    CONNECTION(V4, "15B", 2)
    CONNECTION(V2, "15B", 1)

    CONNECTION(V16_n, "15B", 9)
    CONNECTION(V8_n, "15B", 10)
    CONNECTION(V4_n, "15B", 12)
    CONNECTION(V2_n, "15B", 13)

    CONNECTION("15B", 6, "13B", 12)
    CONNECTION("15B", 8, "13B", 11)

    CONNECTION("7J", 2, "12B", 2)
    CONNECTION("13B", 13, "12B", 1)
    CONNECTION("10C", 6, "12B", 13)

    CONNECTION("13B", 1, "14C", 2)
    CONNECTION("14E", 13, "14C", 4)
    CONNECTION("C1", 2, "14C", 5)
    CONNECTION("12B", 12, "14C", 1)

    CONNECTION("14C", 6, "13A", 9)





    /* Fence Generation */
    CONNECTION("12H", 6, "15F", 5)
    CONNECTION("13F", 11, "15F", 6)

    CONNECTION("11A", 4, "14D", 1)
    CONNECTION("14H", 12, "14D", 2)
    CONNECTION("15J", 4, "14D", 4)
    CONNECTION("15J", 6, "14D", 5)

    CONNECTION("11A", 15, "14D", 12)
    CONNECTION("14H", 12, "14D", 13)
    CONNECTION("15H", 11, "14D", 10)
    CONNECTION("15H", 8, "14D", 9)   

    CONNECTION("14D", 8, "14E", 8)
    CONNECTION("14D", 6, "14E", 9)

    // Including the optional capacitor breaks right wall collisions.
    //CONNECTION("14E", 10, "C3", 1) // Optional capacitor?

    CONNECTION("15F", 7, "14E", 12)
    //CONNECTION("C3", 2, "14E", 11)
    CONNECTION("14E", 10, "14E", 11)

    //CONNECTION("C3", 2, "15D", 13)
    CONNECTION("14E", 10, "15D", 13)

    CONNECTION("15F", 7, "15C", 1)
    CONNECTION("15D", 12, "15C", 2)

    CONNECTION("14E", 13, "15C", 4)
    CONNECTION("10J", 1, "15C", 5)

    CONNECTION("15C", 6, "15D", 9)

    CONNECTION("14D", 8, "12C", 9)
    CONNECTION("11C", 3, "12C", 10)

    CONNECTION("14D", 6, "12C", 5)
    CONNECTION("11C", 6, "12C", 4)

    CONNECTION("12C", 8, "13C", 12)
    CONNECTION(BALL, "13C", 13)

    CONNECTION(BALL, "13C", 2)
    CONNECTION("12C", 6, "13C", 1)

    CONNECTION("13C", 11, "13C", 5)
    CONNECTION("13C", 3, "13C", 4)

    CONNECTION("13C", 11, "13D", 4)
    CONNECTION("13D", 6, "13D", 2)
    CONNECTION("14G", 3, "13D", 3)
    CONNECTION("13C", 3, "13D", 1)




    /* H Direction Control */
    CONNECTION("15C", 3, "13C", 10)
    CONNECTION("13C", 6, "13C", 9)

    CONNECTION("13C", 6, "15D", 1)

    // Positive edge on 15C outputs drives a high voltage onto 15D inputs,
    // which causes 15D outputs to go low for a period of time until capacitor finishes
    // charging. TODO: is this accurate?
    CONNECTION("15C", 11, "RC1", 1)
    CONNECTION(GND, "RC1", 2)

    CONNECTION("RC1", 3, "15D", 3)

    //CONNECTION("15D", 4, "15C", 12)
    CONNECTION("15D", 4, "BUF1", 1) // Prevents resonance in rc circuit
    CONNECTION("BUF1", 2, "15C", 12)
    CONNECTION("15D", 2, "15C", 13)
    

    CONNECTION("13C", 8, "C6", 1)

    CONNECTION("15C", 8, "RC2", 1)
    CONNECTION(GND, "RC2", 2)

    CONNECTION("RC2", 3, "15D", 5)

    //CONNECTION("15D", 6, "15C", 9)
    CONNECTION("15D", 6, "BUF2", 1) // Prevents resonance in rc circuit
    CONNECTION("BUF2", 2, "15C", 9)
    CONNECTION("C6", 2, "15C", 10)





    /* Dummy Position */
    // Outer Left #1
    CONNECTION(VCC, "5H", 4)
    CONNECTION("10C", 12, "5H", 2)

    CONNECTION("5H", 3, "6E", 9)
    
    CONNECTION("6E", 8, "5G", 13)
    CONNECTION("6G", 8, "5G", 12)

    CONNECTION("6G", 8, "5G", 10)
    CONNECTION(V1, "5G", 9)

    CONNECTION("5H", 3, "6H", 2)
    CONNECTION("5H", 3, "6H", 3)
    CONNECTION("5G", 8, "6H", 14)
    CONNECTION("6H", 12, "6H", 1)

    CONNECTION("6H", 12, "6G", 13)
    CONNECTION("6H", 9, "6G", 10)
    CONNECTION("6H", 8, "6G", 9)
    CONNECTION("6H", 11, "6G", 12)

    // Inner Right #2
    CONNECTION(VCC, "3F", 4)
    CONNECTION("10C", 12, "3F", 2)

    CONNECTION("3F", 3, "3E", 9)
    
    CONNECTION("3E", 8, "3G", 1)
    CONNECTION("4G", 6, "3G", 2)

    CONNECTION("4G", 6, "3G", 4)
    CONNECTION(V1, "3G", 5)

    CONNECTION("3F", 3, "4F", 2)
    CONNECTION("3F", 3, "4F", 3)
    CONNECTION("3G", 6, "4F", 14)
    CONNECTION("4F", 12, "4F", 1)

    CONNECTION("4F", 12, "4G", 1)
    CONNECTION("4F", 9, "4G", 4)
    CONNECTION("4F", 8, "4G", 5)
    CONNECTION("4F", 11, "4G", 2)

    // Inner Left #3
    CONNECTION(VCC, "3H", 4)
    CONNECTION("10C", 12, "3H", 2)

    CONNECTION("3H", 3, "3E", 13)
    
    CONNECTION("3E", 12, "3G", 13)
    CONNECTION("4G", 8, "3G", 12)

    CONNECTION("4G", 8, "3G", 10)
    CONNECTION(V1, "3G", 9)

    CONNECTION("3H", 3, "4H", 2)
    CONNECTION("3H", 3, "4H", 3)
    CONNECTION("3G", 8, "4H", 14)
    CONNECTION("4H", 12, "4H", 1)

    CONNECTION("4H", 12, "4G", 13)
    CONNECTION("4H", 9, "4G", 10)
    CONNECTION("4H", 8, "4G", 9)
    CONNECTION("4H", 11, "4G", 12)

    // Outer Right #4
    CONNECTION(VCC, "5F", 4)
    CONNECTION("10C", 12, "5F", 2)

    CONNECTION("5F", 3, "6E", 11)
    
    CONNECTION("6E", 10, "5G", 1)
    CONNECTION("6G", 6, "5G", 2)

    CONNECTION("6G", 6, "5G", 4)
    CONNECTION(V1, "5G", 5)

    CONNECTION("5F", 3, "6F", 2)
    CONNECTION("5F", 3, "6F", 3)
    CONNECTION("5G", 6, "6F", 14)
    CONNECTION("6F", 12, "6F", 1)

    CONNECTION("6F", 12, "6G", 1)
    CONNECTION("6F", 9, "6G", 4)
    CONNECTION("6F", 8, "6G", 5)
    CONNECTION("6F", 11, "6G", 2)




    /* Dummy Generation */
    CONNECTION("6H", 9, "4E", 10)
    CONNECTION("4B", 8, "4E", 9)
    CONNECTION("6F", 9, "4E", 13)
    CONNECTION("3E", 6, "4E", 1)
    CONNECTION("4H", 9, "4E", 3)
    CONNECTION("4A", 11, "4E", 2)
    CONNECTION("4F", 9, "4E", 5)
    CONNECTION("4A", 8, "4E", 4)

    CONNECTION("6H", 8, "4D", 10)
    CONNECTION("4B", 8, "4D", 9)
    CONNECTION("6F", 8, "4D", 13)
    CONNECTION("3E", 6, "4D", 1)
    CONNECTION("4H", 8, "4D", 3)
    CONNECTION("4A", 11, "4D", 2)
    CONNECTION("4F", 8, "4D", 5)
    CONNECTION("4A", 8, "4D", 4)

    CONNECTION("6H", 11, "4C", 10)
    CONNECTION("4B", 8, "4C", 9)
    CONNECTION("6F", 11, "4C", 13)
    CONNECTION("3E", 6, "4C", 1)
    CONNECTION("4H", 11, "4C", 3)
    CONNECTION("4A", 11, "4C", 2)
    CONNECTION("4F", 11, "4C", 5)
    CONNECTION("4A", 8, "4C", 4)

    CONNECTION("4E", 8, "7E", 13)
    CONNECTION("4D", 8, "7E", 1)
    CONNECTION("4C", 8, "7E", 11)

	/*CONNECTION("7E", 12, "1E", 13)
	CONNECTION("7E", 2, "1E", 3)
	CONNECTION("7E", 10, "1E", 1)
	CONNECTION("7E", 10, "1E", 15)
	CONNECTION(GND, "1E", 2)
	CONNECTION(GND, "1E", 14)
    
    CONNECTION("1E", 9, "DUMMY", ROW0)
	CONNECTION("1E", 10, "DUMMY", ROW1)
	CONNECTION("1E", 11, "DUMMY", ROW2)
	CONNECTION("1E", 12, "DUMMY", ROW3)
	CONNECTION("1E", 7, "DUMMY", ROW4)
	CONNECTION("1E", 6, "DUMMY", ROW5)
	CONNECTION("1E", 5, "DUMMY", ROW6)
	CONNECTION("1E", 4, "DUMMY", ROW7)
	
	CONNECTION("DUMMY", COL0, "2E", 4)
	CONNECTION("DUMMY", COL1, "2E", 3)
	CONNECTION("DUMMY", COL2, "2E", 2)
	CONNECTION("DUMMY", COL3, "2E", 1)
	CONNECTION(GND, "2E", 15)
	CONNECTION(GND, "2E", 14)
	CONNECTION(GND, "2E", 13)
	CONNECTION(GND, "2E", 12)
	CONNECTION("5J", 11, "2E", 11)
	CONNECTION("5J", 8, "2E", 10)
	CONNECTION(GND, "2E", 9)
	CONNECTION(GND, "2E", 7)*/

    CONNECTION("7E", 10, "2E", i5)
    CONNECTION("7E", 2, "2E", i4)
    CONNECTION("7E", 12, "2E", i3)
    CONNECTION("5J", 8, "2E", i2)
	CONNECTION("5J", 11, "2E", i1)


    CONNECTION("11A", 13, "9B", 11)
    CONNECTION(H16_n, "9B", 12)

    CONNECTION("11A", 8, "9B", 8)
    CONNECTION(H16, "9B", 9)

    CONNECTION("11A", 5, "9B", 2)
    CONNECTION(H16_n, "9B", 3)

    CONNECTION("11A", 10, "9B", 5)
    CONNECTION(H16, "9B", 6)

    CONNECTION("2E", 5, "14B", 12)
    CONNECTION(V1, "14B", 13)

    CONNECTION("9B", 10, "4A", 1)
    CONNECTION("4J", 6, "4A", 2)

    CONNECTION("4J", 6, "4A", 5)
    CONNECTION("9B", 4, "4A", 4)

    CONNECTION("9B", 10, "4A", 9)
    CONNECTION("4B", 2, "4A", 10)

    CONNECTION("4B", 2, "4A", 13)
    CONNECTION("9B", 4, "4A", 12)

    CONNECTION("9B", 13, "10B", 11)
    CONNECTION("4A", 3, "10B", 12)

    CONNECTION("9B", 1, "10B", 3)
    CONNECTION("4A", 6, "10B", 2)

    CONNECTION("4A", 8, "3E", 11)

    CONNECTION("4A", 11, "3E", 3)

    CONNECTION("5G", 3, "11B", 2)
    CONNECTION("10B", 13, "11B", 13)
    CONNECTION("2E", 6, "11B", 1)

    CONNECTION("5G", 11, "11B", 4)
    CONNECTION("10B", 1, "11B", 3)
    CONNECTION("14B", 11, "11B", 5)

    CONNECTION("2E", 6, "3D", 1)
    CONNECTION("3E", 10, "3D", 13)
    CONNECTION("3G", 3, "3D", 2)

    CONNECTION("14B", 11, "3D", 5)
    CONNECTION("3E", 4, "3D", 3)
    CONNECTION("3G", 11, "3D", 4)

    CONNECTION("11B", 12, "3C", 2)
    CONNECTION("3D", 12, "3C", 3)

    CONNECTION("11B", 6, "3C", 5)
    CONNECTION("3D", 6, "3C", 6)

    CONNECTION("3C", 1, "4B", 11)

    CONNECTION("3C", 4, "4B", 13)

    CONNECTION("4B", 10, "C4", 1)
    CONNECTION("4B", 12, "C5", 1)

    CONNECTION("C4", 2, "11C", 2)
    CONNECTION(GAME_ON, "11C", 1)

    CONNECTION(GAME_ON, "11C", 4)
    CONNECTION("C5", 2, "11C", 5)   

    CONNECTION("11C", 3, "12C", 2)
    CONNECTION("11C", 6, "12C", 1)




    /* Display */
    CONNECTION(H2, "9E", 4)
    CONNECTION(H4, "9E", 5)

    CONNECTION(H8_n, "8D", 11)
    CONNECTION(H4, "8D", 10)
    CONNECTION(H2, "8D", 9)

    CONNECTION("9E", 6, "8E", 6)
    CONNECTION(H8_n, "8E", 5)

    CONNECTION(V2, "8D", 5)
    CONNECTION(V4, "8D", 4)
    CONNECTION(H8_n, "8D", 3)

    CONNECTION(H8, "8C", 9)
    CONNECTION(V4, "8C", 11)
    CONNECTION(V2, "8C", 10)
    
    CONNECTION("8C", 8, "7E", 5)
    
    CONNECTION(H16_n, "9E", 1)
    CONNECTION("11A", 9, "9E", 2)

    CONNECTION(VCC, "7A", 3)
    CONNECTION(VCC, "7A", 4)
    CONNECTION("9E", 3, "7A", 5)
    CONNECTION("5A", 5, "7A", 7)
    CONNECTION("5B", 5, "7A", 1)
    CONNECTION("5C", 5, "7A", 2)
    CONNECTION("5D", 5, "7A", 6)

    CONNECTION("7A", 9, "8A", 11)
    CONNECTION("8D", 8, "8A", 9)
    CONNECTION(V8_n, "8A", 10)

    CONNECTION("7A", 10, "8A", 1)
    CONNECTION(V8_n, "8A", 2)
    CONNECTION("7E", 6, "8A", 13)

    CONNECTION("7A", 11, "8A", 3)
    CONNECTION(V8_n, "8A", 4)
    CONNECTION("8E", 4, "8A", 5)

    CONNECTION("7A", 12, "8B", 11)
    CONNECTION("8E", 4, "8B", 9)
    CONNECTION(V8, "8B", 10)    

    CONNECTION("7A", 13, "8B", 1)
    CONNECTION(V8, "8B", 2)
    CONNECTION("8D", 6, "8B", 13)    

    CONNECTION("7A", 14, "8B", 3)
    CONNECTION("7E", 6, "8B", 5)
    CONNECTION(V8, "8B", 4)    

    CONNECTION("7A", 15, "8C", 3)
    CONNECTION("8D", 8, "8C", 4)
    CONNECTION(V8, "8C", 5)    

    CONNECTION("8A", 8, "9A", 3)
    CONNECTION("8A", 12, "9A", 2)
    CONNECTION("8A", 6, "9A", 1)
    CONNECTION("8B", 8, "9A", 6)
    CONNECTION("8B", 12, "9A", 5)
    CONNECTION("8B", 6, "9A", 4)
    CONNECTION("8C", 6, "9A", 12)
    CONNECTION(VCC, "9A", 11)





    /* Detection (Goal In) */
    CONNECTION("10D", 8, "C7", 1)
    
    CONNECTION("C7", 2, "15E", 10)
    CONNECTION(BALL, "15E", 9)

    CONNECTION("10C", 6, "13E", 13)

    CONNECTION("15B", 6, "14F", 9)
    CONNECTION(BALL, "14F", 11)
    CONNECTION("13E", 12, "14F", 10)

    CONNECTION("15E", 8, "15F", 14)
    CONNECTION("14F", 8, "15F", 15)

    CONNECTION("12B", 12, "13F", 12)
    CONNECTION("15B", 8, "13F", 13)

    CONNECTION("13F", 11, "13E", 11)

    CONNECTION("15F", 13, "14F", 5)
    CONNECTION(BALL, "14F", 4)
    CONNECTION("13E", 10, "14F", 3)

    CONNECTION("11A", 14, "13E", 3)

    CONNECTION("14F", 6, "13E", 5)

    CONNECTION("13E", 4, "15E", 5)
    CONNECTION("13E", 6, "15E", 4)

    CONNECTION("13E", 6, "15E", 2)
    CONNECTION("8H", 8, "15E", 1)

    CONNECTION("13E", 10, "13F", 5)
    CONNECTION("8J", 6, "13F", 4)

    CONNECTION("11E", 4, "15E", 12)
    CONNECTION(BALL, "15E", 13)

    CONNECTION("15E", 6, "15F", 1)
    CONNECTION("15E", 3, "15F", 2)
    CONNECTION("15E", 3, "15F", 3)

    CONNECTION("15E", 3, "15F", 11)
    CONNECTION("15E", 6, "15F", 12)
    CONNECTION("15E", 11, "15F", 10)

    CONNECTION("15F", 4, "13E", 9)

    


    /* Horizontal Speed */
    CONNECTION("15C", 11, "11D", 14)
    CONNECTION(GND, "11D", 2)
    CONNECTION(GND, "11D", 3)
    CONNECTION("11D", 12, "11D", 1)

    CONNECTION("11D", 8, "12D", 1)
    CONNECTION("11D", 9, "12D", 2)

    CONNECTION("11D", 9, "12C", 12)
    CONNECTION("11D", 8, "12C", 13)

    CONNECTION("12D", 3, "12D", 4)
    CONNECTION("12C", 11, "12D", 5)

    CONNECTION("12D", 6, "12D", 9)
    CONNECTION(VRESET, "12D", 10)

    CONNECTION(H256_n, "11E", 8)
    CONNECTION(VRESET, "11E", 9)

    CONNECTION(VRESET, "12D", 13)
    CONNECTION("12C", 11, "12D", 12)

    CONNECTION("12D", 8, "12E", 10)
    CONNECTION(A, "12E", 8)
    CONNECTION("11E", 10, "12E", 9)
    CONNECTION("11E", 13, "12E", 11)

    CONNECTION("12E", 5, "12E", 1)
    CONNECTION("11E", 10, "12E", 12)
    CONNECTION(GND, "12E", 4)
    CONNECTION("12D", 11, "12E", 13)

    CONNECTION("12E", 5, "10E", 4)
    CONNECTION("12E", 3, "10E", 5)
    
    CONNECTION("10E", 6, "12F", 1)

    CONNECTION("15F", 9, "11E", 12)
    CONNECTION("12F", 2, "11E", 11)

    CONNECTION("11E", 13, "10E", 2)
    CONNECTION("13D", 5, "10E", 1)

    CONNECTION("13D", 6, "10E", 12)
    CONNECTION("11E", 13, "10E", 13)

    CONNECTION("10E", 11, "10E", 10)
    CONNECTION("10E", 3, "10E", 9)





    /* Sound Generation */
    CONNECTION("C1", 2, "13G", 13)
    CONNECTION(BALL, "13G", 12)

    CONNECTION(VCC, "14G", 4)
    CONNECTION("13G", 11, "14G", 2)

    CONNECTION("10J", 13, "13E", 1)

    CONNECTION("10J", 13, "14A", 8)
    CONNECTION(VBLANK, "14A", 9)
    CONNECTION("13E", 2, "14A", 11)
    CONNECTION(VCC, "14A", 10)

    CONNECTION("14A", 5, "13G", 5)
    CONNECTION("10F", 14, "13G", 4)

    CONNECTION("15C", 11, "13G", 2)
    CONNECTION("9F", 11, "13G", 1)

    CONNECTION("9F", 12, "13G", 10)
    CONNECTION("14G", 3, "13G", 9)

    CONNECTION("13G", 6, "14F", 1)
    CONNECTION("13G", 3, "14F", 13)
    CONNECTION("13G", 8, "14F", 2)

    CONNECTION("14F", 12, "13F", 1)
    CONNECTION(GAME_ON, "13F", 2)

    CONNECTION("13F", 3, "AUDIO", 1)

    CONNECTION("AUDIO", i1, "AUDIO", Audio::OUTPUT_MONO)




	/* Score & Timer Blanking */
	CONNECTION(GND, "11A", 18)
	CONNECTION(GND, "11A", 19)
	CONNECTION("14J", 3, "11A", 20)
	CONNECTION("14H", 11, "11A", 21)
	CONNECTION("14H", 8, "11A", 22)
	CONNECTION("14H", 9, "11A", 23)
	
    CONNECTION(V128, "10C", 9)
    CONNECTION(V64, "10C", 10)
    CONNECTION(V32, "10C", 11)

    CONNECTION("11A", 6, "10D", 9)
    CONNECTION("11A", 11, "10D", 10)

    //CONNECTION("10D", 8, "13A", 11) // TODO: Should be connected to capacitor C7?
    CONNECTION("C7", 2, "13A", 11)

    CONNECTION(V16, "9G", 5)
    CONNECTION(V8_n, "9G", 4)

    CONNECTION("11A", 8, "11C", 13)
    CONNECTION("11A", 9, "11C", 12)

    CONNECTION(V128_n, "10C", 2)
    CONNECTION(V64_n, "10C", 1)
    CONNECTION(V32, "10C", 13)

    CONNECTION(HBLANK, "10B", 5)
    CONNECTION("10C", 8, "10B", 6)

    CONNECTION("10C", 8, "12B", 5)
    CONNECTION("13A", 10, "12B", 4)
    CONNECTION("9G", 6, "12B", 3)

    CONNECTION("9G", 6, "11B", 9)
    CONNECTION("11C", 11, "11B", 11)
    CONNECTION("10C", 12, "11B", 10)

    CONNECTION("12B", 6, "10D", 2)
    CONNECTION("9A", 8, "10D", 1)

    CONNECTION("9A", 8, "11C", 10)
    CONNECTION("11B", 8, "11C", 9)




    /* Score Storage */
    CONNECTION("15F", 9, "9E", 12)
    CONNECTION(GAME_ON, "9E", 13)

    CONNECTION("15F", 4, "8E", 11)
    CONNECTION("9E", 11, "8E", 12)

    CONNECTION("9E", 11, "8E", 3)
    CONNECTION("13E", 8, "8E", 2)
        
    CONNECTION("8E", 13, "6D", 1)
    CONNECTION(B, "6D", 2)
    CONNECTION(B, "6D", 3)
    CONNECTION(GND, "6D", 7)
    CONNECTION(GND, "6D", 6)

    CONNECTION("8E", 1, "6C", 1)
    CONNECTION(B, "6C", 2)
    CONNECTION(B, "6C", 3)
    CONNECTION(GND, "6C", 7)
    CONNECTION(GND, "6C", 6)

    CONNECTION("6D", 11, "6B", 14)
    CONNECTION(B, "6B", 2)
    CONNECTION(B, "6B", 3)
    CONNECTION(GND, "6B", 7)
    CONNECTION(GND, "6B", 6)
    CONNECTION("6B", 12, "6B", 1)

    CONNECTION("6C", 11, "6A", 14)
    CONNECTION(B, "6A", 2)
    CONNECTION(B, "6A", 3)
    CONNECTION(GND, "6A", 7)
    CONNECTION(GND, "6A", 6)
    CONNECTION("6A", 12, "6A", 1)

    CONNECTION("6D", 12, "5A", 1)
    CONNECTION("6C", 12, "5A", 14)
    CONNECTION("6B", 12, "5A", 2)
    CONNECTION("6A", 12, "5A", 15)
    CONNECTION("9C", 2, "5A", 12)
    CONNECTION("7D", 3, "5A", 4)
    CONNECTION("7B", 3, "5A", 3)
    CONNECTION(GND, "5A", 13)
    CONNECTION(H16, "5A", 11)
    CONNECTION(H32, "5A", 10)
    CONNECTION(H64, "5A", 9)
    CONNECTION(GND, "5A", 7)

    CONNECTION("6D", 9, "5B", 1)
    CONNECTION("6C", 9, "5B", 14)
    CONNECTION("6B", 9, "5B", 2)
    CONNECTION("6A", 9, "5B", 15)
    CONNECTION("7D", 2, "5B", 4)
    CONNECTION("7B", 2, "5B", 3)
    CONNECTION(GND, "5B", 12)
    CONNECTION(GND, "5B", 13)
    CONNECTION(H16, "5B", 11)
    CONNECTION(H32, "5B", 10)
    CONNECTION(H64, "5B", 9)
    CONNECTION(GND, "5B", 7)

    CONNECTION("6D", 8, "5C", 1)
    CONNECTION("6C", 8, "5C", 14)
    CONNECTION("6B", 8, "5C", 2)
    CONNECTION("6A", 8, "5C", 15)
    CONNECTION("7D", 6, "5C", 4)
    CONNECTION("7B", 6, "5C", 3)
    CONNECTION(GND, "5C", 12)
    CONNECTION(GND, "5C", 13)
    CONNECTION(H16, "5C", 11)
    CONNECTION(H32, "5C", 10)
    CONNECTION(H64, "5C", 9)
    CONNECTION(GND, "5C", 7)

    CONNECTION("6D", 11, "5D", 1)
    CONNECTION("6C", 11, "5D", 14)
    CONNECTION("6B", 11, "5D", 2)
    CONNECTION("6A", 11, "5D", 15)
    CONNECTION("7D", 7, "5D", 4)
    CONNECTION("7B", 7, "5D", 3)
    CONNECTION(GND, "5D", 12)
    CONNECTION(GND, "5D", 13)
    CONNECTION(H16, "5D", 11)
    CONNECTION(H32, "5D", 10)
    CONNECTION(H64, "5D", 9)
    CONNECTION(GND, "5D", 7)




    /* Timer Storage */
    CONNECTION(VCC, "9D", 4)

    CONNECTION("6E", 6, "8D", 1)
    CONNECTION("7E", 8, "8D", 13)
    CONNECTION("9D", 3, "8D", 2)

    CONNECTION(GND, "7B", 14)
    CONNECTION("8D", 12, "7B", 4)
    CONNECTION(VCC, "7B", 5)
    CONNECTION(GND, "7B", 1)
    CONNECTION(GND, "7B", 15)
    CONNECTION(GND, "7B", 10)
    CONNECTION(GND, "7B", 9)
    CONNECTION(A, "7B", 11)

    CONNECTION(GND, "7D", 14)
    CONNECTION("7B", 13, "7D", 4)
    CONNECTION(VCC, "7D", 5)
    CONNECTION(VCC, "7D", 1)
    CONNECTION(GND, "7D", 15)
    CONNECTION(GND, "7D", 10)
    CONNECTION(GND, "7D", 9)
    CONNECTION(A, "7D", 11)

    CONNECTION("7D", 13, "7E", 3)

    CONNECTION(VCC, "9C", 1)
    CONNECTION("7E", 4, "9C", 12)
    CONNECTION(VCC, "9C", 4)
    CONNECTION(A, "9C", 13)

    CONNECTION("7D", 3, "7C", 12)
    CONNECTION("7D", 2, "7C", 13)
    CONNECTION("7D", 6, "7C", 10)
    CONNECTION("7D", 7, "7C", 9)

    CONNECTION("7B", 3, "7C", 2)
    CONNECTION("7B", 2, "7C", 1)
    CONNECTION("7B", 6, "7C", 4)
    CONNECTION("7B", 7, "7C", 5)

    CONNECTION("9C", 3, "8C", 2)
    CONNECTION("7C", 8, "8C", 13)
    CONNECTION("7C", 6, "8C", 1)

    CONNECTION("8C", 12, "7E", 9)



    
    /* Game Starting */
    CONNECTION(VCC, "3B", 4)
    CONNECTION("COIN", 1, "3B", 2)

    CONNECTION("START", 1, "3E", 1)

    CONNECTION("3B", 3, "4B", 5) // Actually, transistor used to invert 3B.3

    CONNECTION(VCC, "3J", 10)
    CONNECTION(VCC, "3J", 12)
    CONNECTION("4B", 6, "3J", 11)
    CONNECTION("10B", 10, "3J", 13)

    CONNECTION(VCC, "3J", 4)
    CONNECTION("3J", 9, "3J", 2)
    CONNECTION("3E", 2, "3J", 3)
    CONNECTION("10B", 10, "3J", 1)

    CONNECTION("3J", 8, "3C", 9)
    CONNECTION("3J", 5, "3C", 8)

    CONNECTION(VCC, "4J", 4)
    CONNECTION("3C", 10, "4J", 2)
    CONNECTION("4B", 6, "4J", 3)
    CONNECTION("10B", 10, "4J", 1)

    CONNECTION("4J", 6, "4B", 1)



    CONNECTION(VCC, "12A", 4)
    CONNECTION("3J", 5, "12A", 2)

    CONNECTION("12A", 3, "12B", 9)
    CONNECTION("LATCH", 3, "12B", 11)
    CONNECTION("7E", 8, "12B", 10)

    CONNECTION("7E", 8, "10B", 9)
    CONNECTION("LATCH", 3, "10B", 8)

    CONNECTION("7E", 8, "13A", 13)

    CONNECTION(VCC, "13D", 10) // Not Shown
    CONNECTION("12B", 8, "13D", 12)
    CONNECTION("12B", 6, "13D", 11)
    CONNECTION("12B", 8, "13D", 13)

    CONNECTION("13D", 8, "10D", 4)
    CONNECTION("10B", 10, "10D", 5)

    CONNECTION("10D", 6, "6E", 5)
    
    CONNECTION("13A", 12, "LATCH", 1)
    CONNECTION("4B", 6, "LATCH", 2)

    CONNECTION("4B", 6, "13A", 3)




	/* Video Summing */	
    CONNECTION("10J", 1, "14C", 10)
    CONNECTION("13A", 8, "14C", 9)
    CONNECTION("12C", 3, "14C", 12)
    CONNECTION("11C", 8, "14C", 13)

    CONNECTION("14C", 8, "15D", 11)


	CONNECTION("VIDEO", 1, "10B", 4)
    CONNECTION("VIDEO", 2, "13B", 4)
    CONNECTION("VIDEO", 3, "10D", 3)
    CONNECTION("VIDEO", 4, "15D", 10)

    CONNECTION("VIDEO", Video::HBLANK_PIN, HBLANK)
    CONNECTION("VIDEO", Video::VBLANK_PIN, VBLANK)


#ifdef DEBUG
    CONNECTION("LOG1", 1, "13C", 8)
    CONNECTION("LOG1", 2, "C6", 2)
    CONNECTION("LOG1", 3, "12C", 8)
    CONNECTION("LOG1", 4, "12C", 6)
    CONNECTION("LOG1", 5, "13C", 11)
    CONNECTION("LOG1", 6, "13C", 3)
    CONNECTION("LOG1", 7, "15C", 3)    
    CONNECTION("LOG1", 8, VBLANK)    
    CONNECTION("LOG1", 9, "13C", 6)    
    CONNECTION("LOG1", 10, "10J", 1)    
    CONNECTION("LOG1", 11, "14E", 10)    
    CONNECTION("LOG1", 12, "C3", 2)    
#endif


CIRCUIT_LAYOUT_END

