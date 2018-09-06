# -*- encoding: utf-8 -*-
import os
import sys

from merriam_webster.api import (LearnersDictionary, WordNotFoundException)


def lookup(dictionary_class, key, query):
  dictionary = dictionary_class(key)
  result = dictionary.lookup(query)
  print(str(result))


if __name__ == "__main__":
  learnkey = (os.getenv("MERRIAM_WEBSTER_LEARNERS_KEY"))
  if not (learnkey):
    print("set the MERRIAM_WEBSTER_LEARNERS_KEY environmental variable"
          " to your Merriam-Webster "
          "API keys in order to perform lookups.")
  if learnkey:
    for query in sys.argv[1:]:
      lookup(LearnersDictionary, learnkey, query)
