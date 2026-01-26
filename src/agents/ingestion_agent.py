import os
import json
import uuid
import time
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import google.generativeai as genai
from src.core.schema import KnowledgeBase, KnowledgeNode, Question, Difficulty, QuestionType
from src.core.config import Config

# Configure Gemini
if Config.get_api_key():
    genai.configure(api_key=Config.get_api_key())

import os
import json
import uuid
import time
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import google.generativeai as genai
from src.core.schema import KnowledgeBase, KnowledgeNode, Question, Difficulty, QuestionType
from src.core.config import Config

# Configure Gemini
if Config.get_api_key():
    genai.configure(api_key=Config.get_api_key())

class IngestionAgent:
    """
    Responsible for ingesting content using a Two-Pass 'Architect -> Builder' approach.
    Pass 1: Generate the full hierarchical skeleton (Structure).
    Pass 2: Generate questions for the leaf nodes (Content).
    """

    def __init__(self, data_dir: str = "data/uploads"):
        self.data_dir = data_dir
        self.model_name = Config.LLM_MODEL_NAME
        
        # Initialize Model
        if Config.get_api_key():
             self.model = genai.GenerativeModel(self.model_name)
        else:
             self.model = None
             print("⚠️ IngestionAgent initialized without API Key. Real calls will fail.")
        
        self.node_map = {} 
        self.usage_stats = {"input_tokens": 0, "output_tokens": 0, "calls": 0}

    def load_topic(self, topic_name: str) -> KnowledgeBase:
        """
        Main entry point.
        """
        # Reset stats
        self.usage_stats = {"input_tokens": 0, "output_tokens": 0, "calls": 0}
        self.node_map = {}
        
        topic_path = os.path.join(self.data_dir, topic_name)
        if not os.path.exists(topic_path):
            raise FileNotFoundError(f"Topic directory not found: {topic_path}")

        print(f"📖 Scanning {topic_path}...")
        context = self._load_raw_content(topic_path)
        print(f"🧠 Content loaded ({len(context)} chars).")

        start_time = time.time()
        
        # PASS 1: Generate Skeleton
        print("🏗️  PASS 1: Architecting Structure (One-shot)...")
        root_node = self._generate_full_skeleton(topic_name, context)
        self.node_map[root_node.id] = root_node
        
        # PASS 2: Populate Questions
        print("📝 PASS 2: Populating Content (Questions)...")
        self._populate_leaves(root_node, context)
        
        duration = time.time() - start_time

        # Build KB
        kb = KnowledgeBase(
            topic_name=topic_name,
            root=root_node,
            node_map=self.node_map
        )
        
        self._print_cost_summary(duration)
        return kb

    def _generate_full_skeleton(self, topic_name: str, context: str) -> KnowledgeNode:
        """
        Asks the LLM to plan the ENTIRE hierarchy in one go.
        """
        prompt = f"""
        You are a Senior Curriculum Architect. 
        Create a hierarchical learning path for the topic: "{topic_name}".
        
        Output a Nested JSON Object representing the curriculum tree.
        
        Rules:
        1. **Avoid Infinite Depth**: Max depth is {Config.MAX_HIERARCHY_DEPTH} (e.g. Topic -> Sub -> ... -> Leaf).
        2. **Balanced Width**: Group related concepts logically ({Config.SUBTOPICS_PER_NODE[0]}-{Config.SUBTOPICS_PER_NODE[1]} items per group).
        3. **Atomic Leaves**: The deepest nodes must be specific concepts testable by simple questions.
        
        JSON Structure:
        {{
            "name": "{topic_name}",
            "description": "...",
            "children": [
                {{
                    "name": "Sub Topic A",
                    "description": "...",
                    "children": [
                        {{ "name": "Concept A1", "description": "...", "children": [] }},
                        ...
                    ]
                }},
                ...
            ]
        }}
        
        Content Reference:
        {context[:80000]}
        """
        
        try:
            if not self.model: raise Exception("No API Key")
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            self._update_costs(response)
            data = json.loads(response.text)
            
            # Recursive helper to build KnowledgeNodes from JSON
            def build_node_recursive(data_dict, parent_path, parent_id):
                node_id = str(uuid.uuid4())
                current_path = f"{parent_path} > {data_dict['name']}" if parent_path else data_dict['name']
                
                # Check if leaf (no children in JSON or empty children)
                raw_children = data_dict.get("children", [])
                
                node = KnowledgeNode(
                    id=node_id,
                    name=data_dict["name"],
                    description=data_dict.get("description", ""),
                    path=current_path,
                    parent_id=parent_id,
                    is_leaf=(len(raw_children) == 0),
                    children=[]
                )
                self.node_map[node_id] = node
                
                for child_data in raw_children:
                    child_node = build_node_recursive(child_data, current_path, node_id)
                    node.children.append(child_node)
                
                return node

            return build_node_recursive(data, "", None)

        except Exception as e:
            print(f"      ⚠️ Error in structure generation: {e}")
            # Fallback root
            fallback = KnowledgeNode(id="root_fallback", name=topic_name, description="Fallback", path=topic_name, is_leaf=True)
            self.node_map[fallback.id] = fallback
            return fallback

    def _populate_leaves(self, node: KnowledgeNode, context: str):
        """
        Traverses the tree. If it finds a LEAF, it generates questions.
        """
        if node.is_leaf:
            print(f"      Generating questions for leaf: {node.name}")
            node.questions = self._generate_leaf_questions(node, context)
            return
        
        # Recurse
        for child in node.children:
            self._populate_leaves(child, context)

    def _generate_leaf_questions(self, node: KnowledgeNode, context: str) -> Dict[Difficulty, List[Question]]:
        questions = {d: [] for d in Difficulty}
        
        # Build prompt counts dynamically from Config
        counts = Config.QUESTIONS_PER_LEAF
        count_desc = f"- {counts.get('beginner', 2)} BEGINNER questions.\n" \
                     f"- {counts.get('intermediate', 2)} INTERMEDIATE questions.\n" \
                     f"- {counts.get('advanced', 1)} ADVANCED question."

        prompt = f"""
        Generate questions for the specific concept: "{node.path}".
        Description: {node.description}
        
        Create:
        {count_desc}
        
        Output JSON:
        {{
            "questions": [
                {{
                    "difficulty": "beginner" | "intermediate" | "advanced",
                    "content": "Question text...",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "A", 
                    "explanation": "..."
                }}
            ]
        }}
        
        Focus ONLY on valid sub-content relevant to: {node.name}
        Context:
        {context[:30000]}
        """
        try:
            if not self.model: raise Exception("No API Key")
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            self._update_costs(response)
            data = json.loads(response.text)
            
            for item in data.get("questions", []):
                diff_str = item.get("difficulty", "beginner").lower()
                try: diff_enum = Difficulty(diff_str)
                except: diff_enum = Difficulty.BEGINNER
                
                q = Question(
                    id=str(uuid.uuid4()),
                    difficulty=diff_enum,
                    type=QuestionType.MULTIPLE_CHOICE,
                    content=item["content"],
                    options=item.get("options", []),
                    correct_answer=item.get("correct_answer", ""),
                    explanation=item.get("explanation", ""),
                    metadata={"generated_by": "gemini", "model": self.model_name}
                )
                questions[diff_enum].append(q)
            return questions
        except Exception as e:
            print(f"      ⚠️ Error generating questions for {node.name}: {e}")
            return questions

    def _update_costs(self, response):
        try:
            if hasattr(response, 'usage_metadata'):
                self.usage_stats["input_tokens"] += response.usage_metadata.prompt_token_count
                self.usage_stats["output_tokens"] += response.usage_metadata.candidates_token_count
                self.usage_stats["calls"] += 1
        except: pass

    def _print_cost_summary(self, duration: float):
        in_cost = (self.usage_stats["input_tokens"] / 1_000_000) * Config.PRICE_PER_1M_INPUT_TOKENS
        out_cost = (self.usage_stats["output_tokens"] / 1_000_000) * Config.PRICE_PER_1M_OUTPUT_TOKENS
        total_cost = in_cost + out_cost
        
        print("\n" + "="*50)
        print(f"💰 INGESTION COMPLETE in {duration:.2f}s")
        print(f"   Model: {self.model_name}")
        print(f"   API Calls: {self.usage_stats['calls']}")
        print(f"   Input Tokens:  {self.usage_stats['input_tokens']:,}")
        print(f"   Output Tokens: {self.usage_stats['output_tokens']:,}")
        print(f"   Est. Cost:     ${total_cost:.5f}")
        print("="*50 + "\n")
    
    def _load_raw_content(self, topic_path: str) -> str:
        buffer = ""
        # 1. Files
        if os.path.exists(topic_path):
            for f in os.listdir(topic_path):
                if f.endswith(".txt") or f.endswith(".md"):
                    if f in ["links.txt", "urls.txt"]: continue
                    with open(os.path.join(topic_path, f), "r") as file:
                        buffer += f"\n--- FILE: {f} ---\n{file.read()}"
        # 2. URLs
        links = next((f for f in ["links.txt", "urls.txt"] if os.path.exists(os.path.join(topic_path, f))), None)
        if links:
            with open(os.path.join(topic_path, links), "r") as f:
                urls = [l.strip() for l in f.readlines() if l.strip()]
                for url in urls:
                    buffer += f"\n--- URL: {url} ---\n{self._fetch_url_content(url)}"
        return buffer

    def _fetch_url_content(self, url: str) -> str:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            for s in soup(["script", "style", "nav", "footer"]): s.decompose()
            return soup.get_text()[:20000]
        except: return ""

if __name__ == "__main__":
    agent = IngestionAgent()
    try:
        if not os.path.exists("data/uploads/python_basics"):
             os.makedirs("data/uploads/python_basics", exist_ok=True)
             with open("data/uploads/python_basics/intro_to_python.txt", "w") as f:
                 f.write("Python is a high-level programming language.")

        kb = agent.load_topic("python_basics")
        print(f"✅ Success! Generated KnowledgeBase for '{kb.topic_name}'")
        
        output_path = f"data/db/{kb.topic_name}.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(kb.model_dump_json(indent=2))
        print(f"💾 Saved to {output_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
