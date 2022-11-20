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
button_mappings = None


def load_mappings():
    global enabled_buttons, button_mappings
    with open('./button_mappings.json', 'r') as f:
        button_mappings = json.loads(f.read())

    for grouping in button_mappings:
        enabled_buttons += list(button_mappings[grouping].values())
    enabled_buttons = sorted(enabled_buttons)


load_mappings()
print(enabled_buttons)
print(button_mappings)

#
#
#
#
# def set_default_led_states():
#     for button in enabled_buttons:
#         set_led_green(button)
#
#     # Custom default states
#     set_led_red(0)
#     set_led_red(5)
#     set_led_red(6)
#     set_led_red(32)
#     set_led_yellow(stream_1)  # camera 1
#     set_led_red(69)
#     set_led_yellow(70)
#     set_led_yellow(71)
#     set_led_red(80)
#     set_led_yellow(118)
#     set_led_red(119)
#     set_led_yellow(206)
#     set_led_red(camera_w_led)
#     set_led_yellow(camera_home_reset)


