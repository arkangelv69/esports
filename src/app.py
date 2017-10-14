from neo4j.v1 import GraphDatabase
import json

with open('config.json') as json_data_file:
    cfg = json.load(json_data_file)

print(cfg)

uri = "bolt://"+cfg['database']['domain']+":7687"
driver = GraphDatabase.driver(uri, auth=(cfg['database']['username'], cfg['database']['password']))

game = "csgo"
teamLocalSlug = "beacon-esports"
teamVisitorSlug = "limitless"

scoreGlobal = 0
scoreLocal = 0
scoreVisitor = 0

class Team:
    def __init__(self, attributes, stats, country):
        self.attributes = attributes
        self.stats = stats
        self.country = country

def getTeamBySlugAndGame(slug, game):
    with driver.session() as session:
        with session.begin_transaction() as tx:
            query = "MATCH (tm:Team)-[:PLAYS]->(g:Game)<-[:BELONGS]-(gp:GameProvider{slug:{game}}) \
            MATCH (tm)<-[:BELONGS]-(tmp:TeamProvider) \
            MATCH (tm)-[:HAS]->(st:Stat) \
            MATCH (tm)-[:BELONGS]->(c:Country)<-[:BELONGS]-(cp:CountryProvider) \
            WHERE tmp.slug = {slug} \
            RETURN tmp,st,cp"

            for record in tx.run(query, slug=slug, game=game):
                output = Team(record['tmp'],json.loads(record['st']['stats']),record['cp'])
                return output

localTeam = getTeamBySlugAndGame(teamLocalSlug, game)
visitorTeam = getTeamBySlugAndGame(teamVisitorSlug, game)
