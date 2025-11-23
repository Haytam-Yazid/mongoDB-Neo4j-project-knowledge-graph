from pymongo import MongoClient
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from pymongo.errors import ConnectionFailure
import sys

MONGO_URI = (
    "mongodb_srv_here"
)
MONGODB_DB = "CSC_CourseCatalog"
NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "local4444"
NEO4J_DB = "catalogcsc"

def check_mongo_connection():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        print("[OK] Connected to MongoDB Atlas")
        return client
    except ConnectionFailure as e:
        print(f"[ERROR] Could not connect to MongoDB Atlas: {e}")
        sys.exit(1)

def check_neo4j_connection():
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session(database=NEO4J_DB) as session:
            session.run("RETURN 1")
        print("[OK] Connected to Neo4j")
        return driver
    except ServiceUnavailable as e:
        print(f"[ERROR] Could not connect to Neo4j: {e}")
        sys.exit(1)

def transfer_courses(mongo_client, neo4j_driver):
    db = mongo_client[MONGODB_DB]
    collections = db.list_collection_names()
    print(f"[INFO] Found collections: {collections}")

    with neo4j_driver.session(database=NEO4J_DB) as session:
        for coll_name in collections:
            print(f"\n[INFO] Processing collection: {coll_name}")
            collection = db[coll_name]
            courses = collection.find({})

            for course in courses:
                code = course.get("Course Code")
                if not code:
                    continue
                title = course.get("Course Title", "")
                desc = course.get("Course Description", "")
                discipline = course.get("Course Discipline", "")
                category = course.get("Category", "")
                subcategory = course.get("Subcategory", "")
                status = course.get("Status", "")
                prereqs = course.get("PreOrCoRequisites", [])
                credits = course.get("Number of Credits", 0)
                try:
                    credits = int(credits)
                except (ValueError, TypeError):
                    credits = 0

                session.run("""
                    MERGE (c:Course {code: $code})
                    SET c.title = $title,
                        c.description = $desc,
                        c.discipline = $discipline,
                        c.credits = $credits
                """, {
                    "code": code,
                    "title": title,
                    "desc": desc,
                    "discipline": discipline,
                    "credits": credits
                })

                if category:
                    session.run("""
                        MERGE (cat:Category {name: $category})
                        MERGE (c:Course {code: $code})
                        MERGE (c)-[:BELONGS_TO_CATEGORY]->(cat)
                    """, {"category": category, "code": code})

                if subcategory:
                    session.run("""
                        MERGE (sub:SubCategory {name: $subcategory})
                        MERGE (c:Course {code: $code})
                        MERGE (c)-[:BELONGS_TO_SUBCATEGORY]->(sub)
                    """, {"subcategory": subcategory, "code": code})

                if status:
                    session.run("""
                        MERGE (s:Status {name: $status})
                        MERGE (c:Course {code: $code})
                        MERGE (c)-[:HAS_STATUS]->(s)
                    """, {"status": status, "code": code})

                if prereqs:
                    for prereq_code in prereqs:
                        if prereq_code and isinstance(prereq_code, str):
                            session.run("""
                                MERGE (p:Course {code: $prereq_code})
                                MERGE (c:Course {code: $code})
                                MERGE (p)-[:PREREQUISITE_FOR]->(c)
                            """, {"prereq_code": prereq_code, "code": code})

    print("\n [DONE] All data successfully transferred to Neo4j.\n")

if __name__ == "__main__":
    mongo_client = check_mongo_connection()
    neo4j_driver = check_neo4j_connection()
    transfer_courses(mongo_client, neo4j_driver)