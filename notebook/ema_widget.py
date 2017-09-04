import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
#from ema import read_ecog_speaker_audio, read_ecog_speaker_data, \
#                read_ecog_palate_trace, get_ecog_subject_utterances
from ema import EmaEcogDataLoader

class DataLoaderWidget(pg.GraphicsLayoutWidget):
    '''A widget for selecting EMA-ECOG files to load.'''
    #emasig_speaker_selected = QtCore.pyqtSignal(str)
    data_loaded = QtCore.pyqtSignal()
    selected_elements_changed = QtCore.pyqtSignal()
    xyz_map_changed = QtCore.pyqtSignal()
 
    @property
    def selected_speaker(self):
        return self.spkr.currentText()
 
    @property
    def selected_utterance(self):
        return self.utt.currentText()

    @property
    def selected_rep(self):
        return self.rep.currentText()

    @property
    def elements(self):
        try:
            cols = self.datadf.columns
        except Exception as e:
            cols = []
        return [c.replace('_x', '') for c in cols if c.endswith('_x')]

    @property
    def xyz_map(self):
        return self.xyz_cb.currentText()

    @property
    def selected_elements(self):
        cboxes = self.el_sel.findChildren(QtGui.QCheckBox)
        cboxes = cboxes[::2]  # Skip pos_vel_element checkboxes
        return [c.text() for c in cboxes if c.isChecked()]

    @property
    def selected_pos_vel_elements(self):
        cboxes = self.el_sel.findChildren(QtGui.QCheckBox)
        elboxes = cboxes[::2]  # element checkboxes
        pvboxes = cboxes[1::2] # pos_vel_element checkboxes
        l = []
        for idx, c in enumerate(pvboxes):
            if c.isChecked():
                l.append(elboxes[idx].text())
        return l

    @property
    def selected_element_colors(self):
        '''Return a dict of selected elements as keys and corresponding colors
as values.'''
        clrdict = {}
        for el in self.selected_elements:
            clrdict[el] = self.el_sel.findChild(pg.ColorButton, el).color()
        return clrdict

    @property
    def selected_pos_vel_dim(self):
        return self.pos_vel_dim_cb.currentText()

    def __init__(self, datadir, *args, **kwargs):
        super(DataLoaderWidget, self).__init__(*args, **kwargs)
        self.setStyleSheet('background-color:white;')
        self.data_loader = EmaEcogDataLoader(datadir)
        layout = QtGui.QVBoxLayout()

        self.spkr = QtGui.QComboBox()
        self.utt = QtGui.QComboBox()
        self.rep = QtGui.QComboBox()
        self.el_sel = QtGui.QGroupBox('Elements')
        self.el_sel.setLayout(QtGui.QGridLayout())
        self.add_speakers()

        self.load_button = QtGui.QPushButton('Load utt')

        self.spkr.currentTextChanged.connect(self.speaker_selected)
        self.utt.currentTextChanged.connect(self.utterance_selected)
        self.load_button.clicked.connect(self.load_data)

        layout.addWidget(self.spkr)
        layout.addWidget(self.utt)
        layout.addWidget(self.rep)
        layout.addWidget(self.load_button)
        layout.addWidget(self.el_sel)
        self.setLayout(layout)

    def add_elements(self, checked=[]):
        '''Add element checkboxes and set as checked if in checked.'''
        for idx, el in enumerate(self.elements):
            elbox = QtGui.QCheckBox(el)
            elbox.setChecked(el in checked)
            elbox.stateChanged.connect(self.handle_element_select)
            self.el_sel.layout().addWidget(elbox, idx, 0)
            clrbtn = pg.ColorButton()
            clrbtn.setObjectName(el)
            clrbtn.sigColorChanged.connect(self.handle_element_select)
            self.el_sel.layout().addWidget(clrbtn, idx, 1)
            pvbox = QtGui.QCheckBox()
            pvbox.stateChanged.connect(self.handle_element_select)
            self.el_sel.layout().addWidget(pvbox, idx, 2)

        # Position/velocity dimension selector.
        cb = QtGui.QComboBox()
        cb.addItem('y')
        cb.addItem('x')
        cb.currentIndexChanged.connect(self.handle_element_select)
        self.el_sel.layout().addWidget(cb)
        self.pos_vel_dim_cb = cb
        xyzcb = QtGui.QComboBox()
        xyzcb.setObjectName('xyz_map')
        xyzcb.addItem('xyz')
        xyzcb.addItem('xzy')
        xyzcb.addItem('yxz')
        xyzcb.addItem('yzx')
        xyzcb.addItem('zxy')
        xyzcb.addItem('zyx')
        xyzcb.currentIndexChanged.connect(self.handle_xyz_map_select)
        self.el_sel.layout().addWidget(xyzcb)
        self.xyz_cb = xyzcb

    def clear_elements(self):
        '''Remove the element checkboxes.'''
        checkboxes = self.el_sel.findChildren(QtGui.QCheckBox)
        while self.el_sel.layout().count() > 0:
            self.el_sel.layout().itemAt(0).widget().setParent(None)

    def get_audio(self):
        '''Call data_loader's get_audio() method with current speaker,
utterance, and repetition selections.'''
        return self.data_loader.get_audio(
            self.selected_speaker,
            self.selected_utterance,
            self.selected_rep
        )

    def get_speaker_utt(self):
        '''Call data_loader's get_speaker_utt() method with current speaker,
utterance, and repetition selections.'''
# TODO: add drop_prefixes
        return self.data_loader.get_speaker_utt(
            self.selected_speaker,
            self.selected_utterance,
            self.selected_rep
        )

    def get_palate_trace(self):
        '''Call data_loader's get_palate_trace() method with current speaker
selection.'''
# TODO: don't hardcode trange, xdim, ydim
        return self.data_loader.get_palate_trace(
            self.selected_speaker,
            trange=[8.2, 28.2],
            xdim=self.xyz_map[0],
            ydim=self.xyz_map[1]
        )

    def load_data(self):
        was_selected = self.selected_elements
        self.clear_elements()
        self.rate, self.au = self.get_audio()
        self.datadf = self.get_speaker_utt()
        self.add_elements(was_selected)
        self.landmarkdf = self.get_palate_trace()
        self.data_loaded.emit()

    def add_speakers(self, blockSignals=True):
        '''Add speakers to the speaker combobox.'''
        state = self.spkr.signalsBlocked()
        self.spkr.blockSignals(blockSignals)
        self.spkr.addItem('')
        for s in self.data_loader.get_speaker_list():
            self.spkr.addItem(s)
        self.spkr.blockSignals(state)

    def add_utterances(self, spkr, blockSignals=True):
        '''Clear the utterances listed in the utterance combobox.'''
        state = self.utt.signalsBlocked()
        self.utt.blockSignals(blockSignals)
        self.utt.addItem('')
        for u in self.data_loader.get_utterance_list_for_speaker(spkr):
            self.utt.addItem(u)
        self.utt.blockSignals(state)

    def add_reps(self, spkr, utt, blockSignals=True):
        '''Clear the repetitions listed in the repetition combobox.'''
        state = self.rep.signalsBlocked()
        self.rep.blockSignals(blockSignals)
        self.rep.addItem('')
        for r in self.data_loader.get_rep_list_for_speaker_utterance(spkr, utt):
            self.rep.addItem(r)
        self.rep.blockSignals(state)

    def clear_speakers(self, blockSignals=True):
        '''Clear the speakers listed in the speaker combobox.'''
        state = self.spkr.signalsBlocked()
        self.spkrs.blockSignals(blockSignals)
        while self.spkr.count() > 0:
            self.spkr.removeItem(0)
        self.spkr.blockSignals(state)

    def clear_utterances(self, blockSignals=True):
        '''Clear the utterances listed in the utterance combobox.'''
        state = self.utt.signalsBlocked()
        self.utt.blockSignals(blockSignals)
        while self.utt.count() > 0:
            self.utt.removeItem(0)
        self.utt.blockSignals(state)

    def clear_reps(self, blockSignals=True):
        '''Clear the repetitions listed in the repetition combobox.'''
        state = self.rep.signalsBlocked()
        self.rep.blockSignals(blockSignals)
        while self.rep.count() > 0:
            self.rep.removeItem(0)
        self.rep.blockSignals(state)

    def speaker_selected(self, e):
        '''The e event contains the selection from the speaker combobox.'''
        self.clear_utterances()
        self.clear_reps()
        self.add_utterances(self.selected_speaker)

    def utterance_selected(self, e):
        '''The e event contains the selection from the utterance combobox.'''
        self.clear_reps()
        self.add_reps(self.selected_speaker, self.selected_utterance)

    def handle_element_select(self):
        '''Emit a signal when an element checkbox changes state.'''
        self.selected_elements_changed.emit()

    def handle_xyz_map_select(self):
        '''Reload palate data and emit a signal when xyz_map changes state.'''
        self.landmarkdf = self.get_palate_trace()
        self.xyz_map_changed.emit()
