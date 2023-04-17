"""
Magnetic cube simulator.

After creating a Simulation custom configurations can be loaded.
After start you can execute motions with rotate() and pivotWalk() or the _nowait equivalents.
Runtime user interaction is also possible. Look in simulation.py method __userInputs()__ for key bindings.

@author: Aaron T Becker, Kjell Keune
"""
from sim.simulation import Simulation

def sandbox_onMac():
    sim1 = Simulation()
    sim1.start_onMac()

def sandbox():
    sim1 = Simulation()
    sim1.start()

if __name__ == "__main__":
    sandbox()