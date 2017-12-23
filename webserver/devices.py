from devices import devices

from flask import Blueprint, flash, request, redirect, url_for, get_flashed_messages
from jinja2 import Environment, PackageLoader, select_autoescape
import socket
import datetime
import time

import logging
logger = logging.getLogger(__name__)


hostname = socket.gethostname()
env = Environment(
    loader=PackageLoader('webserver', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)

devices_blueprint = Blueprint("devices", __name__)

""" ROOT """
@devices_blueprint.route('/')
def list_devices():
    chirps = devices.detect_chirp_devices()
    yoctos = devices.detect_yocto_devices()
    template = env.get_template("devices.html")
    return template.render(hostname=hostname, chirps=chirps, yoctos=yoctos, get_flashed_messages=get_flashed_messages)

""" YOCTO """
@devices_blueprint.route('/rename-yocto/<identifier>')
def rename_yocto(identifier):
    newname = request.values.get('newname')
    error = devices.yocto_set_logical_name(identifier, newname.strip())
    if error:
        flash(error)
    return redirect(url_for('devices.list_devices'))

@devices_blueprint.route('/rename-yocto-function/<module>/<function>')
def rename_yocto_function(module, function):
    newname = request.values.get('newname')
    error = devices.yocto_set_logical_name_sensor(module, function, newname.strip())
    if error:
        flash(error)
    return redirect(url_for('devices.list_devices'))
@devices_blueprint.route('/collect-data/<module>/<function>/<on_off>')
def activate_yocto_function(module, function, on_off):
    newname = request.values.get('newname')
    error = devices.yocto_set_data_collection(module, function, on_off)
    if error:
        flash(error)
    return redirect(url_for('devices.list_devices'))

@devices_blueprint.route('/identify-yocto/<identifier>')
def identify_device(identifier):
    error = devices.yocto_identify_device(identifier)
    if error:
        flash(error)
    return redirect(url_for('devices.list_devices'))

""" CHIRP STUFF """

@devices_blueprint.route('/rename-chirp/<identifier>')
def rename_chirp(identifier):
    newname = request.values.get('newname')
    error = devices.chirp_rename_device(identifier, newname.strip())
    if error:
        flash(error)
    return redirect(url_for('devices.list_devices'))

@devices_blueprint.route('/calibrate-chirp/<identifier>')
def calibrate_chirp(identifier):
    minimum = request.values.get('min')
    maximum = request.values.get('max')
    error = devices.chirp_calibrate_device(identifier, minimum, maximum)
    if error:
        flash(error)
    return redirect(url_for('devices.list_devices'))


""" Relay toggle and activation """
@devices_blueprint.route('/temporary-activate-relay/<module>/<function>', methods=['POST'])
def temp_activate_relay(module, function):
    duration_string = request.values.get('duration')
    # parse duraiton and convert to seconds
    duration_time = None
    if duration_string.count(":") == 2:
        duration_time = time.strptime(duration_string,'%H:%M:%S')
    elif duration_string.count(":") == 1:
        duration_time = time.strptime(duration_string,'%H:%M')
    else:
        flash("Malformed duration %s, please check your string", duration_string)
        return redirect(url_for('devices.list_devices'))

    seconds = datetime.timedelta(hours=duration_time.tm_hour,minutes=duration_time.tm_min,
        seconds=duration_time.tm_sec).total_seconds()
    error = devices.activate_relay_seconds(module, function, int(seconds))
    if error:
        flash(error)
    return redirect(url_for('devices.list_devices'))

@devices_blueprint.route('/toggle-relay/<module>/<function>', methods=['GET','POST'])
def toggle_relay(module, function):
    error = devices.toggle_relay(module, function)
    if error:
        flash(error)
    return redirect(url_for('devices.list_devices'))
