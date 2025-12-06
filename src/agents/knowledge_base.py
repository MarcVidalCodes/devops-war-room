import os
import lancedb
import pandas as pd
from typing import List, Dict, Any, Optional
from langchain_ollama import OllamaEmbeddings


class IncidentKnowledgeBase:
    """
    The 'Long-Term Memory' for the DevOps Agents.

    Uses LanceDB (Vector Database) to store and retrieve past incidents.
    This allows the AI to learn from experience (RAG - Retrieval Augmented Generation).
    """

    def __init__(self, db_path: str = "data/lancedb"):
        """
        Initialize the Knowledge Base.

        Args:
            db_path: Local path to store the vector database
        """
        self.db_path = db_path

        # Ensure directory exists
        os.makedirs(db_path, exist_ok=True)

        # Connect to LanceDB
        self.db = lancedb.connect(db_path)

        # Initialize Embeddings Model (Ollama)
        # This converts text into numbers (vectors)
        # Requires: ollama pull nomic-embed-text
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")

        # Create or open the table
        self.table_name = "incidents"
        self._init_table()

    def _init_table(self):
        """Initialize the incidents table if it doesn't exist."""
        if self.table_name not in self.db.table_names():
            # Define schema implicitly by creating a dummy empty dataframe
            # LanceDB is flexible, but having a schema helps
            schema = {
                "vector": [0.0] * 768,  # Gemini embedding dimension
                "alert_name": "init",
                "diagnosis": "init",
                "root_cause": "init",
                "fix": "init",
                "timestamp": "init",
            }
            # We don't strictly need to create it here if we use 'create_table' later
            # but it's good practice to check connection.
            pass

    def add_incident(self, alert_name: str, diagnosis: str, root_cause: str, fix: str):
        """
        Save a resolved incident to memory.
        
        Args:
            alert_name: The alert that fired (e.g., "HighErrorRate")
            diagnosis: The full diagnosis text
            root_cause: The specific root cause identified
            fix: The action taken to fix it
        """
        # 1. Vectorize the "symptoms" (alert name + root cause)
        # We want to find similar root causes in the future
        text_to_embed = f"{alert_name}: {root_cause}"
        vector = self.embeddings.embed_query(text_to_embed)

        # 2. Store in LanceDB
        data = [
            {
                "vector": vector,
                "alert_name": alert_name,
                "diagnosis": diagnosis,
                "root_cause": root_cause,
                "fix": fix,
                "timestamp": pd.Timestamp.now().isoformat(),
            }
        ]

        if self.table_name in self.db.table_names():
            self.db.open_table(self.table_name).add(data)
        else:
            self.db.create_table(self.table_name, data)

    def search_similar(
        self, alert_name: str, current_symptoms: str, limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find similar past incidents.

        Args:
            alert_name: The current alert
            current_symptoms: Description of what's happening now
            limit: How many results to return

        Returns:
            List of similar past incidents
        """
        if self.table_name not in self.db.table_names():
            return []

        # 1. Vectorize the current situation
        query_text = f"{alert_name}: {current_symptoms}"
        query_vector = self.embeddings.embed_query(query_text)

        # 2. Search the database
        results = (
            self.db.open_table(self.table_name)
            .search(query_vector)
            .limit(limit)
            .to_pandas()
        )

        # 3. Convert to list of dicts
        return results.to_dict(orient="records")
