"""
In the sandbox mode you can interact with mmc's via keyboard inputs.
Keybindings will be printed in the console.

@author: Kjell Keune
"""
from sim.simulation import Simulation, KEY_BINDINGS
from com.motion import Idle

if __name__ == "__main__":
    print("\nKeybindings:")
    for name, key in KEY_BINDINGS.items():
        print(f"{key} - {name}")
    sim = Simulation()
    while True:
        sim.executeMotion(Idle(1))