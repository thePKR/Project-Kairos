import os
import datetime
from src.utils import get_neo4j_driver

class KairosGraphManager:
    def __init__(self):
        try:
            self.driver = get_neo4j_driver()
        except Exception as e:
            print(f"[Memory Warning] Neo4j driver could not be initialized: {e}")
            self.driver = None

    def retrieve_context(self, objective: str) -> str:
        """
        Retrieves context of past objectives that are textually similar.
        Increments access_count for LRU optimization.
        """
        if not self.driver: return ""
        
        # Fetch up to 3 recently accessed objectives that might loosely relate
        query = """
        MATCH (o:Objective)-[:GENERATED]->(t:Task)-[:CREATED]->(f:File)
        WHERE toLower(o.name) CONTAINS toLower($keyword) OR toLower($objective) CONTAINS toLower(o.name)
        SET o.last_accessed = datetime(), o.access_count = coalesce(o.access_count, 1) + 1
        RETURN o.name AS obj_ext, collect(DISTINCT t.name) AS tasks, collect(DISTINCT f.path) AS files
        LIMIT 3
        """
        
        # Simple extraction of primary keyword to maximize matches without full-text search backend
        keyword = objective.split()[0] if objective else ""
        
        context_blocks = []
        try:
            with self.driver.session() as session:
                result = session.run(query, keyword=keyword, objective=objective)
                for record in result:
                    context_blocks.append(
                        f"Past Objective: {record['obj_ext']}\n"
                        f"Generated Tasks: {', '.join(record['tasks'][:5])}\n"
                        f"Files Architected: {', '.join(record['files'][:5])}"
                    )
        except Exception as e:
            print(f"[Memory Error] Neo4j read failed (are credentials set?): {e}")
            return ""
                
        if context_blocks:
            return "HISTORICAL CONTEXT (Past Swarm Generations):\n" + "\n---\n".join(context_blocks)
        return ""

    def archive_project(self, objective: str, dep_graph: dict, final_files: dict):
        """
        Saves the dynamically generated file-tree and dependency map into the graph deeply.
        """
        if not self.driver: return
        
        query = """
        MERGE (o:Objective {name: $objective})
        ON CREATE SET o.created_at = datetime(), o.last_accessed = datetime(), o.access_count = 1
        ON MATCH SET o.last_accessed = datetime(), o.access_count = coalesce(o.access_count, 1) + 1
        
        WITH o
        UNWIND $tasks AS task
        MERGE (t:Task {name: task.name})
        ON CREATE SET t.description = task.desc
        MERGE (o)-[:GENERATED]->(t)
        
        WITH o, t
        UNWIND $files AS file
        MERGE (f:File {path: file.path})
        MERGE (t)-[:CREATED]->(f)
        """
        
        tasks_param = [{"name": k, "desc": str(v)} for k, v in dep_graph.items() if isinstance(dep_graph, dict)]
        files_param = [{"path": k} for k in final_files.keys()] if isinstance(final_files, dict) else []
        
        if not tasks_param or not files_param: return
        
        try:
            with self.driver.session() as session:
                session.run(query, objective=objective, tasks=tasks_param, files=files_param)
                print("[Memory] Successfully permanently archived project blueprint in Neo4j.")
        except Exception as e:
            print(f"[Memory Error] Neo4j write failed: {e}")

    def cull_forgotten_memories(self):
        """
        The LRU Graph Janitor.
        Deletes Objective subgraphs that haven't been accessed in 14 days and have access_count < 5.
        """
        if not self.driver: return
        
        query = """
        MATCH (o:Objective)
        WHERE o.last_accessed < datetime() - duration('P14D') AND coalesce(o.access_count, 0) < 5
        OPTIONAL MATCH (o)-[:GENERATED]->(t:Task)
        OPTIONAL MATCH (t)-[:CREATED]->(f:File)
        DETACH DELETE o, t, f
        RETURN count(o) AS deleted_objectives
        """
        try:
            with self.driver.session() as session:
                result = session.run(query)
                record = result.single()
                deleted = record["deleted_objectives"] if record else 0
                print(f"[Janitor] Cleaned up {deleted} forgotten objective memories from the graph.")
        except Exception as e:
            print(f"[Janitor Error] {e}")
