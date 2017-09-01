#!/usr/bin/env python

import sys
from pyqtgraph.Qt import QtGui
from articapp import ArticApp
from ema_widget import DataLoaderWidget

app = QtGui.QApplication(sys.argv)

ecogbase = sys.argv[1]

data_load_widget = DataLoaderWidget(ecogbase)

win = ArticApp(data_loader=data_load_widget)

win.resize(800,700)
win.setWindowTitle('EMA')

win.show()
sys.exit(app.exec_())
