from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
import numpy as np
import simpleaudio as sa

# TODO: right name for the classes?
class ChannelWidget(pg.GraphicsLayoutWidget):
# TODO: signal should be a single range instead of two floats
    cwsig_x_zoomed = QtCore.pyqtSignal(object)
    
    def __init__(self, parent=None, **kwargs):
        super(ChannelWidget, self).__init__(parent)
        self.pen = (255,255,255,200)
        self.audioplot = self.addPlot(row=0)
        #self.init_audioplot_data(data, np.int(rate))
#        self.playback_line = pg.InfiniteLine(0.0, pen=(0, 0, 255, 200))
# TODO: add spectrogram in second row
        self.parent = parent
        self.tcursor = pg.InfiniteLine(movable=True)
        self.selectors = [None, None]
        self.quickzoom_halfwin = 0.100

        # To be set in init_audioplot_data.
        self.data = None
        self.rate = None
        self.sec = None
#        self.stream = None

#    def _open_stream_(self):
#        '''Set up the audio stream for playback.'''
#        self.pya = pyaudio.PyAudio()
#        stream = self.pya.open(
## TODO: support other formats
#            format = pyaudio.paInt16,
#            channels = 1,
#            rate = self.rate,
#            output = True
#        )
#        return stream

    def init_audioplot_data(self, data, rate):
        '''Clear existing plots and load new audio.'''
        self.data = data
        self.rate = rate
        self.sec = np.arange(len(data)) / rate
        self.audioplot.plot(
            x=self.sec,
            y=data,
            pen=self.pen,
            clear=True
        )
        self.audioplot.setDownsampling(auto=True)
        self.audioplot.addItem(self.tcursor)
        self.audioplot.getViewBox().autoRange()
        #if self.stream is None:
        #    self.stream = self._open_stream_()
# TODO: emit signal when data changes (or determine which signal is already emitted)

    def zoom_to_selectors(self):
        '''Zoom viewbox to bounds selected by selectors.'''
        try:
            self.audioplot.getViewBox().setXRange(
                self.selectors[0].value(),
                self.selectors[1].value()
            )
        except AttributeError: # selectors[0] or selectors[1] is None
            pass

    def play_viewbox(self):
        '''Play the audio currently displayed in the viewbox.'''
        xrng = np.array(self.audioplot.getViewBox().viewRange()[0])
#        print('playing', xrng)
        s0, s1 = (xrng * self.rate).astype(np.int)
        self.play_samples(s0, s1)
        
    def play_all(self):
        '''Play all audio.'''
        self.play_samples(0, len(self.data) - 1)

    def play_samples(self, s0, s1):
        '''Play audio from sample s0 to sample s1.'''
        play_obj = sa.play_buffer(
            self.data[s0:s1].astype(np.int16),
            1,   # Number of channels
            2,   # Bytes per sample
            self.rate  # Samplerate
        )
        play_obj.wait_done()
# TODO: support other dtype besides int16
#        print('playing', s0, s1)
#        self.stream.write(
#            self.data[s0:s1].astype(np.int16).tostring()
#        )

    def mousePressEvent(self, e):
        self._pressed_screenpos = e.screenPos()
        super(ChannelWidget, self).mousePressEvent(e)
        
    def mouseReleaseEvent(self, e):
        xpos = self.audioplot.vb.mapSceneToView(e.pos()).x()
        did_pan = e.screenPos() == self._pressed_screenpos        
        cidx = 1 if e.modifiers() == QtCore.Qt.ShiftModifier else 0
        if e.button() == QtCore.Qt.LeftButton and not did_pan:
            if self.selectors[cidx] is None:
                self.selectors[cidx] = pg.InfiniteLine(xpos, movable=True)
                self.audioplot.addItem(self.selectors[cidx])
            if xpos >= 0.0:
# TODO: check that we don't go past the end also
                self.selectors[cidx].setValue(xpos)
# TODO: keep quickzoom behavior?
            if e.modifiers() == QtCore.Qt.ControlModifier:
                self.audioplot.getViewBox().setXRange(
                    xpos - self.quickzoom_halfwin,
                    xpos + self.quickzoom_halfwin
                )
            try:
                self.selectors.sort(key=lambda x: x.value())
            except AttributeError:  # a selector is not yet set
                pass
        elif e.button() == QtCore.Qt.RightButton and did_pan:
# TODO: better name/logic wrt to did_not_pan
            self.cwsig_x_zoomed.emit(
                tuple(self.audioplot.getViewBox().viewRange()[0])
            )

        e.accepted = True  # TODO: useful/needed?
        super(ChannelWidget, self).mouseReleaseEvent(e)

