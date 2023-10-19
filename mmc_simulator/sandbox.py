"""
In the sandbox mode you can interact with mmc's via keyboard inputs.
Keybindings will be printed in the console.

@author: Kjell Keune
"""
import argparse
from sim.simulation import Simulation, KEY_BINDINGS

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mac", action='store_true', default=False, help="Flag when running on mac.")
    args = parser.parse_args()
    print("\nKeybindings:")
    for name, key in KEY_BINDINGS.items():
        print(f"{key} - {name}")
    sim1 = Simulation()
    if args.mac:
        sim1.start_onMac()
    else:
        sim1.start()