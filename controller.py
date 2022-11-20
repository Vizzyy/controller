import time

from functions import init
from functions.init import load_mappings, set_default_led_states, lp, button_mappings, lookup, print_exception, \
    WAIT_TIME


def main():
    load_mappings()
    set_default_led_states()

    print(init.button_mappings)

    while True:
        try:
            if but := lp.ButtonStateRaw():
                button_position = but[0]
                func = button_mappings[str(button_position)]["function"]
                print(f'but: {but} - {func}')
                lookup(f'functions.{func}', func)(button_position)
        except KeyboardInterrupt:
            lp.Reset()  # turn off LEDs
            lp.Close()  # close the Launchpad
            break
        except Exception as e:
            print_exception(e)

        time.sleep(WAIT_TIME)  # reduce busy-waiting


if __name__ == "__main__":
    main()
