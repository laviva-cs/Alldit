import sys, os
from PyQt5.QtCore import QObject, pyqtSignal, QUrl
from PyQt5 import QtCore, QtGui, uic, QtWidgets
import pygame
import urllib.request
import re
from merriam_webster.api import (LearnersDictionary, WordNotFoundException)

qtCreatorFile = "MainDialog.ui"

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class Communicate(QObject):
  setHtml = pyqtSignal(str)


class MyApp(QtWidgets.QDialog, Ui_MainWindow):
  def __init__(self):
    QtWidgets.QDialog.__init__(self)
    Ui_MainWindow.__init__(self)
    self.setupUi(self)
    self.c = Communicate()
    self.dict = LearnersDictionary('466b3ce3-afa8-452d-b328-1fcb2853116f')
    self.textBrowser.setReadOnly(True)
    self.textBrowser.setOpenLinks(False)
    
    self.c.setHtml.connect(self.textBrowser.setHtml)
    
    self.lookUpEntries(['die', 'the', 'about', 'tough'])
  
  def anchor(self, url):
    url = url.url()
    if url.endswith('wav'):
      file = 'bin' + url[url.rfind('/'):]
      if not os.path.isfile(file):
        urllib.request.urlretrieve(url, file)
      
      pygame.mixer.init()
      pygame.mixer.music.load(file)
      pygame.mixer.music.play()
    if 'lookup.dict' in url:
      word = url[url.rfind('/') + 1:]
      word = re.sub(r"[0-9]", "", word)
      word = word.strip()
      self.lookUpEntries([word])
  
  def lookUpEntries(self, entries):
    self.c.setHtml.emit(
      "<br />————————<br />".join([self.dict.lookup(entry) for entry in entries])
    )


if __name__ == "__main__":
  if not os.path.isdir('bin'):
    os.makedirs('bin')
  app = QtWidgets.QApplication(sys.argv)
  window = MyApp()
  window.show()
  sys.exit(app.exec_())
