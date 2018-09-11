<h1 align="center">Alldit</h1>

Help you audit words and phrases via English definitions and pronouncations! Comprehensive practices for your English! 

Supported by: Merriam Webster dictionary API &amp; PyQt5 & MongoDB

English | [简体中文](./README-zh_CN.md)

## ✨ Highlights
- 📗 High quality while free for non-commercial purposes Merriam Webster Learner's Dictionary for definition hints and the audios, super easy for learners to understand
- 🥪 Word definition hints and audios, as well as IPA for you to practice word pronouncations and spellings in a PURE ENGLISH WORLD
- ⚙️ Customizable word lists to suit your various needs
- 📈 Comprehensive statistics information for you to schedule your review
- 👀 Beautiful GUI, which is friendly to your eyes
- 🔌 Very brief source code for Python programming practices and super easy to extend

## 🖥 Environment Support
- Windows
- Linux & BSD
- MacOS

## 📦 Install
- Install git, Python 3 and pip 3 on your OS, then
```bash
git clone https://github.com/laviva-cs/Alldit
cd Alldit
pip3 install PyQt5 pymongo pygame
python3 ./main.py
```

## 🔨 Usage
When started, the GUI is shown like the following: 

<p align="center">
<img width="200" src="./screenshots/lists.PNG"/>
</p>


Word lists are located under *lists/*, and you can add arbitrarily many custom word lists. 
All lists are equal, except the word lists under *TOEFL-categories/* and *show/*. 
When these lists are selected, the words are not hidden, and the displayed words will be changed every 15 seconds. 

The statistics are stored in local MongoDB server, and the summaries are displayed for each list. 

Double click a word list, then you will enter the auditing environment. The questions are shown as the word being audited is hidden and replaced by *__??__*
As you may also noticed, the variants, or the inflections of this word is also hidden. 

<p align="center">
<img width="200" src="./screenshots/question.PNG"/>
</p>
<p style="text-align: center;" >  Word "test" and its plural form "tests" is hidden. </p><br/>

To answer the question, you simply enter the hidden words and press enter, and you can separate different words by spaces to answer in batch. 
- The correctly answered words or inflections are revealed. The others are still hidden. 
<p align="center">
<img width="200" src="./screenshots/inflections.PNG"/>
</p>
<p style="text-align: center;" >  After "test" is typped in, the plural form "tests" is still hidden. </p><br/>

- If all hidden words are correctly answered, the auditing moves forward for a new word. 
- Or if the wrong answers add up to 3 times, the hidden words are displayed in red and the auditee should type all the correct answers to get the next word. 
<p align="center">
<img width="200" src="./screenshots/error-reveal.PNG"/>
</p>
<p style="text-align: center;" > 3 errors lead to a reveal for all remained hidden words. </p><br/>

The audios are played every 15 seconds, to help you associate the pronounciation with the word and the word itself. 

😉 Hope you enjoy! Still in beta version, please submit bugs as directed below: ⬇️

## 🤝 Contributing

All contributions are welcomed. You can submit any ideas as [pull requests](https://github.com/laviva-cs/Alldit/pulls) or as [issues](https://github.com/laviva-cs/Alldit/issues) :)

## 🔗 Links and credits
- [Home page](https://github.com/laviva-cs/Alldit)
- [Merriam Webster Dictionary API](https://www.dictionaryapi.com/)
- [MongoDB](https://www.mongodb.com/)
- [PyMongo](https://api.mongodb.com/python/current/)
- [PyQt5](http://pyqt.sourceforge.net/Docs/PyQt5/)
- [Referenced Python API implementation](https://github.com/pfeyz/merriam-webster-api)
- [PyGame](https://www.pygame.org)
- [Yattag](http://www.yattag.org/)
- [Anki](https://ankiweb.net)
