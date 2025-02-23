import asyncio
import threading
from bleak import BleakScanner, BleakClient

# UUID definitions for the service and characteristic
SERVICE_UUID = "81101fbc-f19e-4e6a-9588-500bbaf60880"
CHAR_UUID = "907ffb4a-b15b-4acd-914d-947984b62ecc"

class DunkatronBreathometer:
    """
    A class to manage the BLE connection to the Dunkatron Breathalyzer,
    receive notifications containing breath amplitude data, and recover from lost connections.
    """

    def __init__(self) -> None:
        self._latest_amplitude: int = 0
        self._lock = threading.Lock()
        self._client: BleakClient | None = None
        self._running = False

    async def connect(self, scan_duration: int = 1) -> bool:
        """
        Scan for BLE devices with 'Dunkatron' in their name and connect.
        Returns True on successful connection.
        """
        print("Scanning for BLE devices...")
        try:
            devices = await BleakScanner.discover(timeout=scan_duration)
        except Exception as e:
            print("Error scanning for devices:", e)
            return False

        target = None
        for d in devices:
            print(f"Found device: {d.name} ({d.address})")
            if d.name and "Dunkatron" in d.name:
                target = d
                print(f"Found target device: {d.name} ({d.address})")
                break

        if target is None:
            print("No Dunkatron device found.")
            return False

        self._client = BleakClient(target.address)
        # Set a callback to handle unexpected disconnections.
        self._client.set_disconnected_callback(self._handle_disconnect)

        try:
            await self._client.connect()
            print("Connected successfully.")
        except Exception as e:
            print("Connection failed:", e)
            return False

        try:
            await self._client.start_notify(CHAR_UUID, self._notification_handler)
        except Exception as e:
            print("Failed to start notifications:", e)
            await self.disconnect()
            return False

        self._running = True
        return True

    def _notification_handler(self, sender: int, data: bytearray) -> None:
        """
        Handle incoming notifications.
        Expected format: 4 bytes (2 sync bytes: 0xBE, 0xEF, then 2 bytes for amplitude in big-endian).
        """
        if len(data) >= 4:
            if data[0] == 0xBE and data[1] == 0xEF:
                amplitude = (data[2] << 8) | data[3]
                with self._lock:
                    self._latest_amplitude = amplitude

    def get_latest_amplitude(self) -> int:
        """Return the most recent amplitude value."""
        with self._lock:
            return self._latest_amplitude

    async def disconnect(self) -> None:
        """Stop notifications and disconnect from the BLE device."""
        self._running = False
        if self._client and self._client.is_connected:
            try:
                await self._client.stop_notify(CHAR_UUID)
            except Exception as e:
                print("Error stopping notifications:", e)
            try:
                await self._client.disconnect()
            except Exception as e:
                print("Error during disconnect:", e)
            print("Disconnected.")

    def _handle_disconnect(self, client: BleakClient) -> None:
        """
        Callback triggered when the BLE device disconnects.
        Attempts to reconnect.
        """
        print("Device disconnected. Attempting to reconnect...")
        # Schedule the reconnect process in the event loop.
        asyncio.create_task(self._reconnect())

    async def _reconnect(self) -> None:
        """Disconnect and then attempt to reconnect using exponential backoff."""
        await self.disconnect()
        backoff = 1
        while not self._running:
            await asyncio.sleep(backoff)
            connected = await self.connect()
            if connected:
                break
            backoff = min(backoff * 1.5, 10)
        if self._running:
            print("Reconnected successfully.")
        else:
            print("Reconnect failed.")


# ------------------------------------------------------------------------------
# Run Function for Testing (Not intended for production use)
# ------------------------------------------------------------------------------
async def run_test() -> None:
    breathometer = DunkatronBreathometer()
    connected = await breathometer.connect()
    if not connected:
        print("Could not connect to Dunkatron device.")
        return

    try:
        # Periodically print the latest amplitude.
        while True:
            amp = breathometer.get_latest_amplitude()
            print(f"Latest amplitude: {amp}")
            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        print("Interrupt received. Disconnecting...")
    except Exception as e:
        print("Error in main loop:", e)
    finally:
        await breathometer.disconnect()


if __name__ == "__main__":
    asyncio.run(run_test())
