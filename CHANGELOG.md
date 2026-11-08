# Changelog

## [Unreleased]

### Added

-   High-side P-FET reverse-polarity protection (Q10 SUM70101EL, R83/R84 gate divider, D23 15 V gate clamp) between the XT60 pass-through bus VBAT_IN and +VBAT.
-   1 µF low-ESR capacitor on the LAN9253 VDDCR pin (DS00003421B §4.1.1).
-   LMR38020 symbol, DDA0008B footprint with 8 thermal vias, and SUM70101EL symbol, footprint and 3D model.
-   Description, manufacturer and supplier part numbers for the EtherCAT and 5 V buck parts.

### Changed

-   5 V buck from LMR51625 (60 V) to LMR38020SDDAR (80 V) at 400 kHz, with a 40.2 k / 10 k feedback divider.
-   Input TVS from bidirectional SMBJ60CA to CHASSIS to unidirectional SMBJ60A to GND on the protected +VBAT.
-   EtherCAT PHY terminations R59-R66 to 0402 and all EtherCAT capacitors to the project footprint library.
-   R43 bus-sense resistor from 0402 to 0805 (working voltage at 58.8 V).
-   CI variant to DRAFT while the PCB layout restarts.

### Fixed

-   DRV8353 SDI on PC12 (SPI3_MOSI) instead of PC13.
-   HALL_B/HALL_C moved off PB8-BOOT0 to PA11/PA12.
-   Resistor/capacitor footprint mix-ups (R8, R9, R10, R13, R14, R15, R48, R59, R78, R79, C18, C20, C47) and the missing J16 Hall connector footprint.

## [1.1.1] - 2025-01-18

### Fixed

-   Replace non-stocked components. 

## [1.1.0] - 2024-04-13

### Added

-   RC snubber passive values.

### Fixed

-   More vias for VBUS and LMR36006 GND pads.
-   Board version voltage reference from +3V3 to +A3V3.

### Changed

-   Motor thermistor resistor divider to 2kOhm for a 10k 3950K thermistor.

## [1.0.2] - 2024-03-12

### Changed

-   Power sequencing graph according to experimental data.

## [1.0.1] - 2024-01-25

### Added

-   Controller target specifications.
-   Credits to moteus on cover page.
-   Optional RC-Snubber to power stage.

### Fixed

-   Chassis guard ring to go around the board.
-   CAN and power TVS diodes now go to chassis.
-   Clearance between nets to respect IEC60664-1 where possible.
-   Comment on precharge.
-   Power TVS diode reference designator from "U" to "D".

### Changed

-   5V 300 mA buck converter with 600 mA version.
-   Chassis-GND capacitor by 1nF 1kV.

## [1.0.0] - 2023-12-12

### Added

-   TVS protection and termination switch to FD-CAN.
-   Low-side switched 12V 600 mA source for external fan.
-   LDO for analog supply.
-   One TVS diode per power connector.
-   Second on-board I2C magnetic encoder for disambiguation.
-   ESD protection to all interfaces.
-   Over-voltage protection on thermistor ADC inputs.
-   Pi filters to inputs of buck regulators and MCU analog supply.
-   Decoupling caps next to power pins of connectors.

### Changed

-   CPH-CPL capacitor to 47 nF (gate driver).
-   FD-CAN transceiver IC.
-   FETs for top cooled variant.
-   Input power TVS diode to bidirectional.
-   Moved SOx low-pass filter to MCU section.
-   PWM_PHASEA with PWM_PHASEC on STM32G474 pinout for easier routing.
-   RS422 pinout on connector.
-   Buck regulators to optimize for low noise.

[Unreleased]: https://github.com/nguyen-v/amulet_controller_kibot/compare/1.1.1...HEAD

[1.1.1]: https://github.com/nguyen-v/amulet_controller_kibot/compare/1.1.1...1.1.1

[1.1.1]: https://github.com/nguyen-v/amulet_controller_kibot/compare/75a4252278e2e99f125718f921b713f39e2bfcda...1.1.1
