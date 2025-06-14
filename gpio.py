import lgpio
import time

class GPIOController:
    def __init__(self):
        # GPIO setup
        self.gpio = lgpio.gpiochip_open(0)  # Open GPIO chip 0
        self.pins = {
            'ac1': 4,
            'ac2': 17,
            'blower': 18,
            'e_fan': 22,
            'exhaust': 27
        }
        for pin in self.pins.values():
            lgpio.gpio_claim_output(self.gpio, pin)

    def turn_on(self, *devices):
        """Turn on multiple devices at once."""
        for device in devices:
            if device in self.pins:
                lgpio.gpio_write(self.gpio, self.pins[device], 0)  # Set LOW to turn on
            else:
                raise ValueError(f"Device {device} not found.")

    def turn_off(self, *devices):
        """Turn off multiple devices at once."""
        for device in devices:
            if device in self.pins:
                lgpio.gpio_write(self.gpio, self.pins[device], 1)  # Set HIGH to turn off
            else:
                raise ValueError(f"Device {device} not found.")

    def turn_on_timed(self, device, duration):
        """Turn on a device for a specific duration, then turn it off."""
        if device in self.pins:
            lgpio.gpio_write(self.gpio, self.pins[device], 0)  # Set LOW to turn on
            time.sleep(duration)
            lgpio.gpio_write(self.gpio, self.pins[device], 1)  # Set HIGH to turn off
        else:
            raise ValueError(f"Device {device} not found.")

    def turn_off_exhaust(self):
        self.turn_off('exhaust')

    def turn_off_blower(self):
        self.turn_off('blower')

    def turn_on_ac_units(self):
        self.turn_on('ac1', 'ac2')

    def turn_off_ac_units(self):
        self.turn_off('ac1', 'ac2')

    def turn_on_e_fans(self):
        self.turn_on('e_fan')

    def turn_off_e_fans(self):
        self.turn_off('e_fan')

    def turn_on_timed_blower(self):
        self.turn_on_timed('blower', 300)

    def turn_on_timed_exhaust(self):
        self.turn_on_timed('exhaust', 180)

    def cleanup(self):
        """Clean up all GPIO pins."""
        lgpio.gpiochip_close(self.gpio)