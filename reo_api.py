import requests
from config import *
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# LOGIN_REQUEST_PAYLOAD = [
#     {
#         "cmd": "Login",
#         "param": {
#             "User": {
#                 "Version": "0",
#                 "userName": f'{NVR_USER}',
#                 "password": f'{NVR_PASS}'
#             }
#         }
#     }
# ]
#
# API_TOKEN = None
#
# def get_login_token():
#     global API_TOKEN
#     try:
#         if not API_TOKEN:
#             response = requests.post(f'https://{NVR_HOST}/api.cgi',
#                                      headers={'content-type': 'application/json'},
#                                      json=LOGIN_REQUEST_PAYLOAD,
#                                      params={'cmd': 'Login'},
#                                      verify=False)
#             response_body = response.json()
#             API_TOKEN = response_body[0]['value']['Token']['name']
#             print(f'get_login_token: {API_TOKEN}')
#     except Exception as e:
#         print(f'{type(e).__name__} - {e}')
#
#     return API_TOKEN


def get_ptz_ctrl_payload(channel: int, op: str, speed: int = None):
    param = {}
    if channel:
        param['channel'] = channel
    if op:
        param['op'] = op
    if speed:
        param['speed'] = speed

    return [
        {
            "cmd": "PtzCtrl",
            "param": param
        }
    ]


def ptz_ctrl(channel: int, op: str, speed: int = None):
    try:
        response = requests.post(f'https://{NVR_HOST}/api.cgi',
                                 headers={'content-type': 'application/json'},
                                 json=get_ptz_ctrl_payload(channel, op, speed),
                                 params={'cmd': 'PtzCtrl', 'username': NVR_USER, 'password': NVR_PASS},
                                 verify=False)
        response_body = response.json()
        print(f'ptz_ctrl: channel - {channel}, op - {op}, speed: {speed}, response - {response_body}')
    except Exception as e:
        print(f'{type(e).__name__} - {e}')


# # RTSP channels start from 01 and go 01,02,03,04...
# rtsp_channel = '04'
# rtsp = f'rtsp://{NVR_USER}:{NVR_PASS}@{NVR_HOST}:554/h264Preview_{rtsp_channel}_sub'
#
# # PTZ channels start from 0, and go 0,1,2,3...
# ptz_channel = 3
#
# ptz_ctrl(ptz_channel, 'Left', 30)
# time.sleep(1)
# ptz_ctrl(ptz_channel, 'Stop')
# time.sleep(1)
# ptz_ctrl(ptz_channel, 'Right', 30)
# time.sleep(1)
# ptz_ctrl(ptz_channel, 'Stop')
