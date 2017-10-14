from neo4j.v1 import GraphDatabase
import json

uri = "bolt://domain:7687"
driver = GraphDatabase.driver(uri, auth=("neo4j", "xxxxx"))

game = "csgo"
teamLocalSlug = "beacon-esports"
teamVisitorSlug = "limitless"

class Team:
    def __init__(self, attributes, stats):
        self.attributes = attributes
        self.stats = stats

def getTeamBySlugAndGame(slug, game):
    with driver.session() as session:
        with session.begin_transaction() as tx:
            query = "MATCH (tm:Team)-[:PLAYS]->(g:Game)<-[:BELONGS]-(gp:GameProvider{slug:{game}}) \
            MATCH (tm)<-[:BELONGS]-(tmp:TeamProvider) \
            MATCH (tm)-[:HAS]->(st:Stat) \
            WHERE tmp.slug = {slug} \
            RETURN tmp,st"

            for record in tx.run(query, slug=slug, game=game):
                output = Team(record['tmp'],json.loads(record['st']['stats']))
                return output

localTeam = getTeamBySlugAndGame(teamLocalSlug, game)
visitorTeam = getTeamBySlugAndGame(teamVisitorSlug, game)
