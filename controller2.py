import launchpad
import requests
import midea_beautiful
from config import *
import subprocess
import time
from onvif import ONVIFCamera
import reo_api

# Mk1 Launchpad:
lp = launchpad.Launchpad()
lp.Open()
lp.ButtonFlush()
lp.LedAllOn()
lp.Reset()  # turn off LEDs

frontcam = None
frontcam_media = None
frontcam_token = None
frontcam_ptz = None
backcam = None
backcam_media = None
backcam_token = None
backcam_ptz = None

appliance = None
pihole_enabled = True
midea_target_temp = 25
WAIT_TIME = .1
garage_safety_on = True
browser_process = None
camera_selected = 1
browser_pid = None
display_sleep_enabled = True
launchpad_sleep_enabled = False
bluetooth_connected = True
volume_settings = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
volume_setting = 4  # current index in above array of preset volumes

stream_reset_button = [207]  # "mixer" button
display_sleep_button = [204]  # "session" button
bluetooth_button = [205]  # "user1" button
launchpad_sleep = [206]  # "user2" button
lights_buttons = [0, 1, 2]
pihole_buttons = [4, 5, 6]
stream_buttons = [64, 65, 66, 67]
midea_buttons = [32, 33, 34, 36, 37]
garage_buttons = [69, 70, 71]
onvif_buttons = [80, 97, 99, 112, 113, 114, 115]
volume_buttons = [104, 120]
audio_buttons = [118, 119]
enabled_buttons = lights_buttons + pihole_buttons + midea_buttons + stream_buttons + \
                  garage_buttons + onvif_buttons + stream_reset_button + display_sleep_button + bluetooth_button + \
                  volume_buttons + audio_buttons + launchpad_sleep


def print_exception(exception, msg=''):
    print(f'{msg}{type(exception).__name__} - {exception}')


def init_stream_process():
    global browser_process, browser_pid

    if browser_process:
        browser_process.kill()

    cmd = f'killall chromium-browser; DISPLAY=:0 chromium-browser --kiosk --incognito --start-maximized ' \
          f'--enable-gpu-rasterization --enable-features=VaapiVideoDecoder ' \
          f'{STREAM_BASE}/1/stream {STREAM_BASE}/2/stream {STREAM_BASE}/3/stream {STREAM_BASE}/4/stream'
    print(f'init_stream_process: {cmd}')

    try:
        # has to execute as 'pi' user, otherwise it won't display on the correct desktop
        browser_process = subprocess.Popen(f"su - pi -c '{cmd}'",
                                           shell=True,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           encoding='utf8')

        print(f'browser_pid: {browser_process.pid} - process.stdout: {browser_process.stdout} - '
              f'process.stderr: {browser_process.stderr}')
    except Exception as ex:
        print_exception(ex, 'Error creating stream browser: ')


def connect_to_bluetooth(connect=True):
    state = 'connect' if connect else 'disconnect'
    cmd = f'bluetoothctl {state} EC:81:93:5B:55:4D'
    print(f'connect_to_bluetooth: {cmd}')

    process = subprocess.run(f"{cmd}",
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             encoding='utf8')
    print(f'process.stdout: {process.stdout} - process.stderr: {process.stderr}')


def init_onvif():
    global frontcam, frontcam_media, frontcam_token, frontcam_ptz, backcam, backcam_media, backcam_token, backcam_ptz
    try:
        frontcam = ONVIFCamera(ONVIF_1_HOST, 8000, ONVIF_1_USER, ONVIF_1_PASS, '/home/pi/wsdl/')
        frontcam_media = frontcam.create_media_service()
        frontcam_token = frontcam_media.GetProfiles()[0].token
        frontcam_ptz = frontcam.create_ptz_service()
        print(f'External Front Camera initialized')
    except Exception as ex:
        print_exception(ex, 'Error initializing Front Camera: ')

    try:
        backcam = ONVIFCamera(ONVIF_2_HOST, 8000, ONVIF_1_USER, ONVIF_1_PASS, '/home/pi/wsdl/')
        backcam_media = backcam.create_media_service()
        backcam_token = backcam_media.GetProfiles()[0].token
        backcam_ptz = backcam.create_ptz_service()
        print(f'External Garage Camera initialized')
    except Exception as ex:
        print_exception(ex, 'Error initializing Garage Camera: ')


def switch_stream_tab(stream_id):
    cmd = f'sh /home/pi/switch-to-tab.sh {stream_id}'
    # print(f'switch_stream_tab: stream_id {stream_id} - {cmd}')

    process = subprocess.run(f"{cmd}",
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             encoding='utf8')
    # print(f'process.stdout: {process.stdout} - process.stderr: {process.stderr}')


def set_display_sleep(enabled):  # enabled is either 0 or 1
    cmd = f'DISPLAY=:0 xrandr --output HDMI-1 --brightness {enabled}'
    print(f'set_display_sleep: {cmd}')

    process = subprocess.run(f"su - pi -c '{cmd}'",
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             encoding='utf8')
    print(f'process.stdout: {process.stdout} - process.stderr: {process.stderr}')


def enable_audio(enabled=True):  # enabled is either 0 or 1
    global camera_selected

    audio_user = ONVIF_1_USER
    audio_pass = ONVIF_1_PASS
    audio_channel = '1'

    if camera_selected == 1:
        audio_address = ONVIF_1_HOST
    elif camera_selected == 2:
        audio_address = ONVIF_2_HOST
    else:
        audio_pass = NVR_PASS
        audio_user = NVR_USER
        audio_address = NVR_HOST
        audio_channel = f'camera_selected'

    if enabled:

        cmd = f'killall ffplay; ' \
              f'DISPLAY=:0 ffplay "rtsp://{audio_user}:{audio_pass}@{audio_address}:554/h264Preview_0{audio_channel}_sub" ' \
              f'-nodisp -fflags nobuffer -flags low_delay -framedrop -strict experimental -rtsp_transport tcp'
    else:
        cmd = f'killall ffplay'
    print(f'enable_audio: {cmd}')

    process = subprocess.Popen(f"su - pi -c '{cmd}'",
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               encoding='utf8')
    print(f'process.pid: {process.pid} - process.stdout: {process.stdout} - process.stderr: {process.stderr}')


def handle_audio(button_position):
    if button_position == 118:
        enable_audio(True)
        set_led_green(118)
    if button_position == 119:
        enable_audio(False)
        set_led_yellow(118)
        set_led_red(119)


def set_volume(volume_index):
    volume_percent = volume_settings[volume_index]
    cmd = f'amixer -q -M sset Master {volume_percent}%'
    print(f'set_volume: {cmd}')

    process = subprocess.run(f"su - pi -c '{cmd}'",
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             encoding='utf8')
    print(f'process.stdout: {process.stdout} - process.stderr: {process.stderr}')


def set_default_led_states():
    for button in enabled_buttons:
        set_led_green(button)

    # Custom default states
    set_led_red(0)
    set_led_red(5)
    set_led_red(6)
    set_led_red(32)
    set_led_yellow(64)  # camera 1
    set_led_red(69)
    set_led_yellow(70)
    set_led_yellow(71)
    set_led_red(80)
    set_led_yellow(118)
    set_led_red(119)
    set_led_yellow(206)


def initialize():
    connect_to_bluetooth()
    init_stream_process()
    init_onvif()
    set_volume(volume_setting)
    set_default_led_states()
    print(f'Finished initializing!')


def set_led_off(button_position):
    lp.LedCtrlRaw(button_position, 0, 0)


def set_led_green(button_position):
    lp.LedCtrlRaw(button_position, 0, 3)


def set_led_yellow(button_position):
    lp.LedCtrlRaw(button_position, 3, 3)


def set_led_red(button_position):
    lp.LedCtrlRaw(button_position, 3, 0)


def office_light_request(mode, button_position):
    r = requests.get(f'http://{OFFICE_LIGHT_HOST}/inside/arrange/{mode}')
    print(f'office_light_request: {mode} - response: {r.status_code}')
    r = requests.get(f'http://{OFFICE_LIGHT_HOST2}/outside/arrange/{mode}')
    print(f'office_light_request2: {mode} - response: {r.status_code}')
    if "clear" in mode:
        set_led_red(button_position)
    else:
        set_led_green(button_position)


def garage_request(mode, button_position):
    r = requests.get(f'http://{GARAGE_HOST}/garage/{mode}')
    print(f'garage_request: {mode} - response: {r.status_code}')
    set_led_green(button_position)


def pihole_request(mode, button_position):
    global pihole_enabled
    r = requests.get(f'http://{PIHOLE_HOST}/admin/api.php?{mode}&auth={PIHOLE_AUTH}')
    print(f'pihole_request: {mode} - response: {r.status_code}')
    if "disable" in mode:
        set_led_yellow(button_position)
        pihole_enabled = False
    else:
        set_led_green(4)
        set_led_red(5)
        set_led_red(6)


def midea_request(button_position, **kwargs):
    global appliance
    print(f'midea_request: {button_position} - response: {kwargs}')
    try:
        if not appliance:
            appliance = midea_beautiful.appliance_state(address=MIDEA_IP, token=MIDEA_TOKEN, key=MIDEA_KEY)
        appliance.set_state(**kwargs)
        if button_position == 32:
            set_led_red(button_position)
        else:
            set_led_green(button_position)
    except Exception as midea_error:
        print(f'MIDEA ERROR: {type(midea_error).__name__} - {midea_error}')


def switch_camera(mode, button_position):
    global camera_selected
    print(f'switch_camera: {mode} - button_position: {button_position}')
    camera_selected = mode
    switch_stream_tab(mode)
    for button_id in stream_buttons:
        if button_id != button_position:
            set_led_green(button_id)
    for button_id in onvif_buttons:
        # if button_position == 66 or button_position == 67:
        #     set_led_yellow(button_id)
        if button_id == 80:
            set_led_red(button_id)
        else:
            set_led_green(button_id)


def handle_display_sleep(button_position):
    global display_sleep_enabled
    if display_sleep_enabled:  # if sleep enabled, then disable
        set_display_sleep(0)
        set_led_red(button_position)
    else:  # if sleep disabled, then enable
        set_display_sleep(1)
        set_led_green(button_position)

    display_sleep_enabled = not display_sleep_enabled


def handle_bluetooth(button_position):
    global bluetooth_connected
    if bluetooth_connected:  # if bluetooth_connected, then disable
        connect_to_bluetooth(False)
        set_led_red(button_position)
    else:  # if not bluetooth_connected, then enable
        connect_to_bluetooth(True)
        set_led_green(button_position)

    bluetooth_connected = not bluetooth_connected


def handle_launchpad_sleep():
    global lp, launchpad_sleep_enabled
    if launchpad_sleep_enabled:
        set_default_led_states()
    else:
        lp.Reset()
        set_led_green(206)
    launchpad_sleep_enabled = not launchpad_sleep_enabled


def handle_volume(button_position):
    global volume_setting

    if button_position == 104:
        if volume_setting + 1 < len(volume_settings):
            volume_setting += 1
            set_led_green(104)
            set_led_green(120)
        else:  # If we reach a limit, set the button red
            set_led_red(button_position)
            return
    if button_position == 120:
        if volume_setting - 1 >= 0:
            volume_setting -= 1
            set_led_green(104)
            set_led_green(120)
        else:  # If we reach a limit, set the button red
            set_led_red(button_position)
            return

    set_volume(volume_setting)


def handle_ptz_api_req(camera_channel, button_position, push_state):
    speed = 10

    print(f'handle_ptz_api_req = camera_channel: {camera_channel} - '
          f'button_position: {button_position} - push_state: {push_state}')

    if button_position == 112:
        if push_state:              # button pushed down
            reo_api.ptz_ctrl(camera_channel - 1, 'Left', speed)
        else:                       # button released
            reo_api.ptz_ctrl(camera_channel - 1, 'Stop')
    if button_position == 114:
        if push_state:              # button pushed down
            reo_api.ptz_ctrl(camera_channel - 1, 'Right', speed)
        else:                       # button released
            reo_api.ptz_ctrl(camera_channel - 1, 'Stop')
    if button_position == 97:
        if push_state:              # button pushed down
            reo_api.ptz_ctrl(camera_channel - 1, 'Up', speed)
        else:                       # button released
            reo_api.ptz_ctrl(camera_channel - 1, 'Stop')
    if button_position == 113:
        if push_state:              # button pushed down
            reo_api.ptz_ctrl(camera_channel - 1, 'Down', speed)
        else:                       # button released
            reo_api.ptz_ctrl(camera_channel - 1, 'Stop')


def onvif(button_position, push_state):
    global frontcam_ptz, backcam_ptz, frontcam_token, backcam_token

    print(f'onvif = button_position: {button_position} - push_state: {push_state} - camera_selected: {camera_selected}')

    # on button push
    if push_state:
        if camera_selected == 1:
            token = frontcam_token
        elif camera_selected == 2:
            token = backcam_token
        else:
            token = None
        request = {
            'ProfileToken': token,
            'Velocity': {
                'PanTilt': {
                    'x': 0,
                    'y': 0
                },
                'Zoom': {
                    'x': 0
                }
            }
        }

        # PanTilt
        if button_position == 112:  # Left
            request['Velocity']['PanTilt']['x'] = -.1
            request['Velocity']['PanTilt']['y'] = 0
        if button_position == 114:  # Right
            request['Velocity']['PanTilt']['x'] = .1
            request['Velocity']['PanTilt']['y'] = 0
        if button_position == 97:  # Up
            request['Velocity']['PanTilt']['x'] = 0
            request['Velocity']['PanTilt']['y'] = .1
        if button_position == 113:  # Down
            request['Velocity']['PanTilt']['x'] = 0
            request['Velocity']['PanTilt']['y'] = -.1

        # Zoom
        if button_position == 99:  # Zoom in
            request['Velocity']['Zoom']['x'] = .1
        if button_position == 115:  # Zoom out
            request['Velocity']['Zoom']['x'] = -.1

        if camera_selected == 1:
            frontcam_ptz.ContinuousMove(request)
        elif camera_selected == 2:
            backcam_ptz.ContinuousMove(request)
        elif camera_selected == 3:
            handle_ptz_api_req(camera_selected, button_position, push_state)
        elif camera_selected == 4:
            handle_ptz_api_req(camera_selected, button_position, push_state)
        else:
            print(f'PTZ is not supported with this camera!')
            return
    # on button release
    else:
        # Reset to default position
        if button_position == 80:
            if camera_selected == 1:
                frontcam_ptz.GotoPreset({
                    'ProfileToken': frontcam_token,
                    'PresetToken': frontcam_ptz.GetPresets({'ProfileToken': frontcam_token})[0].token
                })
            if camera_selected == 2:
                backcam_ptz.GotoPreset({
                    'ProfileToken': backcam_token,
                    'PresetToken': backcam_ptz.GetPresets({'ProfileToken': backcam_token})[0].token
                })
            # TODO: Impl this with E1 cameras
            set_led_red(80)
        else:  # For all other buttons send stop command as soon as button is released
            if camera_selected == 1:
                frontcam_ptz.Stop({'ProfileToken': frontcam_token})
            elif camera_selected == 2:
                backcam_ptz.Stop({'ProfileToken': backcam_token})
            elif camera_selected == 3:
                handle_ptz_api_req(camera_selected, button_position, push_state)
            elif camera_selected == 4:
                handle_ptz_api_req(camera_selected, button_position, push_state)
            else:
                frontcam_ptz.Stop({'ProfileToken': frontcam_token})
                backcam_ptz.Stop({'ProfileToken': backcam_token})
                # TODO: Impl this with E1 cameras

    if button_position != 80:
        set_led_green(button_position)


def process_button(button_state):
    global midea_target_temp, garage_safety_on, camera_selected
    button_position = button_state[0]
    push_state = button_state[1]

    if button_position in enabled_buttons:
        # on down-press
        if push_state:
            set_led_yellow(button_position)
            # Onvif
            if button_position in onvif_buttons:
                onvif(button_position, push_state)
        # on release
        else:
            # Office lights
            if button_position == 0:
                office_light_request('clear', button_position)
            if button_position == 1:
                office_light_request('white', button_position)
            if button_position == 2:
                office_light_request('rainbowCycle', button_position)

            # Pihole
            if button_position == 4:
                pihole_request('enable', button_position)
            if button_position == 5:
                pihole_request('disable=300', button_position)
            if button_position == 6:
                pihole_request('disable=3600', button_position)

            # Midea
            if button_position == 32:
                midea_request(button_position, running=0)
            if button_position == 33:
                midea_request(button_position, mode=1, running=1)
            if button_position == 34:
                midea_request(button_position, mode=3, running=1)
            if button_position == 36:
                midea_target_temp -= .5
                midea_request(button_position, target_temperature=midea_target_temp)
            if button_position == 37:
                midea_target_temp += .5
                midea_request(button_position, target_temperature=midea_target_temp)

            # Streams
            if button_position == 64:
                switch_camera(1, button_position)
            if button_position == 65:
                switch_camera(2, button_position)
            if button_position == 66:
                switch_camera(3, button_position)
            if button_position == 67:
                switch_camera(4, button_position)

            # Garage
            if button_position == 69:
                if garage_safety_on:
                    print(f'Garage Safety DISARMED!')
                    garage_safety_on = False
                    set_led_yellow(69)
                    set_led_green(70)
                    set_led_green(71)
                else:
                    print(f'Garage Safety ARMED!')
                    garage_safety_on = True
                    set_led_red(69)
                    set_led_yellow(70)
                    set_led_yellow(71)
            if button_position == 70:
                if not garage_safety_on:
                    garage_request('light', button_position)
            if button_position == 71:
                if not garage_safety_on:
                    garage_request('door', button_position)

            # Onvif
            if button_position in onvif_buttons:
                onvif(button_position, push_state)

            if button_position in stream_reset_button:
                init_stream_process()
                set_default_led_states()
                camera_selected = 1

            if button_position in display_sleep_button:
                handle_display_sleep(button_position)

            if button_position in bluetooth_button:
                handle_bluetooth(button_position)

            if button_position in volume_buttons:
                handle_volume(button_position)

            if button_position in audio_buttons:
                handle_audio(button_position)

            if button_position in launchpad_sleep:
                handle_launchpad_sleep()

    print(f'button_position: {button_position} - push_state: {push_state}')


initialize()
midea_refresh_counter = 0
midea_refresh_limit = 3000  # 5 minutes
while 1:
    midea_refresh_counter += 1
    try:
        if but := lp.ButtonStateRaw():
            process_button(but)
    except KeyboardInterrupt:
        break
    except Exception as e:
        print_exception(e)

    if appliance and midea_refresh_counter > midea_refresh_limit:
        print(f'Expiring midea token!')
        appliance = None
        midea_refresh_counter = 0

    time.sleep(WAIT_TIME)  # this is super important, otherwise we destroy the CPU with busy-wait cycles

lp.Reset()  # turn off LEDs
lp.Close()  # close the Launchpad
