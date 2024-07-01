from plot_python3 import PlotWithPython3

import time
import numpy as np

class PlotMultipleClients(PlotWithPython3):
    def __init__(
        self,
        filename,
        fig_name = 'multipleclients/'
    ):
        super(PlotMultipleClients, self).__init__(filename)

        # Set the figure name appending the current time
        curr_time = time.strftime('%Y-%m-%d_%H-%M-%S')
        self.fig_name = '%s%s' % (fig_name, curr_time)

    def plot_stats(self):
        # Parse data
        threads = self.data['threads']
        servers = self.data['servers']
        throughput = self.data['throughput']

        # Create axis and figure
        fig, ax = self.plt.subplots()

        for thread in threads.unique():
            # Filter data
            data = self.data[self.data['threads'] == thread]

            # Parse data
            servers = data['servers']
            throughput = data['throughput']

            # Label
            label = "%d threads" % thread if thread > 1 else "%d thread" % thread

            # Scatter plot
            ax.plot(
                servers,
                throughput,
                label=label,
                linewidth=1.5,
                marker='o',
                markersize=4,
            )

        # Decorations
        self.decorate_axis(ax, 'Servers', 'Throughput of Writes')
        self.decorate_figure(fig)

        fig.savefig('%s%s.pdf' % (self.figures_dir, self.fig_name), backend='pgf')


def main():
    plot_object = PlotMultipleClients('multipleclients.csv')
    plot_object.store_data()
    plot_object.plot_stats()

if __name__ == '__main__':
    main()
