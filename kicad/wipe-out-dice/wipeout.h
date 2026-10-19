#include "../circuit_desc.h"
#include "../circuit.h"

/*
 * 7405-based paddle timer circuit
 *
 * 7405 + Capacitor + BJT current source + paddle potentiometer
 *
 * When input is high, capacitor will discharge rapidly through 7405.
 * When input is low, capacitor will charge through BJT constant current source.
 * Rate of charging is determined by paddle potentiometer.
 *
 * Pin 1: Trigger input
 * Pin 2: Capacitor output
 */
typedef Mono555Desc WipeoutPaddleDesc;

static CUSTOM_LOGIC( paddle_control )
{
    WipeoutPaddleDesc* desc = (WipeoutPaddleDesc*)chip->custom_data;

    // Update tp_hl in standard portion based on rc value
    if(chip->output_links.size())
    {
        // Current through 270 ohm resistor (Approximate)
        double i = 5.0 / desc->r;

        // Time to charge capacitor to 2V. dt = C * 2 / i
        double dt = desc->c * 2.0 / i;
        
        chip->output_links[0].chip->delay[0] = uint64_t(dt / Circuit::timescale);

        // Generate event to standard portion of chip
        chip->pending_event = chip->circuit->queue_push(chip, 0);
    }
}

static CHIP_LOGIC( PADDLE_Q )
{
    pin[2] = pin[1] ^ 1;
}

static CHIP_DESC( WIPEOUT_PADDLE ) = 
{
	CUSTOM_CHIP_START(&paddle_control)
        INPUT_PINS( i3 )
        OUTPUT_PIN( i1 ),

	CHIP_START( PADDLE_Q )
        INPUT_PINS( i1, 1 )
        OUTPUT_PIN( 2 )
        OUTPUT_DELAY_NS( 50.0, 50.0 ), // tp_lh will be overwritten

	CHIP_DESC_END
};
