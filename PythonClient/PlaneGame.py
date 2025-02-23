import asyncio
import threading
import time
import math
import pygame
from DunkatronBreathometer import DunkatronBreathometer  # Your BLE API class

# ------------------------------------------------------------
# BLE Manager
# ------------------------------------------------------------
class BLEManager:
    def __init__(self):
        self.breathometer = DunkatronBreathometer()

    async def _ble_task(self):
        if not await self.breathometer.connect():
            print("Could not connect to Dunkatron device.")
        while True:
            await asyncio.sleep(1)

    def start(self):
        thread = threading.Thread(target=self._run_ble_loop, daemon=True)
        thread.start()

    def _run_ble_loop(self):
        asyncio.run(self._ble_task())

    def get_amplitude(self) -> int:
        return self.breathometer.get_latest_amplitude()

    def is_connected(self) -> bool:
        try:
            return self.breathometer._client and self.breathometer._client.is_connected
        except Exception:
            return False

# ------------------------------------------------------------
# LowPassFilter and Chain
# ------------------------------------------------------------
class LowPassFilter:
    def __init__(self, rc: float):
        """
        rc: The smoothing factor (alpha) in range [0,1].
        """
        self.rc = rc
        self.state = None

    def __call__(self, sample: float) -> float:
        if self.state is None:
            self.state = sample
        else:
            self.state += self.rc * (sample - self.state)
        return self.state

class LowPassChain:
    def __init__(self, num_filters: int, rc: float):
        self.filters = [LowPassFilter(rc) for _ in range(num_filters)]

    def __call__(self, sample: float) -> float:
        result = sample
        for filt in self.filters:
            result = filt(result)
        return result

# ------------------------------------------------------------
# Filtering Classes
# ------------------------------------------------------------
class TimedMovingAverage:
    def __init__(self, window_size=10):
        self.window_size = window_size  # Window size in seconds.
        self.values = []  # List of tuples: (timestamp, value).

    def __call__(self, value):
        now = time.time()
        self.values.append((now, value))
        # Remove values older than the window.
        self.values = [(t, v) for (t, v) in self.values if now - t < self.window_size]
        return self.get_average()

    def get_average(self):
        if not self.values:
            return 0
        if len(self.values) == 1:
            # Only one sample available.
            return self.values[0][1]

        # Compute the total time span.
        start_time = self.values[0][0]
        end_time = self.values[-1][0]
        total_time = end_time - start_time
        if total_time <= 0:
            return self.values[-1][1]

        # Use the trapezoidal rule to approximate the time-weighted average.
        weighted_sum = 0.0
        for i in range(len(self.values) - 1):
            t0, v0 = self.values[i]
            t1, v1 = self.values[i + 1]
            dt = t1 - t0
            # Average value over the interval.
            weighted_sum += (v0 + v1) / 2 * dt

        return weighted_sum / total_time
    
# ------------------------------------------------------------
# PeakFilter: Remembers the highest value over time and decays
# ------------------------------------------------------------
class PeakFilter:
    def __init__(self, decay_rate: float = 0.5):
        """
        decay_rate: How fast the stored peak decays (per second).
        """
        self.peak = 0
        self.decay_rate = decay_rate
        self.last_time = time.time()

    def __call__(self, value: float) -> float:
        now = time.time()
        dt = now - self.last_time
        self.last_time = now
        # Decay the current peak exponentially.
        self.peak *= math.exp(-self.decay_rate * dt)
        # Update peak if the new value is higher.
        if value > self.peak:
            self.peak = value
        return self.peak
    
class AmplitudeFilter:
    def __init__(self):
        self.filters = [
            lambda x: x ** (8),
            TimedMovingAverage(4),
            lambda x: x ** (1/4),
            TimedMovingAverage(2),
            lambda x: x ** (1/2),
            LowPassChain(3, 0.0625),
        ]

    def __call__(self, value):
        for filter_ in self.filters:
            value = filter_(value)
        return value

# ------------------------------------------------------------
# Plane Class
# ------------------------------------------------------------
class Plane:
    def __init__(self, init_x, init_y, screen_height, image_path="plane.png"):
        # Load the plane image.
        self.base_surface = pygame.image.load(image_path).convert_alpha()
        # flip the base surface so the plane faces right.
        self.base_surface = pygame.transform.flip(self.base_surface, True, False)
        # Optionally, scale the image if necessary.
        self.base_surface = pygame.transform.scale(self.base_surface, (60, 30))
        self.rect = self.base_surface.get_rect(topleft=(init_x, init_y))
        self.screen_height = screen_height
        self.angle = 0
        

    def update(self, new_height, forward_speed, screen_width):
        self.rect.y = new_height
        # Clamp vertical position so the plane stays on-screen.
        self.rect.y = max(0, min(self.rect.y, self.screen_height - self.base_surface.get_height()))
        buffer = self.base_surface.get_width()
        self.rect.x = (self.rect.x + forward_speed + buffer) % (screen_width + buffer) - buffer

    def set_angle(self, angle):
        self.angle = angle

    def draw(self, screen):
        rotated = pygame.transform.rotate(self.base_surface, -self.angle)
        rotated_rect = rotated.get_rect(center=self.rect.center)
        screen.blit(rotated, rotated_rect.topleft)

# ------------------------------------------------------------
# Cloud Class
# ------------------------------------------------------------
class Cloud:
    def __init__(self, x, y, width, height, speed):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed

    def update(self, screen_width):
        buffer = 2 * self.width
        self.x = (self.x - self.speed + buffer) % (screen_width + buffer) - buffer

    def draw(self, screen):
        # Draw an ellipse to represent the cloud.
        cloud_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.ellipse(screen, (255, 255, 255), cloud_rect)

# ------------------------------------------------------------
# Game Class
# ------------------------------------------------------------
class Game:
    def __init__(self, width, height):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Breath Game: Dunkatron Flight")
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.font = pygame.font.SysFont("Arial", 24)

        # Background colors.
        self.sky_color = (135, 206, 235)      # Sky blue.
        self.floor_color = (34, 139, 34)       # Forest green.

        # Create clouds.
        self.clouds = [
            Cloud(100, 100, 100, 60, 1),
            Cloud(200, 200, 140, 80, 1.5),
            Cloud(300, 50, 120, 90, 1.2),
            Cloud(400, 150, 160, 100, 1.7),
            Cloud(500, 250, 110, 80, 1.3),
            Cloud(600, 100, 90, 30, 1.1),
            Cloud(700, 200, 130, 60, 1.6),
            Cloud(800, 50, 150, 90, 1.4),
        ]

        # Game elements.
        self.forward_speed = 2
        self.plane = Plane(0, 0, height)

        # BLE Manager.
        self.ble_manager = BLEManager()
        self.ble_manager.start()

        # Amplitude filtering.
        self.amplitude_filter = AmplitudeFilter()

        # Sensitivity parameters.
        self.min_amplitude = 10
        
        self.previous_amplitude = 0
        self.derivative_filter = LowPassFilter(0.1)
        self.speed_filter = LowPassFilter(0.1)
            
    def map_amplitude(self, raw_amplitude: int) -> float:
        # Clamp raw_amplitude to the expected range.
        raw_amplitude = max(0, min(raw_amplitude, 8000))
        return (1 - raw_amplitude / 8000) * (HEIGHT - 100)

    def map_speed(self, raw_amplitude: int) -> float:
        return (2 * raw_amplitude / 8000 + 1) ** 2

    def update_background(self):
        # Fill sky.
        self.screen.fill(self.sky_color)
        # Update and draw clouds.
        for cloud in self.clouds:
            cloud.update(self.width)
            cloud.draw(self.screen)
        # Draw floor as a green rectangle at the bottom.
        floor_height = 100
        pygame.draw.rect(self.screen, self.floor_color, (0, self.height - floor_height, self.width, floor_height))

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Update background (sky, clouds, floor).
            self.update_background()

            # Get raw amplitude.
            raw_amp = self.ble_manager.get_amplitude()

            filtered_amp = self.amplitude_filter(raw_amp)
            mapped_amp = self.map_amplitude(filtered_amp)
            
            derivative = self.derivative_filter(mapped_amp - self.previous_amplitude)
            self.previous_amplitude = mapped_amp
            
            # Compute angle so plane faces its direction of motion.
            # self.forward_speed = self.speed_filter(self.map_speed(filtered_amp) ** 16) ** (1.0 / 16)
            angle_rad = math.atan2(derivative, self.forward_speed)
            angle_deg = math.degrees(angle_rad)
            self.plane.set_angle(angle_deg)

            # Update plane.
            self.plane.update(mapped_amp, self.forward_speed, self.width)
            self.plane.draw(self.screen)

            # Render connection and amplitude status.
            connection_status = "Connected" if self.ble_manager.is_connected() else "Disconnected"
            status_surface = self.font.render(f"BLE: {connection_status}", True, (0, 0, 0))
            self.screen.blit(status_surface, (10, 10))
            # amplitude_surface = self.font.render(f"Raw Amp: {raw_amp}", True, (0, 0, 0))
            # self.screen.blit(amplitude_surface, (10, 40))
            # filtered_surface = self.font.render(f"Filtered: {filtered_amp:.2f}", True, (0, 0, 0))
            # self.screen.blit(filtered_surface, (10, 70))

            pygame.display.flip()
            self.clock.tick(self.fps)
        pygame.quit()

# ------------------------------------------------------------
# Main Execution
# ------------------------------------------------------------
if __name__ == '__main__':
    WIDTH, HEIGHT = 800, 600
    game = Game(WIDTH, HEIGHT)
    game.run()
