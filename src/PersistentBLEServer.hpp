#pragma once

#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>

class PersistentBLEServer : public BLEServerCallbacks {
public:
    PersistentBLEServer(const char* deviceName, const char* serviceUUID, const char* charUUID) {
        // Initialize BLE device with the given device name.
        BLEDevice::init(deviceName);

        // Create the BLE server and assign callbacks.
        pServer = BLEDevice::createServer();
        pServer->setCallbacks(this);

        // Create service and characteristic.
        pService = pServer->createService(serviceUUID);
        pCharacteristic = pService->createCharacteristic(
            charUUID,
            BLECharacteristic::PROPERTY_NOTIFY
        );
        pCharacteristic->addDescriptor(new BLE2902());
        pService->start();

        // Set up advertising with service UUID and scan response.
        pAdvertising = BLEDevice::getAdvertising();
        pAdvertising->addServiceUUID(serviceUUID);
        pAdvertising->setScanResponse(true);
        pAdvertising->start();

        deviceConnected = false;

        Serial.println("PersistentBLEServer: Advertising started.");
    }

    // Accessor for the characteristic.
    BLECharacteristic* getCharacteristic() {
        return pCharacteristic;
    }

    // Returns the connection status.
    bool isConnected() const {
        return deviceConnected;
    }

    // Callback: Executed when a client connects.
    void onConnect(BLEServer* pServer) override {
        deviceConnected = true;
        Serial.println("PersistentBLEServer: Client connected.");
        // Stop advertising when a client is connected.
        pAdvertising->stop();
    }

    // Callback: Executed when a client disconnects.
    void onDisconnect(BLEServer* pServer) override {
        deviceConnected = false;
        Serial.println("PersistentBLEServer: Client disconnected; restarting advertising...");
        // Restart advertising upon disconnection.
        pAdvertising->start();
    }

private:
    BLEServer*          pServer;
    BLEService*         pService;
    BLECharacteristic*  pCharacteristic;
    BLEAdvertising*     pAdvertising;
    bool                deviceConnected;
};
