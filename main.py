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
from pymongo import MongoClient

qtCreatorFile = "MainDialog.ui"

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class Communicate(QObject):
  setHtml = pyqtSignal(str)
  next = pyqtSignal()


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
    
    self.treeWidget.itemDoubleClicked.connect(self.selectList)
    self.client = MongoClient('localhost', 27017)
    
    self.initWordLists()
    
    self.c = Communicate()
    self.c.setHtml.connect(self.textBrowser.setHtml)
    self.c.next.connect(self.acceptAnswers)
    
    self.pauseButton.clicked.connect(self.pauseAudit)
    self.backButton.clicked.connect(self.back)
    self.lineEdit.returnPressed.connect(self.acceptAnswers)
    
    self.stackedWidget.setCurrentIndex(0)
    
    self.word = None
    self.list = None
  
  def markWord(self, succeed):
    totalTime = self.accumulatedTime + time.time() - self.startTime
    
    db = self.client.alldit
    
    found = True
    doc = db.words.find_one({"_id": self.word})
    if doc is None:
      found = False
      doc = {
        '_id': self.word,
        "auditCount": 0,
        "failCount": 0,
        "firstAudit": self.startTime,
        "winningStreak": 0,
        "lists": [],
        "audio": [],
        "totalTime": 0
      }
    
    doc['auditCount'] += 1
    doc['failCount'] += 0 if succeed else 1
    doc['lastAudit'] = self.startTime
    doc['winningStreak'] = doc['winningStreak'] + 1 if succeed else 0
    doc['lists'] = list(set(doc['lists'] + [self.list]))
    doc['audio'] = list(set(doc['audio'] + list(self.sounds)))
    doc['totalTime'] += totalTime
    
    if found:
      del doc['_id']
      db.words.replace_one({"_id": self.word}, doc)
    else:
      db.words.insert_one(doc)
    
    found = True
    doc = db.lists.find_one({"_id": self.list})
    if doc is None:
      found = False
      doc = {
        '_id': self.list,
        "auditCount": 0,
        "failCount": 0,
        "totalTime": 0
      }
    
    doc['auditCount'] += 1
    doc['failCount'] += 0 if succeed else 1
    doc['totalTime'] += totalTime
    
    if found:
      del doc['_id']
      db.lists.replace_one({"_id": self.list}, doc)
    else:
      db.lists.insert_one(doc)
  
  def markAsFail(self):
    self.markWord(False)
  
  def markAsSucceed(self):
    self.markWord(True)
  
  def playOneSound(self):
    if len(self.sounds):
      self.playAudio(self.sounds[0])
      self.sounds.rotate(-1)
    
    if not self.hideWord:
      if len(self.sounds):
        self.sounds.pop()
      else:
        self.c.next.emit()
    
    self.timer.setSingleShot(True)
    self.timer.start(15000)
  
  def auditNext(self):
    if len(self.words) == 0:
      self.back()
      QMessageBox().about(self, "Word list complete", "Con!! Word list is COMPLETED. Try another? ")
      return
    
    if self.word is not None:
      if self.wrong > 0:
        self.markAsFail()
      else:
        self.markAsSucceed()
    
    self.lineEdit.setText("")
    self.word = self.words.pop()
    self.remainingReviews -= 1
    self.wrong = 0
    self.startTime = time.time()
    self.accumulatedTime = 0
    
    self.html, self.wordsToHide, self.sounds = self.dict.lookup(self.word)
    if not self.hideWord: self.wordsToHide = []
    
    try: self.wordsToHide = self.wordsToHide.replace("–", "-")
    except: pass
    
    self.sounds = deque(set(self.sounds))
    self.refreshDisplay()
    
    self.playOneSound()
  
  def back(self):
    if self.word is not None and self.wrong >= 0:
      self.markAsFail()
    
    self.setWindowTitle("Alldit")
    self.word = None
    self.list = None
    self.c.setHtml.emit("")
    self.stackedWidget.setCurrentIndex(0)
    self.timer.stop()
    self.initWordLists()
  
  def pauseAudit(self):
    if self.timer.isActive():
      self.timer.stop()
      self.accumulatedTime += time.time() - self.startTime
      self.lineEdit.setDisabled(True)
      self.pauseButton.setText('resume')
    else:
      self.startTime = time.time()
      self.timer.start(15000)
      self.pauseButton.setText('pause')
      self.lineEdit.setDisabled(False)
  
  def acceptAnswers(self):
    text = self.lineEdit.text().strip()
    
    if text in self.wordsToHide:
      self.wordsToHide.remove(text)
    else:
      try:
        answers = set(re.compile(r'\s+').split(text))
      except:
        answers = set()
      
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
    html =  html.replace("–", '-')
    
    if self.hideWord:
      for wordToHide in self.wordsToHide:
        if reveal:
          html = re.sub('([^<"\'])' + '·?'.join(wordToHide).replace('.', '\\.') + '([^>"\'=\\d.])',
                        '\\1<span style="color:red;font-style: italic">%s</span>\\2' % wordToHide, html,
                        flags=re.IGNORECASE)
        else:
          html = re.sub('([^<"\'])' + '·?'.join(wordToHide).replace('.', '\\.') + '([^>"\'=\\d.])', '\\1__??__\\2', html,
                        flags=re.IGNORECASE)
    self.c.setHtml.emit(html)
    
    self.setWindowTitle("Alldit - %d words to review" % (self.remainingReviews) if self.remainingReviews >= 0
                        else "Alldit - %d new words met today" % (-self.remainingReviews) )
  
  def selectList(self, item, column):
    file = ''
    while item is not None:
      file = item.data(0, Qt.DisplayRole) + '/' + file
      item = item.parent()
    
    file = file[0:-1]
    self.list = file
    file = 'lists/' + file
    f = open(file, encoding='utf-8')
    self.words = [re.sub(u"[\u4e00-\u9fa5]+", "", name).strip() for name in f.readlines()]
    f.close()
    self.hideWord = "TOEFL-categories" not in file and "show" not in file
    
    db = self.client.alldit
    
    lastWrong = set()
    lastCorrect = set()
    unmet = set()
    
    for word in self.words:
      doc = db.words.find_one({"_id": word})
      if doc is None:
        unmet.add(word)
      elif doc["winningStreak"] == 0:
        lastWrong.add(word)
      else:
        lastCorrect.add(word)
    
    if len(self.words) <= 0:
      QMessageBox.about(self, "Word list empty", "Word list %s is empty. Try another? " % file)
    else:
      lastCorrect = list(lastCorrect)
      unmet = list(unmet)
      lastWrong = list(lastWrong)
      
      shuffle(lastCorrect)
      shuffle(unmet)
      shuffle(lastWrong)
      
      self.words = lastCorrect + unmet + lastWrong
      self.remainingReviews = len(lastWrong)
      self.stackedWidget.setCurrentIndex(1)
      self.auditNext()
  
  def initWordLists(self):
    tree = self.treeWidget
    tree.clear()
    
    pathToItem = {}
    pathToItem['lists'] = tree
    db = self.client.alldit
    
    for root, dirs, files in os.walk('lists'):
      for dir in dirs:
        item = QTreeWidgetItem(pathToItem[root])
        item.setText(0, dir)
        item.setText(1, "")
        pathToItem[root + os.path.sep + dir] = item
      
      for file in files:
        item = QTreeWidgetItem(pathToItem[root])
        item.setText(0, file)
        
        desc = "New word list! "
        path = (root.replace('\\', '/') + '/' + file)[len('lists/'):]
        
        doc = db.lists.find_one({"_id": path})
        if doc is not None:
          desc = "Total auditing: %d, Total failure: %d, Total time used: %.2f seconds" % \
                 (doc['auditCount'], doc['failCount'], doc['totalTime'])
        
        item.setText(1, desc)
    
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
    file = 'bin/' + url[url.rfind('/') + 1:]
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
  
  def preDownload(self, lists):
    for list in lists:
      f = open('lists/' + list + '.txt', encoding='utf-8')
      words = [name.strip() for name in f.readlines()]
      f.close()
      
      for word in words:
        file = 'bin/' + word + '.xml'
        if not os.path.isfile(file):
          try:
            html, toHide, sounds = self.dict.lookup(word)
            for url in sounds:
              try:
                file = 'bin/' + url[url.rfind('/') + 1:]
                if not os.path.isfile(file):
                  urllib.request.urlretrieve(url, file)
              except:
                print('!! sound %s download failed! for word %s' % (url, word))
          except:
            print('!! word %s failed! in list %s' % (word, list))


if __name__ == "__main__":
  if not os.path.isdir('bin'):
    os.makedirs('bin')
  app = QtWidgets.QApplication(sys.argv)
  window = MyApp()
  # window.preDownload(['CET4&6', 'TOEFL', 'GRE', 'GRE-3000'])
  window.show()
  sys.exit(app.exec_())
