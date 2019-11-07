import time
import app_control
import antenna_control
import logging

logging.basicConfig(level=logging.DEBUG)
app_control.kill_apps()
time.sleep(10)
con = antenna_control.AntennaControl()
con.emergency_stop()
con.park_antenna()
con.connection_exit()
time.sleep(10)
app_control.start_apps()
