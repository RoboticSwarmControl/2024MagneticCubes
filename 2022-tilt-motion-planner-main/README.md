# Tilt Motion Planner

Motion planner that computes short control sequences for TILT assembly.<br />
The project is based on [TumbleTiles](https://github.com/asarg/TumbleTiles).

## General Info

### TILT
TILT is a model in which tiles on a 2D grid are controlled by uniform external forces.
In addition to tiles the grid contains immovable obstacles, that can block the movement of a tile.
There are four different global control signals; one for each of the cardinal directions.
In the model used for this motion planner a control input causes all tiles to move one unit distance
in the corresponding direction, if they are not blocked. <br />
Additionally, tiles can form polyominoes, which can not be separated again.
Each tile can have a different glue on each of it's four edges. Rules define which glues adhere to each other.

### Assembly and motion planing
The goal of this motion planner is to compute control sequences of optimal or sufficiently short length,
that assemble tiles into a desired shape. This is a computationally complex problem. 
Therefore, the motion planner will rely on heuristics to compute such a control sequence efficiently.

## Requirements
- Python 3.8+
- numpy
- pillow  

## Usage
To run the GUI:
> python -m tiltmp

To solve a json-encoded instance and profile the performance:
> python run_experiment.py < input file >

Test instances are provided in the **Testcases** directory.