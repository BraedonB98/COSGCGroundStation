import subprocess
import os
import logging
import log_mod as logger


def kill_apps():
    out = subprocess.run(["taskkill", "/f", "/t", "/im", "xwxtoimg.exe"], universal_newlines=True,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout
    out = out.replace('\n', '')
    res = out.rpartition(':')
    if res[0] == 'ERROR':
        logger.log.warning(res[2])
    else:
        logger.log.info(res[2])
    out = subprocess.run(["taskkill", "/f", "/t", "/im", "SDRSharp.exe"], universal_newlines=True,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout
    out = out.replace('\n', '')
    res = out.rpartition(':')
    if res[0] == 'ERROR':
        logger.log.warning(res[2])
    else:
        logger.log.info(res[2])
    out = subprocess.run(["taskkill", "/f", "/t", "/im", "SatPC32.exe"], universal_newlines=True,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout
    out = out.replace('\n', '')
    res = out.rpartition(':')
    if res[0] == 'ERROR':
        logger.log.warning(res[2])
    else:
        logger.log.info(res[2])


def start_apps():
    os.system("C:\\Users\\COSGC\\PycharmProjects\\noaaauto_v2\\start.bat")
    logger.log.info('Applications restarted')

# kill_apps()
# start_apps()
