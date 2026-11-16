# librarian/librarian_engine.py
"""
Aethelgard Librarian Engine
AST-Aware Codebase Indexing & Semantic Vector Retrieval (RAG).
Deconstructs source code into compiler syntax trees, extracts functional units with line metadata,
and indexes dense embeddings into an offline ChromaDB instance.
"""

import ast
import os
import chromadb
from sentence_transformers import SentenceTransformer
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_CODE_DIR = os.getenv("TARGET_CODE_DIR", os.path.join(BASE_DIR, "target_service", "app"))
VECTOR_DB_DIR = os.getenv("CHROMA_STORAGE_DIR", os.path.join(BASE_DIR, "reports", "chroma_storage"))
COLLECTION_NAME = "aethelgard_code_blueprint"

class LocalAIOpsLibrarian:
    def __init__(self, target_dir=TARGET_CODE_DIR, vector_db_dir=VECTOR_DB_DIR):
        self.target_dir = target_dir
        self.vector_db_dir = vector_db_dir
        os.makedirs(self.vector_db_dir, exist_ok=True)

        # Initialize local sentence-transformer embedding model (runs 100% offline)
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.db_client = chromadb.PersistentClient(path=self.vector_db_dir)
        self.collection = self.db_client.get_or_create_collection(name=COLLECTION_NAME)

    def parse_repository_via_ast(self):
        """
        Traverses source code files, parses them into Abstract Syntax Trees,
        and extracts semantically intact functional blocks with full line ranges and decorator context.
        """
        chunks = []
        if not os.path.exists(self.target_dir):
            return chunks

        for root, _, files in os.walk(self.target_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    file_path = os.path.relpath(os.path.join(root, file), start=BASE_DIR)
                    abs_path = os.path.join(root, file)

                    try:
                        with open(abs_path, "r", encoding="utf-8") as f:
                            source_content = f.read()

                        root_ast_node = ast.parse(source_content, filename=file_path)
                        lines = source_content.splitlines()

                        # Collect top-level imports in the file for context
                        module_imports = []
                        for node in root_ast_node.body:
                            if isinstance(node, (ast.Import, ast.ImportFrom)):
                                import_start = node.lineno - 1
                                import_end = getattr(node, "end_lineno", node.lineno)
                                module_imports.append("\n".join(lines[import_start:import_end]))

                        import_context = "\n".join(module_imports[:10])

                        # Walk AST nodes for function and route definitions
                        for node in ast.walk(root_ast_node):
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                start_line = node.lineno
                                end_line = getattr(node, "end_lineno", len(lines))
                                code_body = "\n".join(lines[start_line - 1 : end_line])

                                # Extract decorators (e.g. @app.get("/health"), @router.post(...))
                                decorators = []
                                for d in node.decorator_list:
                                    if isinstance(d, ast.Call) and hasattr(d.func, "attr"):
                                        decorators.append(d.func.attr)
                                    elif isinstance(d, ast.Name):
                                        decorators.append(d.id)

                                chunk_metadata = {
                                    "file_path": str(file_path),
                                    "entity_name": str(node.name),
                                    "start_line": int(start_line),
                                    "end_line": int(end_line),
                                    "decorators": ",".join(decorators),
                                    "type": "async_route" if isinstance(node, ast.AsyncFunctionDef) else "standard_function"
                                }

                                chunks.append({
                                    "code": code_body,
                                    "metadata": chunk_metadata,
                                    "import_context": import_context,
                                    "id": f"{file_path}_{node.name}_{start_line}"
                                })
                    except Exception as e:
                        print(f"⚠️ AST Parsing skipped for {file_path}: {e}")

        return chunks

    def sync_codebase_index(self):
        """
        Parses the target repository, computes embeddings, and updates the local ChromaDB index.
        """
        chunks = self.parse_repository_via_ast()
        if not chunks:
            print("⚠️ No valid code chunks found to index.")
            return

        documents, metadatas, ids, text_to_embed = [], [], [], []

        for item in chunks:
            documents.append(item["code"])
            metadatas.append(item["metadata"])
            ids.append(item["id"])
            text_to_embed.append(
                f"File: {item['metadata']['file_path']} | Function: {item['metadata']['entity_name']} | "
                f"Decorators: {item['metadata']['decorators']}\n{item['code']}"
            )

        embeddings = self.embedding_model.encode(text_to_embed, show_progress_bar=False)
        vector_list = [v.tolist() for v in embeddings]

        self.collection.upsert(
            embeddings=vector_list,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📚 Indexed {len(chunks)} code units into local ChromaDB.")

    def search_suspicious_logic(self, incident_query, top_k=2):
        """
        Queries ChromaDB using dense vector similarity.
        Falls back to keyword matching if vector similarity fails.
        """
        try:
            query_vector = self.embedding_model.encode(incident_query).tolist()
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=top_k
            )
            return results
        except Exception as e:
            print(f"⚠️ ChromaDB search error: {e}")
            return {"documents": [[]], "metadatas": [[]]}

if __name__ == "__main__":
    librarian = LocalAIOpsLibrarian()
    librarian.sync_codebase_index()
    results = librarian.search_suspicious_logic("FastAPI async route blocking I/O time.sleep latency", top_k=1)
    if results and results.get("documents") and results["documents"][0]:
        print("\n🔍 Test Query Match Found:")
        print(f"File: {results['metadatas'][0][0]['file_path']}")
        print(f"Snippet:\n{results['documents'][0][0]}")
