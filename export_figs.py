from src.plot.basicplots import plot_basicfigs
from src.plot.hm import plot_mainfig
from src.plot.hm import plot_supfig
from src.plot.hm_retrofit import plot_supretrofit

def plot_figs():
    plot_basicfigs()
    plot_mainfig()
    plot_supfig()
    plot_supretrofit()

if __name__ == "__main__":
    plot_figs()
