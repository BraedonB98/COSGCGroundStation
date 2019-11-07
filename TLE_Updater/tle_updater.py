#dependencies for tle
import configparser
import time
import logging
from logging.handlers import TimedRotatingFileHandler
#dependencies for n2yo+celestrak
import http.client
from bs4 import BeautifulSoup
from shutil import copy2
#dependencies for fix_keps
import re
from tempfile import mkstemp
from shutil import move
from os import fdopen, remove
from pathlib import PurePath

formatter = logging.Formatter('%(asctime)s %(levelname)s:%(module)s:%(message)s')
log_folder = PurePath("./")
log_path = log_folder / 'tle_log.log'

def setup_logger(name, log_file, level=logging.INFO, filemode='a'):
    handler = TimedRotatingFileHandler(log_file, when='D', interval=14, backupCount=4, utc=False)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


def celestrak(config, sat, log):
    try:
        conn = http.client.HTTPSConnection("www.celestrak.com")
        conn.request("GET", "/NORAD/elements/"+config.get(sat, "file"))
        r1 = conn.getresponse()
        data = str(r1.read(100000))
        data = data.replace('b\'', '')
        data = data.replace('b\"', '')
        data = data.replace('\'', '')
        data = data.replace('\"', '')
        data = data.replace('\\r', '')
        data = data.replace('\\n', '\n')
        with open(config.get(sat, "endfile"), 'a') as outfile:
            outfile.write(data)
    except http.client.HTTPException:
        log.error("TLE " + config.get(sat, "name" + str(
            idx + 1)) + " in " + sat + " not updated. Could not connect to celestrak.com.")
    except:
        log.error("TLEs in "+config.get(sat, "file")+" not updated. Check filenames and options.")
        return
    #option to run fix_keps
    if config.getboolean(sat, 'fix_keps'):
        fix_keps(config.get(sat, "endfile"))
    log.info("TLEs in "+config.get(sat, "file")+" updated.")


def n2yo(config, sat, log):
    numsats = config.get(sat, 'num_tles')
    conn = http.client.HTTPSConnection("www.n2yo.com")
    with open(config.get(sat, "endfile"), 'w') as outfile:
        for idx in range(int(numsats)):
            try:
                conn.request("GET", "/satellite/?s=" + config.get(sat, "norad_id" + str(idx + 1)))
                r1 = conn.getresponse()
                data = r1.read(30000)  # 30,000 bytes
                # cheating parser that finds the <pre> tag, which is only used for keplers"
                soup = BeautifulSoup(str(data), 'html.parser')
                raw = str(soup.find('pre').contents[0])
                #print(raw)
                # replace escape characters
                ready = raw.replace('\\r', '')
                ready = ready.replace('\\n', '\n')
                outfile.write(config.get(sat, "name"+str(idx+1)))
                outfile.write(ready)
            except AttributeError:
                log.error("TLE "+config.get(sat, "name"+str(idx+1))+" in "+sat+" not updated. Invalid NORAD ID?")
            except http.client.HTTPException:
                log.error("TLE "+config.get(sat, "name"+str(idx+1))+" in "+sat+" not updated. Could not connect to n2yo.com.")
            except:
                log.error("TLE "+config.get(sat, "name"+str(idx+1))+" in "+sat+" not updated. Could not retrieve TLE.")
    log.info("TLEs in "+sat+" updated.")


def local(config, sat, log):
    try:
        copy2(config.get(sat, "file"),config.get(sat, "endfile"))
    except:
        log.error("TLEs in " + sat + " not updated. Check filenames and parameters.")
    log.info('TLEs in "+sat+" updated.')


def fix_keps(file_path):
    # Create temp file
    fh, abs_path = mkstemp()
    with fdopen(fh, 'w') as new_file:
        with open(file_path) as old_file:
            for line in old_file:
                new_line = re.sub(r'(AA )|(AA-)', 'AA', line)
                new_file.write(re.sub(r'METEOR-M ', 'METEOR', new_line))
    # Remove original file
    remove(file_path)
    # Move new file
    move(abs_path, file_path)

#begin TLE download
def main():
    log = setup_logger('logger', log_path, level=logging.INFO)
    log.info('TLE update started')
    config = configparser.ConfigParser()
    try:
        config.read_file(open('tle_conf.ini'))
        files = config.sections()

        for sat in files:
            source = config.get(sat, 'source')
            if source == 'celestrak':
                celestrak(config, sat, log)
            elif source == 'n2yo':
                n2yo(config, sat, log)
            elif source == 'local':
                local(config, sat, log)
            else:
                log.warning('TLEs in '+str(sat)+' not updated. Valid source option not specified.')
    except:
        log.error('Failed to open config file (tle_conf.ini).')
    log.info('TLE updater shutting down\n')

if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        sys.exit()
