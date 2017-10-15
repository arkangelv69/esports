# classes.py

class Scores:
    scoreGlobal = 0
    scoreLocal = 0
    scoreVisitor = 0

    def addLocal(self,score):
        self.scoreLocal += score
    def addVisitor(self,score):
        self.scoreVisitor += score
    def addGlobal(self,score):
        self.scoreGlobal += score
    def getGlobal(self):
        return self.scoreGlobal


class Team:
    def __init__(self, attributes, stats, country):
        self.attributes = attributes
        self.stats = stats
        self.country = country

class Series:
    def __init__(self, seriesRaw):
        self.endDate = seriesRaw['s']['endDate']
        self.results = seriesRaw['results']

    def getLocalScore(self):
        for result in self.results:
            seeding = result[1]
            print(result)
            if seeding['position'] == 1:
                return seeding['score']

    def getVisitorScore(self):
        for result in self.results:
            seeding = result[1]
            print(result)
            if seeding['position'] == 2:
                return seeding['score']