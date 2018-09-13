# -*- encoding: utf-8 -*-
import os
import re
import urllib
import xml.etree.cElementTree as ElementTree

from abc import ABCMeta, abstractmethod, abstractproperty
from urllib.parse import quote, quote_plus
from urllib.request import urlopen
from yattag import Doc


class WordNotFoundException(KeyError):
  def __init__(self, word, suggestions=None, *args, **kwargs):
    self.word = word
    if suggestions is None:
      suggestions = []
    self.suggestions = suggestions
    message = "'{0}' not found.".format(word)
    if suggestions:
      message = "{0} Try: {1}".format(message, ", ".join(suggestions))
    KeyError.__init__(self, message, *args, **kwargs)


class InvalidResponseException(WordNotFoundException):
  def __init__(self, word, *args, **kwargs):
    self.word = word
    self.suggestions = []
    message = "{0} not found. (Malformed XML from server).".format(word)
    KeyError.__init__(self, message, *args, **kwargs)


class InvalidAPIKeyException(Exception):
  pass


class MWApiWrapper(metaclass=ABCMeta):
  """ Defines an interface for wrappers to Merriam Webster web APIs. """
  
  def __init__(self, key=None, urlopen=urlopen):
    """ key is the API key string to use for requests. urlopen is a function
    that accepts a url string and returns a file-like object of the results
    of fetching the url. defaults to urllib2.urlopen, and should throw """
    self.key = key
    self.urlopen = urlopen
  
  @abstractproperty
  def base_url():
    """ The api enpoint url without trailing slash or format (/xml).

    """
    pass
  
  @abstractmethod
  def parse_xml(self, root, word):
    pass
  
  def request_url(self, word):
    """ Returns the target url for an API GET request (w/ API key).

    >>> class MWDict(MWApiWrapper):
    ...     base_url = "mw.com/my-api-endpoint"
    ...     def parse_xml(): pass
    >>> MWDict("API-KEY").request_url("word")
    'mw.com/my-api-endpoint/xml/word?key=API-KEY'

    Override this method if you need something else.
    """
    
    if self.key is None:
      raise InvalidAPIKeyException("API key not set")
    qstring = "{0}?key={1}".format(quote(word), quote_plus(self.key))
    return ("{0}/xml/{1}").format(self.base_url, qstring)
  
  def lookup(self, word):
    file = 'bin/' + word + '.xml'
    if not os.path.isfile(file):
      url = self.request_url(word)
      urllib.request.urlretrieve(url, file)
    f = open(file, encoding='utf-8')
    data = f.read()
    data = data.replace("*encenc*es</if>", "*enc*es</if>")
    f.close()
    
    try:
      root = ElementTree.fromstring(data)
    except ElementTree.ParseError:
      if re.search("Invalid API key", data):
        raise InvalidAPIKeyException()
      data = re.sub(r'&(?!amp;)', '&amp;', data)
      try:
        root = ElementTree.fromstring(data)
      except ElementTree.ParseError:
        raise InvalidResponseException(word)
    
    suggestions = root.findall("suggestion")
    if suggestions:
      suggestions = [s.text for s in suggestions]
      suggested = suggestions[0]
      if suggested == word:
        os.remove(file)
      return self.lookup(suggested)
    
    return self.parse_xml(root, word)


class LearnersDictionary(MWApiWrapper):
  base_url = "http://www.dictionaryapi.com/api/v1/references/learners"
  
  def parse_xml(self, root, word):
    entries = root.findall("entry")
    results = list([self.generateEntry(entry) for entry in entries])
    
    shouldBeHead = None
    i = 0
    for entry in entries:
      if entry.get("id") == word:
        shouldBeHead = results[i]
      i += 1
    
    if shouldBeHead:
      results.remove(shouldBeHead)
      results.insert(0, shouldBeHead)
    
    try:
      return "<br />————————<br />".join([result[0] for result in results]), results[0][1], results[0][2]
    except:
      return "No dictionary entries found for %s! " % (word), [], []
  
  def generateEntry(self, entry):
    doc, tag, text = Doc().tagtext()
    
    wordsToHide = []
    sounds = []
    
    functionColors = {
      'noun': '#cc44aa',
      'verb': '#006400',
      'pronoun': '#00d9ff',
      'adjective': '#cd7830',
      'adverb': '#4adf1c',
      'preposition': '#147a8b',
      'conjunction': '#ffccdd'
    }
    
    infoLable = ('span', 'font-weight:bold;color:#ffffff; background-color: #8b7a14')
    bold = ('span', 'font-weight:bold')
    boldDiv = ('div', 'font-weight:bold')
    plain = ('span', 'font-weight:normal')
    plainDiv = ('div', 'font-weight:normal')
    italic = ('i', '')
    plainIndented = ('div', 'background-color:rgb(253, 254, 236);font-weight:normal;margin-left:10px')
    
    def build_sound_url(fragment):
      base_url = "http://media.merriam-webster.com/soundc11"
      prefix_match = re.search(r'^([0-9]+|gg|bix)', fragment)
      if prefix_match:
        prefix = prefix_match.group(1)
      else:
        prefix = fragment[0]
      return "{0}/{1}/{2}".format(base_url, prefix, fragment)
    
    def build_illustration_url(fragment):
      base_url = "http://www.learnersdictionary.com/art/ld"
      fragment = re.sub(r'\.(tif|eps)', '.gif', fragment)
      return "{0}/{1}".format(base_url, fragment)
    
    def comma():
      with tag('span'):
        text(', ')
    
    def br():
      with tag('br'): pass
    
    def space():
      text(' ')
    
    def plainText(t):
      text(t.replace("*", '·') if t else "")
    
    def pad(t):
      space()
      plainText(t)
      space()
    
    def workOnSound(s):
      for wav in s:
        url = build_sound_url(wav.text)
        with tag('a', href=url):
          with tag('img',
                   src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAQAAAC1QeVaAAAAi0lEQVQokWNgQAYyQFzGsIJBnwED8DNcBpK+DM8YfjMUokqxMRxg+A9m8TJsBLLSEFKMDCuBAv/hCncxfGWQhUn2gaVAktkMXkBSHmh0OwNU8D9csoHhO4MikN7BcAGb5H+GYiDdCTQYq2QubkkkY/E6CLtXdiJ7BTMQMnAHXxFm6IICvhwY8AYQLgCw2U9d90B8BAAAAABJRU5ErkJggg=='):
            pass
        space()
    
    def workOnArt(a):
      pass
    
    def workOnFunctionLabel(fl):
      space()
      with tag('span',
               style='font-size:medium; color:#ffffff; background-color: ' + functionColors.get(fl.text, "#000000")):
        plainText('[ ' + fl.text + ' ]')
      space()
    
    def workOnReference(node):
      if node.text is None: return
      with tag('a', href='http://lookup.dict/' + node.text):
        plainText(node.text)
        
        for child in node:
          traverse(child)
    
    tagTransform = {
      'inf': ('sub', ''),
      'sup': ('span', 'font-size:'),
      'it': italic,
      'dx': italic,
      'cat': italic,
      
      'dxt': workOnReference,
      'sx': workOnReference,
      'sxn': ('sup', ''),
      'dxn': ('sup', ''),
      
      'il': infoLable,
      'pvl': infoLable,
      'vl': infoLable,
      'sl': infoLable,
      
      'gram': infoLable,
      
      'vr': plain,
      'in': plain,
      'def': plainDiv,
      'ca': plain,
      'tag': plain,
      'sd': plain,
      'vi': plainIndented,
      
      'if': bold,
      'pva': bold,
      'va': bold,
      'phrase': bold,
      'pr': bold,
      'dt': boldDiv,
      
      'sound': workOnSound,
      'art': workOnArt,
      'fl': workOnFunctionLabel,
      
      'sn': ('span', 'font-weight:600;color:#cc0000'),
      
      'bnote': ('div', 'font-weight:600; background-color: #8b7a1455'),
      'snote': ('p', 'background-color: #8b7a14; margin-left:10px'),
      'entry': ('div', 'margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; '
                       'text-indent:0px;font-family:\'SimSun\'; font-size:9pt; font-weight:normal; font-style:normal'),
      
      'hw': bold,
      'dro': ('p', 'margin-left:10px'),
      'uro': ('p', 'margin-left:10px'),
      'un': ('div', 'margin-left:10px'),
    }
    
    beforeTag = {
      'sn': lambda: br(),
      'dxnl': lambda: br(),
    }
    
    afterTag = {
      'dxt': lambda: space(),
    }
    
    frontOfTag = {
      'un': lambda: plainText('\n--'),
      'dx': lambda: plainText('\n--'),
      'ca': lambda: plainText('\n--'),
      'sx': lambda: plainText('sym: '),
      'snote': lambda: doc.asis(' &#x269d; '),
      'pr': lambda: plainText('/'),
      'vr': lambda: plainText('('),
      'sl': lambda: plainText('('),
      'gram': lambda: plainText('[ '),
    }
    
    rearOfTag = {
      'pr': lambda: plainText('/'),
      'vr': lambda: plainText(')'),
      'sl': lambda: plainText(')'),
      'gram': lambda: plainText(' ]'),
    }
    
    alias = {
      'sp': 'pr',
      'altpr': 'pr',
      'sgram': 'gram',
      'wsgram': 'gram',
      'phrasev': 'phrase',
      'dre': 'hw',
      'ure': 'hw',
      'rsl': 'sl',
      'ssl': 'sl',
      'hsl': 'sl',
      'slb': 'sl',
      'cl': 'sl',
      'ahw': 'hw',
      'sin': 'in',
      'cx': 'dx',
      'ct': 'dt',
      'dxnl': 'dx',
      'utxt': 'dt',
    }
    
    def traverse(root):
      lookup = alias.get(root.tag, root.tag)
      
      before = beforeTag.get(root.tag, beforeTag.get(lookup, lambda: None))
      after = afterTag.get(root.tag, afterTag.get(lookup, lambda: None))
      front = frontOfTag.get(root.tag, frontOfTag.get(lookup, lambda: None))
      rear = rearOfTag.get(root.tag, rearOfTag.get(lookup, lambda: None))
      
      before()
      
      trans = tagTransform.get(lookup, tagTransform.get(root.tag, ('i', 'background-color: #ff0000')))
      if callable(trans):
        trans(root)
      else:
        with tag(trans[0], style=trans[1]):
          front()
          plainText(root.text)
          for child in root:
            traverse(child)
            plainText(child.tail)
          rear()
      
      after()
    
    traverse(entry)
    
    hw = entry.find('hw')
    if hw is not None:
      wordsToHide.append(re.sub('\\*', '', hw.text).strip())
    
    s = entry.find('sound')
    if s is not None:
      for wav in s.findall('wav'):
        sounds.append(build_sound_url(wav.text))
    
    for inflection in entry.findall('in'):
      word = inflection.find('if')
      if word is not None:
        wordsToHide.insert(0, re.sub('\\*', '', word.text).strip())
      
      s = entry.find('sound')
      if s is not None:
        for wav in s.findall('wav'):
          sounds.append(build_sound_url(wav.text))
    
    return doc.getvalue(), wordsToHide, sounds
