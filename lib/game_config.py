
import configparser

class GameConfig:
    def __init__(self, configFilePath):
        config = configparser.ConfigParser()
        config.read(configFilePath)

        self.gameRoundDuration = int(config["game"]["RoundDuration"])

        self.webUIPort = int(config["web"]["UIPort"])
        self.webControlsPort = int(config["web"]["ControlsPort"])

        self.securityPassword = config["security"]["Password"]

        if len(self.securityPassword.strip()) == 0:
            self.securityPassword = None
