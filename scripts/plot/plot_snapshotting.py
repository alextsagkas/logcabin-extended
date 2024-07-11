import time

from plot_python3 import PlotWithPython3

class PlotSnapshotting(PlotWithPython3):
    def __init__(
        self,
        filename,
        fig_name = 'snapshotting/'
    ):
        super(PlotSnapshotting, self).__init__(filename)

        # Set the figure name appending the current time
        curr_time = time.strftime('%Y-%m-%d_%H-%M-%S')
        self.fig_name = '%s%s' % (fig_name, curr_time)
    
    def plot_stats(self):
        snapshotting = self.data['snapshotting']

        fig, ax = self.plt.subplots()

        for snapshotting_value in snapshotting.unique():
            # Filter data
            data = self.data[self.data['snapshotting'] == snapshotting_value]

            # Parse data
            writes = data['writes']
            time = data['time']
            size = data['size']

            # Caclulate the total size of written data to the log
            kilo_byte = 1024
            total_size = size * writes / kilo_byte

            # Label
            label = "Snapshotting" if snapshotting_value else "Bare-Bones"

            # Scatter plot
            ax.plot(
                time,
                writes,
                label=label,
                linewidth=1.5,
                marker='o',
                markersize=4,
            )

        self.decorate_axis(ax, 'Time (ms)', 'Total Size (KB)')
        self.decorate_figure(fig)

        fig.savefig('%s%s.pdf' % (self.figures_dir, self.fig_name), backend='pgf')

def main():
    plot_object = PlotSnapshotting('snapshotting.csv')
    plot_object.store_data()
    plot_object.plot_stats()

if __name__ == '__main__':
    main()
