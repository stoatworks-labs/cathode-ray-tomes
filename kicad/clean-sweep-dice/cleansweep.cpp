/* Clean Sweep by Ramtek 1974 */

//Based on Revision D schematics

/* ROM CRC from this dump, other revision dumps may exist:
RAMTEK ASSY NO 501082 
COPYRIGHT 1974 MADE IN USA 
.c6 82s123b handwritten stickered 501075 
.d7 82s123b handwritten stickered 501076 
.k3 IM5610 read as 82s123 handwritten stickered 501074 
*/

//Last Update  11/23/2013


#include "../circuit_desc.h"
#include "cleansweep.h"

#define DEBUG
#undef DEBUG

#ifdef DEBUG
static VcdLogDesc vcd_log_desc
(
    "output_cleansweep.vcd",
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

static CleanSweepPaddleDesc cleansweep_pad_desc(K_OHM(2.5), U_FARAD(0.033));
static Paddle1HorizontalDesc pad1_desc(K_OHM(1.0), K_OHM(4.0), &cleansweep_pad_desc);

/*
 static RomDesc c6_desc("cleansweep", "clean.6c", 0xBE02B5F5);  //paddle shape
static RomDesc d7_desc("cleansweep", "clean.d7", 0xBE40B153);  //ball control
static RomDesc k3_desc("cleansweep", "clean.k3", 0x515A34BA);  //number images
*/

const static RomDesc cleansweep_c6_desc("cleansweep", "501075.6c", 0xBE02B5F5);  //paddle shape
const static RomDesc cleansweep_d7_desc("cleansweep", "501076.d7", 0xBE40B153);  //ball control
const static RomDesc cleansweep_k3_desc("cleansweep", "501074.k3", 0x515A34BA);  //number images

static Ram82S16Desc b5_desc;  //P1 dot memory
static Ram82S16Desc c5_desc;  //P2 dot memory

static DipswitchDesc swreplayyn_desc("replay", "dice_dipswitch_1", "Replay", 1, "Disabled", "Enabled");
static DipswitchDesc swballs35_desc("ball_count", "dice_dipswitch_2", "Ball Count", 1, "3", "5");
static DipswitchDesc swplayspercoin12_desc("coinage", "dice_dipswitch_3", "Coinage", 0, "1 Coin / 1 Credit", "1 Coin / 2 Credits");

static BufferDesc buf1_desc(DELAY_NS(10.0), DELAY_NS(10.0)); // Prevents 5F from counting down instead of up on credit insertion. TODO: investigate

static BufferDesc buf2_desc(DELAY_NS(15.0), DELAY_NS(15.0)); // Prevents 6J from failing to reset on game start due to load signal. TODO: investigate

static BufferDesc buf3_desc(DELAY_NS(15.0), DELAY_NS(15.0)); //simulate 9XWRR capacitor charging at power on.  todo: check if accurate timing

static BufferDesc buf4_desc(DELAY_NS(15.0), DELAY_NS(0.0)); //Add a bit of delay to 5WRTA going high so that the right lower dot doesn't get reset at game start. TODO: investigate

static BufferDesc buf5_desc(DELAY_NS(9.0), DELAY_NS(9.0)); 
//fix "HIT" wording on paddle by delaying 8B clocking signal

static MixerDesc mixer_desc({OHM(220.0)}, 0, 0, U_FARAD(0.1)); 

static VIDEO_DESC( cleansweep )
    VIDEO_RESISTANCE(1, K_OHM(2.2))
    //sync    VIDEO_RESISTANCE(2, K_OHM(4.7))
    VIDEO_CONTRAST(2.0)
    // Values guessed based on screenshots. TODO: Make more accurate
    //             X,   Y,   W,    H,    R,    G,    B
    VIDEO_OVERLAY( 0.0, 0.0, -1.0, -1.0, 0.20, 0.90, 0.80 ) // Blue Overlay
    VIDEO_RETRO_V_SIZE(256)  // Also sometimes 253
VIDEO_DESC_END

static AUDIO_DESC( cleansweep )
    AUDIO_GAIN(80.0)
    AUDIO_SPEAKER_CONFIG(MONO) 
AUDIO_DESC_END

static INPUT_DESC( cleansweep ) 
    INPUT_INFO(PADDLE1_HORIZONTAL_INPUT, "Move Paddle")
    INPUT_INFO(BUTTONS1_INPUT, {{ 1 }}, "Serve Ball")  
    INPUT_INFO(COIN_INPUT, {{ 1 }}, "Insert Coin")
    INPUT_INFO(START_INPUT, {{ 1 }}, "Start Game") 
INPUT_DESC_END

//**************************************************************


CIRCUIT_LAYOUT( cleansweep )

/* chips */

//note: all 7421 are actually 74H21 on diagram

CHIP("CRYSTAL", CLOCK_10_733_MHZ)  //0A
CHIP("0B", 7404)  
CHIP("0C", 74S112)
CHIP("0D", 7420)
CHIP("0E", 7420)
CHIP("0F", 7421)
CHIP("0G", 7486)
CHIP("0H", 7420)
CHIP("0J", 7427)
CHIP("0K", 7400)  
CHIP("0L", 7408)

CHIP("1A", 7437)
CHIP("1B", 74S112) 
CHIP("1C", 7437)
CHIP("1D", 7408)
CHIP("1E", 7421)  //mislabeled in one spot as 7408
CHIP("1F", 7404)
CHIP("1G", 7420)
CHIP("1H", 7420)
CHIP("1J", 7427)
CHIP("1K", 7404)
CHIP("1L", 7402)

CHIP("2A", 74161)
CHIP("2B", 74161)
CHIP("2C", 7400)
CHIP("2D", 7404)
CHIP("2E", 7486)
CHIP("2F", 7408)
CHIP("2G", 7421)
CHIP("2H", 7400)
CHIP("2J", 7400)
CHIP("2K", 74166)
CHIP("2L", 7408)

CHIP("3A", 74S112)
CHIP("3B", 74161)
CHIP("3C", 74161)
CHIP("3D", 7404)
CHIP("3E", 7486)
CHIP("3F", 7402)
CHIP("3G", 7421)
CHIP("3H", 7421)
CHIP("3J", 7402)
//CHIP("3K", 82S123, &k3_desc) //I5610
CHIP("3K", 82S123, &cleansweep_k3_desc) //I5610

CHIP("3L", 7400)
CHIP("3M", 74S112)

CHIP("4A", 7400)
CHIP("4B", 7404)  
CHIP("4C", 7400)
CHIP("4D", 7427)
CHIP("4E", 7402)
CHIP("4F", 7421)
CHIP("4G", 74161)  
CHIP("4H", 7420)
CHIP("4J", 74S112)
CHIP("4K", 74151)
CHIP("4L", 74151)
CHIP("4M", 7402)

CHIP("5A", 74S112)
CHIP("5B", 82S16, &b5_desc) //I5523
CHIP("5C", 82S16, &c5_desc) //I5523
CHIP("5D", 7408)
CHIP("5E", 74S112)
CHIP("5F", 74191)
CHIP("5G", 74S112)  
CHIP("5H", 74S112)
CHIP("5J", 7400)
CHIP("5K", 74151)
CHIP("5L", 74151)

CHIP("6A", 74161)
CHIP("6B", 7421)
//CHIP("6C", 82S123, &c6_desc) //I5610
CHIP("6C", 82S123, &cleansweep_c6_desc) //I5610
CHIP("6D", 74S151)
CHIP("6E", 7420)
CHIP("6F", 7402)
CHIP("6G", 7404)
CHIP("6H", 74S112)
CHIP("6J", 74161)  
CHIP("6K", 74161)
CHIP("6L", 74161)
CHIP("6M", 7420)  //labeled 6C on page 3, guess as there is a chip at 6M but it is not on the schematics

CHIP("7A", 7400)
CHIP("7B", 74174)
CHIP("7C", 7486)
//CHIP("7D", 82S123, &d7_desc) //I5610
CHIP("7D", 82S123, &cleansweep_d7_desc) //I5610
CHIP("7E", 74161)
CHIP("7F", 74S112)
CHIP("7G", 7408)
CHIP("7H", 7402)
CHIP("7J", 7421)
CHIP("7K", 74161)
CHIP("7L", 74161)
CHIP("7M", 74S112)

CHIP("8A", 74S174)
CHIP("8B", 74S174)
CHIP("8B2", 74S174)  //hack to fix "HIT" on paddle
CHIP("8C", 74174)  
CHIP("8D", 74161)
CHIP("8E", 74161)
CHIP("8F", 74161)
CHIP("8G", 7400)
CHIP("8H", 7408)
CHIP("8J", 7420)
CHIP("8K", 74161)
CHIP("8L", 74161)
CHIP("8M", 7404)

CHIP("9A", 7404)
CHIP("9B", 7402)
CHIP("9C", 7420)
CHIP("9D", 7400)
CHIP("9E", 74S112)
CHIP("9F", 7400)
CHIP("9G", 74161)
CHIP("9H", 74S112)
CHIP("9J", 7400)
CHIP("9K", 7402)
CHIP("9L", 7420)

CHIP("BUF1", BUFFER, &buf1_desc)
CHIP("BUF2", BUFFER, &buf2_desc)
CHIP("BUF3", BUFFER, &buf3_desc)
CHIP("BUF4", BUFFER, &buf4_desc)
CHIP("BUF5", BUFFER, &buf5_desc)

CHIP("COMBINE", 9322) //hack for P1/P2 combo into PVID

// dip switches
CHIP("SWPLAYSPERCOIN12", DIPSWITCH, &swplayspercoin12_desc)
CHIP("SWREPLAYYN",       DIPSWITCH, &swreplayyn_desc)
CHIP("SWBALLS35",        DIPSWITCH, &swballs35_desc)


// input
CHIP("PADDLE", CLEAN_SWEEP_PADDLE, &cleansweep_pad_desc)
CHIP("PAD1", PADDLE1_HORIZONTAL_INPUT, &pad1_desc)
PADDLE_CONNECTION("PAD1", "PADDLE")

CHIP("SERVE",    BUTTONS1_INPUT)  

CHIP("COIN_IN",  COIN_INPUT)      

CHIP("START_IN", START_INPUT)

//
CHIP("MIXER", MIXER, &mixer_desc)

VIDEO(cleansweep)
AUDIO(cleansweep)
INPUT(cleansweep)

OPTIMIZATION_HINT("0F", 128, 128)
OPTIMIZATION_HINT("2K", 1024, 512)
OPTIMIZATION_HINT("6D", 512, 64)
OPTIMIZATION_HINT("COMBINE", 4, 64)
OPTIMIZATION_HINT("9L", 64, 64)

#ifdef DEBUG
	CHIP("LOG1", VCD_LOG, &vcd_log_desc)
#endif


/* signals */

  //page 1
#define _B999   VCC
#define _SCOR   "5G", 9
#define _5SCOA  "8G", 8
#define _5SCOB  "8G", 11
#define _5SCAA  "9J", 3
#define _SCA0   "8K", 14
#define _SCA1   "8K", 13
#define _SCA2   "8K", 12
#define _SCA3   "8K", 11
#define _5SCBB  "9J", 8
#define _SCB0   "7K", 14
#define _SCB1   "7K", 13
#define _SCB2   "7K", 12
#define _SCB3   "7K", 11
#define _5SCCC  "2J", 11
#define _SCC0   "6K", 14
#define _SCC1   "6K", 13
#define _SCC2   "6K", 12
#define _SCC3   "6K", 11
#define _5SBAA  "9J", 6
#define _SBA0   "8L", 14
#define _SBA1   "8L", 13
#define _SBA2   "8L", 12
#define _SBA3   "8L", 11
#define _5SBBB  "9J", 11
#define _SBB0   "7L", 14
#define _SBB1   "7L", 13
#define _SBB2   "7L", 12
#define _SBB3   "7L", 11
#define _5SBCC  "3L", 3
#define _SBC0   "6L", 14
#define _SBC1   "6L", 13
#define _SBC2   "6L", 12
#define _SBC3   "6L", 11

#define _5SCDA  "8J", 8
#define _5SCDB  "7H", 13
#define _SCDC   "9K", 4
#define _5SEDA  "9K", 13
#define _1SEDA  "9A", 12
#define _GANC   "7M", 9
#define _5GANC  "7M", 7
#define _5SBDA  "9L", 8
#define _5SBDB  "9K", 1
#define _SBDC   "9K", 10
#define _5SUBL  "0K", 6
#define _9XEFE  "SWREPLAYYN", 3  //vcc=no gnd=yes
#define _EFEE   "4M", 1

#define _NACM   "7J", 6
#define _NACL   "7J", 8
#define _5NABA  "1J", 6
#define _NBA0   "6J", 14
#define _NBA1   "6J", 13
#define _NBA2   "6J", 12
#define _NBA3   "6J", 11
#define _7ENDA  "8J", 6
#define _ENDB   "7H", 10
#define _9XBL5  "SWBALLS35", 3  //vcc=3 gnd=5 
#define _BL57   "1L", 13
#define _5BL57  "9A", 10
#define _3XBL5  "1K", 8
#define _BL35   "4M", 10
#define _5BL35  "4M", 4

#define _NGTA   "2F", 3
#define _5NGTB  "3F", 1
#define _NGTC   "3F", 10
#define _5NGTC  "4B", 8  //number video gate
#define _5DNBA  "1G", 6
#define _DNBB   "3F", 4  //ball count gate
#define _ACLN   "2F", 11
#define _FNCA   "3H", 6
#define _FNCB   "3H", 8
#define _5GNCA  "2H", 3
#define _GNCB   "2F", 6
#define _5GNCC  "3F", 13
#define _5GBCA  "1G", 8
#define _GBCB   "2H", 11
#define _5GBCC  "0J", 6
#define _1GBCC  "4B", 6 //number gate
#define _5CNPA  "2H", 6  
#define _AERB   "2H", 8
#define _AERA   "0G", 3
#define _AERC   "2F", 8
#define _5AERD  "1H", 8 //left aerrow gate
#define _5AERE  "1H", 6 //right aerrow gate
#define _5CRBK  "0H", 6

#define _AFNA   "2G", 6
#define _AFNB   "2G", 8
#define _5AFNE  "0J", 8
#define _AFNC   "3G", 6
#define _AFND   "3G", 8
#define _5AFNF  "0J", 12
#define _AFNG   "1J", 8
#define _AFNH   "1J", 12
#define _5AGOT  "3J", 10
#define _AROT   "3J", 13 //aerrow output gate
#define _5SUBK  "2J", 3
#define _5ARBK  "2J", 6
#define _5ASBK  "2J", 8

#define _NCA0   "5K", 5
#define _NCA1   "5L", 5
#define _NCA2   "4K", 5
#define _NCA3   "4L", 5

#define _5NCA3  "4B", 12
#define _ILSB   "0G", 6
#define _5LODD  "0H", 8
#define _NLC3   "2L", 8
#define _NCG7   "3K", 9
#define _NCG6   "3K", 7
#define _NCG5   "3K", 6
#define _NCG4   "3K", 5
#define _NCG3   "3K", 4
#define _NCG2   "3K", 3
#define _NCH7   "0F", 8
#define _NCH6   "4F", 8
#define _5NCHA  "3L", 6
#define _5NCHB  "3L", 8
#define _5NCHC  "3L", 11
#define _NCIV   "2K", 13  //number video

  //page 2
#define _T999   VCC
//ATQ10, BTQ10, DTQ10
#define _1TQ10   "CRYSTAL", 1
#define _6TQ10   "1A", 3
#define _2TQ10   "1A", 6
#define _1TQ05   "1B", 5
#define _6TQ05   "1A", 8
#define _2TQ05   "1A", 11
#define _THSC    "1B", 9
#define _5THSC   "1B", 7   //H sync
#define _6THSC   "1C", 3
#define _2THSC   "1C", 6
#define _TCSC    "4A", 11  //Composit Sync
#define _TEC0    "2A", 14
#define _TEC1    "2A", 13
#define _TEC2    "2A", 12
#define _TEC3    "2A", 11
#define _TECA    "2A", 15
#define _TEC4    "2B", 14
#define _TEC5    "2B", 13
#define _TEC6    "2B", 12
#define _TEC7    "2B", 11
#define _TECB    "2B", 15
#define _5TECC   "2C", 3
#define _1TECC   "0B", 10
#define _TEC8    "3A", 5
#define _5TEC8   "3A", 6
#define _5TECD   "2C", 6
#define _5TEG8   "2C", 8
#define _5TEG7   "2C", 11
#define _1TEG7   "0B", 12
#define _5TEC5   "4B", 2
#define _TL32    "0L", 11
#define _TLC0    "3B", 14
#define _TLC1    "3B", 13
#define _TLC2    "3B", 12
#define _TLC3    "3B", 11
#define _TLCA    "3B", 15
#define _TLC4    "3C", 14
#define _TLC5    "3C", 13
#define _TLC6    "3C", 12
#define _TLC7    "3C", 11
#define _TLCB    "3C", 15
#define _5TLCC   "4A", 3
#define _1TLCC   "4B", 4  //top and bottom border
#define _TLC8    "3A", 9  //top border
#define _5TLC8   "3A", 7
#define _5TLCD   "4A", 6
#define _5TLG8   "4A", 8
#define _TCSA    "4D", 6
#define _5TVSC   "4C", 8   //V sync
#define _5TEC2   "2D", 2
#define _5TEC3   "2D", 4
#define _5TEC4   "2D", 6
#define _1TEC4   "2D", 8
#define _1TEC5   "2D", 10
#define _5TEC6   "2D", 12
#define _5TEC7   "3D", 2
#define _5TEC1   "3D", 4
#define _5TEC0   "3D", 6
#define _5TLC1   "3D", 8
#define _5TLC2   "3D", 10
#define _1PGOT   "3D", 12

#define _TLNA    "1D", 8  
#define _TLHB    "1E", 8 
#define _TLNC    "0C", 5
#define _5TLNC   "0C", 6
#define _TLND    "0C", 9
#define _5TLND   "0C", 7
#define _TLNE    "2E", 11   //Horz Boundry
#define _THBL    "1D", 11   //Horz Blanking

#define _TLGV    "0L", 6
#define _5TVBL   "3J", 1
#define _COBL    "3J", 4
#define _5CVID   "0K", 3
#define _NCOT    "0L", 3
#define _5TLBG   "1L", 4   //dot vid
#define _VIDA    "9L", 6   //comp video output
#define _5TBCF   "1L", 1
#define _1TBCF   "8M", 12
#define _5ALVD   "1L", 10 
 
#define _WRTZ    "5A", 5
#define _WRTA    "5A", 9
#define _5WRTA   "5A", 7
#define _RESA    "4C", 3
#define _WRTB    "5D", 3
#define _5PONF   "4E", 1
#define _5PONG   "4E", 4
#define _PVID_P1 "5B", 6  //P1 dot output
#define _PVID_P2 "5C", 6  //P2 dot output
#define _PVID    "COMBINE", 4  //hack to combine P1 and P2 dot output
#define _1PVBL   "0K", 8
#define _5TLC4   "1F", 2
#define _5TLC5   "1F", 4
#define _5TLC6   "1F", 6
#define _5TLC7   "1F", 8
#define _5THBL   "1F", 10
#define _1RRLM   "1F", 12

#define _TE10    "2E", 3
#define _TL10    "2E", 6
#define _5CONR   "4C", 6
#define _PGHT    "2E", 8
#define _PVGT    "3E", 3
#define _PGTA    "1D", 3
#define _PHGU    "3E", 6
#define _PVGU    "3E", 8
#define _PGTB    "4E", 10
#define _PGTC    "1E", 6   //dot size and shape
#define _5PGOT   "0D", 8   //dot video shaped and blanked
#define _5PVBU   "0D", 6
#define _5PVBL   "0E", 6
#define _PERA    "0F", 6   //ball and dot intercept
#define _5RTEA   "4E", 13  //write "1" into memory

#define _TE78    "1D", 6
#define _5RRLA   "0E", 8
#define _5RRLB   "4C", 11
#define _5RRLM   "5D", 6
#define _RLAA    "7M", 5
#define _RLA0    "5E", 5
#define _5RLA0   "5E", 6
#define _RBLA    "6A", 15
#define _RLA1    "6A", 14
#define _RLA2    "6A", 13
#define _RLA3    "6A", 12
#define _RLA4    "6A", 11
#define _RBLB    "5E", 9 //pin not labeled on diagram
#define _RGTE    "7C", 3 //stop paddle generation once per horz line
#define _5TL01   "1C", 11
#define _RL34    "3E", 11
#define _TL01    "4D", 8
#define _5HITA   "6B", 6
#define _5RLA1   "0K", 11
#define _5RRST   "7A", 3
#define _5RRSU   "7A", 6
//#define _RPFA    "X7405", 2
#define _RPFA    "PADDLE", 2
#define _RAT7    "6C", 9
#define _RAT6    "6C", 7
#define _RAT5    "6C", 6
#define _RAT4    "6C", 5
#define _RAT3    "6C", 4
#define _RAT2    "6C", 3
#define _RAT1    "6C", 2
#define _RAT0    "6C", 1
#define _RVIA    "6D", 6
#define _5RVID   "6E", 6 //paddle video

  //Page 3
#define _N999    VCC
#define _5RHD1   "7B", 2
#define _RHD2    "7B", 5
#define _RHD3    "7B", 7
#define _5RHCL   "7B", 10
#define _RH12    "7A", 8
#define _RSP1    "7C", 6
#define _RSP2    "7C", 8
#define _RSP3    "7C", 11
#define _BPE3    "7D", 9
#define _BPE2    "7D", 7
#define _BPE1    "7D", 6
#define _BPE0    "7D", 5
#define _BPL3    "7D", 4
#define _BPL2    "7D", 3
#define _BPL1    "7D", 2
#define _BPL0    "7D", 1
#define _5ESCL   "6F", 1   // clear register for serve
#define _KBAL    "7G", 3   // ball and horz line intercept
#define _TL48    "5D", 8
#define _5TL48   "1C", 8
#define _RVIC    "7G", 6
#define _KBAR    "7G", 8   // ball and paddle intercept
#define _ENDD    "0G", 8
#define _5PHLB   "9D", 3
#define _5RLA4   "0G", 11
#define _5PHRC   "9F", 3
#define _5BSCL   "9E", 6   // ball control left and right
#define _5BSUP   "9E", 7   // ball control up and down
#define _TL49    "3M", 9
#define _5KBAS   "8G", 3   // ball and top intercept
#define _5UPEA   "9F", 6
#define _UPEB    "6F", 13
#define _5UPEC   "9F", 8
#define _5UPGA   "9F", 11
#define _5UPAA   "7G", 11

#define _5BELD   "7A", 11
#define _BECA    "7E", 15
#define _BECB    "7F", 9
#define _BEBB    "5D", 11
#define _BECC    "8F", 15
#define _5BVAA   "9B", 1
#define _BEGA    "8A", 2
#define _BEGB    "8A", 5
#define _BEGC    "8A", 7
#define _BEGD    "8A", 10
#define _BEGE    "8A", 12
#define _BEGF    "8A", 15
#define _BEGG    "8B", 2
#define _BEGH    "8B", 5
#define _1PERA   "8B", 7
#define _1KBAR   "8B", 10
#define _6TEG8   "8B", 12
#define _6CVID   "8B2", 15
#define _5BVAB   "9B", 4
#define _5BVAC   "9B", 10
#define _5BVAD   "9B", 13
#define _BVBA    "9C", 8
#define _BVCA    "9D", 6
#define _BVCB    "9D", 8
#define _BVCD    "9D", 11
#define _BLCA    "8D", 15
#define _BLCB    "8E", 15
#define _5BLCB   "9A", 4
#define _5BLGA   "8C", 2
#define _5BLGB   "8C", 5
#define _5BLGC   "8C", 7
#define _5BLGD   "8C", 10
#define _5BLGE   "8C", 12
#define _5TPWR   "8C", 15
#define _BVCE    "9C", 6
#define _5BVCF   "6M", 8
#define _1BVCF   "9A", 8   //ball video shaped
#define _1BLGE   "9A", 6

#define _SURR    "2L", 3
#define _5SURZ   "6F", 4
#define _SURV    "7F", 5
#define _5SURV   "7F", 6
#define _5N25C   "1K", 2
#define _CREW    "2L", 6
#define _CREU    "3M", 5
#define _5CREU   "3M", 6
#define _1RVID   "6G", 2
#define _1KBAS   "6G", 4
#define _5ZERO   "6G", 6
#define _1N25C   "6G", 8
#define _5CREW   "6G", 10
#define _5ENDC   "6G", 12

#define _9XPLY   "SWPLAYSPERCOIN12", 3  //vcc=1 gnd=2
#define _5CPLY   "8M", 2
#define _9XWRR   "BUF3", 2 //reset charge cap via resistor to VCC
#define _5UPDN   "6F", 10
#define _CREC    "4D", 12
#define _CRA3    "5F", 7
#define _CRA2    "5F", 6
#define _CRA1    "5F", 2
#define _CRA0    "5F", 3
#define _ZERO    "5F", 12
#define _LIMT    "6B", 8
#define _FLA0    "9G", 14
#define _FLA1    "9G", 13
#define _FLA2    "9G", 12
#define _FLA3    "9G", 11
#define _FLAA    "9G", 15
#define _FLAB    "9H", 5
#define _FLAC    "8H", 8
#define _CONA    "9H", 9
#define _5CONA   "9H", 7
#define _CRE2    "8H", 3
#define _CRE1    "8H", 6
#define _5CREA   "7H", 1
#define _CREB    "7H", 4

#define _ENDA    "6H", 5
#define _5ENDA   "6H", 6
#define _TWOP    "6H", 9
#define _5TWOP   "6H", 7
#define _PONE    "5G", 5   //player one "1"
#define _5PONE   "5G", 6   //player two "1"
#define _ENDC    "0L", 8

#define _4CVID   "1K", 4
#define _5TCSC   "1K", 6

//player input
#define _9X25C   "COIN_IN", i1  //coin=HIGH, normally=LOW
#define _9XSUR   "SERVE", i1    //pressed=HIGH, unpressed=LOW
#define _9XCRU   "START_IN", i1 //pressed=HIGH, unpressed=LOW

//AUDIO
#define _BUZZ     "4F", 6
#define _EBUZ     "5H", 5
#define _5EBUZ    "5H", 6
#define _5BOPD    "8G", 6
#define _EBOP     "5H", 9
#define _5EBOP    "5H", 7
#define _EBEL     "4J", 5
#define _5EBEL    "4J", 6
#define _EHIT     "4J", 9
#define _5EHIT    "4J", 7
#define _EBAA     "4H", 6
//#define _EBC0     "4G", 14
#define _EBC1     "4G", 13
#define _EBC2     "4G", 12
#define _EBC3     "4G", 11
#define _EBCC     "4G", 15
#define _5EBEA    "5J", 3
#define _5EBEB    "5J", 6
#define _5EBEC    "5J", 8
#define _5EBED    "5J", 11
#define _EBEE     "4H", 8
#define _EBEF     "8H", 11


//*****circuit layout  *****
//from (output pins) - to (input pins)

/* Page 1 */

// player scoring (top, left)

CONNECTION(_5GANC,     "5G", 10)
CONNECTION(_1PERA,     "5G", 11)
CONNECTION(_2TQ10,     "5G", 13)
CONNECTION(_TLC8,      "5G", 12)
CONNECTION(_B999,      "5G", 14)

CONNECTION(_SCOR,      "8G", 9)
CONNECTION(_PONE,      "8G", 10)

CONNECTION(_SCOR,      "8G", 12)
CONNECTION(_5PONE,     "8G", 13)

  //PLAYER 1
CONNECTION(_SCA0,      "9J", 2)
CONNECTION(_SCA3,      "9J", 1)

CONNECTION(_5CREU,     "8K", 1)
CONNECTION(_5SCAA,     "8K", 9)
CONNECTION(GND,        "8K", 3)
CONNECTION(GND,        "8K", 4)
CONNECTION(GND,        "8K", 5)
CONNECTION(GND,        "8K", 6)
CONNECTION(_B999,      "8K", 7)
CONNECTION(_B999,      "8K", 10)
CONNECTION(_5SCOA,     "8K", 2)

CONNECTION(_SCB0,      "9J", 9)
CONNECTION(_SCB3,      "9J", 10)

CONNECTION(_5CREU,     "7K", 1)
CONNECTION(_5SCBB,     "7K", 9)
CONNECTION(GND,        "7K", 3)
CONNECTION(GND,        "7K", 4)
CONNECTION(GND,        "7K", 5)
CONNECTION(GND,        "7K", 6)
CONNECTION(_B999,      "7K", 7)
CONNECTION(_B999,      "7K", 10)
CONNECTION(_5SCAA,     "7K", 2)

CONNECTION(_SCC0,      "2J", 12)
CONNECTION(_SCC3,      "2J", 13)

CONNECTION(_5CREU,     "6K", 1)
CONNECTION(_5SCCC,     "6K", 9)
CONNECTION(GND,        "6K", 3)
CONNECTION(GND,        "6K", 4)
CONNECTION(GND,        "6K", 5)
CONNECTION(GND,        "6K", 6)
CONNECTION(_B999,      "6K", 7)
CONNECTION(_B999,      "6K", 10)
CONNECTION(_5SCBB,     "6K", 2)

  //PLAYER 2
CONNECTION(_SBA0,      "9J", 5)
CONNECTION(_SBA3,      "9J", 4)

CONNECTION(_5CREU,     "8L", 1)
CONNECTION(_5SBAA,     "8L", 9)
CONNECTION(GND,        "8L", 3)
CONNECTION(GND,        "8L", 4)
CONNECTION(GND,        "8L", 5)
CONNECTION(GND,        "8L", 6)
CONNECTION(_B999,      "8L", 7)
CONNECTION(_B999,      "8L", 10)
CONNECTION(_5SCOB,     "8L", 2)

CONNECTION(_SBB0,      "9J", 12)
CONNECTION(_SBB3,      "9J", 13)

CONNECTION(_5CREU,     "7L", 1)
CONNECTION(_5SBBB,     "7L", 9)
CONNECTION(GND,        "7L", 3)
CONNECTION(GND,        "7L", 4)
CONNECTION(GND,        "7L", 5)
CONNECTION(GND,        "7L", 6)
CONNECTION(_B999,      "7L", 7)
CONNECTION(_B999,      "7L", 10)
CONNECTION(_5SBAA,     "7L", 2)

CONNECTION(_SBC0,      "3L", 2)
CONNECTION(_SBC3,      "3L", 1)

CONNECTION(_5CREU,     "6L", 1)
CONNECTION(_5SBCC,     "6L", 9)
CONNECTION(GND,        "6L", 3)
CONNECTION(GND,        "6L", 4)
CONNECTION(GND,        "6L", 5)
CONNECTION(GND,        "6L", 6)
CONNECTION(_B999,      "6L", 7)
CONNECTION(_B999,      "6L", 10)
CONNECTION(_5SBBB,     "6L", 2)

// replay decoding and reset decoding for dots (top, right)
CONNECTION(VCC,        "SWREPLAYYN", 1)  //no replay
CONNECTION(GND,        "SWREPLAYYN", 2)  //replay enabled

CONNECTION(_SCA1,      "8J", 9)
CONNECTION(_SCA2,      "8J", 10)
CONNECTION(_SCB0,      "8J", 12)
CONNECTION(_SCB3,      "8J", 13)

CONNECTION(_SCC0,      "7H", 12)
CONNECTION(_SCC1,      "7H", 11)

CONNECTION(_5SCDA,     "9K", 5)
CONNECTION(_5SCDB,     "9K", 6)

CONNECTION(_SCDC,      "9K", 12)
CONNECTION(_SBDC,      "9K", 11)

CONNECTION(_5SEDA,     "9A", 13)

CONNECTION(_B999,      "7M", 10)
CONNECTION(_1SEDA,     "7M", 11)
CONNECTION(_TLC8,      "7M", 13)
CONNECTION(_GANC,      "7M", 12)
CONNECTION(_B999,      "7M", 14)

CONNECTION(_SBA1,      "9L", 9)
CONNECTION(_SBA2,      "9L", 10)
CONNECTION(_SBB0,      "9L", 12)
CONNECTION(_SBB3,      "9L", 13)

CONNECTION(_SBC0,      "9K", 2)
CONNECTION(_SBC1,      "9K", 3)

CONNECTION(_5SBDA,     "9K", 9)
CONNECTION(_5SBDB,     "9K", 8)

//unused? CONNECTION(_TLC8,     "2L", 12)
// CONNECTION(?,         "2L", 13)

CONNECTION(_SURV,     "0K", 4)
CONNECTION(_FLAB,     "0K", 5)

CONNECTION(_9XEFE,    "4M", 2)
CONNECTION(_5SEDA,    "4M", 3)

//skip: lamp drivers 1enda, 6enda, 6twop, 1ebel, 1ganc
//lamp drivers
//CONNECTION(_5ENDA,     "8M", 3)  //end of game
//#define _1ENDA   "8M", 4 DRIVES 2N3134 TRANSISTOR 
//#define _9XLEN   "8M", 4
//CONNECTION(_ENDA,      "8M", 5)  //player 1
//#define _6ENDA   "8M", 6 DRIVES 2N3134 TRANSISTOR
//#define _9XLP1   "8M", 6
//CONNECTION(_TWOP,      "8M", 9)  //player 2
//#define _6TWOP   "8M", 8 DRIVES 2N3134 TRANSISTOR
//#define _9XLP1   "8M", 8
//CONNECTION(_5EBEL,     "1K", 11)
//#define _1EBEL   "1K", 10
//#define _9XRBL   "1K", 10
//CONNECTION(_5GANC,     "1K", 13)
//#define _1GANC   "1K", 10
//#define _9XRPY   "1K", 10
//_5SUBL DRIVES 2N3134 TRANSISTOR as 9XLSB  //surv ball

//Ball counter and decoding (left, middle)
CONNECTION(_EBC3,     "7J", 5)
CONNECTION(_TWOP,     "7J", 4)
CONNECTION(_5PONE,    "7J", 2)
CONNECTION(_5PONE,    "7J", 1)

CONNECTION(_EBC3,     "7J", 9)
CONNECTION(_5TWOP,    "7J", 10)
CONNECTION(_PONE,     "7J", 12)
CONNECTION(_PONE,     "7J", 13)

CONNECTION(_NACL,     "1J", 5)
CONNECTION(_NACM,     "1J", 4)
CONNECTION(_CREU,     "1J", 3)

CONNECTION(_5CREU, "BUF2", 1)

CONNECTION(_5TPWR,    "6J", 1)
//CONNECTION(_5CREU,    "6J", 9)
CONNECTION("BUF2", 2, "6J", 9)
CONNECTION(_B999,     "6J", 3)
CONNECTION(GND,       "6J", 4)
CONNECTION(GND,       "6J", 5)
CONNECTION(GND,       "6J", 6)
CONNECTION(_7ENDA,    "6J", 7)
CONNECTION(_7ENDA,    "6J", 10)
CONNECTION(_5NABA,    "6J", 2)

CONNECTION(_NBA0,     "8J", 5)
CONNECTION(_5BL35,    "8J", 4)
CONNECTION(_5BL57,    "8J", 2)
CONNECTION(_EBC3,     "8J", 1)

CONNECTION(_7ENDA,    "7H", 9)
CONNECTION(_5NABA,    "7H", 8)

CONNECTION(VCC,       "SWBALLS35", 1) //vcc=3
CONNECTION(GND,       "SWBALLS35", 2) //gnd=5

CONNECTION(_9XBL5,    "1L", 12)
CONNECTION(_NBA2,     "1L", 11)

CONNECTION(_BL57,     "9A", 11)

CONNECTION(_9XBL5,    "1K", 9)

CONNECTION(_3XBL5,    "4M", 8)
CONNECTION(_NBA1,     "4M", 9)

CONNECTION(_BL35,     "4M", 5)
CONNECTION(_BL35,     "4M", 6)

//number gating (bottom, left)
CONNECTION(_TLC1,     "2F", 2)
CONNECTION(_TLC2,     "2F", 1)

CONNECTION(_NGTA,     "3F", 2)
CONNECTION(_TLC3,     "3F", 3)

CONNECTION(_5PVBU,    "3F", 9)
CONNECTION(_5NGTB,    "3F", 8)

CONNECTION(_NGTC,     "4B", 9)

CONNECTION(_5TEC3,    "1G", 5)
CONNECTION(_TEC4,     "1G", 4)
CONNECTION(_TEC5,     "1G", 2)
CONNECTION(_TEC6,     "1G", 1)

CONNECTION(_5DNBA,    "3F", 5)
CONNECTION(_TEC7,     "3F", 6)

CONNECTION(_TLC1,     "2F", 12)
CONNECTION(_5TLC2,    "2F", 13)

CONNECTION(_TEC3,     "3H", 5)
CONNECTION(_TEC4,     "3H", 4)
CONNECTION(_5TEC5,    "3H", 2)
CONNECTION(_TEC6,     "3H", 1)

CONNECTION(_FNCA,     "3H", 9)
CONNECTION(_5CRBK,    "3H", 10)
CONNECTION(_TEC7,     "3H", 12)
CONNECTION(_TEC7,     "3H", 13)

CONNECTION(_TEC3,     "2H", 2)
CONNECTION(_TEC4,     "2H", 1)

CONNECTION(_5GNCA,    "2F", 5)
CONNECTION(_TEC5,     "2F", 4)

CONNECTION(_FNCB,     "3F", 12)
CONNECTION(_GNCB,     "3F", 11)

CONNECTION(_TEC6,     "1G", 9)
CONNECTION(_5TEC5,    "1G", 10)
CONNECTION(_5TEC4,    "1G", 12)
CONNECTION(_5TEC3,    "1G", 13)

CONNECTION(_5GBCA,    "2H", 12)
CONNECTION(_5CNPA,    "2H", 13)

CONNECTION(_GBCB,     "0J", 5)
CONNECTION(_FNCB,     "0J", 4)
CONNECTION(_DNBB,     "0J", 3)

CONNECTION(_5GBCC,    "4B", 5)

CONNECTION(_5TEC6,    "2H", 5)
CONNECTION(_TEC5,     "2H", 4)

CONNECTION(_5TEC4,    "2H", 9)
CONNECTION(_TEC3,     "2H", 10)

CONNECTION(_TEC4,     "0G", 2)
CONNECTION(_TEC5,     "0G", 1)

CONNECTION(_AERB,     "2F", 9)
CONNECTION(_AERA,     "2F", 10)

CONNECTION(_TEC6,     "1H", 9)
CONNECTION(_5TEC7,    "1H", 10)
CONNECTION(_AERC,     "1H", 12)
CONNECTION(_AERC,     "1H", 13)

CONNECTION(_5TEC5,    "1H", 5)
CONNECTION(_5TEC6,    "1H", 4)
CONNECTION(_TEC7,     "1H", 2)
CONNECTION(_5GNCA,    "1H", 1)

CONNECTION(_5ENDA,    "0H", 5)
CONNECTION(_FLA3,     "0H", 4)
CONNECTION(_5ZERO,    "0H", 2)
CONNECTION(_5ZERO,    "0H", 1)

//AERROW GATING
CONNECTION(_TEC2,     "2G", 5)
CONNECTION(_5TEC3,    "2G", 4)
CONNECTION(_TEC4,     "2G", 2)
CONNECTION(_5TLC1,    "2G", 1)

CONNECTION(_5TEC2,    "2G", 9)
CONNECTION(_TEC3,     "2G", 10)
CONNECTION(_TEC4,     "2G", 12)
CONNECTION(_NGTA,     "2G", 13)

CONNECTION(_ACLN,     "0J", 9)
CONNECTION(_AFNA,     "0J", 10)
CONNECTION(_AFNB,     "0J", 11)

CONNECTION(_TEC4,     "3G", 5)
CONNECTION(_5TEC3,    "3G", 4)
CONNECTION(_5TEC2,    "3G", 2)
CONNECTION(_5TLC1,    "3G", 1)

CONNECTION(_5TEC4,    "3G", 9)
CONNECTION(_TEC3,     "3G", 10)
CONNECTION(_TEC2,     "3G", 12)
CONNECTION(_NGTA,     "3G", 13)

CONNECTION(_ACLN,     "0J", 13)
CONNECTION(_AFNC,     "0J", 2)
CONNECTION(_AFND,     "0J", 1)

CONNECTION(_5AERD,    "1J", 9)
CONNECTION(_5AFNE,    "1J", 10)
CONNECTION(_5ARBK,    "1J", 11)

CONNECTION(_5AERE,    "1J", 13)
CONNECTION(_5AFNF,    "1J", 2)
CONNECTION(_5ASBK,    "1J", 1)

CONNECTION(_AFNG,     "3J", 9)
CONNECTION(_AFNH,     "3J", 8)

CONNECTION(_5AGOT,    "3J", 12)
CONNECTION(_5NGTC,    "3J", 11)

CONNECTION(_SURV,     "2J", 2)
CONNECTION(_FLA3,     "2J", 1)

CONNECTION(_PONE,     "2J", 5)
CONNECTION(_5SUBK,    "2J", 4)

CONNECTION(_5SUBK,    "2J", 9)
CONNECTION(_5PONE,    "2J", 10)

//NUMBER MULTIPLEXER
CONNECTION(_CRA0,     "5K", 12)
CONNECTION(_SBA0,     "5K", 13)
CONNECTION(_SBB0,     "5K", 14)
CONNECTION(_SBC0,     "5K", 15)
CONNECTION(_NBA0,     "5K", 1)
CONNECTION(_SCA0,     "5K", 2)
CONNECTION(_SCB0,     "5K", 3)
CONNECTION(_SCC0,     "5K", 4)
CONNECTION(_5GNCC,    "5K", 7)
CONNECTION(_1TEG7,    "5K", 9)
CONNECTION(_1TEC4,    "5K", 10)
CONNECTION(_ILSB,     "5K", 11)

CONNECTION(_CRA1,     "5L", 12)
CONNECTION(_SBA1,     "5L", 13)
CONNECTION(_SBB1,     "5L", 14)
CONNECTION(_SBC1,     "5L", 15)
CONNECTION(_NBA1,     "5L", 1)
CONNECTION(_SCA1,     "5L", 2)
CONNECTION(_SCB1,     "5L", 3)
CONNECTION(_SCC1,     "5L", 4)
CONNECTION(_5GNCC,    "5L", 7)
CONNECTION(_1TEG7,    "5L", 9)
CONNECTION(_1TEC4,    "5L", 10)
CONNECTION(_ILSB,     "5L", 11)

CONNECTION(_CRA2,     "4K", 12)
CONNECTION(_SBA2,     "4K", 13)
CONNECTION(_SBB2,     "4K", 14)
CONNECTION(_SBC2,     "4K", 15)
CONNECTION(_NBA2,     "4K", 1)
CONNECTION(_SCA2,     "4K", 2)
CONNECTION(_SCB2,     "4K", 3)
CONNECTION(_SCC2,     "4K", 4)
CONNECTION(_5GNCC,    "4K", 7)
CONNECTION(_1TEG7,    "4K", 9)
CONNECTION(_1TEC4,    "4K", 10)
CONNECTION(_ILSB,     "4K", 11)

CONNECTION(_CRA3,     "4L", 12)
CONNECTION(_SBA3,     "4L", 13)
CONNECTION(_SBB3,     "4L", 14)
CONNECTION(_SBC3,     "4L", 15)
CONNECTION(_NBA3,     "4L", 1)
CONNECTION(_SCA3,     "4L", 2)
CONNECTION(_SCB3,     "4L", 3)
CONNECTION(_SCC3,     "4L", 4)
CONNECTION(_5GNCC,    "4L", 7)
CONNECTION(_1TEG7,    "4L", 9)
CONNECTION(_1TEC4,    "4L", 10)
CONNECTION(_ILSB,     "4L", 11)

//NUMBER CHARACTER GENERATION
CONNECTION(_NCA3,     "4B", 13)

CONNECTION(_DNBB,     "0G", 5)
CONNECTION(_TEC3,     "0G", 4)

CONNECTION(_5TEC0,    "0H", 9)
CONNECTION(_5TEC1,    "0H", 10)
CONNECTION(_5TEC2,    "0H", 12)
CONNECTION(_5TEC2,    "0H", 13)

CONNECTION(_NGTA,     "2L", 9)
CONNECTION(_TLC3,     "2L", 10)

CONNECTION(_NCA2,     "3K", 14)
CONNECTION(_NCA1,     "3K", 13)
CONNECTION(_NCA0,     "3K", 12)
CONNECTION(_5TLC2,    "3K", 11)
CONNECTION(_5TLC1,    "3K", 10)
CONNECTION(GND,       "3K", 15)

CONNECTION(_NCG7,     "0F", 9)
CONNECTION(_5NCHA,    "0F", 10)
CONNECTION(_5NCHB,    "0F", 12)
CONNECTION(_5NCHB,    "0F", 13)

CONNECTION(_NCG6,     "4F", 9)
CONNECTION(_5NCHA,    "4F", 10)
CONNECTION(_5NCHC,    "4F", 12)
CONNECTION(_5NCHC,    "4F", 13)

CONNECTION(_NCG4,     "3L", 5)
CONNECTION(_NLC3,     "3L", 4)

CONNECTION(_NCG3,     "3L", 9)
CONNECTION(_5NCA3,    "3L", 10)

CONNECTION(_NCG2,     "3L", 12)
CONNECTION(_5NCA3,    "3L", 13)

CONNECTION(GND,       "2K", 14)
CONNECTION(_NCH7,     "2K", 12)
CONNECTION(_NCH7,     "2K", 11)
CONNECTION(_NCH6,     "2K", 10)
CONNECTION(_NCH6,     "2K", 5)
CONNECTION(_NCG5,     "2K", 4)
CONNECTION(_NCG5,     "2K", 3)
CONNECTION(GND,       "2K", 2)
CONNECTION(GND,       "2K", 1)
CONNECTION(_5LODD,    "2K", 15)
CONNECTION(_NGTC,     "2K", 9)
CONNECTION(GND,       "2K", 6)
CONNECTION(_6TQ05,    "2K", 7)


/* Page 2 */

// master timing generation (top, left)

CONNECTION(_1TQ10,     "1A", 2)
CONNECTION(_1TQ10,     "1A", 1)

CONNECTION(_6TQ10,     "1A", 5)
CONNECTION(_6TQ10,     "1A", 4)

CONNECTION(_T999,      "1B", 4)
CONNECTION(_T999,      "1B", 3)
CONNECTION(_1TQ10,     "1B", 1)
CONNECTION(_T999,      "1B", 2)
CONNECTION(_T999,      "1B", 15)

CONNECTION(_1TQ05,     "1A", 9)
CONNECTION(_1TQ05,     "1A", 10)

CONNECTION(_6TQ05,     "1A", 12)
CONNECTION(_6TQ05,     "1A", 13)

CONNECTION(_T999,      "1B", 10)
CONNECTION(_5TEC5,     "1B", 11)
CONNECTION(_2TQ05,     "1B", 13)
CONNECTION(_TEC5,      "1B", 12)
CONNECTION(_TEC8,      "1B", 14)

CONNECTION(_THSC,      "1C", 2)
CONNECTION(_THSC,      "1C", 1)

CONNECTION(_6THSC,     "1C", 5)
CONNECTION(_6THSC,     "1C", 4)

CONNECTION(_5THSC,     "4A", 12)
CONNECTION(_5TVSC,     "4A", 13)

  //columns
CONNECTION(_T999,      "2A", 1)
CONNECTION(_5TECC,     "2A", 9)
CONNECTION(_5TEC8,     "2A", 3)
CONNECTION(GND,        "2A", 4)
CONNECTION(_5TEC8,     "2A", 5)
CONNECTION(_T999,      "2A", 6)
CONNECTION(_T999,      "2A", 7)
CONNECTION(_T999,      "2A", 10)
CONNECTION(_6TQ05,     "2A", 2)

CONNECTION(_T999,      "2B", 1)
CONNECTION(_5TECC,     "2B", 9)
CONNECTION(_5TEC8,     "2B", 3)
CONNECTION(_5TEC8,     "2B", 4)
CONNECTION(GND,        "2B", 5)
CONNECTION(_5TEC8,     "2B", 6)
CONNECTION(_TECA,      "2B", 7)
CONNECTION(_TEC3,      "2B", 10)
CONNECTION(_6TQ05,     "2B", 2)

CONNECTION(_TECB,      "2C", 2)
CONNECTION(_TECA,      "2C", 1)

CONNECTION(_5TECC,     "0B", 11)

CONNECTION(_T999,      "3A", 4)
CONNECTION(_1TECC,     "3A", 3)
CONNECTION(_2TQ05,     "3A", 1)
CONNECTION(_1TECC,     "3A", 2)
CONNECTION(_T999,      "3A", 15)

CONNECTION(_TECB,      "2C", 5)
CONNECTION(_TEC8,      "2C", 4)

CONNECTION(_5TECD,     "2C", 9)
CONNECTION(_TEC8,      "2C", 10)

CONNECTION(_TEC7,      "2C", 12)
CONNECTION(_5TECD,     "2C", 13)

CONNECTION(_5TEG7,     "0B", 13)

CONNECTION(_TEC5,      "4B", 1)

  //lines
CONNECTION(_TLC2,      "0L", 12)
CONNECTION(_TLC3,      "0L", 13)

CONNECTION(_T999,      "3B", 1)
CONNECTION(_5TLCC,     "3B", 9)
CONNECTION(GND,        "3B", 3)
CONNECTION(GND,        "3B", 4)
CONNECTION(_TLC8,      "3B", 5)
CONNECTION(GND,        "3B", 6)
CONNECTION(_T999,      "3B", 7)
CONNECTION(_T999,      "3B", 10)
CONNECTION(_6THSC,     "3B", 2)

CONNECTION(_T999,      "3C", 1)
CONNECTION(_5TLCC,     "3C", 9)
CONNECTION(GND,        "3C", 3)
CONNECTION(_5TLC8,     "3C", 4)
CONNECTION(_5TLC8,     "3C", 5)
CONNECTION(_5TLC8,     "3C", 6)
CONNECTION(_TLCA,      "3C", 7)
CONNECTION(_TL32,      "3C", 10)
CONNECTION(_6THSC,     "3C", 2)

CONNECTION(_TLCB,      "4A", 2)
CONNECTION(_TLCA,      "4A", 1)

CONNECTION(_5TLCC,     "4B", 3)

CONNECTION(_T999,      "3A", 10)
CONNECTION(_1TLCC,     "3A", 11)
CONNECTION(_2THSC,     "3A", 13)
CONNECTION(_1TLCC,     "3A", 12)
CONNECTION(_T999,      "3A", 14)

CONNECTION(_TLCB,      "4A", 5)
CONNECTION(_TLC8,      "4A", 4)

CONNECTION(_5TLCD,     "4A", 9)
CONNECTION(_TLC8,      "4A", 10)

CONNECTION(_TLC4,      "4D", 5)
CONNECTION(_TLC3,      "4D", 4)
CONNECTION(_TLC2,      "4D", 3)

CONNECTION(_TCSA,      "4C", 9)
CONNECTION(_TLC8,      "4C", 10)

CONNECTION(_TEC2,      "2D", 1)
CONNECTION(_TEC3,      "2D", 3)
CONNECTION(_TEC4,      "2D", 5)
CONNECTION(_5TEC4,     "2D", 9)
CONNECTION(_5TEC5,     "2D", 11)
CONNECTION(_TEC6,      "2D", 13)

CONNECTION(_TEC7,      "3D", 1)
CONNECTION(_TEC1,      "3D", 3)
CONNECTION(_TEC0,      "3D", 5)
CONNECTION(_TLC1,      "3D", 9)
CONNECTION(_TLC2,      "3D", 11)
CONNECTION(_5PGOT,     "3D", 13)

//Horz Boundry and Blanking (top, right)
CONNECTION(_TECA,      "1D", 9)
CONNECTION(_5TEC7,     "1D", 10)

CONNECTION(_TEC4,      "1E", 9)
CONNECTION(_1TEC5,     "1E", 10)
CONNECTION(_TEC6,      "1E", 12)
CONNECTION(_TEC7,      "1E", 13)

CONNECTION(_T999,      "0C", 4)
CONNECTION(_TLNA,      "0C", 3)
CONNECTION(_2TQ05,     "0C", 1)
CONNECTION(_TLHB,      "0C", 2)
CONNECTION(_T999,      "0C", 15)

CONNECTION(_T999,      "0C", 10)
CONNECTION(_TLNC,      "0C", 11)
CONNECTION(_2TQ05,     "0C", 13)
CONNECTION(_5TLNC,     "0C", 12)
CONNECTION(_T999,      "0C", 14)

CONNECTION(_TLNC,      "2E", 12)
CONNECTION(_TLND,      "2E", 13)

CONNECTION(_5TLND,     "1D", 12)
CONNECTION(_5TLNC,     "1D", 13)

//Composit Video Output Gating (center, middle)
CONNECTION(_1TLCC,     "0L", 5)
CONNECTION(_TLC8,      "0L", 4)

CONNECTION(_TLGV,      "3J", 2)
CONNECTION(_5TLC8,     "3J", 3)

CONNECTION(_5TVBL,     "3J", 5)
CONNECTION(_THBL,      "3J", 6)

CONNECTION(_COBL,      "0K", 2)
CONNECTION(_VIDA,      "0K", 1)

CONNECTION(_1GBCC,     "0L", 2)  //number gate
CONNECTION(_NCIV,      "0L", 1)  //number video

CONNECTION(_NCOT,      "1L", 5)
CONNECTION(_1TBCF,     "1L", 6)

CONNECTION(_5TLBG,     "9L", 5)
CONNECTION(_5PGOT,     "9L", 4)
CONNECTION(_5ALVD,     "9L", 2)
CONNECTION(_5RVID,     "9L", 1)

CONNECTION(_TLGV,      "1L", 2)
CONNECTION(_1BVCF,     "1L", 3) //ball video

CONNECTION(_5TBCF,     "8M", 13)

CONNECTION(_AROT,      "1L", 9) //aerrow video
CONNECTION(_TLNE,      "1L", 8) //top line and video

//DOT RESET AND PLAYER DOT SET SELECTION (left, middle)
CONNECTION(_T999,      "5A", 4)
CONNECTION(_RESA,      "5A", 3)
CONNECTION(_2TQ05,     "5A", 1)
CONNECTION(_WRTA,      "5A", 2)
CONNECTION(_T999,      "5A", 15)

CONNECTION(_T999,      "5A", 10)
CONNECTION(_WRTZ,      "5A", 11)
CONNECTION(_5TVSC,     "5A", 13)
CONNECTION(_WRTA,      "5A", 12)
CONNECTION(_T999,      "5A", 14)

CONNECTION(_5GANC,     "4C", 2)
CONNECTION(_5CREU,     "4C", 1)

CONNECTION(_WRTA,      "5D", 2)
CONNECTION(_CREU,      "5D", 1)

CONNECTION(_WRTB,      "4E", 2)
CONNECTION(_PONE,      "4E", 3)

//DOT VIDEO UNBLANKED AND UNSHAPED (left, bottom)

  //player 1 dot memory
CONNECTION(_5PONF,     "5B", 3)
CONNECTION(_5PONF,     "5B", 4)
CONNECTION(_5PONF,     "5B", 5)
CONNECTION(_5RTEA,     "5B", 12)
 CONNECTION(_5WRTA,     "BUF4", 1)
 CONNECTION("BUF4", 2,     "5B", 13)
//CONNECTION(_5WRTA,     "5B", 13)
CONNECTION(_TLC7,      "5B", 11)
CONNECTION(_TLC6,      "5B", 10)
CONNECTION(_TLC5,      "5B", 9)
CONNECTION(_TLC4,      "5B", 7)
CONNECTION(_TEC7,      "5B", 14)
CONNECTION(_TEC6,      "5B", 15)
CONNECTION(_1TEC5,     "5B", 1)
CONNECTION(_1TEC4,     "5B", 2)

CONNECTION(_WRTB,      "4E", 5)
CONNECTION(_5PONE,     "4E", 6)

CONNECTION(_5PONG,     "5C", 3)
CONNECTION(_5PONG,     "5C", 4)
CONNECTION(_5PONG,     "5C", 5)
CONNECTION(_5RTEA,     "5C", 12)
 CONNECTION("BUF4", 2,  "5C", 13)
 //CONNECTION(_5WRTA,     "5C", 13)
CONNECTION(_TLC7,      "5C", 11)
CONNECTION(_TLC6,      "5C", 10)
CONNECTION(_TLC5,      "5C", 9)
CONNECTION(_TLC4,      "5C", 7)
CONNECTION(_TEC7,      "5C", 14)
CONNECTION(_TEC6,      "5C", 15)
CONNECTION(_1TEC5,     "5C", 1)
CONNECTION(_1TEC4,     "5C", 2)

CONNECTION(_5PVBL,     "0K", 9)
CONNECTION(_5PVBL,     "0K", 10)

CONNECTION(_TLC4,      "1F", 1)
CONNECTION(_TLC5,      "1F", 3)
CONNECTION(_TLC6,      "1F", 5)
CONNECTION(_TLC7,      "1F", 9)
CONNECTION(_THBL,      "1F", 11)
CONNECTION(_5RRLM,     "1F", 13)

//DOT SHAPING AND INTERCEPT GENERATION (left, center)
CONNECTION(_TEC0,      "2E", 2)
CONNECTION(_TEC1,      "2E", 1)

CONNECTION(_TLC0,      "2E", 5)
CONNECTION(_TLC1,      "2E", 4)

CONNECTION(_TE10,      "4C", 5)
CONNECTION(_TL10,      "4C", 4)

CONNECTION(_TEC2,      "2E", 9)
CONNECTION(_TEC3,      "2E", 10)

CONNECTION(_TLC2,      "3E", 2)
CONNECTION(_TLC3,      "3E", 1)

CONNECTION(_PGHT,      "1D", 2)
CONNECTION(_PVGT,      "1D", 1)

CONNECTION(_TEC2,      "3E", 5)
CONNECTION(_TEC1,      "3E", 4)

CONNECTION(_TLC2,      "3E", 9)
CONNECTION(_TLC1,      "3E", 10)

CONNECTION(_PHGU,      "4E", 9)
CONNECTION(_PVGU,      "4E", 8)

CONNECTION(_5CONR,     "1E", 5)
CONNECTION(_PGTA,      "1E", 4)
CONNECTION(_PGTB,      "1E", 2)
CONNECTION(_PGTB,      "1E", 1)

CONNECTION(_PGTC,      "0D", 9)
CONNECTION(_PVID,      "0D", 10)
CONNECTION(_5PVBU,     "0D", 12)
CONNECTION(_5PVBL,     "0D", 13)

CONNECTION(_5TLC4,     "0D", 5)
CONNECTION(_5TLC5,     "0D", 4)
CONNECTION(_5TLC6,     "0D", 2)
CONNECTION(_5TLC7,     "0D", 1)

CONNECTION(_TLC4,      "0E", 5)
CONNECTION(_TLC5,      "0E", 4)
CONNECTION(_TLC6,      "0E", 2)
CONNECTION(_TLC7,      "0E", 1)

CONNECTION(_1PGOT,     "0F", 5)
CONNECTION(_1BVCF,     "0F", 4)
CONNECTION(_ENDA,      "0F", 2)
CONNECTION(_ENDA,      "0F", 1)

CONNECTION(_1PERA,     "4E", 12)
CONNECTION(_WRTA,      "4E", 11)

//PADDLE GENERATION (bottom, right)

  //limit and end of game position
CONNECTION(_1TEG7,     "1D", 5)
CONNECTION(_5TEC8,     "1D", 4)

CONNECTION(_TEC0,     "0E", 9)
CONNECTION(_1TEC5,    "0E", 10)
CONNECTION(_TEC6,     "0E", 12)
CONNECTION(_TE78,     "0E", 13)

CONNECTION(_TE78,     "4C", 12)
CONNECTION(_5ENDA,    "4C", 13)

CONNECTION(_5RRLA,    "5D", 5)
CONNECTION(_5RRLB,    "5D", 4)

CONNECTION(_5RRLM,    "7M", 4)
CONNECTION(_RPFA,     "7M", 3)
CONNECTION(_6TQ05,    "7M", 1)
CONNECTION(GND,       "7M", 2)
CONNECTION(_5THBL,    "7M", 15)

CONNECTION(_T999,     "5E", 4)
CONNECTION(_RLAA,     "5E", 3)
CONNECTION(_2TQ10,    "5E", 1)
CONNECTION(_RLAA,     "5E", 2)
CONNECTION(_5THBL,    "5E", 15)

CONNECTION(_5THBL,    "6A", 1)
CONNECTION(_T999,     "6A", 9)
CONNECTION(GND,       "6A", 3)  //not shown
CONNECTION(GND,       "6A", 4)  //not shown
CONNECTION(GND,       "6A", 5)  //not shown
CONNECTION(GND,       "6A", 6)  //not shown
CONNECTION(_T999,     "6A", 7)
CONNECTION(_RGTE,     "6A", 10)
CONNECTION(_5RLA0,    "6A", 2) //not labeled on diagram

CONNECTION(_T999,     "5E", 10)
CONNECTION(_RBLA,     "5E", 11)
CONNECTION(_RLA0,     "5E", 13)
CONNECTION(GND,       "5E", 12)
CONNECTION(_5THBL,    "5E", 14)

CONNECTION(_RLAA,     "7C", 2)
CONNECTION(_RBLB,     "7C", 1)

 //
CONNECTION(_TL01,     "1C", 12)
CONNECTION(_TL01,     "1C", 13)

CONNECTION(_RLA3,     "3E", 12)
CONNECTION(_RLA4,     "3E", 13)

CONNECTION(_TLC0,     "4D", 9)
CONNECTION(_TLC1,     "4D", 10)
CONNECTION(_TLC2,     "4D", 11)

CONNECTION(_5EHIT,    "6B", 5)
CONNECTION(_RL34,     "6B", 4)
CONNECTION(_5TL01,    "6B", 2)
CONNECTION(_5TL01,    "6B", 1)

CONNECTION(_RLA1,     "0K", 12)
CONNECTION(_RLA1,     "0K", 13)

 // position control
CONNECTION(_5TEC8,    "7A", 2)
CONNECTION(_1RRLM,    "7A", 1)

CONNECTION(_5RRST,    "7A", 5)
CONNECTION(_ENDA,     "7A", 4)

//  CONNECTION(_5RRSU,    "X7405", 1)
//  CONNECTION(_5RRSU,    "X7405", 3)
//  CONNECTION(_5RRSU,    "X7405", 5)
//  CONNECTION(_5RRSU,    "X7405", 9)
//  CONNECTION(_5RRSU,    "X7405", 11)
//  CONNECTION(_5RRSU,    "X7405", 13)
//9XPAD input

 //shape of paddle
CONNECTION(_RLA4,     "6C", 14)
CONNECTION(_RLA3,     "6C", 13)
CONNECTION(_RLA2,     "6C", 12)
CONNECTION(_RLA1,     "6C", 11)
CONNECTION(_RLA0,     "6C", 10)
CONNECTION(GND,       "6C", 15)  //not labeled on diagram

CONNECTION(_RAT7,     "6D", 12)
CONNECTION(_RAT6,     "6D", 13)
CONNECTION(_RAT5,     "6D", 14)
CONNECTION(_RAT4,     "6D", 15)
CONNECTION(_RAT3,     "6D", 1)
CONNECTION(_RAT2,     "6D", 2)
CONNECTION(_RAT1,     "6D", 3)
CONNECTION(_RAT0,     "6D", 4)
CONNECTION(_5HITA,    "6D", 7)
CONNECTION(_TLC2,     "6D", 9)
CONNECTION(_TLC1,     "6D", 10)
CONNECTION(_TLC0,     "6D", 11)

// selection of bottom 8 lines for paddle visible
CONNECTION(_RGTE,     "6E", 5)
CONNECTION(_1PVBL,    "6E", 4)
CONNECTION(_TLC3,     "6E", 2)
CONNECTION(_RVIA,     "6E", 1)


/* Page 3 */

// BALL CONTROL LOGIC (top, left)

  // paddle and ball intercept register
CONNECTION(_5RLA1,     "7B", 3)
CONNECTION(_RLA2,      "7B", 4)
CONNECTION(_RLA3,      "7B", 6)
CONNECTION(_T999,      "7B", 11)
CONNECTION(GND,        "7B", 13) //not shown
CONNECTION(GND,        "7B", 14) //not shown
CONNECTION(_5ESCL,     "7B", 1)
CONNECTION(_1KBAR,     "7B", 9)

CONNECTION(_5RHD1,     "7A", 9)
CONNECTION(_5RHCL,     "7A", 10)

CONNECTION(_RH12,      "7C", 5)
CONNECTION(_5BSCL,     "7C", 4)

CONNECTION(_RHD2,      "7C", 9)
CONNECTION(_5BSCL,     "7C", 10)

CONNECTION(_RHD3,      "7C", 12)
CONNECTION(_5BSCL,     "7C", 13)

  // ball control memory
CONNECTION(_5BSUP,     "7D", 14)
CONNECTION(_5BSCL,     "7D", 13)
CONNECTION(_RSP3,      "7D", 12)
CONNECTION(_RSP2,      "7D", 11)
CONNECTION(_RSP1,      "7D", 10)
CONNECTION(GND,        "7D", 15)

CONNECTION(_5ENDA,     "6F", 2)
CONNECTION(_SURV,      "6F", 3)

CONNECTION(_1BVCF,     "7G", 2)
CONNECTION(_TLNE,      "7G", 1)

CONNECTION(_TLC4,      "5D", 9)
CONNECTION(_TLC8,      "5D", 10)

CONNECTION(_TL48,      "1C", 9)
CONNECTION(_TL48,      "1C", 10)

CONNECTION(_1RVID,     "7G", 5)
CONNECTION(_ENDD,      "7G", 4)

CONNECTION(_RVIC,      "7G", 9)
CONNECTION(_1BVCF,     "7G", 10)

CONNECTION(_ENDA,      "0G", 10)
CONNECTION(_TLC8,      "0G", 9)

CONNECTION(_KBAL,      "9D", 2)
CONNECTION(_1TEG7,     "9D", 1)

CONNECTION(_RLA4,      "0G", 12)
CONNECTION(_T999,      "0G", 13)

CONNECTION(_KBAL,      "9F", 2)
CONNECTION(_5TEG7,     "9F", 1)

CONNECTION(_5PHLB,     "9E", 4)
CONNECTION(_5RLA4,     "9E", 3)
CONNECTION(_1KBAR,     "9E", 1)
CONNECTION(_RLA4,      "9E", 2)
CONNECTION(_5PHRC,     "9E", 15)

CONNECTION(_5UPAA,     "9E", 10)
CONNECTION(_SURV,      "9E", 11)
CONNECTION(_6TQ05,     "9E", 13)
CONNECTION(GND,        "9E", 12)
CONNECTION(_5KBAS,     "9E", 14)

CONNECTION(_5TL48,     "3M", 10)
CONNECTION(GND,        "3M", 11)
CONNECTION(_6THSC,     "3M", 13)
CONNECTION(_NGTA,      "3M", 12)
CONNECTION(_T999,      "3M", 14)

CONNECTION(_TL49,      "8G", 2)
CONNECTION(_1BVCF,     "8G", 1)

CONNECTION(_5TLC8,     "9F", 5)
CONNECTION(_1TLCC,     "9F", 4)

CONNECTION(_5BVCF,     "6F", 12)
CONNECTION(_5UPEA,     "6F", 11)

CONNECTION(_5ENDA,     "9F", 9)
CONNECTION(_UPEB,      "9F", 10)

CONNECTION(_ENDA,      "9F", 12)
CONNECTION(_1KBAR,     "9F", 13)

CONNECTION(_5UPEC,     "7G", 12)
CONNECTION(_5UPGA,     "7G", 13)

//BALL GENERATION (top, right)
  //horz
CONNECTION(_BEGH,      "7A", 12)
CONNECTION(_1BLGE,     "7A", 13)

CONNECTION(_5SURV,     "7E", 1)
CONNECTION(_5BELD,     "7E", 9)
CONNECTION(_BPE0,      "7E", 3)
CONNECTION(_BPE1,      "7E", 4)
CONNECTION(_BPE2,      "7E", 5)
CONNECTION(_BPE3,      "7E", 6)
CONNECTION(_6TEG8,     "7E", 7)
CONNECTION(_6TEG8,     "7E", 10)
CONNECTION(_6TQ10,     "7E", 2)

CONNECTION(_N999,      "7F", 10)
CONNECTION(_BECA,      "7F", 11)
CONNECTION(_2TQ10,     "7F", 13)
CONNECTION(_BECA,      "7F", 12)
CONNECTION(_5SURV,     "7F", 14)

CONNECTION(_BECB,      "5D", 12)
CONNECTION(_BECA,      "5D", 13)

CONNECTION(_N999,      "8F", 1)
CONNECTION(_5SURV,     "8F", 9)
CONNECTION(GND,        "8F", 3)
CONNECTION(GND,        "8F", 4)
CONNECTION(GND,        "8F", 5)
CONNECTION(_N999,      "8F", 6)
CONNECTION(_BEBB,      "8F", 7)
CONNECTION(_BEBB,      "8F", 10)
CONNECTION(_6TQ10,     "8F", 2)

CONNECTION(_BEGA,      "9B", 2)
CONNECTION(_BEGB,      "9B", 3)

CONNECTION(_BECC,      "8A", 3)
CONNECTION(_BEGA,      "8A", 4)
CONNECTION(_BEGB,      "8A", 6)
CONNECTION(_BEGC,      "8A", 11)
CONNECTION(_BEGD,      "8A", 13)
CONNECTION(_BEGE,      "8A", 14)
CONNECTION(_N999,      "8A", 1)
CONNECTION(_6TQ10,     "8A", 9)

CONNECTION(_BEGF,      "8B", 3)
CONNECTION(_BEGG,      "8B", 4)
CONNECTION(_PERA,      "8B", 6)
CONNECTION(_KBAR,      "8B", 11)
CONNECTION(_5TEG8,     "8B", 13)
CONNECTION(_5CVID,     "8B", 14)
CONNECTION(_N999,      "8B", 1)
CONNECTION(_6TQ10,     "8B", 9)

//hack to fix paddle "HIT" wording
 CONNECTION(_6TQ10,     "BUF5", 1)

 CONNECTION(_5CVID,     "8B2", 14)
 CONNECTION(_N999,      "8B2", 1)
 CONNECTION("BUF5", 2,  "8B2", 9)

CONNECTION(_BEGC,      "9B", 5)
CONNECTION(_BEGD,      "9B", 6)

CONNECTION(_BEGE,      "9B", 9)
CONNECTION(_BEGF,      "9B", 8)

CONNECTION(_BEGG,      "9B", 12)
CONNECTION(_BEGH,      "9B", 11)

CONNECTION(_5BVAA,     "9C", 9)
CONNECTION(_5BVAB,     "9C", 10)
CONNECTION(_5BVAC,     "9C", 12)
CONNECTION(_5BVAD,     "9C", 13)

CONNECTION(_5BVAA,     "9D", 5)
CONNECTION(_5BVAD,     "9D", 4)

CONNECTION(_5BLGA,     "9D", 9)
CONNECTION(_5BLGD,     "9D", 10)

CONNECTION(_BVCA,      "9D", 12)
CONNECTION(_BVCB,      "9D", 13)

  //vert
CONNECTION(_5SURV,      "8D", 1)
CONNECTION(_5BLGE,      "8D", 9)
CONNECTION(_BPL0,       "8D", 3)
CONNECTION(_BPL1,       "8D", 4)
CONNECTION(_BPL2,       "8D", 5)
CONNECTION(_BPL3,       "8D", 6)
CONNECTION(_5TLG8,      "8D", 7)
CONNECTION(_5TLG8,      "8D", 10)
CONNECTION(_6THSC,      "8D", 2)

CONNECTION(_N999,       "8E", 1)
CONNECTION(_5SURV,      "8E", 9)
CONNECTION(GND,         "8E", 3)
CONNECTION(_N999,       "8E", 4)
CONNECTION(GND,         "8E", 5)
CONNECTION(GND,         "8E", 6)
CONNECTION(_BLCA,       "8E", 7)
CONNECTION(_BLCA,       "8E", 10)
CONNECTION(_6THSC,      "8E", 2)

CONNECTION(_BLCB,       "9A", 3)

CONNECTION(_5BLCB,      "8C", 3)
CONNECTION(_5BLGA,      "8C", 4)
CONNECTION(_5BLGB,      "8C", 6)
CONNECTION(_5BLGC,      "8C", 11)
CONNECTION(_5BLGD,      "8C", 13)
CONNECTION(_N999,       "8C", 14)
CONNECTION(_9XWRR,      "8C", 1)
CONNECTION(_6THSC,      "8C", 9)

CONNECTION(_5BLGA,      "9C", 5)
CONNECTION(_5BLGB,      "9C", 4)
CONNECTION(_5BLGC,      "9C", 2)
CONNECTION(_5BLGD,      "9C", 1)

CONNECTION(_BVBA,       "6M", 9)
CONNECTION(_BVCD,       "6M", 10)
CONNECTION(_BVCE,       "6M", 12)
CONNECTION(_BVCE,       "6M", 13)

CONNECTION(_5BVCF,      "9A", 9)

CONNECTION(_5BLGE,      "9A", 5)

//INPUT
  //serve
CONNECTION(_1TLCC,      "2L", 2)
CONNECTION(_9XSUR,      "2L", 1)

CONNECTION(_CREU,       "6F", 5)
CONNECTION(GND,         "6F", 6)

CONNECTION(_5SURZ,      "7F", 4)
CONNECTION(_EBUZ,       "7F", 3)
CONNECTION(_1TLCC,      "7F", 1)
CONNECTION(_SURR,       "7F", 2)
CONNECTION(_ENDA,       "7F", 15)

  //coin drop
CONNECTION(_9X25C,      "1K", 1)

  //game credit (start)
CONNECTION(_5ZERO,      "2L", 5)
CONNECTION(_9XCRU,      "2L", 4)

CONNECTION(_N999,       "3M", 4)
CONNECTION(_CREW,       "3M", 3)
CONNECTION(_FLAA,       "3M", 1)
CONNECTION(_5CREW,      "3M", 2)
CONNECTION(_5TPWR,      "3M", 15)

  //
CONNECTION(_5RVID,      "6G", 1)
CONNECTION(_5KBAS,      "6G", 3)
CONNECTION(_ZERO,       "6G", 5)
CONNECTION(_5N25C,      "6G", 9)
CONNECTION(_CREW,       "6G", 11)
CONNECTION(_ENDC,       "6G", 13)

//GAME CREDIT COUNTER AND CONTROL (left, lower)
CONNECTION(VCC,         "SWPLAYSPERCOIN12", 1)  //1 play per coin
CONNECTION(GND,         "SWPLAYSPERCOIN12", 2)  //2 play per coin

CONNECTION(_9XPLY,      "8M", 1)

  //reset RC 9XWRR
CONNECTION(VCC,         "BUF3", 1) 

  //credit counter
CONNECTION(_1SEDA,      "6F", 9)
CONNECTION(_CONA,       "6F", 8)

CONNECTION(_CREU,       "4D", 13)
CONNECTION(_EFEE,       "4D", 2)
CONNECTION(_CREB,       "4D", 1)

CONNECTION(_5UPDN, "BUF1", 1) // Adds delay to 5UPDN to prevent incorrect count direction

CONNECTION(GND,         "5F", 9)
CONNECTION(GND,         "5F", 10)
CONNECTION(GND,         "5F", 1)
CONNECTION(GND,         "5F", 15)
CONNECTION(_5TPWR,      "5F", 11)
//CONNECTION(_5UPDN,      "5F", 5)
CONNECTION("BUF1", 2,   "5F", 5)
CONNECTION(_LIMT,       "5F", 4)
CONNECTION(_CREC,       "5F", 14)

CONNECTION(_CRA3,       "6B", 9)
CONNECTION(_CRA0,       "6B", 10)
CONNECTION(_5CREU,      "6B", 12)
CONNECTION(_5CREU,      "6B", 13)

CONNECTION(_5N25C,      "9G", 1)
CONNECTION(_N999,       "9G", 9)
CONNECTION(GND,         "9G", 3) //not shown
CONNECTION(GND,         "9G", 4) //not shown
CONNECTION(GND,         "9G", 5) //not shown
CONNECTION(GND,         "9G", 6) //not shown
CONNECTION(_1TLCC,      "9G", 7)
CONNECTION(_1TLCC,      "9G", 10)
CONNECTION(_6THSC,      "9G", 2)

CONNECTION(_N999,       "9H", 4)
CONNECTION(_FLAA,       "9H", 3)
CONNECTION(_2THSC,      "9H", 1)
CONNECTION(_FLAA,       "9H", 2)
CONNECTION(_5N25C,      "9H", 15)

CONNECTION(_FLAA,       "8H", 9)
CONNECTION(_FLAB,       "8H", 10)

CONNECTION(_N999,       "9H", 10)
CONNECTION(_1N25C,      "9H", 11)
CONNECTION(_2TQ05,      "9H", 13)
CONNECTION(_FLAC,       "9H", 12)
CONNECTION(_5CREW,      "9H", 14)

CONNECTION(_FLA3,       "8H", 2)
CONNECTION(_5CPLY,      "8H", 1)

CONNECTION(_FLAB,       "8H", 5)
CONNECTION(_9XPLY,      "8H", 4)

CONNECTION(_CRE2,       "7H", 2)
CONNECTION(_CRE1,       "7H", 3)

CONNECTION(_5CONA,      "7H", 5)
CONNECTION(_5CREA,      "7H", 6)

//ACTIVE GAME (bottom, right)
CONNECTION(_N999,       "6H", 4)
CONNECTION(_CREU,       "6H", 3)
CONNECTION(_TLC8,       "6H", 1)
CONNECTION(_ENDB,       "6H", 2)
CONNECTION(_5TPWR,      "6H", 15)

  //2 player
CONNECTION(_N999,       "6H", 10)
CONNECTION(_ENDA,       "6H", 11)
CONNECTION(_5CREU,      "6H", 13)
CONNECTION(_5ENDA,      "6H", 12)
CONNECTION(_5ENDC,      "6H", 14)

  //player up
CONNECTION(_5CREU,      "5G", 4)
CONNECTION(_ENDA,       "5G", 3)
CONNECTION(_EBC3,       "5G", 1)
CONNECTION(_TWOP,       "5G", 2)
CONNECTION(_N999,       "5G", 15)

CONNECTION(_ENDB,       "0L", 9)
CONNECTION(_5ENDA,      "0L", 10)

//VIDEO OUTPUT (bottom, right)
CONNECTION(_6CVID,      "1K", 3)

CONNECTION(_TCSC,       "1K", 5)

//AUDIO
CONNECTION(_TCSC,      "4F", 5)
CONNECTION(_TLC8,      "4F", 4)
CONNECTION(_1BVCF,     "4F", 2)
CONNECTION(_1BVCF,     "4F", 1)

CONNECTION(_N999,      "5H", 4)
CONNECTION(_BUZZ,      "5H", 3)
CONNECTION(_6TQ10,     "5H", 1)
CONNECTION(_EBCC,      "5H", 2)
CONNECTION(_N999,      "5H", 15)

CONNECTION(_KBAL,      "8G", 5)
CONNECTION(_ENDA,      "8G", 4)

CONNECTION(_5BOPD,     "5H", 10)
CONNECTION(_1KBAS,     "5H", 11)
CONNECTION(_2TQ10,     "5H", 13)
CONNECTION(_EBC2,      "5H", 12)
CONNECTION(_ENDA,      "5H", 14)

CONNECTION(_N999,      "4J", 4)
CONNECTION(_1PERA,     "4J", 3)
CONNECTION(_6TQ10,     "4J", 1)
CONNECTION(_EBC1,      "4J", 2)
CONNECTION(_ENDA,      "4J", 15)

CONNECTION(_N999,      "4J", 10)
CONNECTION(_1KBAR,     "4J", 11)
CONNECTION(_2TQ10,     "4J", 13)
CONNECTION(_EBC2,      "4J", 12)
CONNECTION(_5EBUZ,     "4J", 14)

CONNECTION(_5EBUZ,     "4H", 5)
CONNECTION(_5EBOP,     "4H", 4)
CONNECTION(_5EBEL,     "4H", 2)
CONNECTION(_5EHIT,     "4H", 1)

CONNECTION(_EBAA,       "4G", 1)
CONNECTION(_N999,       "4G", 9)
CONNECTION(GND,         "4G", 3) //not shown
CONNECTION(GND,         "4G", 4) //not shown
CONNECTION(GND,         "4G", 5) //not shown
CONNECTION(GND,         "4G", 6) //not shown
CONNECTION(_1TLCC,      "4G", 7)
CONNECTION(_5TLC8,      "4G", 10)
CONNECTION(_6THSC,      "4G", 2)

CONNECTION(_EBUZ,      "5J", 2)
CONNECTION(_TLC6,      "5J", 1)

CONNECTION(_EBOP,      "5J", 5)
CONNECTION(_TLC4,      "5J", 4)

CONNECTION(_EBEL,      "5J", 9)
CONNECTION(_TLC2,      "5J", 10)

CONNECTION(_EHIT,      "5J", 12)
CONNECTION(_TLC3,      "5J", 13)

CONNECTION(_5EBEA,     "4H", 9)  //missed ball
CONNECTION(_5EBEB,     "4H", 10) //ball hit side wall
CONNECTION(_5EBEC,     "4H", 12) //ball hits dot
CONNECTION(_5EBED,     "4H", 13) //ball hits paddle

CONNECTION(_EBEE,      "8H", 12)
CONNECTION(_ENDA,      "8H", 13)


/* output */

CONNECTION("VIDEO", Video::HBLANK_PIN, _THBL)
CONNECTION("VIDEO", Video::VBLANK_PIN, _5TVBL)

CONNECTION("VIDEO", 1, _4CVID)

//CONNECTION("VIDEO", 1, _5GNCC)

//CONNECTION("VIDEO", 1, _TLC8)  //test top line
//CONNECTION("VIDEO", 1, _TLGV)  //test top line
//CONNECTION("VIDEO", 1, _1BVCF)  //test ball video
//CONNECTION("VIDEO", 1, _1TBCF)  //test ball +top line
//CONNECTION("VIDEO", 1, _NCOT)  //test numbers
//CONNECTION("VIDEO", 1, _5TLBG)  //inverted numbers&ball
//CONNECTION("VIDEO", 1, _5ALVD)  //inverted arrow & borders
//CONNECTION("VIDEO", 1, _TLNE)  //side lines
//CONNECTION("VIDEO", 1, _5PGOT) //dot vid
//CONNECTION("VIDEO", 1, _5RVID)  //inverse paddle
//CONNECTION("VIDEO", 1, _PGTC) //ball shape 

//nn sync CONNECTION("VIDEO", 2, "D3", 8)

CONNECTION(_EBEF,       "AUDIO", 1)
CONNECTION("AUDIO", i1, "MIXER", 1)

CONNECTION("AUDIO", Audio::OUTPUT_MONO, "MIXER", i1)



//hack to combine P1 and P2 dot output
 CONNECTION(_PVID_P1,   "COMBINE", 2)  
 CONNECTION(_PVID_P2,   "COMBINE", 3)  
 CONNECTION(_5PONE,     "COMBINE", 1)  
 CONNECTION(GND,        "COMBINE", 15) 

 CONNECTION(_5RRSU, "PADDLE", 1)

//******************************************

#ifdef DEBUG
CONNECTION(_9XCRU, "LOG1", 1)
CONNECTION(_CREU, "LOG1", 2)
CONNECTION(_5RTEA, "LOG1", 3)
CONNECTION(_5WRTA, "LOG1", 4)
CONNECTION("BUF4", 2, "LOG1", 5)

#endif

CIRCUIT_LAYOUT_END

//unused chips:pins
/*
  0B.2
  0B.4
  0B.6
  0B.8
 0K.6 5SUBL
  1B.6
  1K.6 5TCSC
  1K.10
  1K.12
  2L.11
  3K.1
  3K.2
  3M.7
  4B.10
  4G.14
  4M.13
  5A.6
  5E.7
  5F.13
  5G.7
  6M.6
  6D.5
  6E.8
  6J.15
  6K.15
  6L.15
  7B.12
  7B.15
  7E.14
  7E.13
  7E.12
  7E.11
  7F.7
  7K.15
  7L.15
  7M.6
  8D.14
  8D.13
  8D.12
  8D.11
  8E.14
  8E.13
  8E.12
  8E.11
  8F.14
  8F.13
  8F.12
  8F.11
  8K.15
  8L.15
  8M.4
  8M.6
  8M.8
  8M.10
  9A.2 p3-vcc
  9E.5
  9E.9
 9G.14 FLA0
 9G.13 FLA1
 9G.12 FLA2
  9H.6
*/

