import sys, os
from PyQt5.QtCore import QObject, pyqtSignal, Qt, QUrl
from PyQt5 import QtCore, QtGui, uic, QtWidgets
from PyQt5.QtWidgets import QAbstractItemView, QDialog, QTreeWidgetItem, QMessageBox
import pygame
import urllib.request
import re
from merriam_webster.api import (LearnersDictionary, WordNotFoundException)
from random import shuffle
from collections import deque
import time

qtCreatorFile = "MainDialog.ui"

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class Communicate(QObject):
  setHtml = pyqtSignal(str)


class MyApp(QDialog, Ui_MainWindow):
  def __init__(self):
    QDialog.__init__(self)
    Ui_MainWindow.__init__(self)
    self.setupUi(self)
    
    self.timer = QtCore.QTimer()
    self.timer.timeout.connect(self.playOneSound)
    
    self.dict = LearnersDictionary('466b3ce3-afa8-452d-b328-1fcb2853116f')
    self.textBrowser.setReadOnly(True)
    self.textBrowser.setOpenLinks(False)
    self.textBrowser.anchorClicked.connect(self.anchor)
    
    self.treeWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
    self.treeWidget.setAlternatingRowColors(True)
    self.treeWidget.setColumnCount(2)
    self.treeWidget.setHeaderLabels(["Word List", "Description"])
    
    self.treeWidget.itemDoubleClicked.connect(self.list)
    
    self.initWordLists(self.treeWidget)
    
    self.c = Communicate()
    self.c.setHtml.connect(self.textBrowser.setHtml)
    
    self.pauseButton.clicked.connect(self.pauseAudit)
    self.backButton.clicked.connect(self.back)
    self.lineEdit.returnPressed.connect(self.acceptAnswers)
    
    self.stackedWidget.setCurrentIndex(0)
  
  def markAsFail(self):
    pass  # TODO
  
  def markAsSucceed(self):
    pass  # TODO
  
  def playOneSound(self):
    if len(self.sounds):
      self.playAudio(self.sounds[0])
      self.sounds.rotate(-1)
    self.timer.setSingleShot(True)
    self.timer.start(3000)
  
  def auditNext(self):
    if len(self.words) == 0:
      self.back()
      QMessageBox.about(self, "Word list complete", "Con!! Word list is COMPLETED. Try another? ")
      return
    
    if hasattr(self, 'wrong'):
      if self.wrong > 0:
        self.markAsFail()
      else:
        self.markAsSucceed()
    
    self.lineEdit.setText("")
    self.word = self.words.pop()
    self.wrong = 0
    self.startTime = time.time()
    
    self.html, self.wordsToHide, self.sounds = self.dict.lookup(self.word)
    self.sounds = deque(self.sounds)
    self.refreshDisplay()
    
    self.playOneSound()
  
  def back(self):
    self.c.setHtml.emit("")
    self.stackedWidget.setCurrentIndex(0)
  
  def pauseAudit(self):
    if self.timer.isActive():
      self.timer.stop()
      self.lineEdit.setDisabled(True)
      self.pauseButton.setText('resume')
    else:
      self.timer.start(3000)
      self.pauseButton.setText('pause')
      self.lineEdit.setDisabled(False)
  
  def acceptAnswers(self):
    answers = re.compile(r'\s+').split(self.lineEdit.text())
    for answer in answers:
      if answer in self.wordsToHide:
        self.wordsToHide.remove(answer)
      else:
        self.wrong += 1
    
    self.refreshDisplay(self.wrong >= 3)
    
    if len(self.wordsToHide) == 0:
      self.auditNext()
  
  def refreshDisplay(self, reveal=False):
    html = str(self.html)
    for wordToHide in self.wordsToHide:
      if reveal:
        html = re.sub('·*'.join(wordToHide), '<span style="color:red;font-style: italic">%s</span>' % wordToHide, html)
      else:
        html = re.sub('·*'.join(wordToHide), '__??__', html)
    self.c.setHtml.emit(html)
  
  def list(self, item, column):
    file = ''
    while item is not None:
      file = item.data(0, Qt.DisplayRole) + '/' + file
      item = item.parent()
    
    file = 'lists/' + file[0:-1]
    self.list = file
    f = open(file, encoding='utf-8')
    self.words = [name.strip() for name in f.readlines()]
    f.close()
    
    if len(self.words) <= 0:
      QMessageBox.about(self, "Word list empty", "Word list %s is empty. Try another? " % file)
    else:
      shuffle(self.words)
      self.stackedWidget.setCurrentIndex(1)
      self.auditNext()
  
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
      self.playAudio(url)
    if 'lookup.dict' in url:
      word = url[url.rfind('/') + 1:]
      word = re.sub(r"[0-9]", "", word)
      word = word.strip()
      self.lookUpEntries([word])
  
  def playAudio(self, url):
    audioFile = url[url.rfind('/') + 1:]
    file = 'bin/' + audioFile
    if not os.path.isfile(file):
      urllib.request.urlretrieve(url, file)
    
    try:
      pygame.mixer.init()
      pygame.mixer.music.load(file)
      pygame.mixer.music.play()
    except:
      pass
  
  def lookUpEntries(self, entries):
    self.c.setHtml.emit(
      "<br />————————<br />".join([self.dict.lookup(entry)[0] for entry in entries])
    )


if __name__ == "__main__":
  if not os.path.isdir('bin'):
    os.makedirs('bin')
  app = QtWidgets.QApplication(sys.argv)
  window = MyApp()
  window.show()
  sys.exit(app.exec_())
