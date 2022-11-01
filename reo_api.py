import requests
from config import *
import urllib3
import time


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOGIN_REQUEST_PAYLOAD = [
    {
        "cmd": "Login",
        "param": {
            "User": {
                "Version": "0",
                "userName": f'{NVR_USER}',
                "password": f'{NVR_PASS}'
            }
        }
    }
]

API_TOKEN = None
API_TOKEN_TIMESTAMP = time.time()


# https://stackoverflow.com/a/39016088/6506539
def item_generator(json_input, lookup_key):
    if isinstance(json_input, dict):
        for k, v in json_input.items():
            if k == lookup_key:
                yield v
            else:
                yield from item_generator(v, lookup_key)
    elif isinstance(json_input, list):
        for item in json_input:
            yield from item_generator(item, lookup_key)


def get_login_token():
    global API_TOKEN, API_TOKEN_TIMESTAMP
    try:
        response = requests.post(f'https://{NVR_HOST}/api.cgi',
                                 headers={'content-type': 'application/json'},
                                 json=LOGIN_REQUEST_PAYLOAD,
                                 params={'cmd': 'Login'},
                                 verify=False)
        response_body = response.json()
        API_TOKEN = response_body[0]['value']['Token']['name']
        API_TOKEN_TIMESTAMP = time.time()
        print(f'get_login_token: {API_TOKEN}, API_TOKEN_TIMESTAMP: {API_TOKEN_TIMESTAMP}')
    except Exception as e:
        print(f'{type(e).__name__} - {e}')

    return API_TOKEN


def api_ctrl(*,
             channel: int = 0,
             op: str = None,
             speed: int = None,
             preset_id: int = None,
             w_led_state: int = None,
             cmd: str = 'PtzCtrl',

             ):
    global API_TOKEN, API_TOKEN_TIMESTAMP

    param = {}
    if channel is not None:
        param['channel'] = channel
    if op is not None:
        param['op'] = op
    if speed is not None:
        param['speed'] = speed
    if preset_id is not None:
        param['id'] = preset_id
    if w_led_state is not None:
        param = {
            'WhiteLed': {
                'state': w_led_state,
                'channel': channel
            }
        }

    if cmd == 'SetPtzPreset':
        param = {
            'PtzPreset': {
                'channel': channel,
                'enable': 1,
                'id': 1,
                'name': 'Default'
            }
        }

    payload = [
        {
            "cmd": cmd,
            "param": param
        }
    ]
    # print(payload)

    try:
        if not API_TOKEN or time.time() - API_TOKEN_TIMESTAMP > 3600:
            get_login_token()

        response = requests.post(f'https://{NVR_HOST}/api.cgi',
                                 headers={'content-type': 'application/json'},
                                 json=payload,
                                 params={'cmd': cmd, 'token': API_TOKEN},
                                 verify=False)
        response_body = response.json()
        try:
            response_code = next(item_generator(response_body, 'rspCode'))
            if response_code != 200:
                print(f'Received bad response: {response_code}.')
            if response_code in [-5, -6, -7, -21, -27, -503, -505, -506, -507]:
                # potentially all the errors we need to capture relating to login state
                API_TOKEN = None
        except Exception as inner_ex:
            API_TOKEN = None
            raise Exception(f'Inner exception: {type(inner_ex).__name__} - {inner_ex} - {response_body}')
        print(f'api_ctrl: channel - {channel}, op - {op}, speed: {speed}, response - {response_body}')
    except Exception as e:
        print(f'{type(e).__name__} - {e}')


# # RTSP channels start from 01 and go 01,02,03,04...
# rtsp_channel = '04'
# rtsp = f'rtsp://{NVR_USER}:{NVR_PASS}@{NVR_HOST}:554/h264Preview_{rtsp_channel}_sub'
#
# PTZ channels start from 0, and go 0,1,2,3...
# ptz_channel = 0

# api_ctrl(channel=ptz_channel, op='Left', speed=30)
# time.sleep(1)
# api_ctrl(channel=ptz_channel, op='Stop')
# time.sleep(1)
# api_ctrl(channel=ptz_channel, op='Right', speed=30)
# time.sleep(1)
# api_ctrl(channel=ptz_channel, op='Stop')

# api_ctrl(ptz_channel, 'ToPos', 30, 1)
# time.sleep(1)
# api_ctrl(ptz_channel, 'Stop')

# api_ctrl(w_led_state=1, cmd='SetWhiteLed')
# time.sleep(1)
# api_ctrl(w_led_state=0, cmd='SetWhiteLed')

# api_ctrl(channel=ptz_channel, cmd='SetPtzPreset')

