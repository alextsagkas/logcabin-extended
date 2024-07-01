from plot_python3 import PlotWithPython3

import time
import numpy as np

class PlotElectionPerf(PlotWithPython3):
    def __init__(
        self,
        filename,
        fig_name = 'electionperf/'
    ):
        super(PlotElectionPerf, self).__init__(filename)

        # Set the figure name appending the current time
        curr_time = time.strftime('%Y-%m-%d_%H-%M-%S')
        self.fig_name = '%s%s' % (fig_name, curr_time)

    def decorate_figure(self, fig, sc):
        # Color bar
        fig.colorbar(
            sc,
            location = 'right',
            label = 'Election Timeout (ms)',
        )

        fig.set_size_inches(self.fig_size)

    def plot_stats(self):
        # Parse data
        elections = self.data['elections']
        time = self.data['time']
        electionTimeout = self.data['electionTimeout']

        # Create axis and figure
        fig, ax = self.plt.subplots(layout="constrained")

        # Scatter plot
        sc = ax.scatter(
            time,
            elections,
            alpha=0.8,
            c=electionTimeout,
        )

        # Decorations
        self.decorate_axis(ax, 'Duration (s)', 'Elections')
        self.decorate_figure(fig, sc)

        fig.savefig('%s%s.pdf' % (self.figures_dir, self.fig_name), backend='pgf')
        

def main():
    plot_object = PlotElectionPerf('electionperf.csv')
    plot_object.store_data()
    plot_object.plot_stats()

if __name__ == '__main__':
    main()
