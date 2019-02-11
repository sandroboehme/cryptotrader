from backtrader import Cerebro
import matplotlib


class CTCerebro(Cerebro):

    def plotToFile(self, plotter=None, numfigs=1, iplot=True, start=None, end=None,
                   width=16, height=9, dpi=300, tight=True, use=None,
                   path=None, **kwargs):
        if self._exactbars > 0:
            return
        # change to a non-interactive backend
        matplotlib.use('Agg')
        if not plotter:
            from backtrader import plot
            if self.p.oldsync:
                plotter = plot.Plot_OldSync(**kwargs)
            else:
                plotter = plot.Plot(**kwargs)

        import matplotlib.pyplot as plt
        figs = []
        for stratlist in self.runstrats:
            for si, strat in enumerate(stratlist):
                rfig = plotter.plot(strat, figid=si * 100,
                                    numfigs=numfigs, iplot=iplot,
                                    start=start, end=end, use=use)

                figs.append(rfig)
            fig = plt.gcf()
        fig.set_size_inches(width, height)
        if path:
            fig.savefig(path, dpi=dpi)
        return figs