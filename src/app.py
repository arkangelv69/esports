from neo4j.v1 import GraphDatabase
import json
from classes import *

with open('config.json') as json_data_file:
    cfg = json.load(json_data_file)

print(cfg)

uri = "bolt://"+cfg['database']['domain']+":7687"
driver = GraphDatabase.driver(uri, auth=(cfg['database']['username'], cfg['database']['password']))

game = "csgo"
teamLocalSlug = "g2-esports"
teamVisitorSlug = "fnatic"

###-----------variables---score---------###

scores = Scores()

#winrate
winrate50 = 1
winrate60 = 2
winrate70 = 3
#streak
streakPositive = 1
streak4 = 2
streak7 = 3
streakVs = 2
#country
countryEEUU = 1
countryChina = 2
countrykorea = 3
#lastThreeSeries
lastThreeSeriesFirst = 3
lastThreeSeriesVs = 2
#lastFiveSeries
lastFiveSeries2 = 1
lastFiveSeries3 = 2
lastFiveSeries4 = 3
lastFiveSeries5 = 4
lastFiveSeriesVs = 2
lastFiveSeriesVsOtherLoss = 2
#roster
rosterNotChange = 3

###-------------------------------------###


def getTeamBySlugAndGame(slug, game):
    query = "MATCH (tm:Team)-[:PLAYS]->(g:Game)<-[:BELONGS]-(gp:GameProvider{slug:{game}}) \
                MATCH (tm)<-[:BELONGS]-(tmp:TeamProvider) \
                MATCH (tm)-[:HAS]->(st:Stat) \
                MATCH (tm)-[:BELONGS]->(c:Country)<-[:BELONGS]-(cp:CountryProvider) \
                WHERE tmp.slug = {slug} \
                RETURN tmp,st,cp"
    with driver.session() as session:
        with session.begin_transaction() as tx:
            for record in tx.run(query, slug=slug, game=game):
                output = Team(record['tmp'],json.loads(record['st']['stats']),record['cp'])
                return output

def getSeriesTeamVsTeam(slugLocal,slugVisitor,game):
    query = "MATCH (s:Series)<-[:COMPETES_IN]-(r:Roster)<--(t:Team)<--(tp:TeamProvider) \
            MATCH (s)<-[]-(sd:Seed) \
            MATCH (t)-->(g:Game)<--(gp:GameProvider{slug:{game}}) \
            MATCH (sd)<-[seeding:SEEDING]-(r) \
            WHERE (s)<-[:COMPETES_IN]-(:Roster)<-[:BELONGS]-(:Team)<--(:TeamProvider{slug:{slugLocal}}) AND (s)<-[:COMPETES_IN]-(:Roster)<-[:BELONGS]-(:Team)<--(:TeamProvider{slug:{slugVisitor}}) AND s.endDate <> -1 \
            RETURN s,s.endDate as date,collect([tp,seeding]) as results ORDER BY s.endDate DESC LIMIT 3"
    with driver.session() as session:
        with session.begin_transaction() as tx:
            return tx.run(query, slugLocal=slugLocal, slugVisitor=slugVisitor, game=game)

def getSeriesTeam(slug,game):
    query = "MATCH (s:Series)<-[:COMPETES_IN]-(r:Roster)<--(t:Team)<--(tp:TeamProvider) \
            MATCH (s)<-[]-(sd:Seed) \
            MATCH (t)-->(g:Game)<--(gp:GameProvider{slug:{game}}) \
            MATCH (sd)<-[seeding:SEEDING]-(r) \
            WHERE (s)<-[:COMPETES_IN]-(:Roster)<-[:BELONGS]-(:Team)<--(:TeamProvider{slug:{slug}}) AND s.endDate <> -1 \
            RETURN s,s.endDate as date,collect([tp,seeding]) as results ORDER BY s.endDate DESC LIMIT 5"
    with driver.session() as session:
        with session.begin_transaction() as tx:
            return tx.run(query, slug=slug, game=game)

localTeam = getTeamBySlugAndGame(teamLocalSlug, game)
visitorTeam = getTeamBySlugAndGame(teamVisitorSlug, game)

seriesVSRaw = getSeriesTeamVsTeam(teamLocalSlug,teamVisitorSlug,game)

def calculateLastThreeSeries(series,scores):
    e = 1
    winLocal = 0
    winVisitor = 0
    for record in series:
        serie = Series(record)
        localScore = serie.getLocalScore()
        visitorScore = serie.getVisitorScore()
        if localScore > visitorScore:
            if e == 1:
                scores.addLocal(lastThreeSeriesFirst)
                scores.addGlobal(lastThreeSeriesFirst)
            winLocal += 1
        elif localScore < visitorScore:
            if e == 1:
                scores.addVisitor(lastThreeSeriesFirst)
                scores.addGlobal(lastThreeSeriesFirst)
            winVisitor += 1
        e += 1

    if winLocal > winVisitor:
        scores.addLocal(lastThreeSeriesVs)
        scores.addGlobal(lastThreeSeriesVs)
    elif winLocal < winVisitor:
        scores.addVisitor(lastThreeSeriesVs)
        scores.addGlobal(lastThreeSeriesVs)

    print(scores.getGlobal())

    return scores

print('seriesVS:')
scores = calculateLastThreeSeries(seriesVSRaw,scores)

seriesLastLocalRaw = getSeriesTeam(teamLocalSlug,game)
print('sereiesLastLocal:')
for record in seriesLastLocalRaw:
    serie = Series(record)

seriesLastVisitorRaw = getSeriesTeam(teamVisitorSlug,game)
print('sereiesLastVisitor:')
for record in seriesLastVisitorRaw:
    serie = Series(record)

exit()