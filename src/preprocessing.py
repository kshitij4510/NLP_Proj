"""
Text Preprocessing Module
Handles common NLP preprocessing tasks: cleaning, tokenization,
stopword removal, stemming, and lemmatization.
"""

import re
import string
import logging
from typing import List, Optional

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import PorterStemmer, WordNetLemmatizer

# Download required NLTK data on first run
def download_nltk_data():
    packages = ["punkt", "stopwords", "wordnet", "averaged_perceptron_tagger", "punkt_tab"]
    for pkg in packages:
        nltk.download(pkg, quiet=True)


download_nltk_data()

logger = logging.getLogger(__name__)


class TextPreprocessor:
    """A reusable text preprocessing pipeline."""

    def __init__(
        self,
        lowercase: bool = True,
        remove_stopwords: bool = True,
        remove_punctuation: bool = True,
        stemming: bool = False,
        lemmatization: bool = True,
        language: str = "english",
    ):
        self.lowercase = lowercase
        self.remove_stopwords = remove_stopwords
        self.remove_punctuation = remove_punctuation
        self.stemming = stemming
        self.lemmatization = lemmatization

        self.stop_words = set(stopwords.words(language))
        self.stemmer = PorterStemmer() if stemming else None
        self.lemmatizer = WordNetLemmatizer() if lemmatization else None

    def clean(self, text: str) -> str:
        """Remove URLs, HTML tags, and extra whitespace."""
        # Remove URLs
        text = re.sub(r"https?://\S+|www\.\S+", "", text)
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words."""
        return word_tokenize(text)

    def process(self, text: str) -> List[str]:
        """Run the full preprocessing pipeline on a string."""
        text = self.clean(text)

        if self.lowercase:
            text = text.lower()

        tokens = self.tokenize(text)

        if self.remove_punctuation:
            tokens = [t for t in tokens if t not in string.punctuation]

        if self.remove_stopwords:
            tokens = [t for t in tokens if t not in self.stop_words]

        if self.lemmatization and self.lemmatizer:
            tokens = [self.lemmatizer.lemmatize(t) for t in tokens]
        elif self.stemming and self.stemmer:
            tokens = [self.stemmer.stem(t) for t in tokens]

        return tokens

    def process_batch(self, texts: List[str]) -> List[List[str]]:
        """Process a list of texts."""
        return [self.process(text) for text in texts]

    @staticmethod
    def sentence_tokenize(text: str) -> List[str]:
        """Split text into sentences."""
        return sent_tokenize(text)


def get_word_frequencies(tokens: List[str]) -> dict:
    """Count word frequencies from a token list."""
    freq = {}
    for token in tokens:
        freq[token] = freq.get(token, 0) + 1
    return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True))


# ── Demo ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample_texts = [
        "Natural Language Processing (NLP) is a subfield of linguistics and AI.",
        "Check out https://example.com for more information about <b>machine learning</b>!",
        "The quick brown fox jumps over the lazy dog. It was a beautiful day.",
    ]

    preprocessor = TextPreprocessor()

    print("=" * 60)
    print("Text Preprocessing Demo")
    print("=" * 60)

    for text in sample_texts:
        tokens = preprocessor.process(text)
        freq = get_word_frequencies(tokens)
        print(f"\nOriginal : {text}")
        print(f"Tokens   : {tokens}")
        print(f"Top words: {list(freq.items())[:5]}")

    print("\nSentence tokenization:")
    sentences = TextPreprocessor.sentence_tokenize(sample_texts[2])
    for i, sent in enumerate(sentences, 1):
        print(f"  {i}. {sent}")
