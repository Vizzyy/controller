import requests
from config import OFFICE_LIGHT_HOST, OFFICE_LIGHT_HOST2
from functions.init import *


def office_light_request(button_position):
    # Office lights
    if button_position == 0:
        mode = 'clear'
    if button_position == 1:
        mode = 'white'
    if button_position == 2:
        mode = 'rainbowCycle'

    r = requests.get(f'http://{OFFICE_LIGHT_HOST}/inside/arrange/{mode}')
    print(f'office_light_request: {mode} - response: {r.status_code}')
    r = requests.get(f'http://{OFFICE_LIGHT_HOST2}/outside/arrange/{mode}')
    print(f'office_light_request2: {mode} - response: {r.status_code}')
    if "clear" in mode:
        set_led_red(button_position)
    else:
        set_led_green(button_position)
