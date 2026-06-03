# librarian/librarian_engine.py

# Import the native Abstract Syntax Tree module to break Python source code down into logical compiler tree nodes.
import ast
# Import the os module to calculate dynamic path configurations relative to the absolute script placement.
import os
# Import ChromaDB to act as the local, air-gapped, high-performance vector database persistence layer.
import chromadb
# Import SentenceTransformer to compute dense vector embeddings completely offline on local hardware.
from sentence_transformers import SentenceTransformer
# Import datetime to create precise time-series operational log markers.
from datetime import datetime

# Relative path computation mapping vectors to the absolute runtime scaffolding folder configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_CODE_DIR = os.path.join(BASE_DIR, "target_service", "app")
VECTOR_DB_DIR = os.path.join(BASE_DIR, "reports", "chroma_storage")
COLLECTION_NAME = "aethelgard_code_blueprint"

class LocalAIOpsLibrarian:
    def __init__(self):
        # Initialize the deep learning sentence transformer model natively on the host workstation processing matrix.
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        # Instantiate a persistent disk client connection framework targeting our specified local DB layout path.
        self.db_client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
        # Create or pull the active unique vector collection tracking our targeted microservice architecture.
        self.collection = self.db_client.get_or_create_collection(name=COLLECTION_NAME)

    def parse_repository_via_ast(self):
        """
        Walks the target microservice filesystem, compiles raw Python scripts into Abstract 
        Syntax Trees, and extracts complete functions and route blocks with full logical context.
        """
        # Array collection tracking structured data dictionaries representing code scopes.
        chunks = []
        # Fallback safeguard check to establish directory existence boundaries before entering loops.
        if not os.path.exists(TARGET_CODE_DIR):
            return chunks
            
        # Programmatically walk the target application filesystem directories looking for source assets.
        for root, _, files in os.walk(TARGET_CODE_DIR):
            for file in files:
                # Isolate target files by ensuring extension adherence and discarding layout private files.
                if file.endswith(".py") and not file.startswith("__"):
                    # Derive readable reference path tokens for clear data tracking markers.
                    file_path = os.path.relpath(os.path.join(root, file), start=BASE_DIR)
                    # Formulate explicit absolute system address targets.
                    abs_path = os.path.join(root, file)
                    
                    # Extract the contents of the file string cleanly into standard memory bounds.
                    with open(abs_path, "r", encoding="utf-8") as f:
                        source_content = f.read()
                        
                    try:
                        # Convert the complete code file string into a structured compiler Abstract Syntax Tree map.
                        root_ast_node = ast.parse(source_content, filename=file_path)
                        # Split the master string array to accurately reconstruct source lines dynamically.
                        lines = source_content.splitlines()
                        
                        # Traversal loop searching inside the AST map for specific functional declarations.
                        for node in ast.walk(root_ast_node):
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                # Establish starting coordinates of the code snippet block.
                                start_line = node.lineno
                                # Derive ending boundary points safely via structural attribute flags.
                                end_line = getattr(node, "end_lineno", len(lines))
                                # Re-assemble the text snippet representing the unbroken functional code body structure.
                                code_body = "\n".join(lines[start_line - 1 : end_line])
                                
                                # Format immutable telemetry metadata mapping arrays to inject clear prompt scopes.
                                chunk_metadata = {
                                    "file_path": str(file_path),
                                    "entity_name": str(node.name),
                                    "start_line": int(start_line),
                                    "end_line": int(end_line),
                                    "type": "async_route" if isinstance(node, ast.AsyncFunctionDef) else "standard_function"
                                }
                                
                                # Append structured tracking metrics to our execution array block queue.
                                chunks.append({
                                    "code": code_body,
                                    "metadata": chunk_metadata,
                                    "id": f"{file_path}_{node.name}_{start_line}"
                                })
                    except Exception:
                        pass
        return chunks

    def sync_codebase_index(self):
        """
        Converts the extracted structural codebase syntax trees into dense tensors and upserts to ChromaDB.
        """
        # Execute the logical AST filesystem compilation sweep tracker.
        chunks = self.parse_repository_via_ast()
        if not chunks:
            return
            
        # Initialize storage collection arrays to batch-load parameters into ChromaDB database layers.
        documents, metadatas, ids, text_to_embed = [], [], [], []
        
        # Populate serialization lists by mapping parsed data matrices out of code attributes.
        for item in chunks:
            documents.append(item["code"])
            metadatas.append(item["metadata"])
            ids.append(item["id"])
            # Inject explicit contextual enrichment prefixes into the array to sharpen vector closeness scores.
            text_to_embed.append(f"File: {item['metadata']['file_path']} | Function: {item['metadata']['entity_name']} \n {item['code']}")
            
        # Execute parallel forward-pass tensor weights calculations locally using our transformer architecture.
        embeddings = self.embedding_model.encode(text_to_embed, show_progress_bar=False)
        # Cast the calculated multi-dimensional arrays safely into primitive float list structures.
        vector_list = [v.tolist() for v in embeddings]
        
        # Upsert metrics natively to ensure the local database index file matches current file coordinates.
        self.collection.upsert(
            embeddings=vector_list,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def search_suspicious_logic(self, incident_query, top_k=1):
        """
        Queries the indexed codebase embeddings using cosine distance proximity sweeps.
        """
        # Transform incoming analytical metric string contexts into numerical tensor vector points.
        query_vector = self.embedding_model.encode(incident_query).tolist()
        # Perform query checks directly against the air-gapped database collection index limits.
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k
        )
        return results

if __name__ == "__main__":
    # Self-contained validation runner instantiation block.
    engine = LocalAIOpsLibrarian()
    # Synchronize vector storage states.
    engine.sync_codebase_index()
    # Output success frame.
    print(f"[{datetime.now()}] Base codebase successfully indexed into local ChromaDB memory storage clusters.")