# Motion Planning for Magnetic Modular Cubes

We developed a heuristic approach for the motion planning problem of assembling structures with magnetic modular cubes in the 2-dimensional special Euclidean group.
Magnetic modular cubes are cube-shaped bodies with embedded permanent magnets uniformly controlled by a global time-varying magnetic field surrounding the workspace.

A 2D physics simulator is used to simulate global control and the resulting continuous movement of magnetic modular cube structures as well as magnetic attraction and repulsion, while detecting and resolving collisions.
The simulator allows closed-loop control algorithms for planning the connection of two structures at desired faces.
These developed sequences of movements, called local plans, will be used on a global scale to plan the assembly of specified target structures in a rectangular workspace with no internal obstacles.
The assembly is done by generating a building instruction graph for a target structure that we traverse in a depth-first-search approach by applying local plans to current states of the workspace.


## MMC Simulator

The simulator can be found in _mmc_simulator/_.

### Requirements

* Python 3.x
* Pygame 2.1.2 
* pymunk 6.4.0


### sandbox.py

In the sandbox mode you can interact with mmc's via keyboard inputs.
Keybindings will be printed in the console. You can also find them in _mmc_simulator/sim/simulation.py_
For running on mac execute _python3 sandbox.py --mac_.

### example_control.py

This file contains documented examples on how to use the framework to write your own control programs using local and global planner. For all the top-level interfaces you will find documentation in the code.