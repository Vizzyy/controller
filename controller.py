import libs.launchpad as launchpad
import requests
import midea_beautiful
from config import *
import subprocess
import time
import libs.reo_api as reo_api
import json
from functions.init import *

# Mk1 Launchpad:
lp = launchpad.Launchpad()
lp.Open()
lp.ButtonFlush()
lp.LedAllOn()
lp.Reset()  # turn off LEDs


def main():
    load_mappings()
    set_default_led_states()

    while True:
        try:
            if but := lp.ButtonStateRaw():
                # process_button(but)
                print(but)
        except KeyboardInterrupt:
            lp.Reset()  # turn off LEDs
            lp.Close()  # close the Launchpad
            break
        except Exception as e:
            print_exception(e)

        time.sleep(WAIT_TIME)  # reduce busy-waiting


if __name__ == "__main__":
    main()
