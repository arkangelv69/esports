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
        return 1/(self.scoreLocal/self.scoreGlobal)
    def getShareVisitor(self):
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