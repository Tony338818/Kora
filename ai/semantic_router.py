# from sentence_transformers import SentenceTransformer, util
# import torch
# import os

# EMBEDDINGS_PATH = "route_embeddings.pt"

# class SemanticRouter:
#     def __init__(self):
#         # 1. Load the model on my machine
#         self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
#         # 2. Define anchors
#         self.routes = {
#             'casual_conversation': [
#                 "hello", "hi", "hey", "yo", "good morning", "good evening",
#                 "how are you", "how are you doing", "how far", "what's up",
#                 "sup", "how's it going", "are you there", "you there",
#                 "i need help", "can you help me", "i have a question",
#                 "okay", "alright", "hmm", "interesting", "i see",
#                 "thanks", "thank you", "nice one",
#                 "i don't understand", "this is confusing"
#             ],

#             'inventory_conversation': [
#                 "we bought 10 bags of rice",
#                 "we bought 5 cartons of milk",
#                 "add stock for rice",
#                 "add 20 bottles of coke",
#                 "we received new inventory",
#                 "new goods just arrived",
#                 "increase stock for beans",
#                 "reduce stock of yam",
#                 "remove 2 items from stock",
#                 "how many bags of rice do we have",
#                 "what is left in inventory",
#                 "check stock for eggs",
#                 "do we have sugar left",
#                 "current inventory status"
#             ],

#             'sales_conversation': [
#                 "we sold 5 items",
#                 "we sold 3 bags of rice",
#                 "record a sale",
#                 "customer bought 3 shirts",
#                 "customer purchased 2 bottles of coke",
#                 "log this sale",
#                 "we made a sale",
#                 "i just sold something",
#                 "how much did we sell today",
#                 "total sales for today",
#                 "sales summary",
#                 "how many items sold today"
#             ]
#         }
                
#         # 3. Pre-compute embeddings
#         if os.path.exists(EMBEDDINGS_PATH):
#             print("Loading saved embeddings...")
#             self.route_embeddings = torch.load(EMBEDDINGS_PATH)
#         else:
#             print("Computing embeddings...")
#             self.route_embeddings = {}

#             for route_name, anchors in self.routes.items():
#                 self.route_embeddings[route_name] = self.model.encode(
#                     anchors, convert_to_tensor=True
#                 )

#             torch.save(self.route_embeddings, EMBEDDINGS_PATH)
            
            
#     def route(self, user_query, session=None, threshold=0.5):
#         """ 
#         Takes a user query and returns the name of the best LLM to handle it.
#         """
        
#         # 1. Embed incoming messages
#         query_embedding = self.model.encode(user_query, convert_to_tensor=True)
        
#         best_route = None
#         highest_score = -1.0
        
#         last_intent = session.get("last_intent") if session else None
#         mode = session.get("mode") if session else None
        
#         # 2. Compare the embeddings
#         for route_name, anchor_embeddings in self.route_embeddings.items():
#             # util.cos_sim compares the query to ALL anchors in this route at once
#             cosine_scores = util.cos_sim(query_embedding, anchor_embeddings)
            
#             # find the highest matching anchor in a specific route
#             max_score = torch.max(cosine_scores).item()
            
#             if route_name == last_intent:
#                 max_score += 0.10

#             if mode == "task" and (route_name == "inventory_conversation" or route_name == "sales_conversation"):
#                 max_score += 0.15
            
#             if max_score > highest_score:
#                 highest_score = max_score
#                 best_route = route_name
                
#         # 3. The Fallback Safety Net
#         # If the highest score is lower than our threshold, the query is likely unrelated
#         if highest_score < threshold:
#             return "Fallback_General_LLM", highest_score
            
#         return {
#             'best_route' : best_route, 
#             'highest_score': highest_score
#         }


from sentence_transformers import SentenceTransformer, util
import torch
import os

EMBEDDINGS_PATH = "route_embeddings.pt"

class SemanticRouter:
    def __init__(self):
        print("Initializing SemanticRouter...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.routes = {
            'casual_conversation': [
                "hello", "hi", "hey", "yo", "good morning", "good evening",
                "how are you", "how are you doing", "how far", "what's up",
                "sup", "how's it going", "are you there", "you there",
                "i need help", "can you help me", "i have a question",
                "okay", "alright", "hmm", "interesting", "i see",
                "thanks", "thank you", "nice one",
                "i don't understand", "this is confusing"
            ],
            'inventory_conversation': [
                "we bought 10 bags of rice",
                "we bought 5 cartons of milk",
                "add stock for rice",
                "add 20 bottles of coke",
                "we received new inventory",
                "new goods just arrived",
                "increase stock for beans",
                "reduce stock of yam",
                "remove 2 items from stock",
                "how many bags of rice do we have",
                "what is left in inventory",
                "check stock for eggs",
                "do we have sugar left",
                "current inventory status"
            ],
            'sales_conversation': [
                "we sold 5 items",
                "we sold 3 bags of rice",
                "record a sale",
                "customer bought 3 shirts",
                "customer purchased 2 bottles of coke",
                "log this sale",
                "we made a sale",
                "i just sold something",
                "how much did we sell today",
                "total sales for today",
                "sales summary",
                "how many items sold today"
            ]
        }
        
        # Load or compute embeddings ONCE
        self._load_embeddings()
        print("SemanticRouter initialized!")
        
    def _load_embeddings(self):
        """Load embeddings from file or compute them"""
        if os.path.exists(EMBEDDINGS_PATH):
            print("Loading saved embeddings...")
            self.route_embeddings = torch.load(EMBEDDINGS_PATH)
        else:
            print("Computing embeddings (this happens only once)...")
            self.route_embeddings = {}
            for route_name, anchors in self.routes.items():
                self.route_embeddings[route_name] = self.model.encode(
                    anchors, convert_to_tensor=True
                )
            torch.save(self.route_embeddings, EMBEDDINGS_PATH)
            
    def route(self, user_query, session=None, threshold=0.5):
        """
        Takes a user query and returns the name of the best route.
        Uses pre-computed embeddings - NO file loading happens here.
        """
        query_embedding = self.model.encode(user_query, convert_to_tensor=True)
        
        best_route = None
        highest_score = -1.0
        
        last_intent = session.get("last_intent") if session else None
        mode = session.get("mode") if session else None
        
        # Compare using in-memory embeddings
        for route_name, anchor_embeddings in self.route_embeddings.items():
            cosine_scores = util.cos_sim(query_embedding, anchor_embeddings)
            max_score = torch.max(cosine_scores).item()
            
            if route_name == last_intent:
                max_score += 0.10
            if mode == "task" and (route_name == "inventory_conversation" or route_name == "sales_conversation"):
                max_score += 0.15
            
            if max_score > highest_score:
                highest_score = max_score
                best_route = route_name
        
        if highest_score < threshold:
            return {"best_route": "Fallback_General_LLM", "highest_score": highest_score}
            
        return {
            'best_route': best_route, 
            'highest_score': highest_score
        }