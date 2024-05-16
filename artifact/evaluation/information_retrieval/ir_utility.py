from nltk.tokenize import RegexpTokenizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from gensim.summarization.bm25 import BM25
import time
import random

random.seed(10)

tk = RegexpTokenizer(r'[A-Za-z]+')


def bm25_model(corpus):
    start = time.time()
    train_model = BM25(corpus)
    return train_model, time.time() - start


def bm25_score(train_model, query):
    start = time.time()
    scores = train_model.get_scores(query)
    return scores, time.time() - start


def tfidf_model(corpus):
    corpus = [" ".join(x) for x in corpus]
    start = time.time()
    train_model = TfidfVectorizer()
    train_data_matrix = train_model.fit_transform(corpus)
    return train_model, train_data_matrix, time.time() - start


def tfidf_score(train_model, train_data_matrix, query):
    start = time.time()
    query = " ".join(query)
    query_data_matrix = train_model.transform([query])
    cosine_similarities = cosine_similarity(train_data_matrix, query_data_matrix).flatten()
    return list(cosine_similarities), time.time() - start


def camel_case_split(s):
    # TestSplit
    # testSplit
    new_string=""
    for i in range(len(s) - 1):
        if s[i].isupper() and s[i + 1].islower():
            new_string += "*" + s[i]
        else:
            new_string += s[i]
    new_string += s[-1]
    ret = new_string.lower().split("*")
    ret = [x for x in ret if len(x) > 0]
    return ret

def low_tokenization(text_body):
    # best performance in Empirically Revisiting and Enhancing IR-Based Test-Case Prioritization
    """
    (0) breaks text into tokens separated by any whitespace character, and
    (1) filters out all the numbers and operators, 
    (2) segments the long variables by non-alphabetical characters in-between and by the camel-case heuristics
    (3) turn all upper-case letters to lower-case letters.
    """
    # step 0, 1 
    text_body = tk.tokenize(text_body)
    # step 2, 3
    ret = []
    for t in text_body:
        ret += camel_case_split(t)
    return ret

if __name__ == "__main__":
    pass








