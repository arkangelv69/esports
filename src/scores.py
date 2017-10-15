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