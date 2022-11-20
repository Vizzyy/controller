def handle_ptz_api_req(button_position, push_state):
    global camera_selected, camera_w_led_state
    speed = 10
    home_position_index = 1
    api_channel = camera_selected - 1

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
            camera_w_led_state = 1 if camera_w_led_state == 0 else 0
            reo_api.api_ctrl(channel=api_channel, w_led_state=camera_w_led_state, cmd='SetWhiteLed')

        if button_position == camera_home_reset:
            reo_api.api_ctrl(channel=api_channel, cmd='SetPtzPreset')

    else:
        if button_position in [camera_home]:
            set_led_red(button_position)
        elif button_position == camera_w_led:
            if camera_w_led_state:
                set_led_green(camera_w_led)
            else:
                set_led_red(camera_w_led)
        else:
            if button_position not in [camera_home, camera_zm_in, camera_zm_out, camera_w_led, camera_home_reset]:
                reo_api.api_ctrl(channel=api_channel, op='Stop')
            set_led_green(button_position)
