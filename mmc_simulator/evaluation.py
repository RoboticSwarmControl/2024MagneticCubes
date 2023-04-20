import math
import matplotlib.pyplot as plt
import numpy as np

from com.state import Cube

def plot_pivotAngleDistance():
    pAxisLengths = [Cube.RAD * 2, Cube.RAD * 4]
    alpha = np.linspace(0, np.pi, 100)
    for a_p in pAxisLengths:
        d_p = 2 * np.sin(0.5 * alpha) * a_p
        plt.plot(alpha, d_p)
    plt.xlabel('pivot walking angle')
    plt.ylabel('pvot walking distance')
    plt.show()
    

def main():
    plot_pivotAngleDistance()

if __name__ == "__main__":
    main()