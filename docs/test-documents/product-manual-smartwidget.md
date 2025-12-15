# SmartWidget Pro 3000 User Manual

## Product Overview

The SmartWidget Pro 3000 is Contoso's flagship IoT device for smart home automation. This manual covers setup, configuration, troubleshooting, and advanced features.

**Model Number**: SW-PRO-3000  
**Firmware Version**: 4.2.1  
**Release Date**: October 2025

## Technical Specifications

| Specification | Value |
|--------------|-------|
| Dimensions | 4.5" x 3.2" x 1.1" |
| Weight | 185 grams |
| Power | 5V DC, 2A (USB-C) |
| Connectivity | Wi-Fi 6, Bluetooth 5.2, Zigbee 3.0 |
| Memory | 512MB RAM, 4GB Storage |
| Operating Temperature | 32°F - 104°F (0°C - 40°C) |
| Warranty | 2 years limited |

## Chapter 1: Getting Started

### 1.1 Box Contents

Your SmartWidget Pro 3000 package includes:
- SmartWidget Pro 3000 device
- USB-C power cable (6 ft)
- Power adapter (5V/2A)
- Quick start guide
- Wall mounting kit
- Warranty card

### 1.2 Initial Setup

1. **Download the App**: Install the Contoso Smart Home app from the App Store or Google Play
2. **Power On**: Connect the USB-C cable to the device and power adapter
3. **Wait for LED**: The LED will blink blue when ready for setup
4. **Connect**: Open the app and tap "Add New Device"
5. **Select Wi-Fi**: Choose your 2.4GHz or 5GHz network
6. **Complete Setup**: Follow the on-screen instructions

**Note**: The device requires a 2.4GHz or 5GHz Wi-Fi network. 6GHz networks are not supported.

### 1.3 LED Status Indicators

| LED Color | Pattern | Meaning |
|-----------|---------|---------|
| Blue | Blinking | Ready for setup |
| Blue | Solid | Connected and operational |
| Green | Pulse | Processing command |
| Yellow | Blinking | Firmware update in progress |
| Red | Solid | Error - see troubleshooting |
| Red | Blinking | No network connection |

## Chapter 2: Features and Functions

### 2.1 Voice Control

SmartWidget Pro 3000 supports:
- Amazon Alexa
- Google Assistant
- Apple HomeKit (via bridge)

**Sample Commands**:
- "Hey Google, turn on the living room lights"
- "Alexa, set the thermostat to 72 degrees"
- "Siri, lock the front door"

### 2.2 Automation Rules

Create powerful automations using the app:

**Time-based Rules**:
- Turn lights on at sunset
- Adjust thermostat based on schedule
- Run robot vacuum at 2 PM daily

**Sensor-based Rules**:
- Turn on lights when motion detected
- Send alert when door opens
- Adjust AC when temperature exceeds threshold

**Geo-fencing Rules**:
- Arm security when everyone leaves
- Pre-heat home when approaching
- Turn off all lights when last person leaves

### 2.3 Energy Monitoring

The SmartWidget Pro 3000 tracks energy usage for connected devices:
- Real-time power consumption
- Daily/weekly/monthly usage reports
- Cost estimation based on utility rates
- Peak usage alerts

Access reports in the app under **Settings > Energy > Reports**.

## Chapter 3: Troubleshooting

### 3.1 Device Won't Connect to Wi-Fi

**Symptoms**: LED blinks red, app shows "Connection Failed"

**Solutions**:
1. Ensure Wi-Fi password is correct
2. Move device closer to router during setup
3. Verify router is broadcasting 2.4GHz or 5GHz (not 6GHz only)
4. Restart your router
5. Factory reset the device (hold button for 10 seconds)

### 3.2 Device Offline in App

**Symptoms**: App shows device as "Offline" or "Unavailable"

**Solutions**:
1. Check if LED is solid blue (if not, check power)
2. Verify Wi-Fi network is operational
3. Restart the device by unplugging for 30 seconds
4. Check for router firmware updates
5. Ensure device is within Wi-Fi range

### 3.3 Voice Commands Not Working

**Symptoms**: Voice assistant says "device not responding"

**Solutions**:
1. Verify device is online in the Contoso app
2. Re-link the Contoso skill in your voice assistant app
3. Check that device names don't conflict
4. Ensure voice assistant and SmartWidget are on same network
5. Disable and re-enable the Contoso skill

### 3.4 Automation Rules Not Triggering

**Symptoms**: Scheduled automations don't execute

**Solutions**:
1. Verify device timezone is correct in app settings
2. Check that automation is enabled (not paused)
3. Verify all conditions in the rule are met
4. Check for conflicting rules
5. Update to latest firmware version

### 3.5 Factory Reset

To completely reset your SmartWidget Pro 3000:
1. Ensure device is powered on
2. Press and hold the reset button for 10 seconds
3. LED will flash red, then turn off
4. Release button when LED turns off
5. Device will restart and LED will blink blue
6. Set up device again using the app

**Warning**: Factory reset erases all settings, automations, and linked accounts.

## Chapter 4: Advanced Configuration

### 4.1 API Access

Developers can access the SmartWidget API for custom integrations:

**API Endpoint**: `https://api.contoso-smarthome.com/v2/`  
**Authentication**: OAuth 2.0  
**Rate Limit**: 1000 requests/hour

Documentation: https://developer.contoso.com/smartwidget

### 4.2 Local Network Mode

For privacy-conscious users, enable Local Network Mode:
1. Go to **Settings > Privacy > Local Mode**
2. Enable "Local Network Only"
3. Confirm the warning message

**Note**: This disables cloud features including:
- Remote access outside home network
- Voice assistant integration
- Automatic firmware updates
- Energy reports and history

### 4.3 Zigbee Network

SmartWidget Pro 3000 can act as a Zigbee hub:
- Supports up to 50 Zigbee devices
- Compatible with Zigbee 3.0 certified devices
- Mesh networking for extended range

To pair Zigbee devices:
1. Go to **Settings > Zigbee > Add Device**
2. Put your Zigbee device in pairing mode
3. Wait for discovery (up to 60 seconds)
4. Assign room and name

## Chapter 5: Safety and Compliance

### 5.1 Safety Warnings

- Do not expose to water or excessive moisture
- Do not operate outside specified temperature range
- Use only the provided power adapter
- Do not attempt to open or modify the device
- Keep away from heat sources

### 5.2 Regulatory Compliance

- FCC ID: 2ACONTOSO-SW3000
- IC: 12345-SW3000
- CE Mark compliant
- RoHS compliant

### 5.3 Disposal

This product contains electronic components. Please dispose of responsibly:
- Do not dispose in regular household waste
- Take to an e-waste recycling center
- Many retailers offer electronics recycling programs

---

**Support Contact**:  
Email: support@contoso.com  
Phone: 1-800-CONTOSO  
Web: https://support.contoso.com

*Document Version: 4.2.1*  
*Last Updated: December 2025*
