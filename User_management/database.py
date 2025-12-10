from neo4j import GraphDatabase

URI = "neo4j://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "your_password_here"   # Change this

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def get_db():
    return driver.session()
