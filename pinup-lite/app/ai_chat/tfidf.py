from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class ThaiTfidf:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 5),
            lowercase=False,
            max_features=200_000,
        )
        self.matrix = None

    def fit(self, texts: List[str]):
        self.matrix = self.vectorizer.fit_transform(texts)
        return self

    def search(self, query: str, top_k: int = 5) -> List[int]:
        qv = self.vectorizer.transform([query])
        sims = cosine_similarity(qv, self.matrix)[0]
        return np.argsort(-sims)[:top_k].tolist()