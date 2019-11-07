import json
import logging
import subprocess
import sys
import time
from datetime import timedelta, datetime

import requests
from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from darksky import forecast
from pytz import utc

import antenna_control
import app_control
import log_mod as logger
import test_forecast
import system_control

logger.DBG = 0

# lat, long of Boulder, CO
BOULDER = 40.0076, -105.2619
# lat, long of Greenland
# BOULDER = 63.3833, -41.3

max_gust = 44

scheduler = BackgroundScheduler(timezone=utc)

# create jobstores
startupjob = MemoryJobStore()
shutdownjob = MemoryJobStore()
alertstartupjob = MemoryJobStore()
alertshutdownjob = MemoryJobStore()

SG_Power = system_control.PowerControl()

class WeatherObjects:
    plan = list()
    hours48 = list()
    mode = int()


# IFTTT trigger function
# "The antenna has been shut down due to {message1} until {message2}.
#  regular operations will resume at {message3}."
def notification(message1, message2, message3):
    if logger.DBG == 0:
        report = {"value1": message1, "value2": message2, "value3": message3}
        requests.post("https://maker.ifttt.com/trigger/shutdown_triggered/with/key/ge8JjtsnPuA-kK0jFxD5VFw9yVYBEEDQDjR6jj7aykK", data=report)

#check to see if system is running
def get_apps_state():
    #determine state of three main automation programs
    out = subprocess.run(["tasklist", "/fi", "IMAGENAME eq xwxtoimg.exe"], universal_newlines=True, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT).stdout
    if out.find("INFO: No tasks are running which match the specified criteria.") != -1:
        task1 = False
    else:
        task1 = True
    out = subprocess.run(["tasklist", "/fi", "IMAGENAME eq SDRSharp.exe"], universal_newlines=True, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT).stdout
    if out.find("INFO: No tasks are running which match the specified criteria.") != -1:
        task2 = False
    else:
        task2 = True
    out = subprocess.run(["tasklist", "/fi", "IMAGENAME eq SatPC32.exe"], universal_newlines=True, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT).stdout
    if out.find("INFO: No tasks are running which match the specified criteria.") != -1:
        task3 = False
    else:
        task3 = True
    if task1 and task2 and task3:
        #programs running normally
        logger.log.debug('all programs running')
        return True
    elif task1 or task2 or task3:
        #not all programs running
        logger.log.warning('Not all automation programs are running:')
        if not task1:
            logger.log.warning('WXtoIMG is stopped')
        if not task2:
            logger.log.warning('SDRSharp is stopped')
        if not task3:
            logger.log.warning('SatPC32 is stopped')
        return True
    else:
        #no programs running (expected state after shutdown)
        logger.log.debug('all programs stopped')
        return False

# gets string for start/stop messages
def get_msg_time(timestamp):
    if timestamp == -1 or timestamp == 1799:
        return "none"
    else:
        return datetime.utcfromtimestamp(timestamp).strftime("%a, %H:%M")


# define function to run every 48 hours
def hourly_two_day():
    # initialize current date and time
    now = datetime.now()
    today = datetime.today()

    logger.log.info('Requesting weather data...')

    if logger.DBG == 1:
        testjson = json.load(open('test_input.json','r'))
        data = test_forecast.forecast_generator(testjson)
    else:
        data = forecast('8d92b5778ac6f73e8de298d4f4fb761b', *BOULDER)
    # submit API key
    with data as boulder:
        # print any weather alerts
        if hasattr(boulder, "alerts"):
            logger.log.warning('A weather alert has been detected.')
            for alert in boulder.alerts:
                print(alert.title, "\n",
                      alert.description, "\n",
                      datetime.utcfromtimestamp(alert.expires), "UTC", "\n",
                      alert.severity)
                if alert.severity == "advisory":
                    logger.log.info('Weather advisory is %s%s', alert.title, ".")
                    logger.log.info('The antenna remains fully operational.')
                elif alert.severity == "watch" and alert.title != "High Wind Watch" and alert.title != "Severe Thunderstorm Watch":
                    logger.log.info('Weather watch is %s%s', alert.title, ".")
                    logger.log.info('The antenna remains operational, despite inclement weather watch.')
                else:
                    # shut down antenna for high wind, thunderstorms, and any warning
                    slackMsg = 'Weather Alert'
                    lightning = False
                    if alert.title == "High Wind Watch":
                        logger.log.info('Weather watch is %s%s', alert.title, '.')
                    elif alert.title == "Severe Thunderstorm Watch" or alert.title == "Severe Thunderstorm Warning":
                        logger.log.info('Weather watch is %s%s', alert.title, '.')
                        lightning = True
                        slackMsg = "Lightning Protection"
                    else:
                        logger.log.info('Weather warning is %s%s', alert.title, '.')
                    logger.log.info('Alert begins at '+str(datetime.utcfromtimestamp(alert.time).strftime('%Y-%m-%d %H:%M:S')))
                    logger.log.info('Alert ends at '+str(datetime.utcfromtimestamp(alert.expires).strftime('%Y-%m-%d %H:%M:S')))
                    logger.log.info('The antenna parks and communications cease due to weather conditions.')
                    if not lightning:
                        scheduler.add_job(alert_startup, 'date', run_date=datetime.utcfromtimestamp(alert.expires),
                                          jobstore='alertstartupjob')
                        scheduler.add_job(alert_shutdown, 'date', run_date=datetime.utcfromtimestamp(alert.time),
                                          jobstore='alertshutdownjob')
                    else:
                    # call tstorm_shutdown
                        scheduler.add_job(tstorm_startup, 'date', run_date=datetime.utcfromtimestamp(alert.expires),
                                          jobstore='alertstartupjob')
                        scheduler.add_job(tstorm_shutdown, 'date', run_date=datetime.utcfromtimestamp(alert.time),
                                          jobstore='alertshutdownjob')
                    # IFTTT alert here
                    notification(slackMsg,
                                 get_msg_time(alert.time),
                                 get_msg_time(alert.expires))
                    logger.log.info("Slack message sent due to weather alert.")
        else:
            logger.log.info('No weather alerts detected.')

        #add in a check of currently to determine what the current state of the station should be (and adjust if required)
        gust = int(boulder['currently']['windGust'])
        state = get_apps_state()
        if state == False and gust < 44:
            startup()
        if state == True and gust >= 44:
            shutdown()

            # create a dictionary for day, hour, summary, wind speed, and wind gust for upcoming 48 hours
        WeatherObjects.hours48.clear()
        for hour in boulder.hourly:
            hour = (dict(timestamp=hour.time,
                         day=datetime.strftime(today, '%a'),
                         hour=datetime.strftime(now, '%H'),
                         sum=hour.summary,
                         speed=hour.windSpeed,
                         gust=hour.windGust
                         # gustTime = datetime.utcfromtimestamp(hour.windGustTime)
                         ))
            WeatherObjects.hours48.append(hour)
            # print dictionary contents to command window
            print('{day}, {hour}: {sum}. Wind speed: {speed}mph. Wind gust: {gust}mph'.format(**hour))
            # increment day and time by one hour
            now += timedelta(hours=1)
            today += timedelta(hours=1)
        planning()


def planning():
    WeatherObjects.plan.clear()
    stoptimes = list()
    starttimes = list()
    # plan = list()
    for i in range(48):
        if (WeatherObjects.hours48[i].get('gust') < max_gust) and (
                WeatherObjects.hours48[i + 1].get('gust') >= max_gust):
            stoptimes.append((WeatherObjects.hours48[i].get('day'), WeatherObjects.hours48[i].get('hour'),
                              WeatherObjects.hours48[i].get('timestamp')))
        if (i != 0 and WeatherObjects.hours48[i].get('gust') < max_gust) and (
                WeatherObjects.hours48[i - 1].get('gust') >= max_gust):
            starttimes.append((WeatherObjects.hours48[i].get('day'), WeatherObjects.hours48[i].get('hour'),
                               WeatherObjects.hours48[i].get('timestamp')))
    if len(starttimes) == 0:
        starttimes.append((-1, -1, -1))
        logger.log.info("No start times in list. Placeholder added.")
    if len(stoptimes) == 0:
        stoptimes.append((-1, -1, -1))
        logger.log.info("No stop times in list. Placeholder added.")
    if len(starttimes) > len(stoptimes):
        stoptimes.insert(0, (-1, -1, -1))
        logger.log.info("Unpaired start time. Placeholder added.")
    if len(starttimes) < len(stoptimes):
        starttimes.append((-1, -1, -1))
        logger.log.info("Unpaired stop time. Placeholder added.")
    logger.log.info("Beginning list of stop and start times")
    for i in range(len(stoptimes)):
        WeatherObjects.plan.append((stoptimes[i], starttimes[i]))
        logger.log.info("Stop: " + str(stoptimes[i]) + " Start: " + str(starttimes[i]))
    parse_plan()


# schedules shutdowns and startups
def parse_plan():
    for cmd in WeatherObjects.plan:
        # schedule shutdown
        if cmd[0] != (-1, -1, -1):
            shutdowntime = datetime.utcfromtimestamp(cmd[0][2] + 1800)
            shutdownjob = scheduler.add_job(shutdown, 'date', run_date=shutdowntime, jobstore='shutdownjob')
            pass
        # schedule startup
        if cmd[1] != (-1, -1, -1):
            startuptime = datetime.utcfromtimestamp(cmd[1][2])
            startupjob = scheduler.add_job(startup, 'date', run_date=startuptime, jobstore='startupjob')
            pass
        if cmd != ((-1,-1,-1),(-1,-1,-1)):
            notification("Two-Day Forecast", get_msg_time(cmd[0][2] + 1800), get_msg_time(cmd[1][2]))
            logger.log.info("Slack message sent due to scheduled shutdown.")
        else:
            logger.log.info("No slack message due to no shutdowns.")
    if WeatherObjects.mode != 1:
        WeatherObjects.mode = 1
        logger.log.info("mode temporarily set to 'auto' to allow jobs to be updated.")


# # same as above, but for current conditions
# def current_conditions():
#     now = datetime.now()
#     today = datetime.today()
#     with forecast('8d92b5778ac6f73e8de298d4f4fb761b', *BOULDER) as boulder:
#         current = dict(day=datetime.strftime(today, '%a'),
#                     current=datetime.strftime(now, '%H'),
#                     sum=boulder.currently.summary,
#                     speed=boulder.currently.windSpeed,
#                     gust=boulder.currently.windGust,
#                     # gustTime = datetime.utcfromtimestamp(current.windGustTime)
#                     )
#         print('{day}, {current}: {sum}. Wind speed: {speed}mph. Wind gust: {gust}mph'.format(**current))


def shutdown():
    app_control.kill_apps()
    time.sleep(10)
    con = antenna_control.AntennaControl()
    con.emergency_stop()
    con.park_antenna()
    con.connection_exit()


def startup():
    if not get_apps_state():
        app_control.start_apps()

def tstorm_shutdown():
    logger.log.info("Shutdown due to lightning.")
    job_list = startupjob.get_all_jobs()
    for job in job_list:
        job.pause()
    app_control.kill_apps()
    time.sleep(10)
    SG_Power.turn_off()

def tstorm_startup():
    logger.log.info("Startup due to lightning.")
    SG_Power.turn_on()
    time.sleep(10)
    startup()
    job_list = startupjob.get_all_jobs()
    for job in job_list:
        job.resume()


def alert_shutdown():
    logger.log.info("Shutdown due to alert.")
    job_list = startupjob.get_all_jobs()
    for job in job_list:
        job.pause()
    shutdown()


def alert_startup():
    logger.log.info("Startup due to alert.")
    SG_Power.turn_on()
    time.sleep(4)
    startup()
    job_list = startupjob.get_all_jobs()
    for job in job_list:
        job.resume()


def check_mode():
    with open("change_mode.txt", 'r') as f:
        modestr = f.readline(16)
        if modestr.find("auto") != -1:
            if WeatherObjects.mode != 1:
                WeatherObjects.mode = 1
                try:
                    job_list = shutdownjob.get_all_jobs()
                    for job in job_list:
                        job.resume()
                    job_list = startupjob.get_all_jobs()
                    for job in job_list:
                        job.resume()
                    job_list = alertshutdownjob.get_all_jobs()
                    for job in job_list:
                        job.resume()
                    job_list = alertstartupjob.get_all_jobs()
                    for job in job_list:
                        job.resume()
                except JobLookupError:
                    logger.log.info("Mode switch attempted to modify invalid jobs.")
                logger.log.info("Switched mode to automatic.")
        elif modestr.find("manual") != -1:
            if WeatherObjects.mode != -1:
                WeatherObjects.mode = -1
                try:
                    job_list = shutdownjob.get_all_jobs()
                    for job in job_list:
                        job.pause()
                    job_list = startupjob.get_all_jobs()
                    for job in job_list:
                        job.pause()
                    job_list = alertshutdownjob.get_all_jobs()
                    for job in job_list:
                        job.pause()
                    job_list = alertstartupjob.get_all_jobs()
                    for job in job_list:
                        job.pause()
                except JobLookupError:
                    logger.log.info("Mode switch attempted to modify invalid jobs.")
                logger.log.info("Switched mode to manual.")
        else:
            WeatherObjects.mode = 0
            logger.log.warning("Could not parse mode from file.")


def main():

    logger.log.info("\n----------------Restart----------------\n")
    logging.getLogger('apscheduler').setLevel(logging.WARNING)

    hourly_two_day_job = scheduler.add_job(hourly_two_day, 'interval', hours=24, id='48hourforecast')
    check_mode_job = scheduler.add_job(check_mode, 'interval', seconds=90, id='checkmodejob')
    #add jobstores to scheduler
    scheduler.add_jobstore(startupjob, 'startupjob')
    scheduler.add_jobstore(shutdownjob, 'shutdownjob')
    scheduler.add_jobstore(alertstartupjob, 'alertstartupjob')
    scheduler.add_jobstore(alertshutdownjob, 'alertshutdownjob')
    scheduler.start()
    # # uncomment this if you need to debug current conditions
    # current_conditions()
    # obj = WeatherObjects()
    hourly_two_day()
    scheduler.print_jobs()
    logger.log.info("List of currently scheduled jobs:")
    job_info = scheduler.get_jobs()
    for job in job_info:
        logger.log.info("Scheduled job: " + str(job))
    check_mode()

    while True:
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        scheduler.shutdown()
        sys.exit()
