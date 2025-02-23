#pragma once

#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Wire.h>
#include <stdarg.h>

class OLEDHelper
{
public:
    // Constructor: Create an OLEDHelper object.
    // width: Display width in pixels (typically 128).
    // height: Display height in pixels (typically 64).
    // resetPin: Reset pin for the display (-1 if not used).
    // i2cAddr: I2C address for the display (commonly 0x3C).
    OLEDHelper(uint8_t width = 128, uint8_t height = 64, int8_t resetPin = -1, uint8_t i2cAddr = 0x3C)
        : _display(width, height, &Wire, resetPin), _i2cAddr(i2cAddr) {}

    // Initialize the OLED display.
    // Returns true if the initialization is successful.
    bool begin()
    {
        if (!_display.begin(SSD1306_SWITCHCAPVCC, _i2cAddr))
            return false;
        clear();
        setTextSize(1);
        setTextColor(SSD1306_WHITE);
        return true;
    }

    // Clear the display.
    inline void clear()
    {
        _display.clearDisplay();
    }

    // Set the cursor position.
    inline void setCursor(int16_t x, int16_t y)
    {
        _display.setCursor(x, y);
    }

    // Set the text size.
    inline void setTextSize(uint8_t size)
    {
        _display.setTextSize(size);
    }

    // Set the text color.
    inline void setTextColor(uint16_t color)
    {
        _display.setTextColor(color);
    }

    // Print a line of text (with newline).
    inline void println(const char *text)
    {
        // Get the bounding box of the text
        int16_t x1, y1;
        uint16_t w, h;
        _display.getTextBounds(text, 0, 0, &x1, &y1, &w, &h);

        // Calculate horizontal offset to center text
        int16_t x = (_display.width() - w) / 2;

        // Set the new cursor position before printing
        _display.setCursor(x, _display.getCursorY());
        _display.println(text);
    }

    // Update the display (flush the buffer).
    inline void display()
    {
        _display.display();
    }

    // Draw a horizontal percentage bar from left to right.
    // The input 'percentage' is clamped between 0 and 255.
    // The bar is drawn at the bottom of the display with a fixed height.
    inline void drawPercentageBar(uint16_t percentage)
    {
        if (percentage > 256)
            percentage = 255;

        uint8_t barWidth = _display.width();
        uint8_t barHeight = 10; // Fixed bar height; adjust as needed.

        uint8_t fillWidth = (barWidth * percentage) / 256;
        uint8_t y = _display.height() - barHeight; // Draw bar at the bottom.

        // Draw the border of the bar.
        _display.drawRect(0, y, barWidth, barHeight, SSD1306_WHITE);
        // Fill in the bar with the given percentage.
        _display.fillRect(0, y, fillWidth, barHeight, SSD1306_WHITE);
    }

private:
    Adafruit_SSD1306 _display;
    uint8_t _i2cAddr;
};
