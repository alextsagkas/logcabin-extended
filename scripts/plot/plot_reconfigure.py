from plot_python3 import PlotWithPython3

import time

class PlotReconfigure(PlotWithPython3):
    def __init__(
        self,
        filename,
        fig_name = 'reconfigure/'
    ):
        super(PlotReconfigure, self).__init__(filename)

        # Set the figure name appending the current time
        curr_time = time.strftime('%Y-%m-%d_%H-%M-%S')
        self.fig_name = '%s%s' % (fig_name, curr_time)
    
    def plot_stats(self):
        servers = self.data['servers']
        time = self.data['time']
        tries = self.data['tries']

        fig, ax = self.plt.subplots()

        # Plot Sample RTT
        ax.plot(
            time,
            servers, 
            label='Test'
        )

        self.decorate_axis(ax, 'Time (s)', 'Servers')
        self.decorate_figure(fig)

        fig.savefig('%s%s.pdf' % (self.figures_dir, self.fig_name), backend='pgf')
        

def main():
    plot_object = PlotReconfigure('reconfigure.csv')
    plot_object.store_data()
    plot_object.plot_stats()

if __name__ == '__main__':
    main()
