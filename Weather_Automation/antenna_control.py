import logging
import log_mod as logger
import time

import serial


class AntennaControl:
    def __init__(self):
        # initialise serial communication for antenna rotator controller
        try:
            self.ser = serial.Serial(
                port='COM2',
                baudrate=9600,
                parity="N",
                stopbits=1,
                bytesize=8,
                timeout=8
            )
            logger.log.info('Serial connection established')
        except serial.SerialException:
            logger.log.error('Serial connection failed')

    def emergency_stop(self):  # processes button press to stop current rotator instruction execution
        self.ser.write('s\r\n'.encode('utf-8'))

    def connection_exit(self):  # processes button press to close serial session and exit the program
        logger.log.info('Serial connection terminated')
        self.ser.close()

    def park_antenna(self):  # set the antenna to the parking position
        # returns 0 if successful after 2x expected rotation time, 1 otherwise
        self.ser.write('W180 090\r\n'.encode('utf-8'))
        time.sleep(75)

        self.ser.write(('c2' + '\r\n').encode('utf-8'))
        self.current_posi = self.ser.read(16)
        self.current_posi = self.current_posi[0:14]

        self.current_az = self.current_posi[3:6]
        self.current_el = self.current_posi[11:14]

        if not (178 <= int(self.current_az) <= 182 and 88 <= int(self.current_el) <= 92):
            time.sleep(75)

            self.ser.write(('c2' + '\r\n').encode('utf-8'))
            self.current_posi = self.ser.read(16)
            self.current_posi = self.current_posi[0:14]

            self.current_az = self.current_posi[3:6]
            self.current_el = self.current_posi[11:14]
            if not (178 <= int(self.current_az) <= 182 and 88 <= int(self.current_el) <= 92):
                logger.log.warning('Failed to park antenna within expected time')
        logger.log.info('Antenna parked')

# con = AntennaControl()
# con.emergency_stop()
# con.park_antenna()
# con.connection_exit()
