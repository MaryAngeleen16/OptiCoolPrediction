import time
import lgpio

class GPIOController:
    def __init__(self):
        # Open GPIO chip 0
        try:
            self.gpio = lgpio.gpiochip_open(0)
        except Exception as e:
            raise RuntimeError("Failed to open GPIO chip. Are you running on a Raspberry Pi with lgpio?") from e

        self.pins = {
            'ac1': 4,
            'ac2': 17,
            'blower': 18,
            'e_fan': 22,
            'exhaust': 27
        }

        for pin in self.pins.values():
            lgpio.gpio_claim_output(self.gpio, pin)
            lgpio.gpio_write(self.gpio, pin, 1)  # default OFF (HIGH)

    def turn_on(self, *devices):
        """Turn on multiple devices at once (LOW signal)."""
        for device in devices:
            if device in self.pins:
                lgpio.gpio_write(self.gpio, self.pins[device], 0)
            else:
                raise ValueError(f"Device '{device}' not found.")

    def turn_off(self, *devices):
        """Turn off multiple devices at once (HIGH signal)."""
        for device in devices:
            if device in self.pins:
                lgpio.gpio_write(self.gpio, self.pins[device], 1)
            else:
                raise ValueError(f"Device '{device}' not found.")

    def turn_on_timed(self, device, duration):
        """Turn on a device for 'duration' seconds then turn it off."""
        if device in self.pins:
            lgpio.gpio_write(self.gpio, self.pins[device], 0)
            time.sleep(duration)
            lgpio.gpio_write(self.gpio, self.pins[device], 1)
        else:
            raise ValueError(f"Device '{device}' not found.")

    def turn_on_ac_units(self):
        self.turn_on('ac1', 'ac2')

    def turn_off_ac_units(self):
        self.turn_off('ac1', 'ac2')

    def turn_on_e_fans(self):
        self.turn_on('e_fan')

    def turn_off_e_fans(self):
        self.turn_off('e_fan')

    def turn_on_timed_blower(self):
        self.turn_on_timed('blower', 300)  # 5 mins

    def turn_on_timed_exhaust(self):
        self.turn_on_timed('exhaust', 180)  # 3 mins

    def turn_off_blower(self):
        self.turn_off('blower')

    def turn_off_exhaust(self):
        self.turn_off('exhaust')

    def cleanup(self):
        """Unclaim and close GPIO resources."""
        lgpio.gpiochip_close(self.gpio)
