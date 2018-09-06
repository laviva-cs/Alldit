import sys, os
from PyQt5.QtCore import QObject, pyqtSignal, Qt, QUrl
from PyQt5 import QtCore, QtGui, uic, QtWidgets
from PyQt5.QtWidgets import QAbstractItemView, QDialog, QTreeWidgetItem
from PyQt5.QtGui import QStandardItemModel
import pygame
import urllib.request
import re
from merriam_webster.api import (LearnersDictionary, WordNotFoundException)

qtCreatorFile = "MainDialog.ui"

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class Communicate(QObject):
  setHtml = pyqtSignal(str)


class MyApp(QDialog, Ui_MainWindow):
  def __init__(self):
    QDialog.__init__(self)
    Ui_MainWindow.__init__(self)
    self.setupUi(self)
    self.c = Communicate()
    self.dict = LearnersDictionary('466b3ce3-afa8-452d-b328-1fcb2853116f')
    self.textBrowser.setReadOnly(True)
    self.textBrowser.setOpenLinks(False)
    
    self.treeWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
    self.treeWidget.setAlternatingRowColors(True)
    self.treeWidget.setColumnCount(2)
    self.treeWidget.setHeaderLabels(["Word List", "Description"])
    
    self.initWordLists(self.treeWidget)
    
    self.c.setHtml.connect(self.textBrowser.setHtml)
    
  def list(self, item, column):
    file = ''
    while item is not None:
      file = item.data(0, Qt.DisplayRole) + '/' + file
      item = item.parent()
    
    file = 'lists/' + file[0:-1]
    self.list = file
    f = open(file)
    self.words = f.readlines()
  
  def initWordLists(self, tree):
    pathToItem = {}
    pathToItem['lists'] = tree
    
    for root, dirs, files in os.walk('lists'):
      for dir in dirs:
        item = QTreeWidgetItem(pathToItem[root])
        item.setText(0, dir)
        item.setText(1, "")
        pathToItem[root + os.path.sep + dir] = item
        
      for file in files:
        item = QTreeWidgetItem(pathToItem[root])
        item.setText(0, file)
        item.setText(1, "")

    tree.expandAll()
    for i in range(2):
      tree.resizeColumnToContents(i)
    
  def anchor(self, url):
    url = url.url()
    if url.endswith('wav'):
      audioFile = url[url.rfind('/') + 1:]
      self.playAudio(audioFile, url)
    if 'lookup.dict' in url:
      word = url[url.rfind('/') + 1:]
      word = re.sub(r"[0-9]", "", word)
      word = word.strip()
      self.lookUpEntries([word])
  
  def playAudio(self, audioFile, url):
    file = 'bin/' + audioFile
    if not os.path.isfile(file):
      urllib.request.urlretrieve(url, file)
    pygame.mixer.init()
    pygame.mixer.music.load(file)
    pygame.mixer.music.play()
  
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
