import random, string, time
import numpy as np
import gridGenerator
import time
import analyse

np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning) 
games = {}
#maxGameLength = 55 + (10 * gridSize) + (90 * (howManyEachAction * clientCount))

### I may have stole this from https://stackoverflow.com/a/25588771 and edited it quite a bit. -used to make printing pretty of course! ###

class prettyPrinter():
    def flattenList(self, t):
        flat_list = [item for sublist in t for item in sublist]
        return flat_list

    def format__1(self, digits,num):
        if digits<len(str(num)):
            raise Exception("digits<len(str(num))")
        return ' '*(digits-len(str(num))) + str(num)
    def printmat(self, arr,row_labels, col_labels): #print a 2d numpy array (maybe) or nested list
        max_chars = max([len(str(item)) for item in self.flattenList(arr)+col_labels]) #the maximum number of chars required to display any item in list
        if row_labels==[] and col_labels==[]:
            for row in arr:
                print('[%s]' %(' '.join(self.format__1(max_chars,i) for i in row)))
        elif row_labels!=[] and col_labels!=[]:
            rw = max([len(str(item)) for item in row_labels]) #max char width of row__labels
            print('%s %s' % (' '*(rw+1), ' '.join(self.format__1(max_chars,i) for i in col_labels)))
            for row_label, row in zip(row_labels, arr):
                print('%s [%s]' % (self.format__1(rw,row_label), ' '.join(self.format__1(max_chars,i) for i in row)))
        else:
            raise Exception("This case is not implemented...either both row_labels and col_labels must be given, or neither.")

### CLASSES USED TO DESCRIBE GAMES AND CLIENTS ###

class gameHandler():
    def __init__(self, gameName, ownerID, gridDim, turnTime):
        def updateBOARDS(whatToUpdate):
            BOARDS = np.load("boards.npy", allow_pickle=True).tolist()
            if whatToUpdate[0] == None:
                BOARDS[self.about["name"]][1] = whatToUpdate[1]
            elif whatToUpdate[1] == None:
                BOARDS[self.about["name"]][0] = whatToUpdate[0]
            else:
                BOARDS[self.about["name"]] = whatToUpdate
            np.save("boards.npy", BOARDS)
        
        maxEstTime = turnTime * gridDim[0] * gridDim[1]
        self.about = {"name": gameName, "turnTime":turnTime, "maxEstTime":maxEstTime, "ownerID": ownerID, "gridDim":gridDim, "turnNum":-1, "tileOverride":False, "chosenTiles":[], "clients":{}}
        self.about["eventHandler"] = analyse.gameEventHandler(self)
        self.about["estimateHandler"] = analyse.gameEstimateHandler(self)
        self.tempGroupChoices = []
        

        BOARDS = np.load("boards.npy", allow_pickle=True).tolist()
        if self.about["name"] not in BOARDS:
            updateBOARDS([self.about, {}])
            print(self.about["name"], "@@@@ CREATED by client", str(ownerID), "with", gridDim, "dimensions.")
        else:
            print(self.about["name"], "@@@@ RECOVERED by client", str(ownerID), "with", gridDim, "dimensions.")
        
        self.pP = prettyPrinter()

    def genNewTile(self):
        options = []
        for x in range(self.about["gridDim"][0]):
            for y in range(self.about["gridDim"][1]):
                if (x,y) not in self.about["chosenTiles"]:
                    options.append((x,y))
        return random.choice(options)
    
    def whoIsOnThatLine(self, rOrC, coord):
        victims = []
        for client in self.about["clients"]:
            if rOrC == 1:
                if self.about["clients"][client].about["column"] == coord:
                    victims.append(client)
            else:
                if self.about["clients"][client].about["row"] == coord:
                    victims.append(client)
        return victims
    
    def groupDecisionAdd(self, event, choice):
        if event["event"] == "D":
                self.tempGroupChoices.append(choice)
    def groupDecisionConclude(self, event):
        if event["event"] == "D":
            if self.tempGroupChoices.count("mirror") > 1: #Mirror
                rOrC = event["other"][0]
                if rOrC == 1:
                    choice = event["source"].about["column"]
                else:
                    choice = event["source"].about["row"]
                victims = self.game.whoIsOnThatLine(rOrC, choice)
                self.about["events"].append(self.game.about["eventHandler"].make({"public":True, "event":whatHappened, "source":random.choice(event["targets"]), "targets":[self.game.about["clients"][victim] for victim in victims], "other":[rOrC, choice]})) #EVENT HANDLER
                for victim in victims:
                    self.game.about["clients"][victim].beActedOn("D", self.about) ###ACT
            elif self.tempGroupChoices.count("shield") > 1: #Shield
                pass
            else:
                for client in self.tempGroupChoices:
                    self.about["clients"][client].forceActedOn("D")
            self.tempGroupChoices = []

    def newTurn(self):
        BOARDS = np.load("boards.npy", allow_pickle=True).tolist()
        if self.about["tileOverride"] == False:
            notUnique = True
            while notUnique:
                newTile = (self.randomCoords[self.about["turnNum"]-1][0], self.randomCoords[self.about["turnNum"]-1][1]) #x,y
                if newTile not in self.about["chosenTiles"]:
                    notUnique = False
        else:
            newTile = self.about["tileOverride"]
            self.about["tileOverride"] = False
        self.about["chosenTiles"].append(newTile)
        print(self.about["name"], "@@ ------------------------ Turn", self.about["turnNum"] + 1, "--- Tile", (newTile[0] + 1, newTile[1] + 1), "------------------------")

        actions = []
        for client in self.about["clients"]:
            self.about["clients"][client].logScore()
            self.about["clients"][client].act(BOARDS[self.about["name"]][1][client][newTile[1]][newTile[0]])
        if len(self.tempGroupChoices) > 0:
            whatThatLineDoes()
            
            #actions.append(BOARDS[self.gameIDNum][client][newTile[0]][newTile[1]])
        #for a in range(len(actions)):
            #if actions[a] == #B for bomb, K for kill, so on...
            #This needs to be ASYNC so that whenever a client response comes in on what they've chosen to do, it's executed immediately
            #Each client's turn should be processed based on the new tile coordinate, and if it requires user input or not, broadcasted back to the Vue server to be presented to the clients.
        #A signal should be emitted here to the Vue Server holding the new turn's tile coordinates, for each vue client to process what on their grid
    def status(self):
        return self.about

    def leaderboard(self):
        clientByScore = {}
        for client in self.about["clients"]:
            clientByScore[client] = self.about["clients"][client].about["scoreHistory"][-1]
        out = {}
        for client in sorted(clientByScore, key=clientByScore.get, reverse=True):
            out[client] = {"score":clientByScore[client], "money":self.about["clients"][client].about["money"], "bank":self.about["clients"][client].about["bank"]}
        return out
    
    def joinLobby(self, clients):
        BOARDS = np.load("boards.npy", allow_pickle=True).tolist()
        #BOARDS[self.gameIDNum][client] = [[]] #whatever the fuck the vue server sent back about each user's grid
        out = []
        for client, about in clients.items():
            try:
                gr = gridGenerator.makeGrid(self.about["gridDim"])
                self.about["clients"][client] = clientHandler(self, client, about)
                if about["isPlaying"]:
                    BOARDS[self.about["name"]][1][client] = gr[0]
                out.append(True)
            except Exception as e:
                out.append(e)
        BOARDS = np.save("boards.npy", BOARDS)
        return out
    
    def exit(self, clients):
        BOARDS = np.load("boards.npy", allow_pickle=True).tolist()
        #BOARDS[self.gameIDNum][client] = [[]] #whatever the fuck the vue server sent back about each user's grid
        out = []
        for client in clients:
            try:
                del self.about["clients"][client]
                del BOARDS[self.about["name"]][1][client]
                out.append(True)
            except:
                out.append(False)
        BOARDS = np.save("boards.npy", BOARDS)
        return out

    def printBoards(self):
        BOARDS = np.load("boards.npy", allow_pickle=True).tolist()
        for client in self.about["clients"]:
            print(self.about["name"], "@ Client", self.about["clients"][client].about["name"], "has stats", self.about["clients"][client].about, "and board...")
            row_labels = [str(y+1) for y in range(self.about["gridDim"][1])]
            col_labels = [str(x+1) for x in range(self.about["gridDim"][0])]
            tempBOARD = BOARDS[self.about["name"]][1][client]
            for tile in self.about["chosenTiles"]:
                tempBOARD[tile[1]][tile[0]] = "-"
            self.pP.printmat(tempBOARD, row_labels, col_labels)

    def start(self):
        BOARDS = np.load("boards.npy", allow_pickle=True).tolist()

        np.save("boards.npy", BOARDS)   

        self.randomCoords = []
        for x in range(gridDim[0]):
            for y in range(gridDim[1]):
                self.randomCoords.append((x,y))
        random.shuffle(self.randomCoords)
        print(self.about["name"], "@@@ STARTED with", len(self.about["clients"]), "clients and has stats", self.status())
        self.printBoards()

    def turnHandle(self):
        self.about["turnNum"] += 1
        self.newTurn()
        self.printBoards()
    
    def delete(self):
        BOARDS = np.load("boards.npy", allow_pickle=True).tolist()
        del BOARDS[self.about["name"]]
        np.save("boards.npy", BOARDS)

class clientHandler():
    def __init__(self, game, client, about):
        self.game = game

        if about["isPlaying"]:
            self.about = {"name":client, "isPlaying": about["isPlaying"], "events":[], "authCode":''.join(random.choice(string.ascii_letters + string.digits) for x in range(60)), "money":0, "bank":0, "scoreHistory":[], "shield":False, "mirror":False, "column":random.randint(0,self.game.about["gridDim"][0]-1), "row":random.randint(0,self.game.about["gridDim"][1]-1)}
        else:
            self.about = {"name":client, "isPlaying": about["isPlaying"]}
    
    def logScore(self):
        self.about["scoreHistory"].append(self.about["money"] + self.about["bank"])
    
    def rOrCandCoordChoice(self):
        rOrC = random.randint(0,1)
        if rOrC == 1:
            columns = [i for i in range(self.game.about["gridDim"][0])]
            columns.remove(self.about["column"])
            choice = random.choice(columns)
        else:
            rows = [i for i in range(self.game.about["gridDim"][1])]
            rows.remove(self.about["row"])
            choice = random.choice(rows)
        return rOrC, choice

    def responseChoice(self):
        options = []
        for key,value in {"none":True, "mirror":self.about["mirror"], "shield":self.about["shield"]}.items():
            if value:
                options.append(key)
        return random.choice(options)
    
    def victimChoice(self):
        options = []
        for client in self.game.about["clients"]:
            if client != self.about["name"]:
                options.append(client)
        return random.choice(options)

    def act(self, whatHappened): ###THIS IS CURRENTLY ALL RANDOMISED, ALL THE RANDOM CODE PARTS SHOULD BE REPLACED WITH COMMUNICATION WITH VUE.
        if whatHappened == "A": #A - Rob
            choice = self.victimChoice()
            self.game.about["eventHandler"].make({"public":True, "event":whatHappened, "source":self, "targets":[self.game.about["clients"][choice]], "other":[]}) #EVENT HANDLER
            self.game.about["clients"][choice].beActedOn("A", self.about) ###ACT
            print(self.game.about["name"], "@", self.about["name"], "robs", self.game.about["clients"][choice].about["name"])
        if whatHappened == "B": #B - Kill
            choice = self.victimChoice()
            self.game.about["eventHandler"].make({"public":True, "event":whatHappened, "source":self, "targets":[self.game.about["clients"][choice]], "other":[]}) #EVENT HANDLER
            self.game.about["clients"][choice].beActedOn("B", self.about) ###ACT
            print(self.game.about["name"], "@", self.about["name"], "kills", self.game.about["clients"][choice].about["name"])
        if whatHappened == "C": #C - Present (Give someone 1000 of YOUR OWN cash)
            choice = self.victimChoice()
            self.game.about["eventHandler"].make({"public":True, "event":whatHappened, "source":self, "targets":[self.game.about["clients"][choice]], "other":[]}) #EVENT HANDLER
            self.game.about["clients"][choice].beActedOn("C", self.about) ###ACT
            print(self.game.about["name"], "@", self.about["name"], "gifts", self.game.about["clients"][choice].about["name"])
        if whatHappened == "D": #D - Skull and Crossbones (Wipe out (Number of players)/3 people)
            rOrC, choice = self.rOrCandCoordChoice()
            victims = self.game.whoIsOnThatLine(rOrC, choice)
            self.about["events"].append(self.game.about["eventHandler"].make({"public":True, "event":whatHappened, "source":self, "targets":[self.game.about["clients"][victim] for victim in victims], "other":[rOrC, choice]})) #EVENT HANDLER
            for victim in victims:
                self.game.about["clients"][victim].beActedOn("D", self.about) ###ACT
            if rOrC == 1:
                print(self.game.about["name"], "@", self.about["name"], "wiped out column", choice, "which held", [self.game.about["clients"][victim].about["name"] for victim in victims])
            else:
                print(self.game.about["name"], "@", self.about["name"], "wiped out row", choice, "which held", [self.game.about["clients"][victim].about["name"] for victim in victims])
        if whatHappened == "E": #E - Swap
            choice = self.victimChoice()
            self.about["events"].append(self.game.about["eventHandler"].make({"public":True, "event":whatHappened, "source":self, "targets":[self.game.about["clients"][choice]], "other":[]})) #EVENT HANDLER
            self.game.about["clients"][choice].beActedOn("E", self.about) ###ACT
            print(self.game.about["name"], "@", self.about["name"], "swaps with", self.game.about["clients"][choice].about["name"])
        if whatHappened == "F": #F - Choose Next Square
            self.game.about["eventHandler"].make({"public":True, "event":whatHappened, "source":self, "targets":[self.game], "other":[]}) #EVENT HANDLER
            self.game.about["tileOverride"] = self.game.genNewTile()
            print(self.game.about["name"], "@", self.about["name"], "chose the next square", (self.game.about["tileOverride"][0] + 1, self.game.about["tileOverride"][1] + 1))
        if whatHappened == "G": #G - Shield
            self.about["shield"] = True ###ACT
            print(self.game.about["name"], "@", self.about["name"], "gains a shield.")
        if whatHappened == "H": #H - Mirror
            self.about["mirror"] = True ###ACT
            print(self.game.about["name"], "@", self.about["name"], "gains a mirror.")
        if whatHappened == "I": #I - Bomb (You go to 0)
            self.about["money"] = 0 ###ACT
            print(self.game.about["name"], "@", self.about["name"], "got bombed.")
        if whatHappened == "J": #J - Double Cash
            self.about["money"] *= 2 ###ACT
            print(self.game.about["name"], "@", self.about["name"], "got their cash doubled.")
        if whatHappened == "K": #K - Bank
            self.about["bank"] += self.about["money"] ###ACT
            self.about["money"] = 0 ###ACT
            print(self.game.about["name"], "@", self.about["name"], "banked their money.")
        if whatHappened == "5000": #£5000
            self.about["money"] += 5000 ###ACT
            print(self.game.about["name"], "@", self.about["name"], "gained £5000.")
        if whatHappened == "3000": #£3000
            self.about["money"] += 3000 ###ACT
            print(self.game.about["name"], "@", self.about["name"], "gained £3000.")
        if whatHappened == "1000": #£1000
            self.about["money"] += 1000 ###ACT
            print(self.game.about["name"], "@", self.about["name"], "gained £1000.")
        if whatHappened == "200": #£200
            self.about["money"] += 200 ###ACT
            print(self.game.about["name"], "@", self.about["name"], "gained £200.")
    
    def beActedOn(self, whatHappened, aboutTheSender): #These are all the functions that involve interaction between players
        #if self.about[shield] or self.about[mirror]:
            ###check with the vue server here about whether the user wants to use a shield or mirror?
        if whatHappened == "A":
            choice = self.responseChoice()
            if choice == "none":
                self.game.about["clients"][aboutTheSender["name"]].about["money"] += self.about["money"]
                self.about["money"] = 0
            elif choice == "shield":
                self.about["shield"] = False
            elif choice == "mirror":
                self.about["mirror"] = False
                self.game.about["clients"][aboutTheSender["name"]].beActedOn("A", self.about)
        if whatHappened == "B":
            choice = self.responseChoice()
            if choice == "none":
                self.about["money"], self.about["bank"] = 0, 0
            if choice == "shield":
                self.about["shield"] = False
            elif choice == "mirror":
                self.about["mirror"] = False
                self.game.about["clients"][aboutTheSender["name"]].beActedOn("B", self.about)
        if whatHappened == "C":
            choice = self.responseChoice()
            if choice == "none":
                if self.game.about["clients"][aboutTheSender["name"]].about["money"] >= 1000:
                    self.about["money"] += 1000
                    self.game.about["clients"][aboutTheSender["name"]].about["money"] -= 1000
                elif self.game.about["clients"][aboutTheSender["name"]].about["money"] > 0:
                    self.about["money"] += self.game.about["clients"][aboutTheSender["name"]].about["money"]
                    self.game.about["clients"][aboutTheSender["name"]].about["money"] = 0
            if choice == "shield":
                self.about["shield"] = False
            if choice == "mirror":
                self.about["mirror"] = False
                self.game.about["clients"][aboutTheSender["name"]].beActedOn("C", self.about)
        if whatHappened == "D":
            choice = self.responseChoice()
            self.game.groupDecisionAdd(self, aboutTheSender["actions"][-1], choice)
        if whatHappened == "E":
            self.about["money"], self.game.about["clients"][aboutTheSender["name"]].about["money"] = self.game.about["clients"][aboutTheSender["name"]].about["money"], self.about["money"]
    
    def forceActedOn(self, whatHappened):
        if whatHappened == "D":
            self.about["money"] = 0

### FUNCTIONS THAT ALLOW APP.PY TO INTERACT WITH GAME AND CLIENT OBJECTS, ###
### and also the main thread, which includes demo code. ###

#if not playing will they need an id to see the game stats or is that spoiling the fun?
def makeGame(gameName, ownerID, gridDim, turnTime):
    if gameName not in games:
        if gameName == "":
            chars = string.ascii_letters + string.punctuation
            gameName = ''.join(random.choice(chars) for x in range(6))

        g = gameHandler(gameName, ownerID, gridDim, turnTime)
        games[gameName] = g
    else:
        print(gameName, "@@@@ FAILED GAME CREATION, that game name is already in use.")

#delete game(s) by Name
def deleteGame(gameNames):
    success = []
    fail = []
    for gameName in gameNames:
        try:
            games[gameName].delete()
            del games[gameName]
            success.append(gameName)
        except:
            fail.append(gameName)
    if len(fail) > 0:
        print(fail, "@@@@ NOT DELETED", success, "DELETED")
    elif len(success) > 0:
        print(success, "@@@@ DELETED")
    else:
        print("@@@@ NOTHING DELETED")

#get the status of a game by name
def status(gameName):
    try:
        return games[gameName].status()
    except:
        return False

#get the clients of a game by name and return either public or private information
def listClients(about):
    if about["private"]:
        out = {}
        for client in games[about["name"]].about["clients"]:
            out[client] = games[about["name"]].about["clients"][client].about
    else:
        out = {}
        for client in games[about["name"]].about["clients"]:
            tempAbout = games[about["name"]].about["clients"][client].about
            tempAbout["authCode"] = None
            tempAbout["money"] = None
            tempAbout["bank"] = None
            tempAbout["scoreHistory"] = None
            tempAbout["shield"] = None
            tempAbout["mirror"] = None
            tempAbout["column"] = None
            tempAbout["row"] = None
            out[client] = games[about["name"]].about["clients"][client].about
    return out

#join one or several clients to a lobby
def joinLobby(gameName, clients):
    return games[gameName].joinLobby(clients)

def exitLobby(gameName, clients):
    return games[gameName].exit(clients)

def leaderboard(gameName):
    return games[gameName].leaderboard()

def turnHandle(gameName):
    return games[gameName].turnHandle()

def start(gameName):
    return games[gameName].start()

def returnEvents(gameName, about):
    if about["public"]:
        return games[gameName].about["eventHandler"].about["publicLog"]
    else:
        return games[gameName].about["eventHandler"].about["privateLog"]

def alterClients(gameName, clientNames, alterations):
    for clientName in clientNames:
        if clientName in games[gameName].about["clients"]:
            for key,value in alterations.items():
                if key in games[gameName].about["clients"][clientName].about:
                    games[gameName].about["clients"][clientName].about[key] = value
                else:
                    success.append("Key", key, "doesn't exist for value", value, "to be assigned to.")
        else:
            for a in alterations.items():
                success.append("Client", clientName, "doesn't exist.")

def alterGames(gameNames, alterations):
    for gameName in gameNames:
        if gameName in games:
            for key,value in alterations.items():
                if key in games[gameName].about:
                    games[gameName].about[key] = value
                    success.append(True)
                else:
                    success.append("Key", key, "doesn't exist for value", value, "to be assigned to.")
        else:
            for a in alterations.items():
                success.append("Game", gameName, "doesn't exist.")
    return success

### MAIN THREAD ###
if __name__ == "__main__":
    ###Loading games that are "running", stored in boards.npy in case the backend crashes or something.
    try:
        BOARDS = np.load("boards.npy", allow_pickle=True).tolist()
        for gameName in BOARDS:
            try:
                gameName = gameName
                ownerID = BOARDS[gameName][0]["ownerID"]
                gridDim = BOARDS[gameName][0]["gridDim"]
                turnTime = BOARDS[gameName][0]["turnTime"]
                makeGame(gameName, ownerID, gridDim, turnTime)
            except:
                print(gameName, "@@@@ FAILED GAME RECOVERY, it's using a different format.")
    except:
        print("@@@@ No games were loaded.")
        BOARDS = {}
        np.save("boards.npy", BOARDS)
    
    ###And then deleting all those recovered games, because they're not necessary to test one new game.
    deleteGame([key for key in games])

    while True:
        ###Let's set up a few variables about our new test game...
        gridDim = (8,8)
        gridSize = gridDim[0] * gridDim[1]
        turnCount = gridSize + 1 #maximum of gridSize + 1
        ownerID = 1
        gameName = "Test-Game " + str(time.time())[-6:]
        turnTime = 30

        ###Setting up a test game
        makeGame(gameName, ownerID, gridDim, turnTime)

        ###Adding each of the imaginary players to the lobby sequentially.
        clients = {"Jamie":{"isPlaying":True}, "Tom":{"isPlaying":True}, "Alex":{"isPlaying":True}} #Player name, then info about them which currently consists of whether they're playing.
        joinLobby(gameName, clients) #This will create all the new players listed above so they're part of the gameHandler instance as individual clientHandler instances.
        #In future, when a user decides they don't want to play but still want to be in a game, the frontend will have to communicate with the backend to tell it to replace the isPlaying attribute in self.game.about["clients"][client].about
        
        ###Kicking one of the imaginary players. (regardless of whether the game is in lobby or cycling turns)
        exitLobby(gameName, ["Jamie"])

        ###Simulating the interaction with the vue server, pinging the processing of each successive turn like the Vue server will every time it's happy with client responses turn-by-turn.
        print("Enter any key to iterate a turn...")
        shallIContinue = input()

        start(gameName)
        for turn in range(turnCount): #Simulate the frontend calling the new turns over and over.
            shallIContinue = input()
            turnHandle(gameName)
            returnEvents(gameName, {"public":True})
        
        print(gameName, "@@@ Game over.")
        print("Leaderboard:", leaderboard(gameName))
        deleteGame([key for key in games])
        for i in range(3):
            print("")