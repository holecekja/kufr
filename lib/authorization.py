import lib.game_config

from typing import *
import os
import uuid

class Authorization:
    def __init__(self, rootPath:str):
        self.config = lib.game_config.GameConfig(os.path.join(rootPath, "config.ini"))
        self.authorizedSessions = set()

    def try_authorize(self, password, response) -> bool:
        if self.config.securityPassword is None or self.config.securityPassword == password:
            sessionID = str(uuid.uuid4())
            self.authorizedSessions.add(sessionID)
            response.add_header('Set-Cookie', "session="+sessionID)
            return True
        else:
            return False

    def is_authorized(self, request) -> bool:
        if self.config.securityPassword is None:
            return True
        else:
            session = request.cookies.get("session")
            return session is not None and session.value in self.authorizedSessions

