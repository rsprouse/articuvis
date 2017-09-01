import re
import numpy as np
from pyqtgraph.Qt import QtGui
import pyqtgraph as pg

class ArticuWidget(pg.GraphicsLayoutWidget):
    '''Widget that encapsulates element-based articulatory data, e.g. EMA,
x-ray microbeam.'''

    @property
    def _element_cols(self):
        return  {
            'x': ['{}_{}'.format(el, self.xyz[0]) for el in self.elements],
            'y': ['{}_{}'.format(el, self.xyz[1]) for el in self.elements]
        }

    @property
    def selected_element_brushes(self):
        '''Return a list of symbolBrushes for currently selected elements.'''
        if self._selected_element_brushes == {}:
            self.set_selected_element_brushes()
        return self._selected_element_brushes

    def set_selected_element_brushes(self):
# TODO: don't hardcode default here
        default = pg.mkBrush(color=(100, 100, 100, 255))
        br = []
# TODO: make sure self.elements is in same order as df columns
# TODO: add logic for determining that an element is selected
        for el in self.elements:
            try:
                br.append(pg.mkBrush(color=self.brushes[el]))
            except KeyError:
                br.append(default)
        self._selected_element_brushes = br

    @property
    def _selected_range(self):
        '''Return the range of the currently selected data.'''
        xmin = self._sel_df.loc[:, self._element_cols['x']].min().min()
        xmax = self._sel_df.loc[:, self._element_cols['x']].max().max()
        ymin = self._sel_df.loc[:, self._element_cols['y']].min().min()
        ymax = self._sel_df.loc[:, self._element_cols['y']].max().max()
        if self.landmarkdf is not None:
            xmin = np.min([xmin, self.landmarkdf.x.min()])
            xmax = np.max([xmax, self.landmarkdf.x.max()])
            ymin = np.min([ymin, self.landmarkdf.y.min()])
            ymax = np.max([ymax, self.landmarkdf.y.max()])
        return ((xmin, xmax), (ymin, ymax))

    def __init__(self, parent=None, **kwargs):
        super(ArticuWidget, self).__init__(parent)
        self.parent = parent
        self.plots = []
        self.df = None
        self.frameplot = self.addPlot(row=0, col=0)  # Plot of a single frame
        self.frameplot.setAspectLocked(True)
        self.traceplot = self.addPlot(row=0, col=1)  # Plot of time trace
        self.traceplot.setAspectLocked(True)
        self.posplot = self.addPlot(row=1, col=0)    # Plot of element position over time
        self.velplot = self.addPlot(row=1, col=1)    # Plot of element velocity over time
        self.pos_tcursor = pg.InfiniteLine(movable=True)
        self.vel_tcursor = pg.InfiniteLine(movable=True)
        self.clear_plots()

    def clear_plots(self):
        self.landmarkdf = None
        self.lines = []  # List of element dicts to link as a line.
        self.brushes = {}  # dict of symbolBrushes, one key per element
        self.elements = [] # List of elements to plot
# TODO: don't hardcode xyz
        self.xyz = 'xyz'  # Mapping of displayed dims to data dims
        self._is_updating = False
# TODO: rename _sel* attributes and think about appropriate place to update values
        self._sel_t1 = None
        self._sel_t2 = None
        self._sel_df = None
        self._sel_landmarkdf = None
        self._selected_element_brushes = {}
# TODO: hide tcursors
        self.pos_tcursor.setPos(0.0)
        self.vel_tcursor.setPos(0.0)


    def init_dataplots(self, df, landmarkdf, lines, brushes, xyz):
        self.df = df
        self.landmarkdf = landmarkdf
        self.lines = lines or []  # List of element names to link as a line.
        self.brushes = brushes or {}  # dict of symbolBrushes, one per element
        self.pen = pg.mkPen('g')
        self.xyz = xyz
# TODO: update *._ as appropriate when object attributes change
#        self._line_elements = [e for subl in self.lines for e in subl]
        self._line_cols = {}
        self.pos_vel_dim = 'x'
        self.pos_vel_elements = []
        self.minsymbsize = 1   # Minimum symbol size
        self.maxsymbsize = 5   # Maximum symbol size
        self.minalpha = 1      # Minimum alpha
        self.maxalpha = 255    # Maximum alpha
        
    def tselect(self, t1, t2):
        '''Select a time range from dataframes and cache.'''
        self._sel_t1 = t1
        self._sel_t2 = t2
        xmask = (self.df.sec >= t1) & (self.df.sec <= t2)
        if not xmask.any():  # Zero length region is selected.
            # Select row nearest xend.
            xmask[(self.df.sec - t2).abs().argmin()] = True
            minsymbsize = self.maxsymbsize
            minalpha = self.maxalpha
        else:
            minsymbsize = self.minsymbsize
            minalpha = self.minalpha
        symbsizes = np.linspace(minsymbsize, self.maxsymbsize, num=xmask.sum())
        alphas = np.linspace(minalpha, self.maxalpha, num=xmask.sum())
        mskdf = self.df.loc[xmask, :].copy()
        mskdf = mskdf.assign(symbsizes=symbsizes)
        self._sel_df = mskdf
        
    def tplot(self, t1, t2):
        '''Create plots for time range.'''
        if t1 != self._sel_t1 and t2 != self._sel_t2:
            self.tselect(t1, t2)
        self.frameplot.clear()
        self.traceplot.clear()
        self.posplot.clear()
        self.velplot.clear()
        (xrng, yrng) = self._selected_range
        if not np.any(np.isnan([xrng, yrng])):
            self.frameplot.setRange(xRange=xrng, yRange=yrng)
            self.traceplot.setRange(xRange=xrng, yRange=yrng)
        elemdims = [
            '{}_{}'.format(el, self.pos_vel_dim) for el in self.pos_vel_elements
        ]
        for ed, el in zip(elemdims, self.pos_vel_elements):
            try:
                symbr = pg.mkBrush(color=self.brushes[el])
            except KeyError:
                symbr = pg.mkBrush(color=(128, 128, 128, 128))
            self.posplot.plot(
                self._sel_df.sec.values,
                self._sel_df.loc[:, [ed]].values.squeeze(),
                symbol='o',
                pen=None,
                symbolBrush=symbr,
                symbolSize=self.maxsymbsize
            )
            self.posplot.showGrid(x=True, y=True, alpha=0.5)
            self.posplot.addItem(self.pos_tcursor)
            self.velplot.plot(
                self._sel_df.sec.values,
                self._sel_df.loc[:, [ed + '_vel']].values.squeeze(),
                symbol='o',
                pen=None,
                symbolBrush=symbr,
                symbolSize=self.maxsymbsize
            )
            self.velplot.showGrid(x=True, y=True, alpha=0.5)
            self.velplot.addItem(self.vel_tcursor)
        if self.landmarkdf is not None:
            for g in self.landmarkdf.groupby('landmark'):
                wfr = self.frameplot.plot(
                    g[1].x.values, g[1].y.values, pen=self.pen
                )
                wfr.setObjectName('_landmark_{}'.format(g[1].landmark))
                wtr = self.traceplot.plot(
                    g[1].x.values, g[1].y.values, pen=self.pen
                )
                wfr.setObjectName('_landmark_{}'.format(g[1].landmark))
        self.update_tplot(t1, t1)   # Set to start of frame

    def update_tplot(self, t1=None, t2=None):
        '''Update existing tplot between t1 and t2. Return True on success,
False if no update occurs.'''
        if self.df is None:
            return False
        # Skip current update if another update is still executing in order to
        # avoid RecursionError when too many calls to update_tplot() are made.
        if self._is_updating is True:
            return False
        else:
            self._is_updating = True
        if t1 is None:
            t1 = self._sel_t1
        if t2 is None:
            t2 = self._sel_t2
        #cw.audioplot.dataItems[0].setData(cw.data[::-2])
# TODO: throw an error if t1:t2 not bounded by self._sel_df.sec
#        print('update_tplot {:0.4f} {:0.4f}'.format(t1, t2))
        self.pos_tcursor.setValue(t2)
        self.vel_tcursor.setValue(t2)
        xmask = (self._sel_df.sec >= t1) & (self._sel_df.sec <= t2)
# TODO: is choosing first row right solution for all-false xmask?
        if not xmask.any():
            xmask.iloc[0] = True
        mskdf = self._sel_df.loc[xmask, :]
        endidx = xmask[::-1].argmax()  # index of last selected value
        # Plot element lines.
        for name, desc in self.lines.items():
# TODO: not right place to set _line_cols
            self._line_cols[name] = {
                'x': ['{}_{}'.format(el, self.xyz[0]) for el in desc['elements']],
                'y': ['{}_{}'.format(el, self.xyz[1]) for el in desc['elements']]
            }
            try:
                di = self.frameplot.findChild(pg.PlotDataItem, '_line_' + name)
                assert(di is not None)
                di.setData(
                    mskdf.loc[endidx, self._line_cols[name]['x']].values,
                    mskdf.loc[endidx, self._line_cols[name]['y']].values
                )
            except AssertionError:
                # Plot line at end of time selection.
                line = self.frameplot.plot(
                    mskdf.loc[endidx, self._line_cols[name]['x']].values,
                    mskdf.loc[endidx, self._line_cols[name]['y']].values,
                    pen=desc['pen']
                )
                line.setParent(self.frameplot)
                line.setObjectName('_line_{}'.format(name))
                self.frameplot.showGrid(x=True, y=True, alpha=0.5)
                self.frameplot.setAspectLocked(True)
        # Scatter plot of elements.
        try:
            di = self.frameplot.findChild(
                pg.PlotDataItem,
                '_frameplot_scatter_'
            )
            assert(di is not None)
            di.setData(
                mskdf.loc[endidx, self._element_cols['x']].values,
                mskdf.loc[endidx, self._element_cols['y']].values
            )
        except AssertionError:
            # Plot non-tongue elements at end of selection.
            frsc = self.frameplot.plot(
                mskdf.loc[endidx, self._element_cols['x']].values,
                mskdf.loc[endidx, self._element_cols['y']].values,
                symbol='o',
                pen=None,
                symbolBrush=self.selected_element_brushes,
                symbolSize=self.maxsymbsize
            )
            frsc.setParent(self.frameplot)
            frsc.setObjectName('_frameplot_scatter_')
        for idx, pts in enumerate(
                zip(self._element_cols['x'], self._element_cols['y'])
            ):
            elx, ely = pts
            try:
                # elx[:-2] is element name without suffix '_x', '_y', or '_z'.
                symbr = pg.mkBrush(color=self.brushes[elx[:-2]])
            except KeyError:
                symbr = pg.mkBrush(color=(128, 128, 128, 128))
            try:
                di = self.traceplot.findChild(pg.PlotDataItem, '_element_'+elx)
                assert(di is not None)
                di.setData(
                    mskdf.loc[:endidx, elx].values,
                    mskdf.loc[:endidx, ely].values
                )
            except AssertionError:
                trp = self.traceplot.plot(
                    mskdf.loc[:endidx, elx].values,
                    mskdf.loc[:endidx, ely].values,
                    symbolSize=mskdf.loc[:endidx, 'symbsizes'],
                    pen=None,
                    symbol='o',
                    symbolBrush=symbr
                )
                trp.setParent(self.traceplot)
                trp.setObjectName('_element_{}'.format(elx))
                self.traceplot.showGrid(x=True, y=True, alpha=0.5)
                self.traceplot.setAspectLocked(True)
        pg.QtGui.QApplication.processEvents()
        self._is_updating = False
        return True

    def animate(self):
        '''Animate tplots based on currently selected times.'''
        if self._sel_t1 is None or self._sel_t2 is None:
            return
        tstep = 0.020
        nsteps = np.ceil((self._sel_t2 - self._sel_t1) / tstep) + 2
        tsel = np.linspace(self._sel_t1, self._sel_t2, nsteps)
        for t in tsel:
            self.update_tplot(self._sel_t1, t)

