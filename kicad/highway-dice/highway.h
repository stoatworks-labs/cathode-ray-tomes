#include "../circuit_desc.h"
#include "../circuit.h"

/*
 * Highway Speed Control
 * Capcitor C17 discharges when Gas or /GT are low,
 * charges rapidly when OFR (off-road) or CRASH are high.
 * Capacitor charge controls rate of astable 555 timer D9.
 * 
 * 555 Capacitor C18 charges through either:
 * - R40 + R22 when CRASH is high
 * - Constant current source Q4 (controlled by C17 voltage)
 *   when CRASH is LOW
 * 555 Discharges through R22
 * 555 Trigger voltage is ~0.966 V due to diode CR5
 *
 * NOTE: All open collector inverters are included in this model.
 * Input pin 1: GAS
 * Input pin 2: CRASH
 * Input pin 3: OFR
 * Input pin 4: /GT
 *
 * Output Pin 5: 555 Output (D9.3) 
 * Output Pin 6: B9.2 (CRASH delayed)
 * Output Pin 7: Q3 Collector (CRASH inverted + delayed)
 */

extern CUSTOM_LOGIC( clock );

struct HighwaySpeedDesc
{
    // Cap circuit constants
    static constexpr double R_GAS[] = { K_OHM(33.0), OHM(560) };
    static constexpr double V_GAS[] = { 0.0, 13.5 };
    static constexpr double R_CRASH = K_OHM(1.5);
    static constexpr double V_CRASH = 14.3; // ~0.7 drop across diode CR4
    static constexpr double R_OFR   = OHM(470.0);
    static constexpr double V_OFR   = 14.3 - 1.0; // TEMP HACK - TODO: OFR current seems to be too high? Car cannot move at all when offoad.
    static constexpr double R_GT    = K_OHM(2.2);
    static constexpr double R_VCC   = K_OHM(47.0);
    static constexpr double V_VCC   = 14.3;
    static constexpr double R_GND   = K_OHM(33.0) + K_OHM(10.0);
    static constexpr double C       = U_FARAD(220.0);
    static constexpr double DT      = 25.0E-6; // 25 us    

    // 555 circuit constants
    static constexpr double C_555      = U_FARAD(0.1);
    static constexpr double R1_555     = K_OHM(1.5);
    static constexpr double R2_555     = K_OHM(3.3);
    static constexpr double R_CCS      = K_OHM(33.0);
    static constexpr double THRESH_LO  = 5.0 / 3.0 - 0.7;
    static constexpr double THRESH_HI  = 2.0 * 5.0 / 3.0;
    const double DISCHG_EXP = 1.0 - exp(-DT / (R2_555 * C_555));
    const double CHG_EXP    = 1.0 - exp(-DT / ((R1_555+R2_555) * C_555));

    enum { GAS_MASK = 1, CRASH_MASK = 2, OFR_MASK = 4, GT_MASK = 8, TIMER_MASK = 16 };

    double v_cap;
    double v_555;

    void update_cap(Chip* chip);
    void update_555(Chip* chip);
};

constexpr double HighwaySpeedDesc::R_GAS[];
constexpr double HighwaySpeedDesc::V_GAS[];

void HighwaySpeedDesc::update_cap(Chip* chip)
{
    int gas = chip->inputs & GAS_MASK;

    double r_total = 1.0 / R_VCC; 
    r_total += 1.0 / R_GAS[gas];
    r_total += (chip->inputs & GAS_MASK) ? 1.0 / R_GND : 0.0;
    r_total += (chip->inputs & CRASH_MASK) ? 1.0 / R_CRASH : 0.0;
    r_total += (chip->inputs & OFR_MASK) ? 1.0 / R_OFR : 0.0;
    r_total += (chip->inputs & GT_MASK) ? 1.0 / R_GT : 0.0;
    r_total = 1.0 / r_total;
    
    double c_exp = 1.0 - exp(-DT / (r_total * C));

    double i = V_VCC / R_VCC; 
    i += V_GAS[gas] / R_GAS[gas];
    i += (chip->inputs & CRASH_MASK) ? V_CRASH / R_CRASH : 0.0;
    i += (chip->inputs & OFR_MASK) ? V_OFR / R_OFR : 0.0;

    double v = i * r_total;
    
    // TODO: Precompute all of the above into a 16-entry table?

    v_cap += (v - v_cap) * c_exp;
}

void HighwaySpeedDesc::update_555(Chip* chip)
{
    if(chip->output == 0) // Discharging through R22
    {
        v_555 -= v_555 * DISCHG_EXP;
    }
    else if(chip->inputs & CRASH_MASK) // Q1 enabled, charge cap through R40 + R22
    {
        v_555 += (V_VCC - v_555) * CHG_EXP;
    }
    else // Charge through constant current source Q4
    {
        double i = (15.0 - (v_cap + 0.7)) / R_CCS;
        if(i < 0.0) i = 0.0;
        v_555 += i * DT / C_555;
    }

    int new_out;
    
    if(v_555 < THRESH_LO) new_out = 1;
    else if(v_555 > THRESH_HI) new_out = 0;
    else new_out = chip->output;
    
    if(new_out != chip->output) 
        chip->pending_event = chip->circuit->queue_push(chip, chip->delay[0]);

    /*printf("%lld, %d, %d, %d, %d, %g, %g\n", 
           chip->circuit->global_time,
           (chip->inputs >> 0) & 1,
           (chip->inputs >> 1) & 1,
           (chip->inputs >> 2) & 1,
           (chip->inputs >> 3) & 1,
           v_cap, v_555);*/
}

static CUSTOM_LOGIC( highway_speed )
{
    HighwaySpeedDesc* desc = (HighwaySpeedDesc*)chip->custom_data;

    if(mask == 0) // Init
    {
        desc->v_cap = desc->v_555 = 0.0;
    }

    chip->inputs ^= mask;
    
    if(mask != HighwaySpeedDesc::TIMER_MASK) return;

    desc->update_cap(chip);
    desc->update_555(chip);
}

static CHIP_LOGIC( crash_cap )
{
    pin[6] = pin[2];
}

static CHIP_LOGIC( crash_cap_n )
{
    pin[7] = pin[2] ^ 1;
}

static CHIP_DESC( HIGHWAY_SPEED_CONTROL ) = 
{
    CUSTOM_CHIP_START(&clock)
        OUTPUT_PIN( i1 )
        OUTPUT_DELAY_US( 25.0, 25.0 ),
    
    // Adjusts D9 frequency based on state of speed inputs
    // TODO: Improve accuracy    
    CUSTOM_CHIP_START(&highway_speed)
        INPUT_PINS( 1, 6, 3, 4, i1 )
        OUTPUT_PIN( 5 )
        OUTPUT_DELAY_NS( 10.0, 10.0),

	CHIP_START( crash_cap )
        INPUT_PINS( 2 )
        OUTPUT_PIN( 6 )
        OUTPUT_DELAY_MS( 0.1, 300.0 ),

    CHIP_START( crash_cap_n )
        INPUT_PINS( 2 )
        OUTPUT_PIN( 7 )
        OUTPUT_DELAY_MS( 300.0, 0.1 ), 

	CHIP_DESC_END
};
