# classes.py

class Scores:
    scoreGlobal = 0
    scoreLocal = 0
    scoreVisitor = 0

    def addLocal(self,score,label):
        self.scoreLocal += score
        self.addGlobal(score)
        print('Incremento local de: '+str(score)+' por: '+label)
    def addVisitor(self,score,label):
        self.scoreVisitor += score
        self.addGlobal(score)
        print('Incremento visitante de: ' + str(score) + ' por: ' + label)
    def addGlobal(self,score):
        self.scoreGlobal += score
    def getLocal(self):
        return self.scoreLocal
    def getVisitor(self):
        return self.scoreVisitor
    def getGlobal(self):
        return self.scoreGlobal
    def getShareLocal(self):
        if self.scoreGlobal == 0:
            exit('\033[91mcero puntos obtenidos\033[0m')
        if self.scoreLocal == 0:
            exit('\033[91mcero puntos obtenidos\033[0m')
        return 1/(self.scoreLocal/self.scoreGlobal)
    def getShareVisitor(self):
        if self.scoreGlobal == 0:
            exit('\033[91mcero puntos obtenidos\033[0m')
        if self.scoreVisitor == 0:
            exit('\033[91mcero puntos obtenidos\033[0m')
        return 1/(self.scoreVisitor/self.scoreGlobal)


class Team:
    def __init__(self, attributes, stats, country):
        self.attributes = attributes
        self.stats = stats
        self.country = country

    def getWinrate(self):
        return self.stats['winrate']['series']['rate']

    def getStreak(self):
        return self.stats['streak']['series']['current']

    def getShortNameCountry(self):
        return self.country['shortName']

class Series:
    def __init__(self, seriesRaw):
        self.endDate = seriesRaw['s']['endDate']
        self.results = seriesRaw['results']

    def getScoreBySlug(self,slug):
        for result in self.results:
            team = result[0]
            teamSlug = result[0]['slug']
            seeding = result[1]
            if teamSlug == slug:
                return seeding['score']

    def getOtherScore(self,slug):
        for result in self.results:
            team = result[0]
            teamSlug = result[0]['slug']
            seeding = result[1]
            if teamSlug != slug:
                return seeding['score']

    def getOtherSlug(self,slug):
        for result in self.results:
            team = result[0]
            teamSlug = result[0]['slug']
            seeding = result[1]
            if teamSlug != slug:
                return teamSlug

    def getLocalScore(self):
        for result in self.results:
            seeding = result[1]
            if seeding['position'] == 1:
                return seeding['score']

    def getVisitorScore(self):
        for result in self.results:
            seeding = result[1]
            if seeding['position'] == 2:
                return seeding['score']

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'