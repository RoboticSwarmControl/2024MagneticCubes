import simulation
import time

if __name__ == "__main__":
    sim = simulation.Simulation()
    sim.start()
    time.sleep(3)
    sim.stop()
    