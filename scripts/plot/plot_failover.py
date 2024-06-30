from plot_python3 import PlotWithPython3

import time

class PlotFailover(PlotWithPython3):
    def __init__(
        self,
        filename,
        fig_name = 'failover/'
    ):
        super(PlotFailover, self).__init__(filename)

        # Set the figure name appending the current time
        curr_time = time.strftime('%Y-%m-%d_%H-%M-%S')
        self.fig_name = '%s%s' % (fig_name, curr_time)

    def plot_unique(
        self, 
        column,
        fig,
        ax
    ):
        """
        Plot unique values of a column in a scatter plot. The x-axis is the time
        and the y-axis is the writes.
        """

        for unique in column.unique():
            data_unique = self.data[self.data[column.name] == unique]

            time = data_unique['time']
            writes = data_unique['writes']

            # Plot Sample RTT
            ax.scatter(
                time,
                writes,
                label="%s: %ds" % (column.name, unique),
            )

            self.decorate_axis(ax, 'Time (s)', 'Writes')
            self.decorate_figure(fig)

    def plot_stats(self):
        # Parse columns of the CSV file
        killintervals = self.data['killinterval']
        launchdelays = self.data['launchdelay']

        fig1, ax1 = self.plt.subplots()
        self.plot_unique(killintervals, fig1, ax1)

        # self.plt.show()
        fig1.savefig('%s%s.pdf' % (self.figures_dir, self.fig_name), backend='pgf')
        

def main():
    plot_object = PlotFailover('failover.csv')
    plot_object.store_data()
    plot_object.plot_stats()

if __name__ == '__main__':
    main()
