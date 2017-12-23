import time, datetime
import threading
import os
import json
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from flask import Blueprint, flash, request, redirect, url_for, get_flashed_messages, current_app as app
from jinja2 import Environment, PackageLoader, select_autoescape


import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

scheduler_blueprint = Blueprint("scheduler", __name__)

env = Environment(
    loader=PackageLoader('webserver', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)

@scheduler_blueprint.route("/")
def list_schedules():
    template = env.get_template("scheduler.html")
    with open('schedules.json') as configfile:
        schedules = json.load(configfile)
    return template.render(schedules=schedules, get_flashed_messages=get_flashed_messages)

@scheduler_blueprint.route("/delete/<int:index>")
def delete_schedules(index):
    with open('schedules.json') as configfile:
        schedules = json.load(configfile)
        if len(schedules) > index:
            schedules.pop(index)
            flash("Deleted schedule")
            with open('schedules.json', 'w') as configfile:
                json.dump(schedules, configfile, indent=4)
        else:
            flash("Problem when deleting. Index out of range")

    return redirect(url_for("scheduler.list_schedules"))


@scheduler_blueprint.route("/add", methods=['POST'])
def add_schedule():
    error = None

    url_string = request.values.get("url")
    params_string = request.values.get("parameters")
    time_string = request.values.get("time")
    recurring_string = request.values.get("recurring")

    try:
        recurring = ("recurring" in request.values)
        individual_params = [p.split("=") for p in params_string.split(";") if p.strip()]
        params = {kv[0].strip() : kv[1].strip() for kv in individual_params}
        with open('schedules.json', 'r') as configfile:
            schedules = json.load(configfile)
            schedules.append(
                {
                    "url" : url_string,
                    "params" :  params,
                    "time" : time_string,
                    "recurring" : recurring
                }
            )
        with open('schedules.json', 'w') as configfile:
            json.dump(schedules, configfile, indent=4)
    except:
        logger.error("Problem when adding schedule", exc_info=True)
        error = "There was a problem when adding the schedule. Try again and watch for typos..."

    if error:
        flash(error)
    else:
        flash("Added schedule")
    return redirect(url_for("scheduler.list_schedules"))


def start_scheduler(timeout=60):
    while True:
        time_now = datetime.datetime.now().time().strftime("%H:%M")
        print("Checking schedules ", time_now)
        with open('schedules.json') as configfile:
            schedules = json.load(configfile)
            for schedule in schedules:
                if time_now == schedule["time"]:
                    execute_schedule(schedule)
                    if not schedule["recurring"]:
                        schedules.remove(schedule)
            with open('schedules.json', 'w') as configfile:
                json.dump(schedules, configfile, indent=4)
        time.sleep(timeout) # one minute timeout


def execute_schedule(schedule):
    logger.debug("Executing schedule")
    try:
        my_url = urljoin("http://localhost:8080", schedule["url"])
        req = Request(my_url, urlencode(schedule["params"]).encode())
        urlopen(req).read() #.decode()
    except Exception as e:
        print("Error during execution of schedule \n", schedule)
        print(e)

schedule_thread = threading.Thread(target=start_scheduler, args=[])
schedule_thread.start()
