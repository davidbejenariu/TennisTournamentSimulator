import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt

# TODO change distribution

output = open('output.txt', 'w')


class Player:
    def __init__(self, name, rank, ovrWinRate, hardWinRate, clayWinRate, grassWinRate, wonFirstSetWR, lostFirstSetWR,
                 h2h):
        self.name = name
        self.rank = rank
        self.ovrWR = ovrWinRate
        self.hardWR = hardWinRate
        self.clayWR = clayWinRate
        self.grassWR = grassWinRate
        self.wonFirstSetWR = wonFirstSetWR
        self.lostFirstSetWR = lostFirstSetWR
        self.h2h = h2h
        self.pointsWon = 0
        self.totalPoints = 0
        self.servePointsWon = 0
        self.totalServePoints = 0

    def __str__(self):
        s = "name: " + str(self.name) + ", rank: " + str(self.rank) + ", overall win rate: " + str(self.ovrWR) \
            + "\n\thard win rate: " + str(self.hardWR) + ", clay win rate: " + str(
            self.clayWR) + ", grass win rate: " + str(self.grassWR) \
            + "\n\tafter winning first set win rate: " + str(
            self.wonFirstSetWR) + ", after losing first set win rate: " + str(self.lostFirstSetWR) \
            + "\n\twin rate against:"

        for k in self.h2h.keys():
            s += "\n\t\t" + str(k) + " - " + str(self.h2h[k])

        return s


class Simulator:
    def __init__(self, playersCount):
        self.playersName = []
        self.playersData = {}
        self.playersCount = playersCount

    def __str__(self):
        s = ""

        for p in self.playersName:
            s += self.playersData[p].__str__() + "\n"

        return s

    def addPlayer(self, name, rank, ovrWinRate, hardWinRate, clayWinRate, grassWinRate, wonFirstSetWR, lostFirstSetWR,
                  h2h):
        self.playersName.append(name)
        self.playersData[name] = Player(name, rank, ovrWinRate, hardWinRate, clayWinRate, grassWinRate, wonFirstSetWR,
                                        lostFirstSetWR, h2h)

    def parseExcelFile(self, path):
        data = pd.read_excel(path)
        data = data.fillna('empty')
        data = data.values

        for i in range(self.playersCount):
            h2h = {}
            k = self.playersCount + 2

            for j in range(1, self.playersCount + 1):
                if data[k][j] != data[i][0]:
                    h2h[data[k][j]] = data[k + i + 1][j] / (data[k + i + 1][j] + data[k + j][i + 1])

            self.addPlayer(data[i][0], data[i][1], data[i][2], data[i][3], data[i][4], data[i][5], data[i][6],
                           data[i][7], h2h)

    # Formula:
    #   p1 = overallWR * surfaceWR + 1/rank + h2h(p2)
    #   p2 = overallWR * surfaceWR + 1/rank + h2h(p1)
    #   probP1 = p1 / (p1 + p2)
    #   probP2 = p2 / (p1 + p2)
    def computeInitialOdds(self, player1, player2, surface):
        if surface == "hard":
            p1 = self.playersData[player1].hardWR
            p2 = self.playersData[player2].hardWR
        elif surface == "clay":
            p1 = self.playersData[player1].clayWR
            p2 = self.playersData[player2].clayWR
        else:
            p1 = self.playersData[player1].grassWR
            p2 = self.playersData[player2].grassWR

        # p1 = p1 * self.playersData[player1].ovrWR + 1 / self.playersData[player1].rank + self.playersData[player1].h2h[player2]
        # p2 = p2 * self.playersData[player2].ovrWR + 1 / self.playersData[player2].rank + self.playersData[player2].h2h[player1]

        p1 = p1 * self.playersData[player1].ovrWR + self.playersData[player1].h2h[player2]
        p2 = p2 * self.playersData[player2].ovrWR + self.playersData[player2].h2h[player1]

        return p1, p2

    def getInitialProb(self, player1, player2, surface):
        p1, p2 = self.computeInitialOdds(player1, player2, surface)

        return [p1 / (p1 + p2), p2 / (p1 + p2)]

    # Formula:
    #   winner = won first set
    #   loser = lost first set
    #   probWinner = probWinner * wonFirstSetWR
    #   probLoser = probLoser * lostFirstSetWR
    def updateSecondSet(self, player1, player2, surface, winner):
        p1, p2 = self.computeInitialOdds(player1, player2, surface)

        if winner == player1:
            p1 += self.playersData[player1].wonFirstSetWR
            p2 += self.playersData[player2].lostFirstSetWR
        else:
            p1 += self.playersData[player1].lostFirstSetWR
            p2 += self.playersData[player2].wonFirstSetWR

        return [p1 / (p1 + p2), p2 / (p1 + p2)]

    # Formula:
    #   get back to initial prob
    def updateThirdSet(self, player1, player2, surface):
        return self.getInitialProb(player1, player2, surface)

    def coinToss(self):
        if np.random.uniform() <= 0.5:
            return 0
        else:
            return 1

    def simulatePoint(self, player1, player2, p1):
        if np.random.uniform() <= p1:
            return player1
        else:
            return player2

    def simulateGame(self, game, server, receiver, p1, p2):
        # The player who serves should have a considerably higher chance to win the game
        prob1 = p1 + p2 / 3
        prob2 = 1 - prob1
        # prob1 = p1
        # prob2 = p2

        output.write("\t\tGame " + str(game) + ": " + server + " to serve\n")
        # print(prob1, prob2)

        scores = [0, 15, 30, 40, -1]
        score1 = 0
        score2 = 0

        while score1 < 4 and score2 < 4:
            output.write("\t\t\t" + str(scores[score1]) + "-" + str(scores[score2]) + "\n")

            # Deuce
            if score1 == 3 and score2 == 3:
                while score1 < 5 and score2 < 5:
                    self.playersData[server].totalPoints += 1
                    self.playersData[server].totalServePoints += 1
                    self.playersData[receiver].totalPoints += 1

                    if self.simulatePoint(server, receiver, prob1) == server:
                        self.playersData[server].pointsWon += 1
                        self.playersData[server].servePointsWon += 1

                        if score2 == 4:
                            score2 -= 1
                            output.write("\t\t\t40-40\n")
                        else:
                            score1 += 1

                            if score1 == 4:
                                output.write("\t\t\tAd-40\n")
                    else:
                        self.playersData[receiver].pointsWon += 1

                        if score1 == 4:
                            score1 -= 1
                            output.write("\t\t\t40-40\n")
                        else:
                            score2 += 1

                            if score2 == 4:
                                output.write("\t\t\t40-Ad\n")
            else:
                self.playersData[server].totalPoints += 1
                self.playersData[server].totalServePoints += 1
                self.playersData[receiver].totalPoints += 1

                if self.simulatePoint(server, receiver, prob1) == server:
                    score1 += 1
                    self.playersData[server].pointsWon += 1
                    self.playersData[server].servePointsWon += 1
                else:
                    score2 += 1
                    self.playersData[receiver].pointsWon += 1

        if score1 >= 4:
            output.write("\t\t\tW " + server + "\n")
            return server
        else:
            output.write("\t\t\tW " + receiver + "\n")
            return receiver

    def simulateTieBreak(self, game, player1, player2, p1, p2):
        score1 = 0
        score2 = 0
        server = player1

        output.write("\t\tGame " + str(game) + ": TIE-BREAK\n")

        while True:
            if score1 >= 7 and score1 - score2 >= 2:
                output.write("\t\t\tW " + player1 + "\n")
                return player1
            elif score2 >= 7 and score2 - score1 >= 2:
                output.write("\t\t\tW " + player2 + "\n")
                return player2
            else:
                winner = self.simulatePoint(player1, player2, p1)

                if winner == player1:
                    score1 += 1
                    self.playersData[player1].pointsWon += 1

                    if player1 == server:
                        self.playersData[player1].servePointsWon += 1
                else:
                    score2 += 1
                    self.playersData[player2].pointsWon += 1

                    if player2 == server:
                        self.playersData[player2].servePointsWon += 1

                output.write("\t\t\t" + player1 + " " + str(score1) + "-" + str(score2) + " " + player2 + "\n")

                self.playersData[player1].totalPoints += 1
                self.playersData[player2].totalPoints += 1

                if player1 == server:
                    self.playersData[player1].totalServePoints += 1

                    if (score1 + score2) % 2 == 1:
                        server = player2
                else:
                    self.playersData[player2].totalServePoints += 1

                    if (score1 + score2) % 2 == 1:
                        server = player1

    # different distribution, different formulas????
    def simulateMatch(self, player1, player2, surface):
        prob = self.getInitialProb(player1, player2, surface)
        players = [player1, player2]
        playerToServe = self.coinToss()
        gameCount = 1
        set1 = 0
        set2 = 0

        output.write(
            "\tIntial match predictor:\n\t\t " + player1 + " - " + str(prob[0] * 100)[:5] + "%\n\t\t " + player2 \
            + " - " + str(prob[1] * 100)[:5] + "%\n")
        output.write("\t" + players[playerToServe] + " won the coin toss and will serve in the opening.\n\n")
        output.write("\tSTARTING MATCH...\n")
        output.write("\t---------------------------------------------------------------\n")

        while set1 < 2 and set2 < 2:
            game1 = 0
            game2 = 0

            if set1 == 1 and set2 == 0:
                prob = self.updateSecondSet(player1, player2, surface, player1)
            elif set1 == 0 and set2 == 1:
                prob = self.updateSecondSet(player1, player2, surface, player2)
            elif set1 == 1 and set2 == 1:
                prob = self.updateThirdSet(player1, player2, surface)

            output.write("\tSet " + str(set1 + set2 + 1) + "\n")
            # print(prob[0], prob[1])

            while True:
                if game1 == 6 and game2 <= 4:
                    set1 += 1
                    break
                elif game2 == 6 and game1 <= 4:
                    set2 += 1
                    break
                elif game1 == 7 and game2 == 5:
                    set1 += 1
                    break
                elif game2 == 7 and game1 == 5:
                    set2 += 1
                    break
                elif game1 == 6 and game2 == 6:
                    winner = self.simulateTieBreak(gameCount, players[playerToServe], players[1 - playerToServe],
                                                   prob[playerToServe], prob[1 - playerToServe])

                    if winner == player1:
                        set1 += 1
                    else:
                        set2 += 1

                    gameCount += 1
                    playerToServe = 1 - playerToServe

                    break
                else:
                    winner = self.simulateGame(gameCount, players[playerToServe], players[1 - playerToServe],
                                               prob[playerToServe], prob[1 - playerToServe])

                    if winner == player1:
                        game1 += 1
                    else:
                        game2 += 1

                    output.write("\t\tGAMES: " + player1 + " " + str(game1) + "-" + str(game2) + " " + player2 + "\n")

                    gameCount += 1
                    playerToServe = 1 - playerToServe

            output.write("\tSETS: " + player1 + " " + str(set1) + "-" + str(set2) + " " + player2 + "\n")

        output.write("\t---------------------------------------------------------------\n")

        if set1 > set2:
            output.write("\tMATCH END\n\tWINNER: " + player1 + "\n")
            return player1
        else:
            output.write("\tMATCH END\n\tWINNER: " + player2 + "\n")
            return player2

    def simulateTournament(self, surface):
        names = self.playersName
        np.random.shuffle(names)

        totalRounds = int(math.log2(self.playersCount))
        draw = [names] + [[] for i in range(totalRounds - 1)]
        rounds = ["ROUND OF " + str(2 ** x) for x in range(totalRounds, 3, -1)] + ["QUARTERFINAL", "SEMIFINAL", "FINAL"]
        currentRound = 0

        while currentRound < totalRounds - 1:
            output.write("\n-------------------------------------------------------------------\n")
            output.write(rounds[currentRound] + "\n")
            output.write("-------------------------------------------------------------------\n")

            size = len(draw[currentRound])

            for i in range(int(size / 2)):
                output.write("\n" + draw[currentRound][2 * i] + " vs " + draw[currentRound][2 * i + 1] + "\n")
                draw[currentRound + 1].append(
                    self.simulateMatch(draw[currentRound][2 * i], draw[currentRound][2 * i + 1], surface))

            currentRound += 1

        output.write("\n-------------------------------------------------------------------\n")
        output.write("FINAL\n")
        output.write("-------------------------------------------------------------------\n")

        winner = self.simulateMatch(draw[totalRounds - 1][0], draw[totalRounds - 1][1], surface)

        output.write("\n-------------------------------------------------------------------\n")
        output.write("TOURNAMENT END\n")
        output.write("WINNER: " + winner + "\n")
        output.write("-------------------------------------------------------------------\n")

        return winner


if __name__ == '__main__':
    simulator = Simulator(16)
    simulator.parseExcelFile("player_data.xlsx")
    surfaces = ["hard", "clay", "grass"]

    player = input("See stats for player: ")
    points = [(0, 0)]
    servePoints = [(0, 0)]

    for j in range(5):
        print(surfaces[np.random.randint(0, 3)])
        print(simulator.simulateTournament(surfaces[np.random.randint(0, 3)]))

        # print(simulator.playersData[player].pointsWon / simulator.playersData[player].totalPoints)
        points.append((simulator.playersData[player].pointsWon - points[-1][0],
                       simulator.playersData[player].totalPoints - points[-1][1]))
        servePoints.append((simulator.playersData[player].servePointsWon - servePoints[-1][0],
                            simulator.playersData[player].totalServePoints - servePoints[-1][1]))

    points = [100 * (points[i][0] / points[i][1]) for i in range(1, len(points))]
    servePoints = [100 * (servePoints[i][0] / servePoints[i][1]) for i in range(1, len(servePoints))]

    # print(points)
    # print(servePoints)

    plot1 = plt.figure(1)
    plt.title("Point Win Percentages for " + player)
    # plt.ylim([0, 100])
    plt.plot(["Tournament 1", "Tournament 2", "Tournament 3", "Tournament 4", "Tournament 5"], points)

    plot2 = plt.figure(2)
    plt.title("Serve Point Win Percentages for " + player)
    # plt.ylim([0, 100])
    plt.plot(["Tournament 1", "Tournament 2", "Tournament 3", "Tournament 4", "Tournament 5"], servePoints)

    pointsAll = [100 * (simulator.playersData[player].pointsWon / simulator.playersData[player].totalPoints) for player
                 in simulator.playersName]
    servePointsAll = [
        100 * (simulator.playersData[player].servePointsWon / simulator.playersData[player].totalServePoints) for player
        in simulator.playersName]

    # print(pointsAll)
    # print(servePointsAll)

    plot3 = plt.figure(3)
    plt.title("Point Win Percentages by Player")
    plt.plot(simulator.playersName, pointsAll)
    plt.xticks(simulator.playersName, simulator.playersName, rotation='vertical')

    plot4 = plt.figure(4)
    plt.title("Serve Point Win Percentages by Player")
    plt.plot(simulator.playersName, servePointsAll)
    plt.xticks(simulator.playersName, simulator.playersName, rotation='vertical')

    plt.show()
