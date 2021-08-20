import lib.game_config
import lib.words_database

from typing import *
import os
import json
import time

class GameState:
    def __init__(self, rootPath:str):
        self.config = lib.game_config.GameConfig(os.path.join(rootPath, "config.ini"))
        self.words = lib.words_database.WordsDatabase(rootPath)
        self.currentWord:Optional[str] = None
        self.started = False
        self.points:int = 0
        self.gameStart:float = 0.0
        self.paused:bool = False
        self.pausedAt:float = 0.0

    def advance_to_next_word(self):
        if self.started and (not self.paused or not self.currentWord) and not self._expired():
            # Only add the point if there was a word (i.e. we didn't run out)
            if self.currentWord:
                self.points += 1

            self._fetch_next_word()

    def skip_to_next_word(self):
        if self.started and (not self.paused or not self.currentWord) and not self._expired():
            self._fetch_next_word()

    def _fetch_next_word(self):
        self.currentWord = self.words.extract_next_word()

        # If we couldn't find another word, we'll pause the game automatically
        if not self.currentWord:
            self.pause()
        else:
            self.resume()

    def reset(self):
        self.points = 0
        self.currentWord = None
        self.gameStart = 0.0
        self.started = False
        self.paused = False

    def start(self):
        if not self.started:
            self.started = True
            self.gameStart = time.time()
            self.skip_to_next_word()

    def pause(self):
        if not self.paused:
            self.paused = True
            self.pausedAt = time.time()

    def resume(self):
        if self.paused:
            # Adjust the start time with the time duration we were paused for
            elapsed = time.time() - self.pausedAt
            self.gameStart += elapsed
            self.paused = False

    def modify_points(self, amount:int):
        self.points += amount

    def modify_timer(self, amount:float):
        self.gameStart += amount

    def nuke_used_words(self):
        self.words.nuke_used_words()

    def serialize(self):
        return {
            "word": self.currentWord if self.currentWord is not None else "",
            "points": self.points,
            "started": self.started,
            "startTime": self.gameStart,
            "roundDuration": self.config.gameRoundDuration,
            "paused": self.paused,
            "pausedAt": self.pausedAt,
            "status": self._get_status_message(),
        }

    def _elapsed(self):
        return (self.pausedAt if self.paused else time.time()) - self.gameStart

    def _expired(self):
        return self.started and self._elapsed() > self.config.gameRoundDuration

    def _get_status_message(self):
        if not self.started:
            return "Press \"Start\" to start a new game."

        if self._expired():
            return "Game over! Use \"Reset\" to prepare for a new game."

        if self.currentWord is None:
            return "No unused words available. Either add more words or reset the used words. Then press NEXT/SKIP to resume the game."

        if self.paused:
            return "Game paused. Resume/reset to continue"

        return "OK"



