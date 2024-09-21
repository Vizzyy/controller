import schedule
import launchpad
import requests
from config import *
import subprocess
import time
import reo_api
import rpi_backlight
import re
import json

# Mk1 Launchpad:
lp = launchpad.Launchpad()
lp.Open()
lp.ButtonFlush()
lp.LedAllOn()
lp.Reset()  # turn off LEDs

appliance = None
pihole_enabled = True
WAIT_TIME = .1
garage_safety_on = True
browser_process = None
default_stream = 8 # 8 = external medley
camera_selected = default_stream
camera_w_led_state = 0
browser_pid = None
display_sleep_enabled = True
launchpad_sleep_enabled = False
bluetooth_connected = False
volume_settings = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
volume_setting = 4  # current index in above array of preset volumes

backlight = rpi_backlight.Backlight()
brightness_settings = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
backlight.fade_duration = 0.5
brightness_setting = 4

stream_reset_button = [207]  # "mixer" button
stream_refresh_button = [7]  # right below "mixer" button
display_sleep_button = [204]  # "session" button
bluetooth_button = [205]  # "user1" button
launchpad_sleep = [206]  # "user2" button
lights_off = 0
lights_white = 1
lights_rainbow = 2
lights_loft_lamp = 17
lights_loft_stairs = 18
lights_buttons = [lights_off, lights_white, lights_rainbow, lights_loft_lamp, lights_loft_stairs]
pihole_on = 4
# pihole_off_5 = 5
pihole_off_60 = 5
pihole_buttons = [pihole_on, pihole_off_60]
stream_1 = 64
stream_2 = 65
stream_3 = 66
stream_4 = 67
stream_5 = 68
stream_6 = 69
stream_7 = 85 # previously 70
stream_medley = 84
brightness_inc = 8
brightness_dec = 24
stream_buttons = [stream_1, stream_2, stream_3, stream_4, stream_5, stream_6, stream_7,
                  stream_medley, brightness_inc, brightness_dec]
garage_safety = 71
garage_light = 72
garage_door = 56
garage_buttons = [garage_safety, garage_light, garage_door]
camera_home = 80
camera_up = 97
camera_left = 112
camera_down = 113
camera_right = 114
camera_zm_out = 115
camera_zm_in = 99
camera_w_led = 82
camera_home_reset = 81
camera_buttons = [camera_home, camera_up, camera_zm_in, camera_left, camera_home_reset,
                  camera_down, camera_right, camera_zm_out, camera_w_led]
volume_up = 104
volume_down = 120
volume_buttons = [volume_up, volume_down]
audio_enable = 118
audio_disable = 119
audio_buttons = [audio_enable, audio_disable]
enabled_buttons = lights_buttons + pihole_buttons + stream_buttons + garage_buttons + \
                  camera_buttons + stream_reset_button + display_sleep_button + bluetooth_button + \
                  volume_buttons + audio_buttons + launchpad_sleep + stream_refresh_button

kasa_device_state = {
    lights_loft_lamp: {
        'alias': 'Loft Lamp',
        'state': True
    }, 
    lights_loft_stairs: {
        'alias': 'Loft Stairs',
        'state': True
    },
    garage_light: {
        'alias': 'Garage',
        'state': False
    }
}


def print_exception(exception, msg=''):
    print(f'{msg}{type(exception).__name__} - {exception}')


def init_stream_process():
    global browser_process, browser_pid, camera_selected

    if browser_process:
        browser_process.kill()

    cmd = f'killall chromium-browser; DISPLAY=:0 chromium-browser --kiosk --incognito --start-maximized ' \
          f'--enable-gpu-rasterization --enable-features=VaapiVideoDecoder ' \
          f'{STREAM_BASE}/1/stream {STREAM_BASE}/2/stream {STREAM_BASE}/3/stream {STREAM_BASE}/4/stream ' \
          f'{STREAM_BASE}/5/stream {STREAM_BASE}/6/stream {STREAM_BASE}/7/stream {STREAM_MEDLEY}'
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

        print(f'Switching to default stream: {default_stream}')
        time.sleep(3)
        camera_selected = default_stream
        switch_stream_tab(default_stream)
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


def switch_stream_tab(stream_id):
    cmd = f'sh /home/pi/switch-to-tab.sh {stream_id}'
    print(f'switch_stream_tab: stream_id {stream_id} - {cmd}')

    process = subprocess.run(f"{cmd}",
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             encoding='utf8')
    print(f'process.stdout: {process.stdout} - process.stderr: {process.stderr}')

def refresh_stream_tab():
    cmd = f'sh /home/pi/refresh-tab.sh'
    print(f'refresh_stream_tab - {cmd}')

    process = subprocess.run(f"{cmd}",
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             encoding='utf8')
    print(f'process.stdout: {process.stdout} - process.stderr: {process.stderr}')

def set_display_sleep(enabled):  # enabled is either 0 or 1
    enabled_bool = enabled == 1
    print(f'set_display_sleep: {enabled_bool}')
    backlight.power = enabled_bool


def set_display_brightness(brightness_idx):  # position in brightness_settings array
    print(f'set_display_brightness: {brightness_idx}')
    backlight.brightness = brightness_settings[brightness_idx]


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
        audio_channel = f'{camera_selected}'

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
    if button_position == audio_enable:
        enable_audio(True)
        set_led_green(audio_enable)
    if button_position == audio_disable:
        enable_audio(False)
        set_led_yellow(audio_enable)
        set_led_red(audio_disable)


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


def kasa_request(alias, new_state):
    cmd = f'kasa --alias "{alias}" --type dimmer {"on" if new_state else "off"}'
    print(f'kasa_request: {cmd}')

    process = subprocess.run(f"su - pi -c '{cmd}'",
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             encoding='utf8')
    print(f'process.stdout: {process.stdout} - process.stderr: {process.stderr}')


def kasa_get_state(alias):
    cmd = f'kasa --alias "{alias}" --type plug'
    print(f'kasa_request: {cmd}')

    process = subprocess.run(f"su - pi -c '{cmd}'",
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             encoding='utf8')
    print(f'process.stdout: {process.stdout} - process.stderr: {process.stderr}')

    m = re.search(r'.*Device state: (True|False)\b.*', process.stdout)
    state = True if m.group(1) == "True" else False
    print(f'State: {alias} = {state}')
    return state


def update_kasa_states():
    if kasa_get_state('Loft Stairs'):
        set_led_green(lights_loft_stairs)
        kasa_device_state[lights_loft_stairs]['state'] = True
    else:
        set_led_yellow(lights_loft_stairs)
        kasa_device_state[lights_loft_stairs]['state'] = False


    if kasa_get_state('Loft Lamp'):
        set_led_green(lights_loft_lamp)
        kasa_device_state[lights_loft_lamp]['state'] = True
    else:
        set_led_yellow(lights_loft_lamp)  
        kasa_device_state[lights_loft_lamp]['state'] = False  


def set_default_led_states():
    for button in enabled_buttons:
        set_led_green(button)

    # Custom default states
    set_led_red(lights_off)
    # set_led_red(pihole_off_5)
    set_led_yellow(stream_refresh_button[0])
    set_led_red(pihole_off_60)
    set_led_yellow(stream_medley)  # default stream, stream 7
    set_led_red(garage_safety)
    set_led_yellow(garage_light)
    set_led_yellow(garage_door)
    set_led_red(camera_home)
    set_led_yellow(audio_enable)
    set_led_red(audio_disable)
    set_led_yellow(launchpad_sleep[0])
    set_led_red(camera_w_led)
    set_led_yellow(camera_home_reset)


def initialize():
    init_stream_process()
    set_volume(volume_setting)
    connect_to_bluetooth()
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


def ha_api_request(mode, entity, button_position, action='toggle'):
    r = requests.post(f'http://{HA_HOST}/api/services/{mode}/{action}',
    headers={
        'Authorization': f'Bearer {HA_API_KEY}',
        'content-type': 'application/json'
    },
    json = {
        'entity_id': f'{entity}'
    })
    print(f'ha_api_request: {mode} - text: {r.text} - action: {action} - status_code: {r.status_code}')
    set_led_green(button_position)


def pihole_request(mode, button_position):
    global pihole_enabled
    try:
        r = requests.get(f'http://{PIHOLE_HOST}/admin/api.php?{mode}&auth={PIHOLE_AUTH}', timeout=2)
        print(f'pihole_request: {mode} - status_code: {r.status_code}')
        if "disable" in mode:
            set_led_yellow(button_position)
            pihole_enabled = False
        else:
            set_led_green(4)
            set_led_red(5)
    except requests.exceptions.Timeout:
        print('The request timed out.')


def switch_camera(mode, button_position):
    global camera_selected, camera_w_led_state
    print(f'switch_camera: {mode} - button_position: {button_position}')
    camera_selected = mode
    camera_w_led_state = 0  # reset LED state any time we switch
    switch_stream_tab(mode)
    for button_id in stream_buttons:
        if button_id != button_position:
            set_led_green(button_id)
    for button_id in camera_buttons:
        if button_id in [camera_home, camera_w_led]:
            set_led_red(button_id)
        elif button_id in [camera_home_reset]:
            set_led_yellow(button_id)
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
        set_led_green(launchpad_sleep[0])
    launchpad_sleep_enabled = not launchpad_sleep_enabled


def handle_volume(button_position):
    global volume_setting

    if button_position == volume_up:
        if volume_setting + 1 < len(volume_settings):
            volume_setting += 1
            set_led_green(volume_up)
            set_led_green(volume_down)
        else:  # If we reach a limit, set the button red
            set_led_red(button_position)
            return
    if button_position == volume_down:
        if volume_setting - 1 >= 0:
            volume_setting -= 1
            set_led_green(volume_up)
            set_led_green(volume_down)
        else:  # If we reach a limit, set the button red
            set_led_red(button_position)
            return

    set_volume(volume_setting)


def handle_ptz_api_req(button_position, push_state):
    global camera_selected, camera_w_led_state
    speed = 10
    home_position_index = 1
    api_channel = camera_selected - 1

    # From medley screen (8), control the puppy cam 
    if camera_selected == 8:
        api_channel -= 1

    # print(f'handle_ptz_api_req = camera_selected: {camera_selected} - '
    #       f'button_position: {button_position} - push_state: {push_state}')

    if push_state:
        if button_position == camera_left:
            reo_api.api_ctrl(channel=api_channel, op='Left', speed=speed)

        if button_position == camera_right:
            reo_api.api_ctrl(channel=api_channel, op='Right', speed=speed)

        if button_position == camera_up:
            reo_api.api_ctrl(channel=api_channel, op='Up', speed=speed)

        if button_position == camera_down:
            reo_api.api_ctrl(channel=api_channel, op='Down', speed=speed)

        if button_position == camera_zm_in:
            reo_api.api_ctrl(channel=api_channel, op='ZoomInc', speed=speed)

        if button_position == camera_zm_out:
            reo_api.api_ctrl(channel=api_channel, op='ZoomDec', speed=speed)

        if button_position == camera_home:
            reo_api.api_ctrl(channel=api_channel, op='ToPos', speed=speed, preset_id=home_position_index)

        if button_position == camera_w_led:
            if camera_selected < 7:
                camera_w_led_state = 1 if camera_w_led_state == 0 else 0
                reo_api.api_ctrl(channel=api_channel, w_led_state=camera_w_led_state, cmd='SetWhiteLed')
            else:
                # we want to reuse the LED button for a second default position for the puppy cam
                reo_api.api_ctrl(channel=api_channel, op='ToPos', speed=speed, preset_id=0)

        if button_position == camera_home_reset:
            if camera_selected < 7:
                reo_api.api_ctrl(channel=api_channel, cmd='SetPtzPreset')
            else:
                # we want to reuse the LED button for a second default position for the puppy cam
                reo_api.api_ctrl(channel=api_channel, op='ToPos', speed=speed, preset_id=2)

    else:
        if button_position in [camera_home]:
            set_led_red(button_position)
        elif button_position == camera_w_led:
            if camera_w_led_state:
                set_led_green(camera_w_led)
            else:
                set_led_red(camera_w_led)
        else:
            if button_position not in [camera_home, camera_w_led, camera_home_reset]:
                reo_api.api_ctrl(channel=api_channel, op='Stop')
            set_led_green(button_position)


def process_button(button_state):
    global garage_safety_on, camera_selected, brightness_setting
    button_position = button_state[0]
    push_state = button_state[1]

    if button_position in enabled_buttons:
        # on down-press
        if push_state:
            set_led_yellow(button_position)
            # Onvif
            if button_position in camera_buttons:
                handle_ptz_api_req(button_position, push_state)
        # on release
        else:
            # Office lights
            if button_position == lights_off:
                office_light_request('clear', button_position)
            if button_position == lights_white:
                office_light_request('white', button_position)
            if button_position == lights_rainbow:
                office_light_request('rainbowCycle', button_position)
            if button_position in [lights_loft_lamp, lights_loft_stairs]:
                kasa_device_state[button_position]['state'] = not kasa_device_state[button_position]['state']
                # kasa_request(kasa_device_state[button_position]['alias'], kasa_device_state[button_position]['state'])
                if kasa_device_state[button_position]['state']:
                    action = 'turn_on'
                else:
                    action = 'turn_off'
                if button_position == lights_loft_lamp:
                    ha_api_request('light', HA_LOFT_LAMP_ENTITY, button_position, action)
                elif button_position == lights_loft_stairs:
                    ha_api_request('light', HA_LOFT_STAIRS_ENTITY, button_position, action)
                set_led_green(button_position) if kasa_device_state[button_position]['state'] else set_led_yellow(button_position)

            # Pihole
            if button_position == pihole_on:
                pihole_request('enable', button_position)
            # if button_position == pihole_off_5:
            #     pihole_request('disable=300', button_position)
            if button_position == pihole_off_60:
                pihole_request('disable=3600', button_position)

            # Streams
            if button_position == stream_1:
                switch_camera(1, button_position)
            if button_position == stream_2:
                switch_camera(2, button_position)
            if button_position == stream_3:
                switch_camera(3, button_position)
            if button_position == stream_4:
                switch_camera(4, button_position)
            if button_position == stream_5:
                switch_camera(5, button_position)
            if button_position == stream_6:
                switch_camera(6, button_position)
            if button_position == stream_7:
                switch_camera(7, button_position)
            if button_position == stream_medley:
                switch_camera(8, button_position)

            # Brightness
            if button_position == brightness_inc:
                if brightness_setting < len(brightness_settings) - 1:
                    brightness_setting += 1
                set_display_brightness(brightness_setting)
                set_led_green(brightness_inc)
            if button_position == brightness_dec:
                if brightness_setting > 0:
                    brightness_setting -= 1
                set_display_brightness(brightness_setting)
                set_led_green(brightness_dec)

            # Garage
            if button_position == garage_safety:
                if garage_safety_on:
                    print(f'Garage Safety DISARMED!')
                    garage_safety_on = False
                    set_led_yellow(garage_safety)
                    set_led_green(garage_light)
                    set_led_green(garage_door)
                else:
                    print(f'Garage Safety ARMED!')
                    garage_safety_on = True
                    set_led_red(garage_safety)
                    set_led_yellow(garage_light)
                    set_led_yellow(garage_door)
            if button_position == garage_light:
                if not garage_safety_on:
                    kasa_device_state[button_position]['state'] = not kasa_device_state[button_position]['state']
                    ha_api_request('light', HA_GARAGE_LIGHT_1_ENTITY, button_position)
                    ha_api_request('light', HA_GARAGE_LIGHT_2_ENTITY, button_position)
                    ha_api_request('light', HA_GARAGE_LIGHT_3_ENTITY, button_position)
                    set_led_green(button_position) if kasa_device_state[button_position]['state'] else set_led_yellow(button_position)
            if button_position == garage_door:
                if not garage_safety_on:
                    ha_api_request('cover', HA_GARAGE_DOOR_ENTITY, button_position)

            # Onvif
            if button_position in camera_buttons:
                handle_ptz_api_req(button_position, push_state)

            if button_position in stream_reset_button:
                init_stream_process()
                set_default_led_states()
                camera_selected = 1

            if button_position in stream_refresh_button:
                refresh_stream_tab()

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
schedule.every().day.at("05:40").do(init_stream_process)
schedule.every(10).minutes.do(update_kasa_states)
update_kasa_states()

while 1:
    try:
        if but := lp.ButtonStateRaw():
            process_button(but)
    except KeyboardInterrupt:
        break
    except Exception as e:
        print_exception(e)

    schedule.run_pending()
    time.sleep(WAIT_TIME)  # this is super important, otherwise we destroy the CPU with busy-wait cycles

lp.Reset()  # turn off LEDs
lp.Close()  # close the Launchpad
