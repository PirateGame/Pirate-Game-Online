from flask import Flask, render_template, request, jsonify, redirect
from flask_socketio import SocketIO, emit
import random, string
import numpy as np
import game as game


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

#Make the app
app = Flask(__name__)

print("-" * 50)
print("Version 2 Main Development Branch")
print("If the program crashes, check the known issues section on our Github. If the crash doesn't appear to be there, please add it!")
print("-" * 50)

#Bootstrap old games
print("Input ENTER to purge, otherwise - bootstrapped games won't be purged.")
shallI = str(input())
if shallI == "":
    game.bootstrap({"purge":True})
else:
    game.bootstrap({"purge":False})



def auth(playerName, gameName, code):
    try:
        secret = game.clientInfo({"gameName":gameName, "clientName":playerName})["about"]["authCode"]
    except Exception as e:
        print("FAIL AUTH. exception:", e)
        return False
    if code == secret:
        return True
    else:
        print("FAIL AUTH.", playerName, secret, code)
        return False

def isHost(gameName, playerName):
    secret = game.gameInfo(gameName)["about"]["admins"][0]["name"]
    if playerName == secret:
        return True
    else:
        return False


### SOCKET ROUTES...

@socketio.on('connect')
def test_connect():
    print("user has connected")
    emit('my response', {'data': 'Connected'})


@socketio.on('createGame')
def createGame(data):
    print("create_game requested")
    gameName = data["gameName"]
    ownerName = data["ownerName"]
    Sizex = int(data["Sizex"])
    Sizey = int(data["Sizey"])
    isPlaying = data["isHostPlaying"]
    playerCap = 12 #DEFAULT (must be the same as what's on the website)
    debug=True
    gridDim = (Sizex, Sizey)
    #This sets the standard decision time
    turnTime = 30
    nameUniqueFilter = None
    nameNaughtyFilter = None
    quickplay = True

    if gameName is None:
        gameName = ''
    if ownerName is None:
        ownerName = ''
    for char in gameName:
        if char not in string.ascii_letters:
            data = {"error": "Game name can only contain letters"}
            emit("response", data)

    for char in ownerName:
        if char not in (string.ascii_letters + ' '):
            data = {"error": "Your name can only contain letters"}
            emit("response", data)

    gameAbout = {"gameName":gameName, "admins":[{"name":ownerName, "type":"human"}], "isSim":False, "quickplay":quickplay, "debug":debug, "gridDim":gridDim, "turnTime":turnTime, "playerCap":playerCap, "nameUniqueFilter":nameUniqueFilter, "nameNaughtyFilter":nameNaughtyFilter}
    if not isPlaying:
        gameAbout["admins"] = [{"name":ownerName, "type":"spectator"}]
    out = game.makeGame(gameAbout) ###CREATING THE GAME.
    if not out:
        data = {"error": "could not create game"}
        emit("response", data)
    else:
        gameName = out["gameName"]
        admins = out["admins"]

    join_room(gameName)
    alterClients(gameName, [ownerName], {"socket":request.sid})

    authcode = game.clientInfo({"gameName":gameName, "clientName":admins[0]["name"]})["about"]["authCode"]
    
    data = {"error": False, "authcode": authcode, "playerName":admins[0]["name"], "gameName":gameName}
    emit("response", data)


@socketio.on('joinGame')
def joinGame(data):
    gameName = data["gameName"]
    playerName = data["playerName"]


    if len(gameName)<1:
        data = {"error": "Please enter a game name"}
        emit("response", data)
    if len(playerName)<1:
        data = {"error": "please enter a name"}
        emit("response", data)


    for char in gameName:
        if char not in string.ascii_letters:
            data = {"error": "Game name can only contain letters"}
            emit("response", data)

    for char in playerName:
        if char not in (string.ascii_letters + ' '):
            data = {"error": "Your name can only contain letters"}
            emit("response", data)


    if game.joinLobby(gameName, [{"name":playerName, "type":"human"}]):
        authcode = game.clientInfo({"gameName":gameName, "clientName":playerName})["about"]["authCode"]
        join_room(gameName)
        alterClients(gameName, [playerName], {"socket":request.sid})
        data = {"error": False, "authcode": authcode}
        emit("response", data)
    else:
        data = {"error": "Something went wrong"}
        emit("response", data)


@socketio.on('getBarTiles')
def getBarTiles(data): #This is used for building the list of tiles that are going to be displayed in the side board for the user to drag across.
    gameName = data["gameName"]
    playerName = data["playerName"]
        
    data = game.gameInfo(gameName)["gridTemplate"]["tileNums"]
    
    return jsonify(game.serialReadBoard(gameName, playerName, positions=False))

@socketio.on('getGridDim')
def getGridDim(data):
    gameName = data["gameName"]
    playerName = data["playerName"]

    data = game.gameInfo(gameName)["about"]["gridDim"]
    out = {"x": data[0], "y": data[1]}

    return jsonify(out)

@socketio.on('startGame')
def startGame(data):
    gameName = data["gameName"]
    playerName = data["playerName"]
    authCode = data["authCode"]

    if auth(playerName, gameName, authCode):
        if isHost(gameName, playerName):
            if game.start(gameName):
                game.turnHandle(gameName)
                data = ({"error":False})
                emit("response", data)
            else:
                data = ({"error":"game not found"})
                emit("response", data)
        else:
            data = ({"error":"You can't do this"})
            emit("response", data)
    else:
        data = ({"error": "Authentication failed"})
        emit("response", data)


@socketio.on('submitResponse')
def submitResponse(data):
    gameName = data["gameName"]
    playerName = data["playerName"]
    authCode = data["authCode"]
    choice = data["choice"]

    game.FRONTresponse(gameName, playerName, choice)

    data = {"error": False}
    emit("response", data)

@socketio.on('modifyGame')
def modifyGame(data):
    gameName = data["gameName"]
    playerName = data["playerName"]
    authCode = data["authCode"]
    naughty = data["naughty"]
    similar = data["similar"]
    DecisionTime = data["DecisionTime"]
    randmoiseOnly = data["randomiseOnly"]
    playerCap = int(data["playerLimit"])

    if auth(playerName, gameName, authCode):
        if isHost(gameName, playerName):
            game.alterGames([gameName], {"nameUniqueFilter":similar, "nameNaughtyFilter":naughty, "turnTime":DecisionTime, "playerCap": playerCap})
            data = ({"error": False})
            emit("response", data)
        else:
            data = ({"error": "You do not have permission to do this"})
            emit("response", data)

    else:
        data = ({"error": "Authentication failed"})
        emit("response", data)


#Set team/ship
@socketio.on('setTeam')
def setTeam(data):
    gameName = data["gameName"]
    playerName = data["playerName"]
    authCode = data["authCode"]
    Captain = data["Captain"]
    ship = ["A","B","C"][data["Ship"]]

    if auth(playerName, gameName, authCode):
        game.alterClients(gameName, [playerName], {"row": str(ship)}) #Ship
        game.alterClients(gameName, [playerName], {"column": str(Captain)}) #captain
        data = ({"error": False})
        emit("response", data)
    else:
        data = ({"error": "Authentication failed"})
        emit("response", data)
    return


@socketio.on('saveBoard')
def saveBoard(data):
    gameName = data["gameName"]
    playerName = data["playerName"]
    authCode = data["authCode"]
    board = data["board"]

    if auth(playerName, gameName, authCode):
        if game.serialWriteBoard(gameName, playerName, board):
            game.readyUp(gameName, playerName)
            data = {"error": False}
            emit("response", data)
        else:

            data = {"error": "board did not fit requirements"}
            emit("response", data)
    else:
        data = ({"error": "Authentication failed"})
        emit("response", data)


@socketio.on('randomiseBoard')
def randomiseBoard(data):
    gameName = data["gameName"]
    playerName = data["playerName"]
    authCode = data["authCode"]

    if auth(playerName, gameName, authCode):
        game.randomiseBoard(gameName, playerName)

        board = game.serialReadBoard(gameName, playerName)
        return jsonify(board)
    else:
        data = ({"error": "Authentication failed"})
        emit("response", data)

@socketio.on('getBoard')
def getBoard(data):
    gameName = data["gameName"]
    playerName = data["playerName"]
    authCode = data["authCode"]

    if auth(playerName, gameName, authCode):
        board = game.serialReadBoard(gameName, playerName)
        return jsonify(board)
    else:
        data = ({"error": "Authentication failed"})
        emit("response", data)
    



@socketio.on('amIHost')
def amIHost(data):
    gameName = data["gameName"]
    playerName = data["playerName"]
    authCode = data["authCode"]

    if auth(playerName, gameName, authCode):
        if isHost(gameName, playerName):
            data = ({"error": False})
            emit("response", data)
        else:
            data = ({"error": "You do not have permission to do this"})
            emit("response", data)

    else:
        data = ({"error": "Authentication failed"})
        emit("response", data)


@socketio.on('kickPlayer')
def kickPlayer(data):
    gameName = data["gameName"]
    playerName = data["playerName"]
    authCode = data["authCode"]
    playerToKick = data["playerToKick"]
    
    if auth(playerName, gameName, authCode):
        if isHost(gameName, playerName):
            if game.leave(gameName, [playerToKick]):
                print("hopefully that kicked a player?")
                data = ({"error": False})
                emit("response", data)
            else:
                data = ({"error": "Player kick failed"})
                emit("response", data)
        else:
            data = ({"error": "You do not have permission to do this"})
            emit("response", data)

    else:
        data = ({"error": "Authentication failed"})
        emit("response", data)

@socketio.on('addAI')
def addAI(data):
    gameName = data["gameName"]
    playerName = data["playerName"]
    authCode = data["authCode"]
    
    if auth(playerName, gameName, authCode):
        if isHost(gameName, playerName):
            if game.joinLobby(gameName=gameName, clients=[{"name":"", "type":"AI"}]):
                data = ({"error": False})
                emit("response", data)
            else:
                data = ({"error": "adding AI failed"})
                emit("response", data)
        else:
            data = ({"error": "You do not have permission to do this"})
            emit("response", data)

    else:
        data = ({"error": "Authentication failed"})
        emit("response", data)



#Functions that send the client data to update them.



def sendPlayerListToClients(gameName):
    session = game.gameInfo(gameName)
    if session == False:
        data = {"error": "game not found"}
        emit("response", data, room=gameName)
    
    clientList = game.listClients(gameName)
    toSend = []
    for clientName,about in clientList.items():
        text = str(about["type"]) + ": " + str(clientName)
        toSend.append(text)
    data = {"names":toSend}

    data.update({"error": False})
    emit("response", data, room=gameName)



def SendGameStatusToClient(gameName, data):
    emit("status", data, room=gameName)



def sendUpdateToClient(gameName, playerName, group, data):
    if group:
        emit("event", data, room=gameName)
    else:
        emit("event", data, room=game.clientInfo({"gameName":gameName, "clientName":playerName})["about"]["socket"])


def turnUpdate(gameName, playerName):

    tiles = game.gameInfo(gameName)["about"]["chosenTiles"]
    width = game.gameInfo(gameName)["about"]["gridDim"][1]
    ids = []
    #print(tiles)
    for turn in tiles:
        ids.append((tiles[turn][0] * width) + tiles[turn][1])
    
    
    money = game.clientInfo({"gameName":gameName, "clientName": playerName})["about"]["money"]
    bank = game.clientInfo({"gameName":gameName, "clientName": playerName})["about"]["bank"]
    shield = game.clientInfo({"gameName":gameName, "clientName": playerName})["about"]["shield"]
    mirror = game.clientInfo({"gameName":gameName, "clientName": playerName})["about"]["mirror"]

    Events = game.sortEvents(gameName, "timestamp", game.filterEvents(gameName, {}, ['"' + playerName + '"' + ' in event["whoToShow"]']))
    descriptions = game.describeEvents(gameName, unshownEvents)
    data = {"error": False, "events": descriptions, "questions": questions, "ids":ids, "money": money, "bank": bank, "shield": shield, "mirror": mirror, "events": descriptions}
    
    emit("turn", data, room=game.clientInfo({"gameName":gameName, "clientName":playerName})["about"]["socket"])


if __name__ == "__main__":
    socketio.run(app, debug=True, host="localhost")

"""def tryNewTurn(gameName):
    rQ = game.getRemainingQuestions(gameName)
    fE = game.filterEvents(gameName, {}, ['len(event["whoToShow"]) > 0'])
    tN = game.gameInfo(gameName)["about"]["turnNum"]
    if len(rQ) == 0 and len(fE) == 0 and tN != -1:
        #print("Starting next round as all events have been shown and there are no remaining questions.")
        game.turnHandle(gameName)
        return True
    else:
        #print("A new turn can't be triggered as there are still questions to be answered or events to be shown.")
        #print(rQ, fE, tN)
        return False"""