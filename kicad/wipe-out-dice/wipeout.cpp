/* Leader by Midway was licensed from Ramtek in 1973
   Ramtek released it as Wipe Out in 1974      */

//Schematics - Revision D, DWG NO 500945

//Last update 12/12/2013


#include "../circuit_desc.h"
#include "wipeout.h"

#define DEBUG
#undef DEBUG

#ifdef DEBUG
static VcdLogDesc vcd_log_desc
(
    "output_wipeout.vcd",
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


static RomDesc d4_desc("wipeout", "wipeout.d4", 0x205BF9A1);    
static RomDesc g7_desc("wipeout", "wipeout.g7", 0x215437E1);

static CapacitorDesc cap32_desc(U_FARAD(0.002));

static WipeoutPaddleDesc wipeout_pad1_desc(K_OHM(2.5), U_FARAD(6.8));
static WipeoutPaddleDesc wipeout_pad2_desc(K_OHM(2.5), P_FARAD(393.0));
static WipeoutPaddleDesc wipeout_pad3_desc(K_OHM(2.5), U_FARAD(6.8));
static WipeoutPaddleDesc wipeout_pad4_desc(K_OHM(2.5), P_FARAD(393.0));

static Paddle1VerticalDesc pad1_desc(K_OHM(0.0), K_OHM(6.0), &wipeout_pad1_desc);
static Paddle3VerticalDesc pad3_desc(K_OHM(0.0), K_OHM(6.0), &wipeout_pad3_desc);
static Paddle2HorizontalDesc pad2_desc(K_OHM(0.0), K_OHM(400.0), &wipeout_pad2_desc);
static Paddle4HorizontalDesc pad4_desc(K_OHM(0.0), K_OHM(400.0), &wipeout_pad4_desc);


static DipswitchDesc swmiss57_desc("misses", "dice_dipswitch_1", "Starting Score", 0, "5", "7");

static MixerDesc mixer_desc({OHM(220.0)}, 0, 0, U_FARAD(0.1)); 

static INPUT_DESC( wipeout )
    INPUT_INFO(PADDLE1_VERTICAL_INPUT, "Move Left Paddle")
    INPUT_INFO(PADDLE2_HORIZONTAL_INPUT, "Move Top Paddle")    
    INPUT_INFO(PADDLE3_VERTICAL_INPUT, "Move Right Paddle")
    INPUT_INFO(PADDLE4_HORIZONTAL_INPUT, "Move Bottom Paddle")
    INPUT_INFO(COIN_INPUT, {{ 1 }}, "Insert Coin")
    INPUT_INFO(START_INPUT, {{ 1 }}, "Start Game")
INPUT_DESC_END

static VIDEO_DESC( wipeout )
    VIDEO_RESISTANCE(1, K_OHM(2.2))
    VIDEO_CONTRAST(2.0)
    VIDEO_RETRO_V_SIZE(225)
VIDEO_DESC_END

static AUDIO_DESC( wipeout )
    AUDIO_GAIN(80.0)
    AUDIO_SPEAKER_CONFIG(MONO) 
AUDIO_DESC_END

CIRCUIT_LAYOUT( wipeout )
/* * * CHIPS * * */

//note all 7421 are actually 74H21 on diagram

CHIP("CRYSTAL", CLOCK_10_733_MHZ)  //0A
CHIP("0B",  7404)    //unused out 2 4 6 8 (clock and T999) 
CHIP("0C",  74S112)  //unused out 6
CHIP("0D",  7437)    
CHIP("0E",  7486)    
CHIP("0F",  7402)    
CHIP("0G",  74S112)
CHIP("0H",  7402)    //unused 2;3->1 
CHIP("0J",  7420)    

CHIP("1A",  74161)   //unused out 12 13
CHIP("1B",  74161)
CHIP("1C",  74S112)
CHIP("1D",  7400)    
CHIP("1E",  7427)    
CHIP("1F",  7400)    
CHIP("1G",  7408)    
CHIP("1H",  7402)    
CHIP("1J",  7427)    
//CHIP("1K",  7405)

CHIP("2A",  74161)   //unused out 13
CHIP("2B",  74161)
CHIP("2C",  7404)    
CHIP("2D",  7400)    
CHIP("2E",  7421)    
CHIP("2F",  7421)    
CHIP("2G",  7408)    
CHIP("2H",  7404)    //unused out 10 (sync)    
CHIP("2J",  7408)    
CHIP("2K",  74S112)
CHIP("2M",  7402)    

CHIP("3A",  74161)   //unused out 11
CHIP("3B",  74161)   //unused out 11
CHIP("3C",  74161)   //unused out 11
CHIP("3D",  74161)   //unused out 11
CHIP("3E",  74161)   //unused out 14 15
CHIP("3F",  7427)    
CHIP("3G",  7420)    
CHIP("3H",  7486)    
CHIP("3J",  7402)    

CHIP("4A",  74153)
CHIP("4B",  74153)
CHIP("4C",  7404)    //unused out 12 (N999)    
CHIP("4D",  82S123, &d4_desc)  //I5610 unused out 1 2 character generator ROM
CHIP("4E",  74166)
CHIP("4F",  7427)    
CHIP("4G",  7402)     
CHIP("4H",  7400)    
CHIP("4J",  7427)    

CHIP("5A",  74174)
CHIP("5B",  74153)
CHIP("5C",  74153)
CHIP("5D",  7421)    
CHIP("5E",  7400)    
CHIP("5F",  7427)    
CHIP("5G",  74174)
CHIP("5H",  74S112)  //unused out 9 (lamp)
CHIP("5J",  74S112)
//CHIP("5K",  75453)

CHIP("6A",  7404)    
CHIP("6B",  7400)    
CHIP("6C",  7404)    
CHIP("6D",  74161)   //unused out 14
CHIP("6E",  74161)   //unused out 14
CHIP("6F",  74161)   //unused out 14
CHIP("6G",  74161)   //unused out 14
CHIP("6H",  7402)    
CHIP("6J",  74S112)

CHIP("7A",  7420)    
CHIP("7B",  74S112)
CHIP("7C",  74161)   //unused out 14 13 11
CHIP("7D",  74161)   //unused out 14 13 12 11
CHIP("7E",  74161)   //unused out 14 13 12 11
CHIP("7F",  74157)   //unused out 12
CHIP("7G",  82S123, &g7_desc) //I5610 ball movement ROM
CHIP("7H",  74157)
CHIP("7J",  74161)   //unused out 11 14 15
CHIP("7K",  74S112)

CHIP("8A",  7404)    //unused out 2 (B999)  
CHIP("8B",  74174)
CHIP("8C",  74174)
CHIP("8D",  74161)   //unused out 14 13 12 11
CHIP("8E",  74161)   //unused out 14 13 12 11
CHIP("8F",  74S112)
CHIP("8G",  7400)    
CHIP("8H",  74157)
CHIP("8J",  74174)   //unused out 15 (VDSC sync)
//CHIP("8K",  7405)

CHIP("9A",  7400)    
CHIP("9B",  7420)    
CHIP("9C",  7420)    
CHIP("9D",  7402)    
CHIP("9E",  7402)    
CHIP("9F",  7400)    
CHIP("9G",  7400)    
CHIP("9H",  7400)    
CHIP("9J",  7400)    

CHIP("CAP32", CAPACITOR, &cap32_desc)


//inputs
CHIP("COIN_IN",   COIN_INPUT)
CHIP("START_IN",  START_INPUT)

CHIP("PADDLE1", WIPEOUT_PADDLE, &wipeout_pad1_desc)
CHIP("PADDLE2", WIPEOUT_PADDLE, &wipeout_pad2_desc)
CHIP("PADDLE3", WIPEOUT_PADDLE, &wipeout_pad3_desc)
CHIP("PADDLE4", WIPEOUT_PADDLE, &wipeout_pad4_desc)

CHIP("PAD1", PADDLE1_VERTICAL_INPUT, &pad1_desc)
PADDLE_CONNECTION("PAD1", "PADDLE1")

CHIP("PAD3", PADDLE3_VERTICAL_INPUT, &pad3_desc)
PADDLE_CONNECTION("PAD3", "PADDLE3")
    
CHIP("PAD2", PADDLE2_HORIZONTAL_INPUT, &pad2_desc)
PADDLE_CONNECTION("PAD2", "PADDLE2")
    
CHIP("PAD4", PADDLE4_HORIZONTAL_INPUT, &pad4_desc)
PADDLE_CONNECTION("PAD4", "PADDLE4")

CHIP("MIXER", MIXER, &mixer_desc)

// dip switches
CHIP("SWMISS57",         DIPSWITCH, &swmiss57_desc)

//outputs
#ifdef DEBUG
	CHIP("LOG1", VCD_LOG, &vcd_log_desc)
#endif
	
VIDEO(wipeout)
AUDIO(wipeout)
INPUT(wipeout)

/* * * signals * * */

/* PAGE 1 */

  //POWER
#define _T999   VCC

  //CLOCK
#define _1TQ05  "0C", 5
#define _6TQ05  "0D", 3  
#define _2TQ05  "0D", 6  
#define _THSC   "0C", 9  //HSYNC 
#define _5THSC  "0C", 7  //HSYNC
#define _6THSC  "0D", 8
#define _2THSC  "0D", 11
#define _TCSC   "1F", 8  //COMP SYNC

  //Timing/Syncing/Blanking
#define _TECA   "1A", 15
#define _TEC0   "1A", 14
#define _TEC3   "1A", 11
#define _TEC4   "1B", 14
#define _TEC5   "1B", 13
#define _TEC6   "1B", 12
#define _TEC7   "1B", 11
#define _TECB   "1B", 15
#define _5TEC0  "2C", 2
#define _5TEC5  "2C", 4
#define _5TECC  "1D", 3
#define _1TECC  "0B", 10
#define _TEC8   "1C", 5
#define _5TEC8  "1C", 6
#define _5TECD  "1D", 6
#define _5TEG7  "1D", 8
#define _5TEG8  "1D", 11
#define _1TEG7  "2C", 8

#define _TLCA   "2A", 15 
#define _TLC0   "2A", 14
#define _TLC2   "2A", 12
#define _TLC3   "2A", 11
#define _TLC4   "2B", 14
#define _TLC5   "2B", 13
#define _TLC6   "2B", 12
#define _TLC7   "2B", 11
#define _TLCB   "2B", 15
#define _5TLC0  "2C", 6
#define _5TLCC  "2D", 3
#define _1TLCC  "0B", 12
#define _TLC8   "1C", 9
#define _5TLC8  "1C", 7
#define _5TLCD  "2D", 6
#define _5TLG8  "2D", 11
#define _5TVSC  "3G", 6   //VERT SYNC
#define _5TLG7  "2D", 8
#define _1TLG7  "2C", 10

#define _5TCBL  "0H", 13  //COMP BLANKING

  // T/B goal gate
#define _TE76   "0E", 3
#define _TE75   "0E", 6
#define _TELG   "1E", 6
#define _5TELA  "1F", 3
#define _TEVL   "0F", 1  
#define _THBG   "0G", 5
#define _5THBG  "0G", 6
#define _THBL   "0F", 10  //HORIZ BLANKING
#define _THYZ   "2M", 1

  // L/R goal gate
#define _TL76   "0E", 8
#define _TL75   "0E", 11
#define _TLLG   "1E", 8
#define _5TLLG  "2H", 2
#define _5TLLA  "1F", 6
#define _TLHL   "0F", 4
#define _TVBG   "0G", 9
#define _5TVBG  "0G", 7
#define _TVBL   "0F", 13  //VERT BLANKING
#define _TVYZ   "2M", 4

  // H/V cross gen
#define _TEKG   "1G", 3
#define _THCL   "2E", 6
#define _TLKG   "1G", 6
#define _1TCKG  "6A", 2
#define _TVCL   "2E", 8
#define _5TCKG  "CAP32", 2
#define _THCH   "2G", 3
#define _TPVR   "2G", 6
#define _TVCH   "2G", 8
#define _TPHR   "2G", 11

  //determine 2/4 players
#define _TPSA   "1G", 8
#define _TPSB   "1G", 11
#define _5TPSC  "1E", 12
#define _1TPSC  "2H", 4  //2 OR 4 PLAYER PAD

  //score enable
#define _TNSA   "0H", 4
#define _TNSB   "0H", 10
#define _5TNSC  "3J", 1
#define _1TNSC  "2H", 6  //SCORE ENABLE

  // H/V paddle
#define _TPHS   "2F", 6  //HORIZ PADDLE
#define _TPVS   "2F", 8  //VERT PADDLE

  // L/R select
#define _TE43   "3H", 3
#define _5TGLG  "1J", 6
#define _5TGRG  "1J", 8
#define _5TVPG  "0J", 6
#define _TVLG   "1H", 1
#define _TVPD   "1H", 10  //L/R PADDLE SELECT
#define _TVLN   "2J", 3   //L/R LINE SELECT

  // T/B select
#define _TL43   "3H", 6
#define _5TGTG  "1J", 12
#define _5TGBG  "4J", 6
#define _5THPG  "0J", 8
#define _THLG   "1H", 4
#define _THPD   "1H", 13  //T/B PADDLE SELECT
#define _THLN   "2J", 6   //T/B LINE SELECT

  // counters
#define _NCLA   "3F", 6
#define _NCL0   "3A", 14
#define _NCL1   "3A", 13
#define _NCL2   "3A", 12
#define _NCLC   "3A", 15

#define _NCRA   "3F", 8
#define _NCR0   "3C", 14
#define _NCR1   "3C", 13
#define _NCR2   "3C", 12
#define _NCRC   "3C", 15

#define _NCTA   "3F", 12
#define _NCT0   "3B", 14
#define _NCT1   "3B", 13
#define _NCT2   "3B", 12
#define _NCTC   "3B", 15

#define _NCBA   "4F", 6
#define _NCB0   "3D", 14
#define _NCB1   "3D", 13
#define _NCB2   "3D", 12
#define _NCBC   "3D", 15

//END OF GAME
#define _5NCFA  "4J", 8
#define _5NCFB  "4H", 6
#define _NCFC   "3J", 10

//PLAYER 1
#define _5NCFG  "3J", 4
#define _1NCFG  "2H", 8

//PLAYER 2
#define _5NCAD  "4J", 12
#define _5NCFE  "4H", 8
#define _NCFF   "3J", 13

//number generation
#define _NCS2   "4A", 7
#define _NCS1   "4A", 9
#define _NCS0   "4B", 7
#define _NCSC   "4B", 9
#define _5NCS2  "4C", 2
#define _5NCS1  "4C", 4
#define _5NCS0  "4C", 6
#define _5NCG3  "4C", 8
#define _5NCG2  "4C", 10
#define _N999   VCC   //"4C", 12
#define _NCG7   "4D", 9
#define _NCG6   "4D", 7
#define _NCG5   "4D", 6
#define _NCG4   "4D", 5
#define _NCG3   "4D", 4
#define _NCG2   "4D", 3
#define _5NCGA  "4H", 3
#define _NCH7   "5D", 6
#define _NCH6   "5D", 8
#define _NCCE   "4G", 1
#define _5NCCE  "2C", 12
#define _NCC1   "3E", 13
#define _NCC2   "3E", 12
#define _NCC3   "3E", 11
#define _5NCCC  "1F", 11
#define _NCVD   "4E", 13


/* Page 2 */

//RECLOCK PADDLE POS & INTERSECT

#define _PKE8   "5G", 2
#define _PKL8   "5G", 5
#define _PKE5   "5G", 7
#define _PKL5   "5G", 10
#define _KABC   "5G", 12
#define _KABD   "5G", 15
#define _5PKE8  "6C", 2
#define _5PKL8  "6C", 4
#define _5PKE5  "6C", 6
#define _5PKL5  "6C", 8

//LEFT PADDLE POSITION
#define _PCLB   "2K", 5
#define _5PCLB  "2K", 6
#define _PCLE   "4F", 8
#define _PCL1   "6E", 13
#define _PCL2   "6E", 12
#define _PCL3   "6E", 11
#define _PCLC   "6E", 15

//RIGHT PADDLE POSITION
#define _PCRB   "2K", 9
#define _5PCRB  "2K", 7
#define _PCRE   "5F", 6
#define _PCR1   "6F", 13
#define _PCR2   "6F", 12
#define _PCR3   "6F", 11
#define _PCRC   "6F", 15

//TOP PADDLE POSITION
#define _PCTB   "7K", 5
#define _5PCTB  "7K", 6
#define _PCTE   "5F", 8
#define _PCT1   "6G", 13
#define _PCT2   "6G", 12
#define _PCT3   "6G", 11
#define _PCTC   "6G", 15

//BOTTOM PADDLE POSITION
#define _PCBB   "7K", 9
#define _5PCBB  "7K", 7
#define _PCBE   "5F", 12
#define _PCB1   "6D", 13
#define _PCB2   "6D", 12
#define _PCB3   "6D", 11
#define _PCBC   "6D", 15

//2 PLAYER PADDLE MULTIPLEXER
#define _PCSE   "5C", 7
#define _PCS3   "5C", 9
#define _PCS2   "5B", 7
#define _PCS1   "5B", 9
#define _5PJC1  "6A", 4
#define _5PCX3  "2M", 10
#define _1PCX3  "6B", 11

//REBOUND CONTROL
#define _PDPS   "5A", 2
#define _PDS3   "5A", 5
#define _PDS2   "5A", 7
#define _PDS1   "5A", 10
#define _PJC0   "5A", 12
#define _PJC1   "5A", 15
#define _5PDPS  "6C", 10
#define _5PCS3  "6C", 12

//DIRECTION CHANGE
#define _PDGS   "6J", 5
#define _5PDGS  "6J", 6
#define _5PDLC  "5E", 6
#define _5PDEC  "5E", 8

//GAME FLAG
#define _PGSC   "5H", 5
#define _5PGSC  "5H", 6
#define _5PGSR  "5E", 11

// 2/4 PLAYER INDICATOR
#define _5PGSB  "5E", 3
#define _1PGSB  "6A", 6

//COIN COUNT
#define _PGCC   "5J", 5
#define _5PGCC  "5J", 6

// 2 PLAYERS DETECT
#define _PGCD   "4G", 4
#define _PGCE   "5J", 9
#define _5PGCE  "5J", 7

// 4 PLAYERS DETECT
#define _PGCF   "6H", 1
#define _PGCH   "6H", 4
#define _PGCG   "5H", 9
#define _5PGCG  "5H", 7


/* Page 3 */

//POWER
#define _B999   VCC  //PULL UP

//REBOUND DIRECTION CONTROL
#define _5BDSR  "8G", 3
#define _5BDSL  "8G", 6
#define _BDRR   "8F", 5
#define _5BDRR  "8F", 6
#define _5BDGR  "9J", 3
#define _5BDSD  "8G", 8
#define _5BDSU  "8G", 11
#define _BDRD   "8F", 9
#define _5BDRD  "8F", 7
#define _5BDGD  "9J", 8
#define _BGS3   "9J", 6

//BALL SPEED
#define _BSC2   "7J", 14
#define _BSC3   "7J", 13
#define _BSC4   "7J", 12
#define _5BSCG  "9H", 3
#define _BSCD   "9E", 1

// L/R T/B SELECTOR
#define _BDEC   "8H", 4
#define _5BDEC  "8H", 7
#define _BDLC   "8H", 9
#define _5BDLC  "8H", 12

//VELOCITY GEN FROM REBOUND ADDRESS
#define _BXYZ   "9H", 11
#define _BGS2   "7F", 4
#define _BGS1   "7F", 7
#define _BGS0   "7F", 9

//BASIC CONTROL OF BALL MOVEMENT
#define _BPE3   "7G", 9
#define _BPE2   "7G", 7
#define _BPE1   "7G", 6
#define _BPE0   "7G", 5
#define _BPL3   "7G", 4
#define _BPL2   "7G", 3
#define _BPL1   "7G", 2
#define _BPL0   "7G", 1

//HORIZ & VERT BALL MOVEMENT MULTIPLEXER
#define _BPSV   "3H", 8
#define _BPSC   "3H", 11
#define _BPS3   "7H", 4
#define _BPS2   "7H", 7
#define _BPS1   "7H", 9
#define _BPS0   "7H", 12

//INTERCEPT DIRECTION DEFINITION
#define _5KBCH  "6H", 10
#define _KACA   "9H", 6
#define _5KBDG  "6H", 13
#define _KACB   "9H", 8

//INTERSECT CLOCK
#define _2KQEA  "9D", 1

//BOUNDERY INTERSECT
#define _KACE   "9F", 6

//PADDLE OR CROSS INTERSECT
#define _KACF   "9F", 11

//SCORE
#define _KXYA   "9E", 13
#define _5KACG  "9G", 8
#define _5KACH  "9G", 11
#define _KADG   "9F", 3

//ball intercepts vert pad & horz cross
#define _5KAAA  "4G", 10
#define _KAAC   "9E", 4  

//ball intercepts vert cross & horz pad
#define _5KAAB  "4G", 13
#define _KAAD   "9E", 10  


//INTERCEPT
#define _5KAAE  "9G", 3  //ball intercept vert line
#define _5KAAF  "9G", 6  //ball intercept horiz line
#define _KAAG   "2J", 8  //ball intercept top & bottom scoring regions
#define _KAAH   "2J", 11 //ball intercept left & right scoring regions

//RECLOCK
#define _5KABE  "8J", 2
#define _5KABF  "8J", 5
#define _KABG   "8J", 7
#define _KABH   "8J", 10
#define _5VDAF  "8J", 12
#define _VDSC   "8J", 15

#define _5KABC  "6A", 8
#define _5KABD  "6A", 10

//
#define _6KQCA  "9F", 8
#define _2KQLN  "9D", 4
#define _2KQEL  "9D", 10
#define _7KQPD  "9D", 13
#define _KAYA   "2M", 13

//COMPOSITE VIDEO
#define _5VDAC  "4F", 12
#define _VDAD   "3G", 8
#define _5VDAE  "4H", 11

#define _5VDS0  "2H", 10
#define _1VDAF  "2H", 12

//BALL GENERATION AND CONTROL
  //horiz
#define _5BECL  "9C", 6
#define _BECA   "7E", 15
#define _BECB   "7D", 15
#define _5BECB  "8A", 4
#define _5BEGA  "8C", 2
#define _5BEGB  "8C", 5
#define _5BEGC  "8C", 7
#define _5BEGD  "8C", 10
#define _PGCB   "8C", 12
#define _1PGCC  "8C", 15
#define _1BEGD  "8A", 8
  //vert
#define _5BLCL  "9A", 3
#define _BLCA   "8E", 15
#define _BLCB   "8D", 15
#define _5BLCB  "8A", 6
#define _5BLGA  "8B", 2
#define _5BLGB  "8B", 5
#define _5BLGC  "8B", 7
#define _5BLGD  "8B", 10
#define _1BLGE  "8B", 12
#define _1EBCA  "8B", 15
#define _1BLGD  "8A", 10
  //ball gen & shaping
#define _BVAA   "9A", 6
#define _BVAB   "9A", 8
#define _5BVAD  "9A", 11
#define _BVAC   "9B", 6
#define _BVAE   "9B", 8
#define _5BVAF  "9C", 8
#define _1BVAF  "8A", 12

//BALL HITS
  //ball hits paddle & cross
#define _EBIP   "7B", 5
#define _5EBIP  "7B", 6
  //ball hits boundry
#define _EBOP   "6J", 9
#define _5EBOP  "6J", 7
  //ball hits score
#define _EBUZ   "7B", 9
#define _5EBUZ  "7B", 7

//AUDIO
#define _5EBEA  "6B", 3
#define _5EBEB  "6B", 6
#define _5EBEC  "6B", 8
#define _EBEL   "7A", 6

//INTERSECT
#define _EBCA   "7A", 8
#define _5EBCA  "6A", 12

//AUDIO DURATION COUNTER
#define _EBC2   "7C", 12
#define _EBCC   "7C", 15


//INPUTS

  //PADDLE IN
//#define _9XCLA //player 1 IN (LEFT)
//#define _9XCRA //player 3 IN (RIGHT)
//#define _9XCTA //player 2 IN (TOP)
//#define _9XCBA //player 4 IN (BOTTOM)

#define _5PCLA "PADDLE1", 2
#define _5PCRA "PADDLE3", 2
#define _5PCTA "PADDLE2", 2
#define _5PCBA "PADDLE4", 2

  //POWER RELAY IN
#define _9XPRS  VCC  

  //START GAME IN
//#define _4XCST "START_IN", i1 //pressed=HIGH, unpressed=LOW
#define _PGSA  "START_IN", i1 //pressed=HIGH, unpressed=LOW

  //COINT CTR IN
//#define _4XGCA "COIN_IN", i1  //coin=HIGH, normally=LOW
#define _PGCA  "COIN_IN", i1  //coin=HIGH, normally=LOW

  //5-7 GAME SELECT
#define _9X7PT  "SWMISS57", 3 //LO=5 misses, HI=7 misses


/* * * CONNECTIONS * * */

/* PAGE 1 */

//Clock (top, left)

CONNECTION(_T999,          "0C", 4)
CONNECTION(_T999,          "0C", 3)
CONNECTION("CRYSTAL", 1,   "0C", 1)
CONNECTION(_T999,          "0C", 2)
CONNECTION(_T999,          "0C", 15)

CONNECTION(_1TQ05,         "0D", 2)
CONNECTION(_1TQ05,         "0D", 1)

CONNECTION(_6TQ05,         "0D", 5)
CONNECTION(_6TQ05,         "0D", 4)

CONNECTION(_T999,          "0C", 10)
CONNECTION(_5TEC5,         "0C", 11)
CONNECTION(_2TQ05,         "0C", 13)
CONNECTION(_TEC5,          "0C", 12)
CONNECTION(_TEC8,          "0C", 14)

CONNECTION(_THSC,          "0D", 9)
CONNECTION(_THSC,          "0D", 10)

CONNECTION(_6THSC,         "0D", 12)
CONNECTION(_6THSC,         "0D", 13)

CONNECTION(_5THSC,         "1F", 9)
CONNECTION(_5TVSC,         "1F", 10)

//Basic timing & sync & blanking

  //horiz count
CONNECTION(_T999,          "1A", 1)
CONNECTION(_5TECC,         "1A", 9)
CONNECTION(GND,            "1A", 3)
CONNECTION(GND,            "1A", 4)
CONNECTION(GND,            "1A", 5)
CONNECTION(_T999,          "1A", 6)
CONNECTION(_T999,          "1A", 7)
CONNECTION(_T999,          "1A", 10)
CONNECTION(_6TQ05,         "1A", 2)

CONNECTION(_T999,          "1B", 1)
CONNECTION(_5TECC,         "1B", 9)
CONNECTION(_5TEC8,         "1B", 3)
CONNECTION(_5TEC8,         "1B", 4)
CONNECTION(GND,            "1B", 5)
CONNECTION(_5TEC8,         "1B", 6)
CONNECTION(_TECA,          "1B", 7)
CONNECTION(_TEC3,          "1B", 10)
CONNECTION(_6TQ05,         "1B", 2)

CONNECTION(_TEC0,          "2C", 1)

CONNECTION(_TEC5,          "2C", 3)

CONNECTION(_TECB,          "1D", 2)
CONNECTION(_TECA,          "1D", 1)

CONNECTION(_5TECC,         "0B", 11)

CONNECTION(_T999,          "1C", 4)
CONNECTION(_1TECC,         "1C", 3)
CONNECTION(_2TQ05,         "1C", 1)
CONNECTION(_1TECC,         "1C", 2)
CONNECTION(_T999,          "1C", 15)

CONNECTION(_TECB,          "1D", 5)
CONNECTION(_TEC8,          "1D", 4)

CONNECTION(_TEC7,          "1D", 9)
CONNECTION(_5TECD,         "1D", 10)

CONNECTION(_5TEG7,         "2C", 9)

CONNECTION(_5TECD,         "1D", 12)
CONNECTION(_TEC8,          "1D", 13)

  //vert count
CONNECTION(_T999,          "2A", 1)
CONNECTION(_5TLCC,         "2A", 9)
CONNECTION(GND,            "2A", 3)
CONNECTION(GND,            "2A", 4)
CONNECTION(GND,            "2A", 5)
CONNECTION(_TLC8,          "2A", 6)
CONNECTION(_T999,          "2A", 7)
CONNECTION(_T999,          "2A", 10)
CONNECTION(_6THSC,         "2A", 2)

CONNECTION(_T999,          "2B", 1)
CONNECTION(_5TLCC,         "2B", 9)
CONNECTION(GND,            "2B", 3)
CONNECTION(_5TLC8,         "2B", 4)
CONNECTION(_5TLC8,         "2B", 5)
CONNECTION(_5TLC8,         "2B", 6)
CONNECTION(_TLCA,          "2B", 7)
CONNECTION(_TLC3,          "2B", 10)
CONNECTION(_6THSC,         "2B", 2)

CONNECTION(_TLC0,          "2C", 5)

CONNECTION(_TLCB,          "2D", 2)
CONNECTION(_TLCA,          "2D", 1)

CONNECTION(_5TLCC,         "0B", 13)

CONNECTION(_T999,          "1C", 10)
CONNECTION(_1TLCC,         "1C", 11)
CONNECTION(_2THSC,         "1C", 13)
CONNECTION(_1TLCC,         "1C", 12)
CONNECTION(_T999,          "1C", 14)

CONNECTION(_5TLC8,         "3G", 5)
CONNECTION(_5TLC8,         "3G", 4)
CONNECTION(_TLCB,          "3G", 2)
CONNECTION(_TLC2,          "3G", 1)  //vert sync

CONNECTION(_TLC8,          "2D", 5)
CONNECTION(_TLCB,          "2D", 4)

CONNECTION(_5TLCD,         "2D", 12)
CONNECTION(_TLC8,          "2D", 13)

CONNECTION(_TLC7,          "2D", 9)
CONNECTION(_5TLCD,         "2D", 10)  

CONNECTION(_5TLG7,         "2C", 11)


  //comp blanking
CONNECTION(_THBL,          "0H", 12)
CONNECTION(_TVBL,          "0H", 11) 


// T/B GOAL GATE (bottom, left)

CONNECTION(_TEC7,          "0E", 2)
CONNECTION(_TEC6,          "0E", 1) 

CONNECTION(_TEC7,          "0E", 5)
CONNECTION(_TEC5,          "0E", 4) 

CONNECTION(_TE76,          "1E", 5)
CONNECTION(_TEC8,          "1E", 4) 
CONNECTION(_TE75,          "1E", 3) 

CONNECTION(_TECA,          "1F", 2)
CONNECTION(_TELG,          "1F", 1) 

CONNECTION(_TEC4,          "0F", 2)
CONNECTION(_5TELA,         "0F", 3) 

CONNECTION(_T999,          "0G", 4)
CONNECTION(_TEVL,          "0G", 3)
CONNECTION(_2TQ05,         "0G", 1)
CONNECTION(_TEVL,          "0G", 2) 
CONNECTION(_5TEC8,         "0G", 15)

CONNECTION(_TEVL,          "0F", 9)
CONNECTION(_THBG,          "0F", 8) 

CONNECTION(_5THBG,         "2M", 2) 
CONNECTION(_PGSC,          "2M", 3) 


// L/R GOAL GATE (bottom, left)

CONNECTION(_TLC7,          "0E", 9)
CONNECTION(_TLC6,          "0E", 10) 

CONNECTION(_TLC7,          "0E", 12)
CONNECTION(_TLC5,          "0E", 13)

CONNECTION(_TL76,          "1E", 9)
CONNECTION(_TLC8,          "1E", 10) 
CONNECTION(_TL75,          "1E", 11)

CONNECTION(_TLLG,          "2H", 1)

CONNECTION(_TLCA,          "1F", 5)
CONNECTION(_TLLG,          "1F", 4) 

CONNECTION(_TLC4,          "0F", 5) 
CONNECTION(_5TLLA,         "0F", 6) 

CONNECTION(_T999,          "0G", 10)
CONNECTION(_TLHL,          "0G", 11)
CONNECTION(_2THSC,         "0G", 13)
CONNECTION(_TLHL,          "0G", 12) 
CONNECTION(_5TLC8,         "0G", 14)

CONNECTION(_TLHL,          "0F", 12)
CONNECTION(_TVBG,          "0F", 11) 

CONNECTION(_5TVBG,         "2M", 5) 
CONNECTION(_PGSC,          "2M", 6)


// HORIZ CROSS GEN (bottom, left)

CONNECTION(_TE76,          "1G", 2) 
CONNECTION(_TE75,          "1G", 1)

CONNECTION(_TLKG,          "9J", 12) 
CONNECTION(_TEKG,          "9J", 13)

CONNECTION("9J", 11,       "CAP32", 1) 

CONNECTION(_5TCKG,         "6A", 1)

CONNECTION(_TLC6,          "2E", 5) 
CONNECTION(_TLC5,          "2E", 4)
CONNECTION(_TLC4,          "2E", 2) 
CONNECTION(_TLCA,          "2E", 1)

CONNECTION(_TEKG,          "2G", 2) 
CONNECTION(_THCL,          "2G", 1)

CONNECTION(_THCL,          "2G", 5) 
CONNECTION(_TVYZ,          "2G", 4)


// VERT CROSS GEN (bottom, left)

CONNECTION(_TL76,          "1G", 5) 
CONNECTION(_TL75,          "1G", 4)

CONNECTION(_TEC6,          "2E", 9) 
CONNECTION(_TEC5,          "2E", 10)
CONNECTION(_TEC4,          "2E", 13) 
CONNECTION(_TECA,          "2E", 12)

CONNECTION(_TLKG,          "2G", 9) 
CONNECTION(_TVCL,          "2G", 10)

CONNECTION(_TVCL,          "2G", 12) 
CONNECTION(_THYZ,          "2G", 13)


// DETERMINE 2 OR 4 PLAYERS PAD (bottom, left)

CONNECTION(_TELG,          "1G", 9) 
CONNECTION(_5TEG7,         "1G", 10)

CONNECTION(_TLLG,          "1G", 12) 
CONNECTION(_5TLG7,         "1G", 13)

CONNECTION(_TPSA,          "1E", 13) 
CONNECTION(_5PGCG,         "1E", 2)
CONNECTION(_TPSB,          "1E", 1) 

CONNECTION(_5TPSC,         "2H", 3) 


// SCORE ENABLE (bottom, left)

CONNECTION(_TEKG,          "0H", 5) 
CONNECTION(_1TEG7,         "0H", 6)

CONNECTION(_TLKG,          "0H", 9) 
CONNECTION(_1TLG7,         "0H", 8)

CONNECTION(_TNSA,          "3J", 2) 
CONNECTION(_TNSB,          "3J", 3) 

CONNECTION(_5TNSC,         "2H", 5) 


// H/V PADDLE (bottom, left)

CONNECTION(_1TEG7,         "2F", 5) 
CONNECTION(_TEC6,          "2F", 4)
CONNECTION(_TEC4,          "2F", 2) 
CONNECTION(_THBG,          "2F", 1)

CONNECTION(_1TLG7,         "2F", 9) 
CONNECTION(_TLC6,          "2F", 10)
CONNECTION(_TLC4,          "2F", 13) 
CONNECTION(_TVBG,          "2F", 12)


// L/R PADDLE (bottom, left)

CONNECTION(_TEC4,          "3H", 2) 
CONNECTION(_TEC3,          "3H", 1)

CONNECTION(_1TEG7,         "1J", 5) 
CONNECTION(_NCLC,          "1J", 4)
CONNECTION(_TLLG,          "1J", 3) 

CONNECTION(_5TEG7,         "1J", 9) 
CONNECTION(_NCRC,          "1J", 10)
CONNECTION(_TLLG,          "1J", 11) 

CONNECTION(_TE43,          "0J", 5) 
CONNECTION(_TELG,          "0J", 4)
CONNECTION(_THBG,          "0J", 2) 
CONNECTION(_PCSE,          "0J", 1) 

CONNECTION(_5TGLG,         "1H", 2)
CONNECTION(_5TGRG,         "1H", 3)

CONNECTION(_5TVPG,         "1H", 9)
CONNECTION(_TVLG,          "1H", 8)

CONNECTION(_TVLG,          "2J", 2)
CONNECTION(_TEVL,          "2J", 1)


// T/B PADDLE (bottom, left)

CONNECTION(_TLC4,          "3H", 5) 
CONNECTION(_TLC3,          "3H", 4)

CONNECTION(_1TLG7,         "1J", 13) 
CONNECTION(_NCTC,          "1J", 2)
CONNECTION(_TELG,          "1J", 1) 

CONNECTION(_5TLG7,         "4J", 5) 
CONNECTION(_NCBC,          "4J", 4)
CONNECTION(_TELG,          "4J", 3) 

CONNECTION(_TL43,          "0J", 9) 
CONNECTION(_TLLG,          "0J", 10)
CONNECTION(_TVBG,          "0J", 12) 
CONNECTION(_PCSE,          "0J", 13) 

CONNECTION(_5TGTG,         "1H", 5)
CONNECTION(_5TGBG,         "1H", 6)

CONNECTION(_5THPG,         "1H", 12)
CONNECTION(_THLG,          "1H", 11)

CONNECTION(_THLG,          "2J", 5)
CONNECTION(_TLHL,          "2J", 4)


// COUNTERS (top, right)

  //left score counter
CONNECTION(_NCLC,          "3F", 5) 
CONNECTION(_1TEG7,         "3F", 4)
CONNECTION(_5KACH,         "3F", 3) 

CONNECTION(_N999,          "3A", 1) 
CONNECTION(_5PGSR,         "3A", 9)
CONNECTION(GND,            "3A", 3) 
CONNECTION(_9X7PT,         "3A", 4) 
CONNECTION(GND,            "3A", 5)
CONNECTION(_N999,          "3A", 6) 
CONNECTION(_NCLA,          "3A", 7) 
CONNECTION(_N999,          "3A", 10)
CONNECTION(_6TQ05,         "3A", 2) 

  //right score counter
CONNECTION(_NCRC,          "3F", 9) 
CONNECTION(_5TEG7,         "3F", 10)
CONNECTION(_5KACH,         "3F", 11) 

CONNECTION(_N999,          "3C", 1) 
CONNECTION(_5PGSR,         "3C", 9)
CONNECTION(GND,            "3C", 3) 
CONNECTION(_9X7PT,         "3C", 4) 
CONNECTION(GND,            "3C", 5)
CONNECTION(_N999,          "3C", 6) 
CONNECTION(_NCRA,          "3C", 7) 
CONNECTION(_N999,          "3C", 10)
CONNECTION(_6TQ05,         "3C", 2) 

  //top score counter
CONNECTION(_NCTC,          "3F", 13) 
CONNECTION(_1TLG7,         "3F", 2)
CONNECTION(_5KACG,         "3F", 1) 

CONNECTION(_N999,          "3B", 1) 
CONNECTION(_5PGSR,         "3B", 9)
CONNECTION(GND,            "3B", 3) 
CONNECTION(_9X7PT,         "3B", 4) 
CONNECTION(GND,            "3B", 5)
CONNECTION(_N999,          "3B", 6) 
CONNECTION(_NCTA,          "3B", 7) 
CONNECTION(_N999,          "3B", 10)
CONNECTION(_6TQ05,         "3B", 2) 

  //bottom score counter
CONNECTION(_NCBC,          "4F", 5) 
CONNECTION(_5TLG7,         "4F", 4)
CONNECTION(_5KACG,         "4F", 3) 

CONNECTION(_N999,          "3D", 1) 
CONNECTION(_5PGSR,         "3D", 9)
CONNECTION(GND,            "3D", 3) 
CONNECTION(_9X7PT,         "3D", 4) 
CONNECTION(GND,            "3D", 5)
CONNECTION(_N999,          "3D", 6) 
CONNECTION(_NCBA,          "3D", 7) 
CONNECTION(_N999,          "3D", 10)
CONNECTION(_6TQ05,         "3D", 2) 


// END OF GAME (top, right)

CONNECTION(_NCTC,          "4J", 9) 
CONNECTION(_NCBC,          "4J", 10)
CONNECTION(_5PGCG,         "4J", 11)

CONNECTION(_NCLC,          "4H", 5)
CONNECTION(_NCRC,          "4H", 4)

CONNECTION(_5NCFA,         "3J", 9)
CONNECTION(_5NCFB,         "3J", 8)


// PLAYER 1 (top, right)

CONNECTION(_NCFC,          "3J", 5)
CONNECTION(_NCFF,          "3J", 6)

CONNECTION(_5NCFG,         "2H", 9)


// PLAYER 2 (top, right)

CONNECTION(_NCLC,          "4J", 13)
CONNECTION(_NCRC,          "4J", 2)
CONNECTION(_5PGCG,         "4J", 1)

CONNECTION(_NCTC,          "4H", 9)
CONNECTION(_NCBC,          "4H", 10)

CONNECTION(_5NCAD,         "3J", 12)
CONNECTION(_5NCFE,         "3J", 11)


// NUMBER GENERATION (bottom, right)

CONNECTION(_NCL2,          "4A", 3)
CONNECTION(_NCR2,          "4A", 4)
CONNECTION(_NCT2,          "4A", 5)
CONNECTION(_NCB2,          "4A", 6)
CONNECTION(GND,            "4A", 1)
CONNECTION(_NCL1,          "4A", 13)
CONNECTION(_NCR1,          "4A", 12)
CONNECTION(_NCT1,          "4A", 11)
CONNECTION(_NCB1,          "4A", 10)
CONNECTION(GND,            "4A", 15)
CONNECTION(_TLKG,          "4A", 2)
CONNECTION(_1TNSC,         "4A", 14)

CONNECTION(_NCL0,          "4B", 3)
CONNECTION(_NCR0,          "4B", 4)
CONNECTION(_NCT0,          "4B", 5)
CONNECTION(_NCB0,          "4B", 6)
CONNECTION(GND,            "4B", 1)
CONNECTION(_TEC6,          "4B", 13)
CONNECTION(_TEC6,          "4B", 12)
CONNECTION(_TEC7,          "4B", 11)
CONNECTION(_TEC7,          "4B", 10)
CONNECTION(_TEC8,          "4B", 15)
CONNECTION(_TLKG,          "4B", 2)
CONNECTION(_1TNSC,         "4B", 14)

CONNECTION(_NCS2,          "4C", 1)
CONNECTION(_NCS1,          "4C", 3)
CONNECTION(_NCS0,          "4C", 5)
CONNECTION(_NCG3,          "4C", 9)
CONNECTION(_NCG2,          "4C", 11)
CONNECTION(GND,            "4C", 13)

CONNECTION(_5NCS2,         "4D", 14)
CONNECTION(_5NCS1,         "4D", 13)
CONNECTION(_5NCS0,         "4D", 12)
CONNECTION(_NCC2,          "4D", 11)
CONNECTION(_NCC1,          "4D", 10)
CONNECTION(GND,            "4D", 15)

CONNECTION(_NCG4,          "4H", 2)
CONNECTION(_NCC3,          "4H", 1)

CONNECTION(_NCG7,          "5D", 5)
CONNECTION(_5NCG3,         "5D", 4)
CONNECTION(_5NCGA,         "5D", 2)
CONNECTION(_5NCGA,         "5D", 1)

CONNECTION(_NCG6,          "5D", 9)
CONNECTION(_5NCG2,         "5D", 10)
CONNECTION(_5NCGA,         "5D", 12)
CONNECTION(_5NCGA,         "5D", 13)

CONNECTION(_TLC5,          "4G", 2)
CONNECTION(_TLLG,          "4G", 3)

CONNECTION(_NCCE,          "2C", 13)

CONNECTION(_N999,          "3E", 1)
CONNECTION(_NCCE,          "3E", 9)
CONNECTION(GND,            "3E", 3)
CONNECTION(GND,            "3E", 4)
CONNECTION(GND,            "3E", 5)
CONNECTION(GND,            "3E", 6)
CONNECTION(_5NCCC,         "3E", 7)
CONNECTION(_5NCCC,         "3E", 10)
CONNECTION(_6THSC,         "3E", 2)

CONNECTION(_NCC1,          "1F", 13)
CONNECTION(_NCC3,          "1F", 12)

CONNECTION(GND,            "4E", 14)
CONNECTION(_NCH7,          "4E", 12)
CONNECTION(_NCH6,          "4E", 11)
CONNECTION(_NCG5,          "4E", 10)
CONNECTION(GND,            "4E", 5)
CONNECTION(GND,            "4E", 4)
CONNECTION(GND,            "4E", 3)
CONNECTION(GND,            "4E", 2)
CONNECTION(GND,            "4E", 1)
CONNECTION(_NCSC,          "4E", 15)
CONNECTION(_5NCCC,         "4E", 9)
CONNECTION(_5NCCE,         "4E", 6)
CONNECTION(_TEC0,          "4E", 7)


/* Page 2 */


//PADDLE IN (left)
  //DIFFERENT THAN SCHEMATIC
//1K, 8K CONNECTIONS
CONNECTION(_PKL5, "PADDLE1", 1)
CONNECTION(_PKL5, "PADDLE3", 1)

CONNECTION(_PKE5, "PADDLE2", 1)
CONNECTION(_PKE5, "PADDLE4", 1)

//RECLOCK PADDLE POS & INTERSECT (P2 top, left)

CONNECTION(_TEC8,    "5G", 3)
CONNECTION(_TLC8,    "5G", 4)
CONNECTION(_TPHS,    "5G", 6)
CONNECTION(_TPVS,    "5G", 11)
CONNECTION(_KAAC,    "5G", 13)
CONNECTION(_KAAD,    "5G", 14)
CONNECTION(_PGSC,    "5G", 1)
CONNECTION(_6TQ05,   "5G", 9)

CONNECTION(_PKE8,    "6C", 1)

CONNECTION(_PKL8,    "6C", 3)

CONNECTION(_PKE5,    "6C", 5)

CONNECTION(_PKL5,    "6C", 9)  //diagram is off


//LEFT PADDLE POSITION (top, left)

CONNECTION(_5PKL5,   "2K", 4)
CONNECTION(_5PCLA,   "2K", 3)
CONNECTION(_2THSC,   "2K", 1)
CONNECTION(_TPVR,    "2K", 2)
CONNECTION(_5PKL8,   "2K", 15)

CONNECTION(_5PCLB,   "4F", 9)
CONNECTION(_PCLC,    "4F", 10)
CONNECTION(_TLLG,    "4F", 11)

CONNECTION(_N999,    "6E", 1)
CONNECTION(_PCLB,    "6E", 9)
CONNECTION(GND,      "6E", 3)
CONNECTION(GND,      "6E", 4)
CONNECTION(GND,      "6E", 5)
CONNECTION(GND,      "6E", 6)
CONNECTION(_PCLE,    "6E", 7)
CONNECTION(_N999,    "6E", 10)
CONNECTION(_6THSC,   "6E", 2)


//RIGHT PADDLE POSITION (top, left)

CONNECTION(_5PKL5,   "2K", 10)
CONNECTION(_5PCRA,   "2K", 11)
CONNECTION(_2THSC,   "2K", 13)
CONNECTION(_TPVR,    "2K", 12)
CONNECTION(_5PKL8,   "2K", 14)

CONNECTION(_5PCRB,   "5F", 5)
CONNECTION(_PCRC,    "5F", 4)
CONNECTION(_TLLG,    "5F", 3)

CONNECTION(_N999,    "6F", 1)
CONNECTION(_PCRB,    "6F", 9)
CONNECTION(GND,      "6F", 3)
CONNECTION(GND,      "6F", 4)
CONNECTION(GND,      "6F", 5)
CONNECTION(GND,      "6F", 6)
CONNECTION(_PCRE,    "6F", 7)
CONNECTION(_N999,    "6F", 10)
CONNECTION(_6THSC,   "6F", 2)


//TOP PADDLE POSITION (bottom, left)

CONNECTION(_5PKE5,   "7K", 4)
CONNECTION(_5PCTA,   "7K", 3)
CONNECTION(_2TQ05,   "7K", 1)
CONNECTION(_TPHR,    "7K", 2)
CONNECTION(_5PKE8,   "7K", 15)

CONNECTION(_5PCTB,   "5F", 9)
CONNECTION(_PCTC,    "5F", 10)
CONNECTION(_TELG,    "5F", 11)

CONNECTION(_N999,    "6G", 1)
CONNECTION(_PCTB,    "6G", 9)
CONNECTION(GND,      "6G", 3)
CONNECTION(GND,      "6G", 4)
CONNECTION(GND,      "6G", 5)
CONNECTION(GND,      "6G", 6)
CONNECTION(_PCTE,    "6G", 7)
CONNECTION(_N999,    "6G", 10)
CONNECTION(_6TQ05,   "6G", 2)


//BOTTOM PADDLE POSITION (top, left)

CONNECTION(_5PKE5,   "7K", 10)
CONNECTION(_5PCBA,   "7K", 11)
CONNECTION(_2TQ05,   "7K", 13)
CONNECTION(_TPHR,    "7K", 12)
CONNECTION(_5PKE8,   "7K", 14)

CONNECTION(_5PCBB,   "5F", 13)
CONNECTION(_PCBC,    "5F", 2)
CONNECTION(_TELG,    "5F", 1)

CONNECTION(_N999,    "6D", 1)
CONNECTION(_PCBB,    "6D", 9)
CONNECTION(GND,      "6D", 3)
CONNECTION(GND,      "6D", 4)
CONNECTION(GND,      "6D", 5)
CONNECTION(GND,      "6D", 6)
CONNECTION(_PCBE,    "6D", 7)
CONNECTION(_N999,    "6D", 10)
CONNECTION(_6TQ05,   "6D", 2)


//2 PLAYER PADDLE MULTIPLEXER (top, right)

CONNECTION(_PCLE,    "5C", 3)
CONNECTION(_PCRE,    "5C", 4)
CONNECTION(_PCTE,    "5C", 5)
CONNECTION(_PCBE,    "5C", 6)
CONNECTION(GND,      "5C", 1)
CONNECTION(_PCL3,    "5C", 13)
CONNECTION(_PCR3,    "5C", 12)
CONNECTION(_PCT3,    "5C", 11)
CONNECTION(_PCB3,    "5C", 10)
CONNECTION(GND,      "5C", 15)
CONNECTION(_5TLLG,   "5C", 2)
CONNECTION(_1TPSC,   "5C", 14)

CONNECTION(_5PDGS,   "2M", 9)
CONNECTION(_PCS3,    "2M", 8)

CONNECTION(_5PCX3,   "6B", 12)
CONNECTION(_5PCX3,   "6B", 13)

CONNECTION(_PJC1,    "6A", 3)

CONNECTION(_PCL2,    "5B", 3)
CONNECTION(_PCR2,    "5B", 4)
CONNECTION(_PCT2,    "5B", 5)
CONNECTION(_PCB2,    "5B", 6)
CONNECTION(_5PDGS,   "5B", 1)
CONNECTION(_PCL1,    "5B", 13)
CONNECTION(_PCR1,    "5B", 12)
CONNECTION(_PCT1,    "5B", 11)
CONNECTION(_PCB1,    "5B", 10)
CONNECTION(_5PDGS,   "5B", 15)
CONNECTION(_5TLLG,   "5B", 2)
CONNECTION(_1TPSC,   "5B", 14)


//REBOUND CONTROL (top, right)

CONNECTION(_KABD,    "5A", 3)
CONNECTION(_1PCX3,   "5A", 4)
CONNECTION(_PCS2,    "5A", 6)
CONNECTION(_PCS1,    "5A", 11)
CONNECTION(_5PJC1,   "5A", 13)
CONNECTION(_PJC0,    "5A", 14)
CONNECTION(_N999,    "5A", 1)
CONNECTION(_7KQPD,   "5A", 9)

CONNECTION(_PDPS,    "6C", 11)

CONNECTION(_PCS3,    "6C", 13)


//DIRECTION CHANGE F.F. (top, right)

CONNECTION(_PGSC,    "6J", 4)
CONNECTION(_N999,    "6J", 3)
CONNECTION(_2KQEA,   "6J", 1)
CONNECTION(GND,      "6J", 2)
CONNECTION(_5EBUZ,   "6J", 15)

  //vert direction change ind
CONNECTION(_5PDGS,   "5E", 5)
CONNECTION(_PDPS,    "5E", 4)

  //horiz direction change ind
CONNECTION(_5PDGS,   "5E", 9)
CONNECTION(_5PDPS,   "5E", 10)


//GAME FLAG (top, right)

CONNECTION(_N999,    "5H", 4)
CONNECTION(_1PGSB,   "5H", 3)
CONNECTION(_2TQ05,   "5H", 1)
CONNECTION(_1NCFG,   "5H", 2)
CONNECTION(_9XPRS,   "5H", 15)

CONNECTION(_1PGCC,   "5E", 12)
CONNECTION(_PGSC,    "5E", 13)


// 2/4 PLAYER INDICATOR (bottom, right)

CONNECTION(_PGCE,    "5E", 2)
CONNECTION(_PGSA,    "5E", 1)

CONNECTION(_5PGSB,   "6A", 5)


//COIN COUNT (bottom, right)

CONNECTION(_N999,    "5J", 4)
CONNECTION(_PGCB,    "5J", 3)
CONNECTION(_TLC8,    "5J", 1)  
CONNECTION(_PGSC,    "5J", 2)
CONNECTION(_9XPRS,   "5J", 15)


// 2 PLAYERS DETECT (bottom, right)

CONNECTION(_PGCB,    "4G", 5)
CONNECTION(_5PGCC,   "4G", 6)

CONNECTION(_N999,    "5J", 10)
CONNECTION(_PGCD,    "5J", 11)
CONNECTION(_TLC8,    "5J", 13)
CONNECTION(_PGSC,    "5J", 12)
CONNECTION(_9XPRS,   "5J", 14)

// 4 PLAYERS DETECT (bottom, right)

CONNECTION(_5PGCE,   "6H", 2)
CONNECTION(_PGCD,    "6H", 3)

CONNECTION(_PGSC,    "6H", 5)
CONNECTION(_PGCE,    "6H", 6)

CONNECTION(_N999,    "5H", 10)
CONNECTION(_PGCF,    "5H", 11)
CONNECTION(_TLC8,    "5H", 13)  
CONNECTION(_PGCH,    "5H", 12)
CONNECTION(_9XPRS,   "5H", 14)

// 5-7 game select dipswitch (9X7PT)
CONNECTION(VCC,      "SWMISS57", 1)
CONNECTION(GND,      "SWMISS57", 2)

//LAMP DRIVERS (bottom, right)
//CONNECTION(_5PGC0,   "5K", 10)
//CONNECTION(_5PGC0,   "5K", 11)
//CONNECTION(_5PGCC,   "5K", 6)
//CONNECTION(_PGCG,    "5K", 5)
//CONNECTION(_2PGCC,   "5K", 2)
//CONNECTION(_PCSC,    "5K", 1)
//OUT 9 - 4 PLAYER PIN #A
//OUT 7 - 2 PLAYER PIN #2
//OUT 3 - GAME OVER #3



/* Page 3 */

//REBOUND DIRECTION CONTROL (P3 top, left)

CONNECTION(_BDEC,     "8G", 2)
CONNECTION(_KACA,     "8G", 1)

CONNECTION(_5BDEC,    "8G", 5)
CONNECTION(_KACA,     "8G", 4)

  //left/right
CONNECTION(_5BDSR,    "8F", 4)
CONNECTION(_PCS3,     "8F", 3)
CONNECTION(_2KQEL,    "8F", 1)
CONNECTION(_5PCS3,    "8F", 2)
CONNECTION(_5BDSL,    "8F", 15)

CONNECTION(_1BLGE,    "9J", 2)
CONNECTION(_BDRR,     "9J", 1)

CONNECTION(_BDLC,     "8G", 9)
CONNECTION(_KACB,     "8G", 10)

  //up/down
CONNECTION(_5BDLC,    "8G", 12)
CONNECTION(_KACB,     "8G", 13)

CONNECTION(_5BDSD,    "8F", 10)
CONNECTION(_PCS3,     "8F", 11)
CONNECTION(_2KQLN,    "8F", 13)
CONNECTION(_5PCS3,    "8F", 12)
CONNECTION(_5BDSU,    "8F", 14)

CONNECTION(_1BLGD,    "9J", 9)
CONNECTION(_BDRD,     "9J", 10)

CONNECTION(_5BDGR,    "9J", 5)
CONNECTION(_5BDGD,    "9J", 4)


//BALL SPEED (P3 top, left)

CONNECTION(_B999,     "7J", 1)
CONNECTION(_5EBUZ,    "7J", 9)
CONNECTION(GND,       "7J", 3)
CONNECTION(GND,       "7J", 4)
CONNECTION(GND,       "7J", 5)
CONNECTION(GND,       "7J", 6)
CONNECTION(_KACF,     "7J", 7)
CONNECTION(_5EBIP,    "7J", 10)
CONNECTION(_6TQ05,    "7J", 2)

CONNECTION(_BSC4,     "9H", 2)
CONNECTION(_BSC4,     "9H", 1)

CONNECTION(_5TCKG,    "9E", 2)
CONNECTION(_5BSCG,    "9E", 3)


//VELOCITY GEN FROM REBOUND ADDRESS (P3 top, left)

CONNECTION(_5NCFB,    "9H", 12)
CONNECTION(_5NCFE,    "9H", 13)

CONNECTION(_PDGS,     "7F", 3)
CONNECTION(_BSC3,     "7F", 6)
CONNECTION(_BXYZ,     "7F", 10)
CONNECTION(GND,       "7F", 13)
CONNECTION(_PDS3,     "7F", 2)
CONNECTION(_PDS2,     "7F", 5)
CONNECTION(_PDS1,     "7F", 11)
CONNECTION(GND,       "7F", 14)
CONNECTION(GND,       "7F", 15)
CONNECTION(_BPSC,     "7F", 1)


//BALL MOVEMENT (P3 top, left)

CONNECTION(_PGSC,     "7G", 14)
CONNECTION(_BGS3,     "7G", 13)
CONNECTION(_BGS2,     "7G", 12)
CONNECTION(_BGS1,     "7G", 11)
CONNECTION(_BGS0,     "7G", 10)
CONNECTION(GND,       "7G", 15)

CONNECTION(_PDPS,     "3H", 9)
CONNECTION(_5PDGS,    "3H", 10)

CONNECTION(_1BLGE,    "3H", 12)
CONNECTION(_BPSV,     "3H", 13)

CONNECTION(_BPE3,     "7H", 3)
CONNECTION(_BPE2,     "7H", 6)
CONNECTION(_BPE1,     "7H", 10)
CONNECTION(_BPE0,     "7H", 13)
CONNECTION(_BPL3,     "7H", 2)
CONNECTION(_BPL2,     "7H", 5)
CONNECTION(_BPL1,     "7H", 11)
CONNECTION(_BPL0,     "7H", 14)
CONNECTION(GND,       "7H", 15)
CONNECTION(_BPSC,     "7H", 1)


// L/R T/B SELECTOR (P3 bottom, left)

CONNECTION(_5TEG7,    "8H", 3)
CONNECTION(_1TEG7,    "8H", 6)
CONNECTION(_5TLG7,    "8H", 10)
CONNECTION(_1TLG7,    "8H", 13)
CONNECTION(_TEC0,     "8H", 2)
CONNECTION(_5TEC0,    "8H", 5)
CONNECTION(_TLC0,     "8H", 11)
CONNECTION(_5TLC0,    "8H", 14)
CONNECTION(_BSCD,     "8H", 15)
CONNECTION(_5TCKG,    "8H", 1)


//INTERCEPT DIRECTION DEFINITION (P3 bottom, left)

CONNECTION(_KABC,     "6H", 9)
CONNECTION(_KABH,     "6H", 8)

CONNECTION(_5KBCH,    "9H", 5)
CONNECTION(_5KABE,    "9H", 4)

CONNECTION(_KABD,     "6H", 12)
CONNECTION(_KABG,     "6H", 11)

CONNECTION(_5KBDG,    "9H", 9)
CONNECTION(_5KABF,    "9H", 10)


//INTERSECT (P3 left, bottom)

  //intersect clock
CONNECTION(_6TQ05,    "9D", 2)
CONNECTION(_5EBCA,    "9D", 3)

  //boundry intersect
CONNECTION(_5KABE,    "9F", 5)
CONNECTION(_5KABF,    "9F", 4)

  //paddle or cross intersect
CONNECTION(_5KABC,    "9F", 12)
CONNECTION(_5KABD,    "9F", 13)


//INTERCEPTS (P3 bottom, left)

  //ball intercepts vert pad & horiz cross
CONNECTION(_TVPD,     "4G", 9)
CONNECTION(_THCH,     "4G", 8)

CONNECTION(_5BVAF,    "9E", 5)
CONNECTION(_5KAAA,    "9E", 6)

  //ball intercepts vert cross & horiz pad
CONNECTION(_THPD,     "4G", 12)
CONNECTION(_TVCH,     "4G", 11)

CONNECTION(_5BVAF,    "9E", 9)
CONNECTION(_5KAAB,    "9E", 8)

  //ball intercept vert line
CONNECTION(_TVLN,     "9G", 2)
CONNECTION(_1BVAF,    "9G", 1)

  //ball intercept horiz line
CONNECTION(_THLN,     "9G", 4)
CONNECTION(_1BVAF,    "9G", 5)

  //ball intercept top & bottom scoring regions
CONNECTION(_TLCB,     "2J", 9)
CONNECTION(_1BVAF,    "2J", 10)

  //ball intercept left & right scoring regions
CONNECTION(_TECB,     "2J", 12)
CONNECTION(_1BVAF,    "2J", 13)


//SCORE (P3 bottom, left)

CONNECTION(_EBUZ,     "9E", 12)
CONNECTION(_5PGSC,    "9E", 11)

CONNECTION(_KABG,     "9G", 9)
CONNECTION(_KXYA,     "9G", 10)

CONNECTION(_KABH,     "9G", 12)
CONNECTION(_KXYA,     "9G", 13)

CONNECTION(_5KACG,    "9F", 2)
CONNECTION(_5KACH,    "9F", 1)


//RECLOCK (bottom, left)

CONNECTION(_5KAAE,    "8J", 3)
CONNECTION(_5KAAF,    "8J", 4)
CONNECTION(_KAAG,     "8J", 6)
CONNECTION(_KAAH,     "8J", 11)
CONNECTION(_5VDAE,    "8J", 13)
CONNECTION(_TCSC,     "8J", 14)
CONNECTION(_B999,     "8J", 1)
CONNECTION(_6TQ05,    "8J", 9)

CONNECTION(_KABC,     "6A", 9)

CONNECTION(_KABD,     "6A", 11)


//

CONNECTION(_1TQ05,    "9F", 9)
CONNECTION(_KAYA,     "9F", 10)

CONNECTION(_5KABC,    "9D", 5)
CONNECTION(_6KQCA,    "9D", 6)

CONNECTION(_5KABD,    "9D", 9)
CONNECTION(_6KQCA,    "9D", 8)

CONNECTION(_2KQLN,    "9D", 12)
CONNECTION(_2KQEL,    "9D", 11)

CONNECTION(_EBCA,     "2M", 12)
CONNECTION(_1TCKG,    "2M", 11)


//COMPOSITE VIDEO (bottom, left)

CONNECTION(_NCVD,     "4F", 13)  //numbers
CONNECTION(_TVLN,     "4F", 2)   //vert lines
CONNECTION(_THLN,     "4F", 1)   //horiz lines

CONNECTION(_5VDAC,    "3G", 9)   
CONNECTION(_5BVAF,    "3G", 10)  //ball
CONNECTION(_5KAAA,    "3G", 12)  //vert paddle & horiz cross
CONNECTION(_5KAAB,    "3G", 13)  //horiz paddle & vert cross

CONNECTION(_5TCBL,    "4H", 12)
CONNECTION(_VDAD,     "4H", 13)


//BALL GENERATION AND CONTROL (p3, top, right)

  //horiz
CONNECTION(_5PDEC,    "9C", 5)
CONNECTION(_1BLGE,    "9C", 4)
CONNECTION(_1BEGD,    "9C", 2)
CONNECTION(_1BEGD,    "9C", 1)
  
CONNECTION(_B999,     "7E", 1)
CONNECTION(_5BECL,    "7E", 9)
CONNECTION(_BPS0,     "7E", 3)
CONNECTION(_BPS1,     "7E", 4)
CONNECTION(_BPS2,     "7E", 5)
CONNECTION(_BPS3,     "7E", 6)
CONNECTION(_5TEG8,    "7E", 7)
CONNECTION(_5TEG8,    "7E", 10)
CONNECTION(_6TQ05,    "7E", 2)
  
CONNECTION(_B999,     "7D", 1)
CONNECTION(_5EBUZ,    "7D", 9)
CONNECTION(_BDRR,     "7D", 3)
CONNECTION(_BDRR,     "7D", 4)
CONNECTION(_5BDRR,    "7D", 5)
CONNECTION(_BDRR,     "7D", 6)
CONNECTION(_BECA,     "7D", 7)
CONNECTION(_BECA,     "7D", 10)
CONNECTION(_6TQ05,    "7D", 2)

CONNECTION(_BECB,     "8A", 3)

CONNECTION(_5BECB,    "8C", 3)
CONNECTION(_5BEGA,    "8C", 4)
CONNECTION(_5BEGB,    "8C", 6)
CONNECTION(_5BEGC,    "8C", 11)
CONNECTION(_PGCA,     "8C", 13)
CONNECTION(_PGCC,     "8C", 14)
CONNECTION(_B999,     "8C", 1)
CONNECTION(_6TQ05,    "8C", 9)

CONNECTION(_5BEGD,    "8A", 9)

  //vert
CONNECTION(_5PDLC,    "9A", 2)
CONNECTION(_1BLGD,    "9A", 1)
  
CONNECTION(_B999,     "8E", 1)
CONNECTION(_5BLCL,    "8E", 9)
CONNECTION(_BPS0,     "8E", 3)
CONNECTION(_BPS1,     "8E", 4)
CONNECTION(_BPS2,     "8E", 5)
CONNECTION(_BPS3,     "8E", 6)
CONNECTION(_5TLG8,    "8E", 7)
CONNECTION(_5TLG8,    "8E", 10)
CONNECTION(_6THSC,    "8E", 2)
  
CONNECTION(_B999,     "8D", 1)
CONNECTION(_5EBUZ,    "8D", 9)
CONNECTION(_BDRD,     "8D", 3)
CONNECTION(_BDRD,     "8D", 4)
CONNECTION(_5BDRD,    "8D", 5)
CONNECTION(_BDRD,     "8D", 6)
CONNECTION(_BLCA,     "8D", 7)
CONNECTION(_BLCA,     "8D", 10)
CONNECTION(_6THSC,    "8D", 2)

CONNECTION(_BLCB,     "8A", 5)

CONNECTION(_5BLCB,    "8B", 3)
CONNECTION(_5BLGA,    "8B", 4)
CONNECTION(_5BLGB,    "8B", 6)
CONNECTION(_5BLGC,    "8B", 11)
CONNECTION(_1BLGD,    "8B", 13)
CONNECTION(_EBCA,     "8B", 14)
CONNECTION(_B999,     "8B", 1)
CONNECTION(_6THSC,    "8B", 9)

CONNECTION(_5BLGD,    "8A", 11)

//ball gen and shaping

  //corner round decode
CONNECTION(_5BEGA,    "9A", 5)
CONNECTION(_5BEGD,    "9A", 4)

CONNECTION(_5BLGA,    "9A", 9)
CONNECTION(_5BLGD,    "9A", 10)
  
CONNECTION(_BVAA,     "9A", 12)
CONNECTION(_BVAB,     "9A", 13)

  //
CONNECTION(_5BEGA,    "9B", 5)
CONNECTION(_5BEGB,    "9B", 4)
CONNECTION(_5BEGC,    "9B", 2)
CONNECTION(_5BEGD,    "9B", 1)

CONNECTION(_5BLGA,    "9B", 9)
CONNECTION(_5BLGB,    "9B", 10)
CONNECTION(_5BLGC,    "9B", 12)
CONNECTION(_5BLGD,    "9B", 13)

CONNECTION(_BVAC,     "9C", 9)
CONNECTION(_5BVAD,    "9C", 10)
CONNECTION(_5EBUZ,    "9C", 12)
CONNECTION(_BVAE,     "9C", 13)

CONNECTION(_5BVAF,    "8A", 13)


//AUDIO GENERATION (P3 bottom, right)

  //ball hits paddle & cross
CONNECTION(_B999,     "7B", 4)
CONNECTION(_KACF,     "7B", 3)
CONNECTION(_2TQ05,    "7B", 1)
CONNECTION(_EBC2,     "7B", 2)
CONNECTION(_PGSC,     "7B", 15)

  //ball hits boundary
CONNECTION(_B999,     "6J", 10)
CONNECTION(_KACE,     "6J", 11)
CONNECTION(_2TQ05,    "6J", 13)
CONNECTION(_EBC2,     "6J", 12)
CONNECTION(_PGSC,     "6J", 14)

  //ball hits score
CONNECTION(_5PGSR,    "7B", 10)
CONNECTION(_KADG,     "7B", 11)
CONNECTION(_2TQ05,    "7B", 13)
CONNECTION(_EBCC,     "7B", 12)
CONNECTION(_B999,     "7B", 14)

CONNECTION(_EBIP,     "6B", 2)
CONNECTION(_TLC3,     "6B", 1)

CONNECTION(_EBOP,     "6B", 5)
CONNECTION(_TLC4,     "6B", 4)

CONNECTION(_EBUZ,     "6B", 9)
CONNECTION(_TLC6,     "6B", 10)

CONNECTION(_5EBEA,    "7A", 5)  //audio
CONNECTION(_5EBEB,    "7A", 4)
CONNECTION(_5EBEC,    "7A", 2)
CONNECTION(_5EBEC,    "7A", 1)


//INTERSECT (bottom, right)

CONNECTION(_5EBIP,    "7A", 9)
CONNECTION(_5EBOP,    "7A", 10)
CONNECTION(_5EBUZ,    "7A", 12)
CONNECTION(_5EBUZ,    "7A", 13)

CONNECTION(_EBCA,     "6A", 13)

//AUDIO DURATION COUNTER (bottom, right)

CONNECTION(_B999,     "7C", 1)
CONNECTION(_1EBCA,    "7C", 9)
CONNECTION(GND,       "7C", 3)
CONNECTION(GND,       "7C", 4)
CONNECTION(GND,       "7C", 5)
CONNECTION(GND,       "7C", 6)
CONNECTION(_1TLCC,    "7C", 7)
CONNECTION(_5TLC8,    "7C", 10)
CONNECTION(_6THSC,    "7C", 2)


/*  OUTPUT  */

//nn sync CONNECTION(_VDSC,     "2H", 11)

CONNECTION(_5VDAF,    "2H", 13)

//video

CONNECTION("VIDEO", 1, _1VDAF)
//nn sync CONNECTION(_5VDSO     "VIDEO", 2)
    
CONNECTION("VIDEO", Video::HBLANK_PIN, _THSC)
CONNECTION("VIDEO", Video::VBLANK_PIN, _TVBL)

//audio

CONNECTION(_EBEL,       "AUDIO", 1)
CONNECTION("AUDIO", i1, "MIXER", 1)

CONNECTION("AUDIO", Audio::OUTPUT_MONO, "MIXER", i1)


/* * * * * * * * */
#ifdef DEBUG

CONNECTION(_THCH, "LOG1", 1)
CONNECTION(_THPD, "LOG1", 2)
CONNECTION(_5KAAB, "LOG1", 3)
CONNECTION(_5BVAF, "LOG1", 4)
CONNECTION(_KAAD, "LOG1", 5)

#endif

CIRCUIT_LAYOUT_END

