
from lib.rest_server import RESTServer, RESTRequest
import lib.game_state
import lib.authorization


def setupCommonAPI(state:lib.game_state.GameState, server:RESTServer):
    server.add_function("getState", lambda: state.serialize())

def setupGameServer(state:lib.game_state.GameState):
    server = RESTServer(state.config.webUIPort)
    server.enable_file_access(indexFile="game.html")

    setupCommonAPI(state, server)

    # The game UI does not require authorization
    server.add_function("isAuthorized", lambda: {"authorized": True})

    return server


def setupControlsServer(state:lib.game_state.GameState, authorization:lib.authorization.Authorization):
    server = RESTServer(state.config.webControlsPort)
    server.enable_file_access(indexFile="controls.html")

    setupCommonAPI(state, server)

    server.add_function("nextWord", lambda: state.advance_to_next_word())
    server.add_function("skipWord", lambda: state.skip_to_next_word())
    server.add_function("nukeUsedWords", lambda: state.nuke_used_words())

    server.add_function("reset", lambda: state.reset())
    server.add_function("start", lambda: state.start())
    server.add_function("pause", lambda: state.pause())
    server.add_function("resume", lambda: state.resume())

    server.add_function("modifyPoints", lambda points: state.modify_points(int(points)))
    server.add_function("modifyTimer", lambda seconds: state.modify_timer(float(seconds)))

    # Authorization
    server.defaultAuthorizationCheck = lambda request: authorization.is_authorized(request)
    server.add_extended_function("authorize", (lambda request, response, password: {"success": authorization.try_authorize(password, response)}), authorizationCheck=lambda request:True)
    server.add_extended_function("isAuthorized", (lambda request, response: {"authorized": authorization.is_authorized(request)}), authorizationCheck=lambda request: True)

    return server


def main():
    authorization = lib.authorization.Authorization(".")
    state = lib.game_state.GameState(".")

    gameServer = setupGameServer(state)
    print(f"Starting the game server at port {gameServer.port}")

    controlsServer = setupControlsServer(state, authorization)
    print(f"Starting the controls server at port {controlsServer.port}")

    while True:
        try:
            gameServer.serve_once()
            controlsServer.serve_once()
        except KeyboardInterrupt:
            break
        except ConnectionError as ex:
            print(str(ex))

    print("Stopping the server")
    gameServer.server_close()
    controlsServer.server_close()


if __name__ == "__main__":
    main()
