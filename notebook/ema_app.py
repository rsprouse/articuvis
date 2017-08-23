#!/usr/bin/env python

import sys
import pandas as pd
from pyqtgraph.Qt import QtGui
from articapp import ArticApp
from ema import read_ecog_speaker_audio, read_ecog_speaker_data, \
                read_ecog_palate_trace

ecogspeaker = 'SN4'
ecogbase = '/media/sf_EMA-ECOG/pilot-subjects'
token = 'COMMA'
rep = '01'
dont_show = [
    'EMPTY', 'REF', 'UNK', 'FH', 'OS', 'MS', 'TM', 'PL'
]
xyzdims = 'xyz'   # map displayed dims to data dims
paltrace = [8.2, 28.2]   # time range of palate trace
paldims = ['x', 'y']     # dimensions to use as 'x' and 'y' from palate trace

rate, au = read_ecog_speaker_audio(ecogbase, ecogspeaker, token, rep)

# Remove all columns that begin with an element in drop_prefixes.
datadf = read_ecog_speaker_data(
    ecogbase,
    ecogspeaker,
    token,
    rep,
    drop_prefixes=dont_show
)

landmarkdf = read_ecog_palate_trace(
    ecogbase,
    ecogspeaker,
    trange=paltrace,
    xdim=paldims[0],
    ydim=paldims[1]
)

app = QtGui.QApplication(sys.argv)
win = ArticApp(
    au,
    rate,
    datadf,
    landmarkdf,
    xyz=xyzdims,
    lines={
        'tongue': {
            'elements': ['TB', 'TD', 'TL'],
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
    }
)
win.resize(800,700)
win.setWindowTitle('EMA')
win.aw.pos_vel_elements = ['UL', 'LL']  # Which elements to show in position/velocity plots
win.aw.pos_vel_dim = 'x'  # Which dimension to show in position/velocity plots

win.show()
sys.exit(app.exec_())
