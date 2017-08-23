from pyqtgraph.Qt import QtGui
import pyqtgraph as pg
import pyqtgraph.dockarea as dock

from channel import ChannelWidget
from artic import ArticuWidget

class ArticApp(QtGui.QMainWindow):
    def __init__(self, au, rate, datadf, landmarkdf, xyz, lines, brushes, parent=None, **kwargs):
        '''Create an articulation app.'''
        super(ArticApp, self).__init__(parent)

        self.area = dock.DockArea()
        self.setCentralWidget(self.area)
        pg.setConfigOptions(antialias=True) # Enable antialiasing for prettier plots
    
        self.audiodock = dock.Dock('Audio')
        self.articdock = dock.Dock('Articulation')
        self.ctrldock = dock.Dock('Controls', size=(1,1))
    
        self.area.addDock(self.audiodock, 'left')
        self.area.addDock(self.articdock, 'bottom', self.audiodock)
        self.area.addDock(self.ctrldock, 'bottom', self.articdock)
    
        self.playall = QtGui.QPushButton('Play all')
        self.playsel = QtGui.QPushButton('Play sel')
        self.updatesel = QtGui.QPushButton('Update sel')
        self.anim = QtGui.QPushButton('Animate')
        self.ctrldock.addWidget(self.playall, row=0, col=0)
        self.ctrldock.addWidget(self.playsel, row=0, col=1)
        self.ctrldock.addWidget(self.updatesel, row=0, col=2)
        self.ctrldock.addWidget(self.anim, row=0, col=3)
    
        # Make widgets for audio channel and articulation data. Hook them together so that
        # when the xrange changes on the audio channels the articulation windows update.
        self.cw = ChannelWidget(au, rate)
    
        self.aw = ArticuWidget(
            datadf,
            landmarkdf,      # No landmark dataframe
            xyz=xyz,
            lines=lines,
            brushes=brushes,
            parent=None
        )
    
        self.audiodock.addWidget(self.cw)
        self.articdock.addWidget(self.aw)
    
    #    self.cw.audioplot.sigXRangeChanged.connect(self.app_make_tplot)
        #self.cw.cwsig_x_zoomed.connect(self.app_make_tplot)
        self.playall.clicked.connect(self.cw.play_all)
        self.playsel.clicked.connect(self.cw.play_viewbox)
        self.updatesel.clicked.connect(self.app_make_tplot)
        self.anim.clicked.connect(self.aw.animate)
        self.aw.pos_tcursor.sigDragged.connect(self.update_audio_tcursor)
        #self.aw.pos_tcursor.sigDragged.connect(self.update_vel_tcursor)
        self.aw.pos_tcursor.sigDragged.connect(self.update_artic_plots)
        self.aw.vel_tcursor.sigDragged.connect(self.update_audio_tcursor)
        #self.aw.vel_tcursor.sigDragged.connect(self.update_pos_tcursor)
        self.aw.vel_tcursor.sigDragged.connect(self.update_artic_plots)
        #self.cw.tcursor.sigDragged.connect(self.update_pos_tcursor)
        #self.cw.tcursor.sigDragged.connect(self.update_vel_tcursor)
        self.cw.tcursor.sigDragged.connect(self.update_artic_plots)
    # TODO: when click in waveform, update_tplot() to that time
    # TODO: when click in pos/vel windows, update_tplot() and move waveform cursor
    
        self.show()


    def app_make_tplot(self, e):
        '''Handle a zoom event in the audio and pass it to the articulation.'''
        tstart, tend = self.cw.audioplot.getViewBox().viewRange()[0]
        self.aw.tplot(tstart, tend)

    def update_audio_tcursor(self, e):
        x = e.pos()[0]
        self.cw.tcursor.setValue(x)

# TODO: if we do lots of updates by connecting sigDragged to this slot, then
# RecursionError sometimes occurs. Is there a way to detect the condition and
# temporarily stop updates to avoid the error?
    def update_artic_plots(self, e):
        x = e.pos()[0]
        self.aw.update_tplot(t2=x)
