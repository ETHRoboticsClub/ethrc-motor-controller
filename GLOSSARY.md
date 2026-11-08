# ethrc_motor_controller

A single-axis BLDC servo drive for humanoid robot joints, controlled by a central computer over EtherCAT.

## Board

**Drive**:
This board: the servo drive that runs one joint motor.
_Avoid_: ESC, motor controller (as a name for the board), speed controller

## EtherCAT

**ESC**:
The EtherCAT SubDevice Controller on the drive (the LAN9253). Never the board itself.
_Avoid_: EtherCAT slave controller, electronic speed controller

**MainDevice**:
The central computer that runs the EtherCAT network and sends setpoints to every drive.
_Avoid_: master, EtherCAT master

**SubDevice**:
A node on the EtherCAT line that the MainDevice controls; each drive is one SubDevice.
_Avoid_: slave

**Port 0 (IN)**:
The ESC's upstream port, which faces the MainDevice.
_Avoid_: port A, PHY A, ETH_A

**Port 1 (OUT)**:
The ESC's downstream port, which goes to the next SubDevice in the line.
_Avoid_: port B, PHY B, ETH_B

**PDI**:
The Process Data Interface: the link between the drive's MCU and the ESC.
_Avoid_: host bus, ESC SPI (as a name for the link)

**SII EEPROM**:
The non-volatile memory the ESC loads its configuration and identity from at start-up.
_Avoid_: ESC EEPROM, config EEPROM
