import json

appliance = None
pihole_enabled = True
midea_target_temp = 25
WAIT_TIME = .1
garage_safety_on = True
browser_process = None
camera_selected = 1
camera_w_led_state = 0
browser_pid = None
display_sleep_enabled = True
launchpad_sleep_enabled = False
bluetooth_connected = True
volume_setting = 4
enabled_buttons = []
button_mappings = {}
button_reverse_mappings = {}


def load_mappings():
    global enabled_buttons, button_mappings, button_reverse_mappings
    with open('data/button_mappings.json', 'r') as f:
        button_mappings = json.loads(f.read())

    enabled_buttons = sorted([int(b_id) for b_id in list(button_mappings.keys())])
    print(f'Enabled buttons: {enabled_buttons}')

    for button in enabled_buttons:
        button_reverse_mappings[button_mappings[button]['id']] = button


def set_led_off(button_position):
    lp.LedCtrlRaw(button_position, 0, 0)


def set_led_green(button_position):
    lp.LedCtrlRaw(button_position, 0, 3)


def set_led_yellow(button_position):
    lp.LedCtrlRaw(button_position, 3, 3)


def set_led_red(button_position):
    lp.LedCtrlRaw(button_position, 3, 0)


def print_exception(exception, msg=''):
    print(f'{msg}{type(exception).__name__} - {exception}')


def set_default_led_states():
    global button_mappings
    for button in button_mappings:
        default_color = button_mappings[button]['default_color']
        if default_color == "green":
            set_led_green(int(button))
        elif default_color == "yellow":
            set_led_yellow(int(button))
        elif default_color == "red":
            set_led_red(int(button))
        else:
            set_led_off(int(button))
