from plot_python3 import PlotWithPython3

class PlotTimeouts(PlotWithPython3):
    def __init__(
        self,
        filename
    ):
        super(PlotTimeouts, self).__init__(filename)
    
    def plot_stats(self):
        time_axis = self.data['time']
        sample_rtt = self.data['sample_rtt']
        estimated_rtt = self.data['estimated_rtt']
        deviation = self.data['deviation']

        deviation_above = [estimated_rtt[i] + deviation[i] for i in range(len(estimated_rtt))]
        deviation_below = [estimated_rtt[i] - deviation[i] for i in range(len(estimated_rtt))]

        fig, ax = self.plt.subplots()

        # Plot Sample RTT
        ax.plot(
            time_axis,
            sample_rtt, 
            label='Sample RTT'
        )

        # Plot Estimated RTT
        ax.plot(
            time_axis,
            estimated_rtt,
            label='Estimated RTT'
        )

        # Plot Deviation Bounds
        ax.plot(
            time_axis,
            deviation_above,
            color='darkorange',
            linewidth=1,
            linestyle='--'
        )
        ax.plot(
            time_axis,
            deviation_below,
            color='darkorange',
            linewidth=1,
            linestyle='--'
        )
        # Fill Deviation Bounds
        ax.fill_between(
            time_axis,
            deviation_above,
            deviation_below,
            color='darkorange',
            alpha=0.2
        )
        
        self.decorate_axis(ax, 'Time (ms)', 'RTT (ms)')
        self.decorate_figure(fig)

        fig.savefig('%s/timeout_stats.pdf' % self.figures_dir, backend='pgf')
        

def main():
    plot_object = PlotTimeouts('timeout_stats.csv')
    plot_object.store_data()
    plot_object.plot_stats()

if __name__ == '__main__':
    main()
