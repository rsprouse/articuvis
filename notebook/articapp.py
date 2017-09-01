from pyqtgraph.Qt import QtGui
import pyqtgraph as pg
import pyqtgraph.dockarea as dock

from channel import ChannelWidget
from artic import ArticuWidget

class ArticApp(QtGui.QMainWindow):
    def __init__(self, data_loader=None, parent=None, **kwargs):
        '''Create an articulation app.'''
        super(ArticApp, self).__init__(parent)

        self.area = dock.DockArea()
        self.setCentralWidget(self.area)
        pg.setConfigOptions(antialias=True) # Enable antialiasing for prettier plots
        self.data_loader = data_loader
    
        self.audiodock = dock.Dock('Audio')
        self.articdock = dock.Dock('Articulation')
        self.ctrldock = dock.Dock('Controls', size=(1,1))
    
        self.area.addDock(self.ctrldock, 'left')
        self.area.addDock(self.audiodock, 'right', self.ctrldock)
        self.area.addDock(self.articdock, 'bottom', self.audiodock)
    
        self.playall = QtGui.QPushButton('Play all')
        self.playsel = QtGui.QPushButton('Play sel')
        self.updatesel = QtGui.QPushButton('Update sel')
        self.anim = QtGui.QPushButton('Animate')
        self.ctrldock.addWidget(self.playall, row=0)
        self.ctrldock.addWidget(self.playsel, row=1)
        self.ctrldock.addWidget(self.updatesel, row=2)
        self.ctrldock.addWidget(self.anim, row=3)
        if self.data_loader is not None:
            self.ctrldock.addWidget(self.data_loader, row=4)
    
        # Make widgets for audio channel and articulation data. Hook them together so that
        # when the xrange changes on the audio channels the articulation windows update.
        self.cw = ChannelWidget()
    
        self.aw = ArticuWidget(parent=None)
    
        self.audiodock.addWidget(self.cw)
        self.articdock.addWidget(self.aw)
    
    #    self.cw.audioplot.sigXRangeChanged.connect(self.app_make_tplot)
        #self.cw.cwsig_x_zoomed.connect(self.app_make_tplot)
        self.playall.clicked.connect(self.cw.play_all)
        self.playsel.clicked.connect(self.cw.play_viewbox)
        self.updatesel.clicked.connect(self.app_make_tplot)
# TODO: prevent crash if element is selected while animate() is running
        self.anim.clicked.connect(self.aw.animate)

        # Update audio_tcursor when pos_tcursor or vel_tcusor is dragged
        # or when pos_tcursor is changed via animate. (No need to also update
        # when vel_tcursor is changed via animate.)
        self.aw.pos_tcursor.sigPositionChanged.connect(self.update_audio_tcursor)
        self.aw.vel_tcursor.sigDragged.connect(self.update_audio_tcursor)

        # Update all articulation plots when any *_tcursor is dragged.
        self.aw.pos_tcursor.sigDragged.connect(self.update_artic_plots)
        self.aw.vel_tcursor.sigDragged.connect(self.update_artic_plots)
        self.cw.tcursor.sigDragged.connect(self.update_artic_plots)

        if self.data_loader is not None:
            self.data_loader.data_loaded.connect(self.init_plots)
            self.data_loader.xyz_map_changed.connect(self.handle_xyz_map_change)
            self.data_loader.selected_elements_changed.connect(
                self.handle_element_select
            )
    
        self.show()

    def handle_xyz_map_change(self):
        '''Handle change of xyz_map.'''
        self.aw.landmarkdf = self.data_loader.landmarkdf
        self.app_make_tplot(None)

    def handle_element_select(self):
        '''Handle change of selected elements.'''
#        self.aw.elements = self.data_loader.selected_elements
#        self.aw.pos_vel_elements = self.data_loader.selected_pos_vel_elements
#        self.aw.pos_vel_dim = self.data_loader.selected_pos_vel_dim
# TODO: don't use private member _selected_element_brushes
        self.aw._selected_element_brushes = {}
        self.app_make_tplot(None)
# TODO: update plots

    def app_make_tplot(self, e):
        '''Handle a zoom event in the audio and pass it to the articulation.'''
        tstart, tend = self.cw.audioplot.getViewBox().viewRange()[0]
        self.aw.elements = self.data_loader.selected_elements
        self.aw.brushes = self.data_loader.selected_element_colors
        self.aw.pos_vel_elements = self.data_loader.selected_pos_vel_elements
        self.aw.pos_vel_dim = self.data_loader.selected_pos_vel_dim
        self.aw.xyz = self.data_loader.xyz_map
        self.aw.tplot(tstart, tend)

    def update_audio_tcursor(self, e):
        x = e.pos()[0]
        self.cw.tcursor.setValue(x)

    def update_artic_plots(self, e):
        x = e.pos()[0]
        self.aw.update_tplot(t2=x)

    def init_plots(self):
        dl = self.data_loader
        self.cw.init_audioplot_data(dl.au, dl.rate)
        self.aw.init_dataplots(
            dl.datadf,
            dl.landmarkdf,
            xyz=dl.xyz_map,
# TODO: don't hardcode values shown below
            lines={
                'tongue': {
                    'elements': ['TB', 'TL', 'TD'],
                    'pen': (128, 255, 128, 128)
                },
                'mouth': {
                    'elements': ['LL', 'LC', 'UL'],
                    'pen': (128, 128, 255, 128)
                }
            },
            brushes={   # symbolBrushes used for element scatter plots
                'TD': 'r',
                'TB': 'r',
                'TL': 'g',
                'LL': 'y',
                'LC': 'g',
                'JW': 'b',
                'UL': 'y',
                'UI': 'k',
            },
        )
