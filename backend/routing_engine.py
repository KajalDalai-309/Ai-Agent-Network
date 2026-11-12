"""
routing_engine.py
─────────────────
Multi-stage semantic relevance routing engine for AI Agents.
Combines TF-IDF vector cosine similarity with semantic keyword & topic matching.
Ensures accurate, low-latency agent matching without external cloud dependencies.
"""

from __future__ import annotations

import re
from typing import List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SIMILARITY_THRESHOLD = 0.05

# ── Demo seed data ────────────────────────────────────────────────────────────

SEED_AGENTS = [
    {
        "name": "Swiggy Agent",
        "company": "Swiggy",
        "description": (
            "AI agent for Swiggy's food delivery platform. Handles order routing, "
            "restaurant discovery, delivery optimisation and customer experience."
        ),
        "interests": (
            "food delivery, logistics, restaurant, customer experience, "
            "order management, hyperlocal delivery, quick commerce, dining, meals, food"
        ),
        "avatar_color": "#FF6B35",
    },
    {
        "name": "PhonePe Agent",
        "company": "PhonePe",
        "description": (
            "AI agent powering PhonePe's digital payments ecosystem. Specialises in "
            "UPI transactions, financial services, fraud detection, and merchant onboarding."
        ),
        "interests": (
            "fintech, UPI, digital payments, payment, fraud detection, merchant, "
            "wallet, cashback, rewards, money transfer, financial inclusion"
        ),
        "avatar_color": "#5F259F",
    },
    {
        "name": "Flipkart Agent",
        "company": "Flipkart",
        "description": (
            "AI agent for Flipkart's e-commerce marketplace. Manages product discovery, "
            "personalised recommendations, supply chain, and seller management."
        ),
        "interests": (
            "e-commerce, retail, product recommendation, supply chain, "
            "inventory, seller, marketplace, fashion, electronics, shopping, deals, discounts"
        ),
        "avatar_color": "#2874F0",
    },
    {
        "name": "HDFC Bank Agent",
        "company": "HDFC Bank",
        "description": (
            "AI agent for HDFC Bank's retail and corporate banking operations. "
            "Covers loan processing, credit cards, wealth management and compliance."
        ),
        "interests": (
            "banking, finance, loan, credit card, cards, wealth management, "
            "compliance, KYC, risk, investment, insurance, interest, emi, personal loan, gold loan"
        ),
        "avatar_color": "#004C8F",
    },
    {
        "name": "Bajaj Auto Agent",
        "company": "Bajaj Auto",
        "description": (
            "AI agent for Bajaj Auto's manufacturing and sales operations. "
            "Focuses on automotive supply chain, EV technology, dealer network and exports."
        ),
        "interests": (
            "automotive, electric vehicle, EV, manufacturing, supply chain, "
            "dealer, export, two-wheeler, three-wheeler, mobility, bikes, motorcycles, vehicles"
        ),
        "avatar_color": "#1B4B8A",
    },
]


# ── Domain synonym & intent map for enhanced relevance ───────────────────────

DOMAIN_SYNONYMS = {
    "phonepe": ["upi", "pay", "payment", "payments", "cashback", "wallet", "qr", "transaction", "fintech"],
    "hdfc": ["bank", "banking", "loan", "loans", "card", "cards", "credit", "emi", "interest", "finance"],
    "flipkart": ["shopping", "ecommerce", "retail", "deal", "deals", "discount", "discounts", "sale", "order"],
    "swiggy": ["food", "delivery", "dining", "meal", "restaurant", "order", "groceries", "instamart"],
    "bajaj": ["bike", "motorcycle", "ev", "vehicle", "scooter", "auto", "automotive", "ride"],
}

STOPWORDS = {
    "on", "all", "the", "and", "for", "with", "get", "in", "of", "at", "by",
    "is", "a", "an", "to", "this", "that", "it", "from", "your", "my", "our",
    "be", "you", "we", "are", "have", "has", "had", "will", "would", "can"
}


# ── Core routing logic ─────────────────────────────────────────────────────────

class RoutingEngine:
    """
    Multi-tier relevance routing engine:
    1. Extracts post tokens and checks direct semantic keyword & topic matches.
    2. Runs TF-IDF Cosine Similarity against agent interest profiles.
    3. Blends TF-IDF score with keyword relevance to produce a normalized score.
    """

    def route(
        self,
        post_content: str,
        agents: List[dict],
        posting_agent_id: int,
        threshold: float = SIMILARITY_THRESHOLD,
        top_k: int = 5,
    ) -> List[Tuple[int, str, str, float]]:
        """
        Returns list of (agent_id, name, company, score) for relevant agents,
        excluding the posting agent.
        """
        if not agents:
            return []

        clean_post = post_content.lower()
        post_tokens = set(re.findall(r"\b\w+\b", clean_post)) - STOPWORDS

        eligible_agents = [a for a in agents if a["id"] != posting_agent_id]
        if not eligible_agents:
            return []

        agent_docs = []
        for a in eligible_agents:
            combined = (
                f"{a.get('interests', '')} "
                f"{a.get('description', '')} "
                f"{a.get('company', '')} "
                f"{a.get('name', '')}"
            ).lower()
            agent_docs.append(combined)

        # 1. TF-IDF vectorizer
        try:
            vectorizer = TfidfVectorizer(
                strip_accents="unicode",
                lowercase=True,
                ngram_range=(1, 2),
                min_df=1,
            )
            all_docs = agent_docs + [clean_post]
            vectorizer.fit(all_docs)
            agent_matrix = vectorizer.transform(agent_docs)
            post_vector = vectorizer.transform([clean_post])
            cos_similarities = cosine_similarity(post_vector, agent_matrix)[0]
        except Exception:
            cos_similarities = np.zeros(len(eligible_agents))

        # 2. Hybrid evaluation (TF-IDF + Token Match + Domain Synonyms)
        results = []
        for idx, agent in enumerate(eligible_agents):
            agent_text = agent_docs[idx]
            agent_tokens = set(re.findall(r"\b\w+\b", agent_text)) - STOPWORDS
            
            # Direct token overlap
            direct_overlap = post_tokens.intersection(agent_tokens)

            # Domain synonym checks
            comp_key = agent.get("company", "").lower()
            synonym_matches = 0
            for domain_key, syn_list in DOMAIN_SYNONYMS.items():
                if domain_key in comp_key or domain_key in agent.get("name", "").lower():
                    for syn in syn_list:
                        if syn in post_tokens or syn in clean_post:
                            synonym_matches += 1

            tfidf_score = float(cos_similarities[idx])
            keyword_score = min(len(direct_overlap) * 0.20 + synonym_matches * 0.25, 0.75)

            # Combined score
            final_score = (tfidf_score * 0.4) + keyword_score
            if direct_overlap or synonym_matches > 0:
                final_score = max(final_score, 0.25 + 0.15 * (len(direct_overlap) + synonym_matches))

            final_score = min(round(final_score, 3), 0.99)

            if final_score >= threshold:
                results.append((agent["id"], agent["name"], agent["company"], final_score))

        # Sort descending by score
        results.sort(key=lambda x: x[3], reverse=True)
        return results[:top_k]


# Singleton instance
routing_engine = RoutingEngine()
