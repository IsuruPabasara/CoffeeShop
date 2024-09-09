# EE 5450 Project: Multi-characteristic BLE Sensor Node

## Overview

In this project, you will create your own BLE Sensor Node, based on the previous assignment, but using the sensors you want. Choose the official BLE Service profile that makes the most sense. Provide an additional characteristic based on an additional sensor available on your X-NUCLEO-IKS01A3 sensor shield or a sensor that you personally have and are interested in working with.

See the [Bluetooth Profile List](https://www.bluetooth.com/specifications/specs/?types=adopted) (check the Service PDFs for the characteristics tables for each service, not the Profile PDFs) or Page 182 on the [Bluetooth Assigned Numbers](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Assigned_Numbers/out/en/Assigned_Numbers.pdf?v=1711647856831) PDF.

## System overview

You'll need your X-NUCLEO-IKS01A3 sensor board attached to your nRF52-DK board for this. Make sure you turn the board a bit and move the jumper currently on JP6 to not be connected to anything so that all of your buttons on the Nordic board work properly.

In this assignment, you'll have the following hardware as part of your system:

- Nordic nRF52-DK board
  - BLE SoftDevice
  - LEDs
  - Buttons
- ST X-NUCLEO-IKS01A3 (8-bit "addresses" for each device are on the schematics)
  - STTS751 local temperature sensor
  - Another I2C or SPI sensor of your choice (either on this shield or your own wiring).

Do **not** use the built-in Zephyr drivers for this sensor; you must make
the interact with the sensor device using the i2c\_\* functions directly. You may
make your own wrapper driver functions, however, which actually is preferred. This
will allow you to practice reading the datasheet for how to actually interact with
the sensor device.

## Your assignment

1. Go over the datasheets of the other sensor device. Note down the following (you may edit this README):
   1. Device I2C address (if using I2C)
      : 0xBA (LPS22HH sensor)
   1. Device known value register (and the known value)
      : 0x5D
   1. Note the data request method for reading a register for the device (is it write register address then read data, or are there other steps?)
      : Write register then read
   1. Do you need to set any registers to enable the sensor? For example, the HTS221 requires that you set bit 7 in CTRL_REG1 (0x20) to 1 to activate the device.
      : To update the reading at 10 Hz, had to set CTRL_REG1(0x10) to 0x20
   1. Which register do you read values from? What conversions are required in order to get a real temperature value from the binary data?
      : Read from PRESS_OUT_XL(0x28), PRESS_OUT_L(0x29) and PRESS_OUT_H(0x2A). Then bit shifted them as PRESS_OUT_H & PRESS_OUT_L & PRESS_OUT_XL to get a 24 bit number. Converted this to 2's complement and divided by the senstivity of 4096.
1. Create a new section in your DeviceTree Overlay (.dts) file for your other sensor. Make sure the STTS751 still exists as well in your dts file.
1. Draw a system diagram and either a flowchart, state machine, or sequence diagram for each thread in your system below, where all threads should be using message passing (no shared memory variables) to communicate with each other:
   1. One thread that will read the temperature from the STTS751 every second. Log the temperature using the DBG level to confirm that everything is working properly. You can blow on the sensor to heat the sensor up.
   1. One thread that will read from your other sensor at whatever sample rate makes sense for the sensor data type. For instance, accelerometer data should be at a fairly high sample rate (definitely faster than 1 Hz). Log the sensor value using the DBG level to confirm that everything is working properly.
   1. What synchronization primitive do you need to protect your I2C bus?
      Threads with different priorities are used when reading the two sensors also used mutexes when accesing the I2C bus
   1. One thread to handle your BLE service (where we will push sensor data to clients/centrals via the "notify" and/or "indicate" scheme in GATT). This thread will use message passing to receive temperature values from your sensor threads.
   1. The main thread should just be a clock that prints the current uptime every 2 seconds to show that it is alive.
1. Implement your system in Zephyr using the libraries you need.
   1. Are there any changes that you made to your design as a result of implementing your system?
      I was initially using the HTTS temperature sensor to calculate average temperature. But the accuracy of the two temperature sensors was very different, so it didn't make a lot of sense. So I used the pressure sensor instead.
   2. Do your service characteristics make more sense to be notifications or indications?
      They make more sense being indications
