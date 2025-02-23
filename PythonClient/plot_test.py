import asyncio
import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from DunkatronBreathometer import DunkatronBreathometer

# Global instance of the breathometer.
breathometer = DunkatronBreathometer()

def run_ble_client():
    # Create a new persistent event loop for BLE operations.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Schedule the connect() coroutine.
    loop.create_task(breathometer.connect())
    # Run the event loop forever.
    loop.run_forever()

# Start the BLE connection in a separate daemon thread.
ble_thread = threading.Thread(target=run_ble_client, daemon=True)
ble_thread.start()

# Set up live plotting using matplotlib.
fig, ax = plt.subplots()
xdata, ydata = [], []
line, = ax.plot([], [], lw=2)
ax.set_ylim(0, 16000)  # Adjust Y-axis limits based on expected amplitude range.
ax.set_xlim(0, 1000)
ax.set_xlabel("Time (frames)")
ax.set_ylabel("Breath Amplitude")
ax.set_title("Live Breath Amplitude")
ax.grid(True)

def init():
    line.set_data(xdata, ydata)
    return line,

def update(frame):
    # Get the latest amplitude from the breathometer.
    amplitude = breathometer.get_latest_amplitude()
    xdata.append(frame)
    ydata.append(amplitude)
    
    # Keep only the latest 100 points.
    if len(xdata) > 1000:
        xdata.pop(0)
        ydata.pop(0)
        ax.set_xlim(frame - 1000, frame)
    
    line.set_data(xdata, ydata)
    return line,

# Create the animation: update every 100ms.
ani = animation.FuncAnimation(fig, update, init_func=init, interval=10, blit=True)

plt.show()
