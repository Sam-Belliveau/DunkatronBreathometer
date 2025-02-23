#include <Arduino.h>
#include "./PersistentBLEServer.hpp"
#include "./OLEDHelper.hpp"
#include "./TimerHelper.hpp"
#include "./filters/Filters.hpp"

//==================================================
//           Configuration & Constants
//==================================================
#define DEVICE_NAME "Dunkatron Breathometer"
#define SERVICE_UUID "81101fbc-f19e-4e6a-9588-500bbaf60880"
#define CHARACTERISTIC_UUID "907ffb4a-b15b-4acd-914d-947984b62ecc"

constexpr uint8_t MIC_PIN = 15;

//==================================================
//                Debug Configuration
//==================================================
// Uncomment the following line to enable serial debug output.
// #define DEBUG

#ifdef DEBUG
#define DEBUG_PRINT(x) Serial.print(x)
#define DEBUG_PRINTLN(x) Serial.println(x)
#define DEBUG_PRINTF(...) Serial.printf(__VA_ARGS__)
#else
#define DEBUG_PRINT(x)
#define DEBUG_PRINTLN(x)
#define DEBUG_PRINTF(...)
#endif

//==================================================
//                 Filter Chain Setup
//==================================================
auto filter = chain_filters(
    DerivativeFilter(),
    SquaredFilter(), 
    TMAFilter<128>(),
    TMAFilter<128>(),
    LowPassFilter(1.0 / 512.0),
    LowPassFilter(1.0 / 512.0));

//==================================================
//            Global BLE & Data Variables
//==================================================
PersistentBLEServer *pServer = nullptr;
OLEDHelper oled(128, 64, -1, 0x3C);

volatile SampleType breathAmpltude = 0;
volatile uint32_t sampleCount = 0;

//==================================================
//        Timer ISR: Sample the Microphone
//==================================================
void IRAM_ATTR readMicrophone()
{
  // Read ADC sample (ensure MIC_PIN is ADC-capable)
  uint16_t rawValue = analogRead(MIC_PIN);

  // Center the ADC value and shift to improve resolution.
  SampleType sample = clamped_cast((rawValue - (SampleAccumType(1 << 12) / 2)) << 4);

  // Process sample through the filter chain.
  breathAmpltude = filter(sample);
  sampleCount++;
}

//==================================================
//       OLED Update Task (Runs Concurrently)
//==================================================
void oledTask(void *pvParameters)
{
  int waitState = 0;

  for (;;)
  {
    // Clear and prepare the display.
    oled.clear();
    oled.setCursor(0, 0);
    oled.setTextSize(2);
    oled.println("DUNKATRON");
    oled.println("");

    // Display connection status.
    if (pServer->isConnected())
    {
      oled.println("Connected");
    }
    else
    {
      // Cycle through waiting messages.
      switch (waitState)
      {
      case 0:
        oled.println("Waiting.  ");
        waitState = 1;
        break;
      case 1:
        oled.println("Waiting.. ");
        waitState = 2;
        break;
      case 2:
      default:
        oled.println("Waiting...");
        waitState = 0;
        break;
      }
    }

    // Draw a percentage bar using the processed breath amplitude.
    oled.drawPercentageBar(breathAmpltude >> 6);
    oled.display();

    // Update every 100 ms.
    delay(100);
  }
}

//==================================================
//        Setup Function: Initialization
//==================================================
void setup()
{
#ifdef DEBUG
  Serial.begin(115200);
#endif

  // Initialize OLED display.
  oled.begin();

  // Initialize BLE device and create service & characteristic.
  BLEDevice::init(DEVICE_NAME);
  pServer = new PersistentBLEServer(DEVICE_NAME, SERVICE_UUID, CHARACTERISTIC_UUID);

  // Configure ADC settings.
  adcAttachPin(MIC_PIN);
  analogReadResolution(12);
  analogSetClockDiv(1);

  // Configure GPIO 26 as Ground and 27 as VCC
  pinMode(26, OUTPUT);  
  pinMode(27, OUTPUT);
  digitalWrite(26, LOW);
  digitalWrite(27, HIGH);

  // Set up hardware timer (timer divider of 80 gives 1µs tick on an 80MHz clock).
  registerTimerTask(readMicrophone, 4096);

  // Create the OLED update task on core 1.
  xTaskCreatePinnedToCore(oledTask, "OLED Task", 4096, NULL, 1, NULL, 1);

  DEBUG_PRINTLN("Advertising as " DEVICE_NAME);
  DEBUG_PRINTLN("Setup complete.");
}

//==================================================
//   Main Loop: BLE Notifications & Loop Timing
//==================================================
constexpr unsigned long LOOP_PERIOD_US = 1000000 / 30; // 30 Hz update rate.
constexpr unsigned long MAX_RUNAHEAD_US = 1000000;     // Maximum run-ahead: 1 second.
unsigned long loopDeadlineUs = 0;

void loop()
{
  unsigned long now = micros();

  // Debug: print the current filtered value, sample count, and connection status.
  DEBUG_PRINTF(" | Filtered value: %6d | Samples / Loop: %6lu | Connected: %s |\r\n",
               breathAmpltude,
               sampleCount,
               pServer->isConnected() ? "yes" : "no");

  // Reset sample count for the next cycle.
  sampleCount = 0;

  // Send BLE notification if a client is connected.
  if (pServer->isConnected())
  {
    uint8_t data[4] = {
        0xBE, 0xEF,
        static_cast<uint8_t>((breathAmpltude >> 8) & 0xff),
        static_cast<uint8_t>(breathAmpltude & 0xff)};

    pServer->getCharacteristic()->setValue(data, sizeof(data));
    pServer->getCharacteristic()->notify();
  }

  // Loop timing: adjust the deadline to maintain a consistent update rate.
  if (now < loopDeadlineUs - MAX_RUNAHEAD_US || loopDeadlineUs + MAX_RUNAHEAD_US < now)
  {
    loopDeadlineUs = now;
  }
  else
  {
    loopDeadlineUs += LOOP_PERIOD_US;
  }

  // Sleep until the next cycle if needed.
  if (now < loopDeadlineUs)
  {
    int sleepDuration = (loopDeadlineUs - now) / 1000;
    delay(sleepDuration);
  }
}
