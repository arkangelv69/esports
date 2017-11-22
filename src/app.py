from neo4j.v1 import GraphDatabase
import json
from classes import *
import sys

with open('config.json') as json_data_file:
    cfg = json.load(json_data_file)

#print(cfg)

uri = "bolt://"+cfg['database']['domain']+":7687"
driver = GraphDatabase.driver(uri, auth=(cfg['database']['username'], cfg['database']['password']))

teamSlugs = {
    "Team Secret":"team-secret",
    "compLexity":"complexity-gaming",
    "Vici Gaming":"vici-gaming",
    "Mineski":"mineski"
}

game = sys.argv[1] #lol, dota2 ,csgo


#if sys.argv[2] in teamSlugs:
#    teamLocalSlug = teamSlugs[sys.argv[2]]
#else:
    #exit("No tenemos el slug de:"+sys.argv[2])

#if sys.argv[3] in teamSlugs:
#    teamVisitorSlug = teamSlugs[sys.argv[3]]
#else:
    #exit("No tenemos el slug de: "+sys.argv[3])

#MATCH (n:TeamProvider) WHERE n.slug CONTAINS 'telecom' RETURN n.slug LIMIT 25

###-----------variables---score---------###

scores = Scores()

#winrate
winrate50 = 1
winrate60 = 2
winrate70 = 3
winrateVs = 1
#streak
streakPositive = 1
streak4 = 2
streak7 = 3
streakVs = 2
#country
countryEEUU = 1
countryChina = 2
countryKorea = 3
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

def getTeamSlugByNameAndGame(name, game):
    query = "MATCH (tm:Team)-[:PLAYS]->(g:Game)<-[:BELONGS]-(gp:GameProvider{slug:{game}}) \
                MATCH (tm)<-[:BELONGS]-(tmp:TeamProvider) \
                WHERE tmp.name = {name} \
                RETURN tmp.slug"
    with driver.session() as session:
        with session.begin_transaction() as tx:
            for record in tx.run(query, name=name, game=game):
                return record["tmp.slug"]
            return ""


def getTEST(game):
    query = "MATCH (tm:Team)-[:PLAYS]->(g:Game)<-[:BELONGS]-(gp:GameProvider{slug:{game}}) \
                MATCH (tm)<-[:BELONGS]-(tmp:TeamProvider) \
                RETURN tmp.slug,tmp.name"
    with driver.session() as session:
        with session.begin_transaction() as tx:
            return tx.run(query, game=game)

def getTeamBySlugAndGame(slug, game):
    query = "MATCH (tm:Team)-[:PLAYS]->(g:Game)<-[:BELONGS]-(gp:GameProvider{slug:{game}}) \
                MATCH (tm)<-[:BELONGS]-(tmp:TeamProvider) \
                MATCH (tm)-[:HAS]->(st:Stat) \
                MATCH (tm)-[:BELONGS]->(c:Country)<-[:BELONGS]-(cp:CountryProvider) \
                WHERE tmp.slug = {slug} \
                RETURN tmp,st,cp"
    with driver.session() as session:
        with session.begin_transaction() as tx:
            return tx.run(query, slug=slug, game=game)

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

def calculateLastThreeSeries(series):
    e = 1
    winLocal = 0
    winVisitor = 0
    for record in series:
        serie = Series(record)
        localScore = serie.getScoreBySlug(teamLocalSlug)
        visitorScore = serie.getScoreBySlug(teamVisitorSlug)
        if localScore > visitorScore:
            if e == 1:
                scores.addLocal(lastThreeSeriesFirst)
            winLocal += 1
        elif localScore < visitorScore:
            if e == 1:
                scores.addVisitor(lastThreeSeriesFirst)
            winVisitor += 1
        e += 1

    if winLocal > winVisitor:
        scores.addLocal(lastThreeSeriesVs)
    elif winLocal < winVisitor:
        scores.addVisitor(lastThreeSeriesVs)

def calculateCompareLossTeamVsLocal(otherSlug):
    series = getSeriesTeamVsTeam(teamVisitorSlug, otherSlug, game)
    for record in series:
        serie = Series(record)
        localScore = serie.getScoreBySlug(teamVisitorSlug)
        visitorScore = serie.getScoreBySlug(otherSlug)
        if localScore > visitorScore:
            scores.addVisitor(lastFiveSeriesVsOtherLoss)

def calculateCompareLossTeamVsVisitor(otherSlug):
    series = getSeriesTeamVsTeam(teamLocalSlug, otherSlug, game)
    for record in series:
        serie = Series(record)
        localScore = serie.getScoreBySlug(teamLocalSlug)
        visitorScore = serie.getScoreBySlug(otherSlug)
        if localScore > visitorScore:
            scores.addLocal(lastFiveSeriesVsOtherLoss)

def calculateLastFiveSeriesLocal(series):
    win = 0
    for record in series:
        serie = Series(record)
        teamScore = serie.getScoreBySlug(teamLocalSlug)
        otherScore = serie.getOtherScore(teamLocalSlug)
        otherSlug = serie.getOtherSlug(teamLocalSlug)
        if teamScore > otherScore:
            win += 1
        elif teamScore < otherScore:
            calculateCompareLossTeamVsLocal(otherSlug)

    return win


def calculateLastFiveSeriesVisitor(series):
    win = 0
    for record in series:
        serie = Series(record)
        teamScore = serie.getScoreBySlug(teamVisitorSlug)
        otherScore = serie.getOtherScore(teamVisitorSlug)
        otherSlug = serie.getOtherSlug(teamVisitorSlug)
        if teamScore > otherScore:
            win += 1
        elif teamScore < otherScore:
            calculateCompareLossTeamVsVisitor(otherSlug)

    return win

teamLocalSlug = getTeamSlugByNameAndGame(sys.argv[2],game)
teamVisitorSlug = getTeamSlugByNameAndGame(sys.argv[3],game)

if(teamLocalSlug==""):
    if sys.argv[2] in teamSlugs:
        teamLocalSlug = teamSlugs[sys.argv[2]]
    else:
        exit("No tenemos "+sys.argv[2])

if(teamVisitorSlug==""):
    if sys.argv[3] in teamSlugs:
        teamLocalSlug = teamSlugs[sys.argv[3]]
    else:
        exit("No tenemos "+sys.argv[3])

localTeamRaw = getTeamBySlugAndGame(teamLocalSlug, game)
winrateLocal = 0
streakLocal = 0
for record in localTeamRaw:
    team = Team(record['tmp'], json.loads(record['st']['stats']), record['cp'])
    #winrate
    winrateLocal = team.getWinrate()
    if winrateLocal >= 0.7:
        scores.addLocal(winrate70)
    elif winrateLocal >= 0.6:
        scores.addLocal(winrate60)
    elif winrateLocal >= 0.5:
        scores.addLocal(winrate50)
    #streak
    streakLocal = team.getStreak()
    if streakLocal > 0:
        scores.addLocal(streakPositive)
    if streakLocal >= 7:
        scores.addLocal(streak7)
    elif streakLocal >= 4:
        scores.addLocal(streak4)
    #country
    shortName = team.getShortNameCountry()
    if shortName == 'US':
        scores.addLocal(countryEEUU)
    elif shortName == 'HK' or shortName == 'CN':
        scores.addLocal(countryChina)
    elif shortName == 'KR':
        scores.addLocal(countryKorea)

visitorTeamRaw = getTeamBySlugAndGame(teamVisitorSlug, game)
winrateVisitor = 0
streakVisitor = 0
for record in visitorTeamRaw:
    team = Team(record['tmp'], json.loads(record['st']['stats']), record['cp'])
    # winrate
    winrateVisitor = team.getWinrate()
    if winrateVisitor >= 0.7:
        scores.addVisitor(winrate70)
    elif winrateVisitor >= 0.6:
        scores.addVisitor(winrate60)
    elif winrateVisitor >= 0.5:
        scores.addVisitor(winrate50)
    # streak
    streakVisitor = team.getStreak()
    if streakVisitor > 0:
        scores.addVisitor(streakPositive)
    if streakVisitor >= 7:
        scores.addVisitor(streak7)
    elif streakVisitor >= 4:
        scores.addVisitor(streak4)
    # country
    shortName = team.getShortNameCountry()
    if shortName == 'US':
        scores.addVisitor(countryEEUU)
    elif shortName == 'HK' or shortName == 'CN':
        scores.addVisitor(countryChina)
    elif shortName == 'KR':
        scores.addVisitor(countryKorea)

#winrateVs
if winrateLocal > winrateVisitor:
    scores.addLocal(winrateVs)
elif winrateLocal < winrateVisitor:
    scores.addVisitor(winrateVs)

#streakVs
if streakLocal > streakVisitor:
    scores.addLocal(streakVs)
elif streakLocal < streakVisitor:
    scores.addVisitor(streakVs)

#lastThreeSeries
#print('seriesVS:')
seriesVSRaw = getSeriesTeamVsTeam(teamLocalSlug,teamVisitorSlug,game)
calculateLastThreeSeries(seriesVSRaw)

#lastFiveSeries
#print('seriesLastLocal:')
seriesLastLocalRaw = getSeriesTeam(teamLocalSlug,game)
winLocalSeries = calculateLastFiveSeriesLocal(seriesLastLocalRaw)
if winLocalSeries >= 5:
    scores.addLocal(lastFiveSeries5)
elif winLocalSeries >= 4:
    scores.addLocal(lastFiveSeries4)
elif winLocalSeries >= 3:
    scores.addLocal(lastFiveSeries3)
elif winLocalSeries >= 2:
    scores.addLocal(lastFiveSeries2)

#print('seriesLastVisitor:')
seriesLastVisitorRaw = getSeriesTeam(teamVisitorSlug,game)
winVisitorSeries = calculateLastFiveSeriesVisitor(seriesLastVisitorRaw)
if winVisitorSeries >= 5:
    scores.addVisitor(lastFiveSeries5)
elif winVisitorSeries >= 4:
    scores.addVisitor(lastFiveSeries4)
elif winVisitorSeries >= 3:
    scores.addVisitor(lastFiveSeries3)
elif winVisitorSeries >= 2:
    scores.addVisitor(lastFiveSeries2)


if winLocalSeries > winVisitorSeries:
    scores.addLocal(lastFiveSeriesVs)
elif winLocalSeries < winVisitorSeries:
    scores.addVisitor(lastFiveSeriesVs)


#print(scores.getLocal())
#print(scores.getVisitor())
#print(scores.getGlobal())
#print(teamSlugs[sys.argv[2]]+'('+str(scores.getShareLocal())+'): '+sys.argv[4] + ' vs '+teamSlugs[sys.argv[3]]+'('+str(scores.getShareVisitor())+'): '+sys.argv[5])
print(sys.argv[2]+'('+str(scores.getShareLocal())+'): '+sys.argv[4] + ' vs '+sys.argv[3]+'('+str(scores.getShareVisitor())+'): '+sys.argv[5])


#print('Sobre un máximo de 28')
#print('Local: '+str(scores.getLocal()))
#print('Visitante: '+str(scores.getVisitor()))
#print('Total: '+str(scores.getGlobal()))
#print('share '+teamLocalSlug+': ')
#print(scores.getShareLocal())
#print('share '+teamVisitorSlug+': ')
#print(scores.getShareVisitor())


exit()
