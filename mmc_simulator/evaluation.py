import math
import matplotlib.ticker as tck
import matplotlib.pyplot as plt
import numpy as np

from com.state import Cube

def plot_pivotAngleDistance():
    pAxisLengths = [Cube.RAD * 2, Cube.RAD * 4, 6 * Cube.RAD]
    alpha = np.linspace(0, np.pi, 100)
    for a_p in pAxisLengths:
        d_p = 2 * np.sin(0.5 * alpha) * a_p
        plt.plot(alpha/np.pi, d_p/Cube.RAD, label=f"$a_p = ${round(a_p / Cube.RAD)} $r_C$")
    ax = plt.subplot()
    plt.xlabel(r'pivot walking angle $\alpha$')
    plt.ylabel('pivot walking distance $d_p$')
    plt.xlim(xmin=0, xmax=1)
    plt.ylim(ymin=0, ymax=12.5)
    ax.legend()
    ax.xaxis.set_major_formatter(tck.FormatStrFormatter('%g $\pi$'))
    ax.xaxis.set_major_locator(tck.MultipleLocator(base=0.25))
    ax.yaxis.set_major_formatter(tck.FormatStrFormatter('%g $r_C$'))
    ax.yaxis.set_major_locator(tck.MultipleLocator(base=1.0))
    plt.show()
    

def main():
    plot_pivotAngleDistance()

if __name__ == "__main__":
    main()