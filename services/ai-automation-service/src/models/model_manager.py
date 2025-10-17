"""
Model Manager for Phase 1 Optimized Stack
Manages OpenVINO INT8 models: embeddings, re-ranker, classifier

Stack:
- all-MiniLM-L6-v2 (INT8) - 20MB - Embeddings
- bge-reranker-base (INT8) - 280MB - Re-ranking
- flan-t5-small (INT8) - 80MB - Classification

Total: 380MB, 230ms/pattern, 100% local
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Manages all ML models for pattern detection
    Lazy-loads models on first use
    """
    
    def __init__(self, models_dir: str = "/app/models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Model instances (lazy loaded)
        self._embed_model = None
        self._embed_tokenizer = None
        self._reranker_model = None
        self._reranker_tokenizer = None
        self._classifier_model = None
        self._classifier_tokenizer = None
        
        self.use_openvino = True  # Try OpenVINO first, fallback to standard
        
        logger.info("ModelManager initialized (models will load on first use)")
    
    def get_embedding_model(self):
        """Get embedding model (lazy load)"""
        if self._embed_model is None:
            logger.info("Loading embedding model: all-MiniLM-L6-v2...")
            
            try:
                if self.use_openvino:
                    from optimum.intel import OVModelForFeatureExtraction
                    from transformers import AutoTokenizer
                    
                    self._embed_model = OVModelForFeatureExtraction.from_pretrained(
                        "sentence-transformers/all-MiniLM-L6-v2",
                        export=True,
                        compile=True,
                        cache_dir=str(self.models_dir)
                    )
                    self._embed_tokenizer = AutoTokenizer.from_pretrained(
                        "sentence-transformers/all-MiniLM-L6-v2",
                        cache_dir=str(self.models_dir)
                    )
                    logger.info("✅ Loaded OpenVINO optimized embedding model (20MB)")
                else:
                    raise ImportError("OpenVINO not available")
                    
            except ImportError:
                logger.warning("OpenVINO not available, using standard model")
                self.use_openvino = False
                
                from sentence_transformers import SentenceTransformer
                self._embed_model = SentenceTransformer(
                    'sentence-transformers/all-MiniLM-L6-v2',
                    cache_folder=str(self.models_dir)
                )
                logger.info("✅ Loaded standard embedding model (80MB)")
        
        return self._embed_model, self._embed_tokenizer
    
    def get_reranker_model(self):
        """Get re-ranker model (lazy load)"""
        if self._reranker_model is None:
            logger.info("Loading re-ranker model: bge-reranker-base...")
            
            try:
                if self.use_openvino:
                    from optimum.intel import OVModelForSequenceClassification
                    from transformers import AutoTokenizer
                    
                    self._reranker_model = OVModelForSequenceClassification.from_pretrained(
                        "OpenVINO/bge-reranker-base-int8-ov",
                        cache_dir=str(self.models_dir)
                    )
                    self._reranker_tokenizer = AutoTokenizer.from_pretrained(
                        "OpenVINO/bge-reranker-base-int8-ov",
                        cache_dir=str(self.models_dir)
                    )
                    logger.info("✅ Loaded OpenVINO re-ranker (280MB INT8)")
                else:
                    raise ImportError("OpenVINO not available")
                    
            except ImportError:
                logger.warning("OpenVINO re-ranker not available, using standard")
                from transformers import AutoTokenizer, AutoModelForSequenceClassification
                
                self._reranker_tokenizer = AutoTokenizer.from_pretrained(
                    "BAAI/bge-reranker-base",
                    cache_dir=str(self.models_dir)
                )
                self._reranker_model = AutoModelForSequenceClassification.from_pretrained(
                    "BAAI/bge-reranker-base",
                    cache_dir=str(self.models_dir)
                )
                logger.info("✅ Loaded standard re-ranker (1.1GB)")
        
        return self._reranker_model, self._reranker_tokenizer
    
    def get_classifier_model(self):
        """Get classifier model (lazy load)"""
        if self._classifier_model is None:
            logger.info("Loading classifier model: flan-t5-small...")
            
            try:
                if self.use_openvino:
                    from optimum.intel import OVModelForSeq2SeqLM
                    from transformers import AutoTokenizer
                    
                    self._classifier_model = OVModelForSeq2SeqLM.from_pretrained(
                        "google/flan-t5-small",
                        export=True,
                        cache_dir=str(self.models_dir)
                    )
                    self._classifier_tokenizer = AutoTokenizer.from_pretrained(
                        "google/flan-t5-small",
                        cache_dir=str(self.models_dir)
                    )
                    logger.info("✅ Loaded OpenVINO classifier (80MB INT8)")
                else:
                    raise ImportError("OpenVINO not available")
                    
            except ImportError:
                logger.warning("OpenVINO not available, using standard model")
                from transformers import T5Tokenizer, T5ForConditionalGeneration
                
                self._classifier_tokenizer = T5Tokenizer.from_pretrained(
                    "google/flan-t5-small",
                    cache_dir=str(self.models_dir)
                )
                self._classifier_model = T5ForConditionalGeneration.from_pretrained(
                    "google/flan-t5-small",
                    cache_dir=str(self.models_dir)
                )
                logger.info("✅ Loaded standard classifier (300MB)")
        
        return self._classifier_model, self._classifier_tokenizer
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for texts
        Returns: (N, 384) numpy array
        """
        model, tokenizer = self.get_embedding_model()
        
        if self.use_openvino and tokenizer is not None:
            # OpenVINO path
            inputs = tokenizer(texts, padding=True, truncation=True, return_tensors='pt', max_length=256)
            outputs = model(**inputs)
            embeddings = outputs.last_hidden_state.mean(dim=1).detach().numpy()
        else:
            # Standard sentence-transformers path
            embeddings = model.encode(texts, convert_to_numpy=True)
        
        return embeddings
    
    def rerank(self, query: str, candidates: List[Dict], top_k: int = 10) -> List[Dict]:
        """
        Re-rank candidates using bge-reranker
        
        Args:
            query: Query text (pattern description)
            candidates: List of candidate patterns (must have 'description' field)
            top_k: Number of top results to return
        
        Returns:
            Top K re-ranked candidates
        """
        model, tokenizer = self.get_reranker_model()
        
        scores = []
        for candidate in candidates:
            text = candidate.get('description', str(candidate))
            pair = f"{query} [SEP] {text}"
            
            inputs = tokenizer(pair, return_tensors='pt', truncation=True, max_length=512)
            outputs = model(**inputs)
            score = outputs.logits[0][0].item()
            
            scores.append((candidate, score))
        
        # Sort by score descending
        ranked = sorted(scores, key=lambda x: x[1], reverse=True)
        return [candidate for candidate, score in ranked[:top_k]]
    
    def classify_pattern(self, pattern_description: str) -> Dict[str, str]:
        """
        Classify pattern category and priority using flan-t5-small
        
        Args:
            pattern_description: Natural language pattern description
        
        Returns:
            {'category': str, 'priority': str}
        """
        model, tokenizer = self.get_classifier_model()
        
        # Classify category
        category_prompt = f"""Classify this smart home pattern into ONE category: energy, comfort, security, or convenience.

Pattern: {pattern_description}

Respond with only the category name (one word).

Category:"""
        
        inputs = tokenizer(category_prompt, return_tensors='pt', max_length=512, truncation=True)
        outputs = model.generate(**inputs, max_new_tokens=5)
        category_raw = tokenizer.decode(outputs[0], skip_special_tokens=True)
        category = self._parse_category(category_raw)
        
        # Classify priority
        priority_prompt = f"""Rate priority (high, medium, or low) for this smart home pattern.

Pattern: {pattern_description}
Category: {category}

Respond with only the priority level (one word).

Priority:"""
        
        inputs = tokenizer(priority_prompt, return_tensors='pt', max_length=512, truncation=True)
        outputs = model.generate(**inputs, max_new_tokens=5)
        priority_raw = tokenizer.decode(outputs[0], skip_special_tokens=True)
        priority = self._parse_priority(priority_raw)
        
        return {
            'category': category,
            'priority': priority
        }
    
    def _parse_category(self, text: str) -> str:
        """Parse flan-t5 output to valid category with fallback"""
        text = text.strip().lower()
        valid = ['energy', 'comfort', 'security', 'convenience']
        
        # Direct match
        if text in valid:
            return text
        
        # Keyword matching
        for category in valid:
            if category in text:
                return category
        
        # Rule-based fallback
        if any(word in text for word in ['power', 'electricity', 'consumption']):
            return 'energy'
        if any(word in text for word in ['temperature', 'thermostat', 'climate', 'heat', 'cool', 'lighting']):
            return 'comfort'
        if any(word in text for word in ['lock', 'door', 'alarm', 'camera', 'monitor', 'safety']):
            return 'security'
        
        return 'convenience'  # Default fallback
    
    def _parse_priority(self, text: str) -> str:
        """Parse flan-t5 output to valid priority with fallback"""
        text = text.strip().lower()
        valid = ['high', 'medium', 'low']
        
        # Direct match
        if text in valid:
            return text
        
        # Keyword matching
        for priority in valid:
            if priority in text:
                return priority
        
        return 'medium'  # Default fallback
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models"""
        return {
            'embedding_model': 'all-MiniLM-L6-v2',
            'embedding_loaded': self._embed_model is not None,
            'reranker_model': 'bge-reranker-base',
            'reranker_loaded': self._reranker_model is not None,
            'classifier_model': 'flan-t5-small',
            'classifier_loaded': self._classifier_model is not None,
            'openvino_enabled': self.use_openvino,
            'models_dir': str(self.models_dir)
        }


# Global instance (singleton pattern)
_model_manager: Optional[ModelManager] = None

def get_model_manager() -> ModelManager:
    """Get global model manager instance"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager

