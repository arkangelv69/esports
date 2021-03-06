import json
import re
import sys
import datetime

from classes import *
from neo4j.v1 import GraphDatabase

with open('config.json') as json_data_file:
    cfg = json.load(json_data_file)

with open('mapTeamSlugs.json') as json_data_map_team_slugs:
    mapTeamSlugs = json.load(json_data_map_team_slugs)

with open('mapGames.json') as json_data_map_games:
    mapGames = json.load(json_data_map_games)

#print(cfg)

uri = "bolt://"+cfg['database']['domain']+":7687"
driver = GraphDatabase.driver(uri, auth=(cfg['database']['username'], cfg['database']['password']))

today = datetime.datetime.today().strftime('%Y-%m-%d')
seriesName = sys.argv[1]

def getGameBySeriesName(mapGames, seriesName):
    for name in mapGames:
        if re.search('(.*'+name+'.*)', seriesName):
            return mapGames[name]
    exit(bcolors.FAIL +'no existe game para: '+seriesName+bcolors.ENDC)

game = getGameBySeriesName(mapGames,seriesName)

#MATCH (n:TeamProvider) WHERE n.slug CONTAINS 'telecom' RETURN n.slug LIMIT 25

###-----------variables---score---------###

scores = Scores()
bcolors = bcolors()

minGlobal = 6
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
                WHERE tmp.name =~ {name} \
                RETURN tmp.slug"
    with driver.session() as session:
        with session.begin_transaction() as tx:
            for record in tx.run(query, name='(?i).*'+name+'.*', game=game):
                return record["tmp.slug"]
            return ""

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
                scores.addLocal(lastThreeSeriesFirst,'lastThreeSeriesFirst')
            winLocal += 1
        elif localScore < visitorScore:
            if e == 1:
                scores.addVisitor(lastThreeSeriesFirst,'lastThreeSeriesFirst')
            winVisitor += 1
        e += 1

    if winLocal > winVisitor:
        scores.addLocal(lastThreeSeriesVs,'lastThreeSeriesVs')
    elif winLocal < winVisitor:
        scores.addVisitor(lastThreeSeriesVs,'lastThreeSeriesVs')

def calculateCompareLossTeamVsLocal(otherSlug):
    series = getSeriesTeamVsTeam(teamVisitorSlug, otherSlug, game)
    for record in series:
        serie = Series(record)
        localScore = serie.getScoreBySlug(teamVisitorSlug)
        visitorScore = serie.getScoreBySlug(otherSlug)
        if localScore > visitorScore:
            scores.addVisitor(lastFiveSeriesVsOtherLoss,'lastFiveSeriesVsOtherLoss')

def calculateCompareLossTeamVsVisitor(otherSlug):
    series = getSeriesTeamVsTeam(teamLocalSlug, otherSlug, game)
    for record in series:
        serie = Series(record)
        localScore = serie.getScoreBySlug(teamLocalSlug)
        visitorScore = serie.getScoreBySlug(otherSlug)
        if localScore > visitorScore:
            scores.addLocal(lastFiveSeriesVsOtherLoss,'lastFiveSeriesVsOtherLoss')

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

if sys.argv[2] in mapTeamSlugs:
    teamLocalSlug = mapTeamSlugs[sys.argv[2]]
else:
    teamLocalSlug = getTeamSlugByNameAndGame(sys.argv[2], game)
if (teamLocalSlug == ""):
    exit(bcolors.FAIL +"No tenemos "+sys.argv[2]+bcolors.ENDC)
teamLocalShare = float(sys.argv[3])

if sys.argv[4] in mapTeamSlugs:
    teamVisitorSlug = mapTeamSlugs[sys.argv[4]]
else:
    teamVisitorSlug = getTeamSlugByNameAndGame(sys.argv[4], game)
if (teamVisitorSlug == ""):
    exit(bcolors.FAIL +"No tenemos " + sys.argv[4]+bcolors.ENDC)
teamVisitorShare = float(sys.argv[5])




localTeamRaw = getTeamBySlugAndGame(teamLocalSlug, game)
winrateLocal = 0
streakLocal = 0
for record in localTeamRaw:
    team = Team(record['tmp'], json.loads(record['st']['stats']), record['cp'])
    #winrate
    winrateLocal = team.getWinrate()
    if winrateLocal >= 0.7:
        scores.addLocal(winrate70,'winrate70')
    elif winrateLocal >= 0.6:
        scores.addLocal(winrate60,'winrate60')
    elif winrateLocal >= 0.5:
        scores.addLocal(winrate50,'winrate50')
    #streak
    streakLocal = team.getStreak()
    if streakLocal > 0:
        scores.addLocal(streakPositive,'streakPositive')
    if streakLocal >= 7:
        scores.addLocal(streak7,'streak7')
    elif streakLocal >= 4:
        scores.addLocal(streak4,'streak4')
    #country
    shortName = team.getShortNameCountry()
    if shortName == 'US':
        scores.addLocal(countryEEUU,'countryEEUU')
    elif shortName == 'HK' or shortName == 'CN':
        scores.addLocal(countryChina,'countryChina')
    elif shortName == 'KR':
        scores.addLocal(countryKorea,'countryKorea')

visitorTeamRaw = getTeamBySlugAndGame(teamVisitorSlug, game)
winrateVisitor = 0
streakVisitor = 0
for record in visitorTeamRaw:
    team = Team(record['tmp'], json.loads(record['st']['stats']), record['cp'])
    # winrate
    winrateVisitor = team.getWinrate()
    if winrateVisitor >= 0.7:
        scores.addVisitor(winrate70,'winrate70')
    elif winrateVisitor >= 0.6:
        scores.addVisitor(winrate60,'winrate60')
    elif winrateVisitor >= 0.5:
        scores.addVisitor(winrate50,'winrate50')
    # streak
    streakVisitor = team.getStreak()
    if streakVisitor > 0:
        scores.addVisitor(streakPositive,'streakPositive')
    if streakVisitor >= 7:
        scores.addVisitor(streak7,'streak7')
    elif streakVisitor >= 4:
        scores.addVisitor(streak4,'streak4')
    # country
    shortName = team.getShortNameCountry()
    if shortName == 'US':
        scores.addVisitor(countryEEUU,'countryEEUU')
    elif shortName == 'HK' or shortName == 'CN':
        scores.addVisitor(countryChina,'countryChina')
    elif shortName == 'KR':
        scores.addVisitor(countryKorea,'countryKorea')

#winrateVs
if winrateLocal > winrateVisitor:
    scores.addLocal(winrateVs,'winrateVs')
elif winrateLocal < winrateVisitor:
    scores.addVisitor(winrateVs,'winrateVs')

#streakVs
if streakLocal > streakVisitor:
    scores.addLocal(streakVs,'streakVs')
elif streakLocal < streakVisitor:
    scores.addVisitor(streakVs,'streakVs')

#lastThreeSeries
print('Procesando seriesVS...')
seriesVSRaw = getSeriesTeamVsTeam(teamLocalSlug,teamVisitorSlug,game)
calculateLastThreeSeries(seriesVSRaw)

#lastFiveSeries
print('Procesando seriesLastLocal...')
seriesLastLocalRaw = getSeriesTeam(teamLocalSlug,game)
winLocalSeries = calculateLastFiveSeriesLocal(seriesLastLocalRaw)
if winLocalSeries >= 5:
    scores.addLocal(lastFiveSeries5,'lastFiveSeries5')
elif winLocalSeries >= 4:
    scores.addLocal(lastFiveSeries4,'lastFiveSeries4')
elif winLocalSeries >= 3:
    scores.addLocal(lastFiveSeries3,'lastFiveSeries3')
elif winLocalSeries >= 2:
    scores.addLocal(lastFiveSeries2,'lastFiveSeries2')

print('Procesando seriesLastVisitor...')
seriesLastVisitorRaw = getSeriesTeam(teamVisitorSlug,game)
winVisitorSeries = calculateLastFiveSeriesVisitor(seriesLastVisitorRaw)
if winVisitorSeries >= 5:
    scores.addVisitor(lastFiveSeries5,'lastFiveSeries5')
elif winVisitorSeries >= 4:
    scores.addVisitor(lastFiveSeries4,'lastFiveSeries4')
elif winVisitorSeries >= 3:
    scores.addVisitor(lastFiveSeries3,'lastFiveSeries3')
elif winVisitorSeries >= 2:
    scores.addVisitor(lastFiveSeries2,'lastFiveSeries2')


if winLocalSeries > winVisitorSeries:
    scores.addLocal(lastFiveSeriesVs,'lastFiveSeriesVs')
elif winLocalSeries < winVisitorSeries:
    scores.addVisitor(lastFiveSeriesVs,'lastFiveSeriesVs')

#print(scores.getLocal())
#print(scores.getVisitor())
#print(scores.getGlobal())
#print(mapTeamSlugs[sys.argv[2]]+'('+str(scores.getShareLocal())+'): '+sys.argv[4] + ' vs '+mapTeamSlugs[sys.argv[3]]+'('+str(scores.getShareVisitor())+'): '+sys.argv[5])
print(sys.argv[2]+'('+str(scores.getShareLocal())+'): '+sys.argv[3] + ' vs '+sys.argv[4]+'('+str(scores.getShareVisitor())+'): '+sys.argv[5])

#print('Sobre un máximo de 28')
#print('Local: '+str(scores.getLocal()))
#print('Visitante: '+str(scores.getVisitor()))
#print('Total: '+str(scores.getGlobal()))
#print('share '+teamLocalSlug+': ')
#print(scores.getShareLocal())
#print('share '+teamVisitorSlug+': ')
#print(scores.getShareVisitor())

if scores.getLocal() <= minGlobal :
    exit(bcolors.FAIL +"No tenemos suficientes estadísticas sobre la serie"+ bcolors.ENDC)

print('Añdadiendo serie al fichero de resultados...')

#file = open("results/results-"+seriesName+"-"+today, "w+")
file = open("results/results.txt", "a")

important = False
if (teamLocalShare < teamVisitorShare) and scores.getShareVisitor() < teamLocalShare:
    important = True
elif teamLocalShare > teamVisitorShare and scores.getShareLocal() < teamVisitorShare:
    important = True
if important:
    file.write('------------IMPORTANTE!!!-------------\n')
    print(bcolors.OKGREEN +'Detectado un resultado interesante'+ bcolors.ENDC)
else:
    file.write('-------------------------\n')
file.write(seriesName+'\n')
file.write('Local: '+teamLocalSlug+' ('+sys.argv[2]+') --> Share: '+str(scores.getShareLocal())+': ('+sys.argv[3] + ')\n')
file.write('Visitor: '+teamVisitorSlug+' ('+sys.argv[4]+') --> Share: '+str(scores.getShareVisitor())+': ('+sys.argv[5]+')\n')
file.write('-------------------------\n')
file.close()

exit(bcolors.OKBLUE +'Serie guardada con exito'+ bcolors.ENDC)