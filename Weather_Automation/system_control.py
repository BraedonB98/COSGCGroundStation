import logging
import sys
import time
import log_mod as logger

import dlipower


class PowerControl:
    def __init__(self):
        self.switch = dlipower.PowerSwitch(hostname='192.168.1.100', userid='COSGC', password='GndSt@tion')
        if self.switch.verify():
            logger.log.info("Switch is responding")
        else:
            logger.log.critical(dlipower.DLIPowerException)
            sys.exit()

        self.rotator_controller = self.switch[0]
        self.lna_rotator_interface = self.switch[1]
        self.transceiver = self.switch[2]

    def status(self):
        self.switch.printstatus()
        logger.log.debug(self.switch)

    def turn_off(self):
        time.sleep(2)
        self.rotator_controller.state = 'OFF'
        logger.log.info("In turn_off(): %s is now %s", self.rotator_controller.description, self.rotator_controller.state)
        time.sleep(3)
        self.lna_rotator_interface.state = 'OFF'
        logger.log.info("In turn_off(): %s is now %s", self.lna_rotator_interface.description,
                     self.lna_rotator_interface.state)

    def turn_on(self):
        time.sleep(2)
        self.rotator_controller.state = 'ON'
        logger.log.info("In turn_on(): %s is now %s", self.rotator_controller.description, self.rotator_controller.state)
        time.sleep(3)
        self.lna_rotator_interface.state = 'ON'
        logger.log.info("In turn_on(): %s is now %s", self.lna_rotator_interface.description,
                     self.lna_rotator_interface.state)


if __name__ == "__main__":
    SGC_DHD = PowerControl()
    # SGC_DHD.status()
    # time.sleep(3)
    # SGC_DHD.turn_off()
    # SGC_DHD.status()
    # time.sleep(3)
    # SGC_DHD.turn_on()
    # SGC_DHD.status()
