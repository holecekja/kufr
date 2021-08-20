import os
import lib.cached_file
import random
from typing import *

class WordsDatabase:
    def __init__(self, rootPath:str):
        self.wordsFile = lib.cached_file.CachedFile(os.path.join(rootPath, "words.txt"))
        self.usedWordsFile = lib.cached_file.CachedFile(os.path.join(rootPath, "used_words.txt"))

    def extract_next_word(self) -> Optional[str]:
        usedWords = self.usedWordsFile.read()
        availableWords = self.wordsFile.read().copy()

        random.shuffle(availableWords)

        for word in availableWords:
            if word not in usedWords and len(word.strip()) != 0:
                usedWords.append(word)
                self.usedWordsFile.write(usedWords)
                return word

        return None

    def nuke_used_words(self):
        self.usedWordsFile.write([])
