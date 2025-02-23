# Dunkatron Breathometer

**Dunkatron Breathometer** is an embedded project for the ESP32 that measures a user’s breath using an attached microphone, processes the signal through a chain of custom filters, and transmits the processed data via Bluetooth Low Energy (BLE). In addition, an OLED display shows real‑time connection status and breath metrics, while a hardware timer ensures constant sampling rates.

This project was designed to be modular and extensible, with separate components for BLE communication, filtering, OLED output, and timer management. It is ideal for applications like breath analyzers, interactive breathing games, and other sensor‐based projects.

---

## Table of Contents

- [Features](#features)
- [Architecture & Components](#architecture--components)
  - [PersistentBLEServer](#persistentbleserver)
  - [OLEDHelper](#oledhelper)
  - [TimerHelper](#timerhelper)
  - [Filters](#filters)
- [Hardware Requirements](#hardware-requirements)
- [Software Requirements](#software-requirements)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [Customization & Extensions](#customization--extensions)
- [License](#license)

---

## Features

- **Continuous Breath Sampling:**  
  Uses a high‑frequency ADC sampling routine via hardware timer interrupts to capture microphone data.
  
- **Advanced Filtering:**  
  Implements a configurable chain of filters including derivative, squared, timed moving average, and low‑pass filters (using both floating‑point and fixed‑point arithmetic).

- **Bluetooth Low Energy (BLE) Communication:**  
  Advertises a custom BLE service with notifications. The `PersistentBLEServer` class handles connection, reconnection, and data transmission.

- **OLED Display Integration:**  
  An OLED display shows dynamic status messages (e.g. “Connected”, “Waiting...”) and a graphical percentage bar that represents the processed breath amplitude.

- **Task & Timer Management:**  
  Uses FreeRTOS tasks (via `xTaskCreatePinnedToCore`) for offloading OLED updates, ensuring smooth operation while maintaining a constant sampling rate.

---

## Architecture & Components

### PersistentBLEServer

- **Location:** `PersistentBLEServer.hpp`  
- **Description:**  
  This class encapsulates BLE server functionality. It initializes the ESP32 BLE device with a given name, service UUID, and characteristic UUID. It handles callbacks on client connect/disconnect and manages BLE advertising.

- **Key Features:**
  - Automatic restart of advertising when a client disconnects.
  - Provides a getter to access the BLE characteristic for sending notifications.
  - Seamless integration with the rest of the project via a global pointer.

### OLEDHelper

- **Location:** `OLEDHelper.hpp`  
- **Description:**  
  A helper class for managing an SSD1306 OLED display. It encapsulates initialization, text formatting, and drawing functions (including a percentage bar for visualizing breath amplitude).

- **Key Features:**
  - Centered text printing.
  - Drawing a horizontal percentage bar at the bottom of the screen.
  - Methods for clearing, setting cursor position, and updating the display.

### TimerHelper

- **Location:** `TimerHelper.hpp`  
- **Description:**  
  Contains a function (`registerTimerTask`) that sets up hardware timers on the ESP32. These timers trigger high‑frequency sampling routines using interrupts.

- **Key Features:**
  - Configurable timer frequency.
  - Supports multiple timer tasks by storing timer handles in an array.

### Filters

- **Location:** `./filters/Filters.hpp` (and associated files)  
- **Description:**  
  A set of custom filters implemented in C++ that process ADC samples. The filters include:
  - **DerivativeFilter:** Computes the difference between successive samples.
  - **SquaredFilter:** Squares the sample to emphasize higher amplitudes.
  - **TMAFilter:** A timed moving average filter implemented using a circular buffer.
  - **LowPassFilter:** A fixed‑point low‑pass filter that gradually moves its internal state toward the incoming sample.
  - **Chained Filters:** A recursive template that allows the chaining of multiple filters to form a composite filter.

- **Key Features:**
  - Highly configurable – you can easily adjust filter parameters.
  - Chained filters allow complex signal processing in a modular fashion.
  - Both fixed‑point and floating‑point implementations are supported.

---

## Hardware Requirements

- **ESP32 Development Board:**  
  Provides Wi-Fi, Bluetooth, and hardware timer support.
  
- **Microphone Module:**  
  Connected to an ADC‑capable pin (e.g., `MIC_PIN = 15`).

- **OLED Display:**  
  An SSD1306-based OLED display connected via I²C. Default I²C address is 0x3C.
  
- **BLE Antenna:**  
  Built‑in to the ESP32, used for BLE communications.

- **Additional Components:**  
  GPIO pins configured for power management (e.g., using pins 26 and 27 for VCC and GND in this project).

---

## Software Requirements

- **Arduino IDE / PlatformIO:**  
  For compiling and uploading the firmware to the ESP32.

- **ESP32 Board Support Package:**  
  Ensure you have the latest ESP32 core libraries installed.

- **BLE Library:**  
  Uses the built‑in ESP32 BLE libraries (`BLEDevice.h`, `BLEUtils.h`, etc.).

- **Adafruit SSD1306 Library:**  
  For OLED display functionality.

- **FreeRTOS:**  
  Used implicitly through the ESP32 framework for task creation and timer management.

---

## Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/DunkatronBreathometer.git
   cd DunkatronBreathometer
   ```

2. **Install Dependencies:**
   - Install the [Adafruit SSD1306](https://github.com/adafruit/Adafruit_SSD1306) and [Adafruit GFX](https://github.com/adafruit/Adafruit-GFX-Library) libraries via the Arduino Library Manager.
   - Ensure your ESP32 board package is installed in the Arduino IDE.

3. **Hardware Wiring:**
   - Connect the microphone module to the ADC‑capable pin (default is 15).
   - Connect the OLED display via I²C (SDA, SCL; default pins on ESP32 are typically GPIO 21 and 22).
   - Configure additional GPIO pins as required (e.g., pins 26 and 27 for power management).

4. **Configuration:**
   - Edit `DEVICE_NAME`, `SERVICE_UUID`, and `CHARACTERISTIC_UUID` in the main source file if necessary.
   - Adjust filter parameters in `./filters/Filters.hpp` as needed.

5. **Upload the Code:**
   - Compile and upload the project to your ESP32 using the Arduino IDE or PlatformIO.

---

## Usage

Once uploaded, the ESP32 will:
- Initialize the OLED display and begin advertising over BLE.
- Continuously sample the microphone input using a hardware timer interrupt.
- Process the ADC samples through a chain of filters to extract a smooth breath amplitude.
- Update the OLED display with the connection status and a graphical percentage bar representing the breath amplitude.
- Transmit the processed data via BLE notifications to any connected client.

You can monitor the serial output (if DEBUG is enabled) for debug messages regarding the BLE connection and sensor readings.

---

## Customization & Extensions

- **Filter Tuning:**  
  The filter chain is constructed using template functions and lambda functions. You can change the number of cascaded filters, adjust the RC time constants, or add additional filters to modify the response.

- **Display Customization:**  
  The `OLEDHelper` class can be extended to include more advanced graphics, fonts, or animations.

- **BLE Services:**  
  The BLE service can be extended to transmit additional data or support bidirectional communication.

- **Hardware Integration:**  
  Integrate additional sensors (e.g., temperature, humidity) and display more complex information on the OLED or transmit it over BLE.

- **Power Management:**  
  The project is designed to run on battery power. You can add sleep modes or dynamic frequency scaling to extend battery life.

---

## License

This project is released under the MIT License.

---

## Acknowledgements

- **ESP32 Community:**  
  For the robust ESP32 BLE libraries and extensive documentation.
- **Adafruit:**  
  For the SSD1306 and GFX libraries that simplify OLED display handling.
- **Open Source Contributors:**  
  Thanks to everyone who contributes to open‑source libraries and tools used in this project.

---

This README provides a comprehensive overview of the Dunkatron Breathometer project, covering everything from high‑level architecture to installation, usage, and potential extensions. Feel free to modify it as your project evolves.
