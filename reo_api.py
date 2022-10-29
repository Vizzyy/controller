import requests
from config import *
import urllib3

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


def get_login_token():
    global API_TOKEN
    try:
        if not API_TOKEN:
            response = requests.post(f'https://{NVR_HOST}/api.cgi',
                                     headers={'content-type': 'application/json'},
                                     json=LOGIN_REQUEST_PAYLOAD,
                                     params={'cmd': 'Login'},
                                     verify=False)
            response_body = response.json()
            API_TOKEN = response_body[0]['value']['Token']['name']
            print(f'get_login_token: {API_TOKEN}')
    except Exception as e:
        print(f'{type(e).__name__} - {e}')

    return API_TOKEN


def get_ptz_ctrl_payload(channel: int, op: str, speed: int = None, preset_id: int = None):
    param = {}
    if channel is not None:
        param['channel'] = channel
    if op is not None:
        param['op'] = op
    if speed is not None:
        param['speed'] = speed
    if preset_id is not None:
        param['id'] = preset_id

    payload = [
        {
            "cmd": "PtzCtrl",
            "param": param
        }
    ]

    # print(payload)
    return payload


def ptz_ctrl(channel: int, op: str, speed: int = None, preset_id: int = None):
    global API_TOKEN
    try:
        if not API_TOKEN:
            get_login_token()

        response = requests.post(f'https://{NVR_HOST}/api.cgi',
                                 headers={'content-type': 'application/json'},
                                 json=get_ptz_ctrl_payload(channel, op, speed, preset_id),
                                 # params={'cmd': 'PtzCtrl', 'username': NVR_USER, 'password': NVR_PASS},
                                 params={'cmd': 'PtzCtrl', 'token': API_TOKEN},
                                 verify=False)
        response_body = response.json()
        try:
            response_code = response_body[0]['value']['rspCode']
            if response_code != 200:
                print(f'Received bad response: {response_code}, resetting token.')
                API_TOKEN = None
        except Exception as inner_ex:
            API_TOKEN = None
            print(f'Inner exception: {type(inner_ex).__name__} - {inner_ex}')
            raise Exception('')
        print(f'ptz_ctrl: channel - {channel}, op - {op}, speed: {speed}, response - {response_body}')
    except Exception as e:
        print(f'{type(e).__name__} - {e}')


# # RTSP channels start from 01 and go 01,02,03,04...
# rtsp_channel = '04'
# rtsp = f'rtsp://{NVR_USER}:{NVR_PASS}@{NVR_HOST}:554/h264Preview_{rtsp_channel}_sub'
#
# PTZ channels start from 0, and go 0,1,2,3...
# ptz_channel = 0
# import time
#
# ptz_ctrl(ptz_channel, 'Left', 30)
# time.sleep(1)
# ptz_ctrl(ptz_channel, 'Stop')
# time.sleep(1)
# ptz_ctrl(ptz_channel, 'Right', 30)
# time.sleep(1)
# ptz_ctrl(ptz_channel, 'Stop')

# ptz_ctrl(ptz_channel, 'ToPos', 30, 1)
# time.sleep(1)
# ptz_ctrl(ptz_channel, 'Stop')
