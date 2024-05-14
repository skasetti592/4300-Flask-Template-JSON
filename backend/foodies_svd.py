import json
import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity
import warnings

recs_message = ""

def custom_warning(message, category, filename, lineno, file=None, line=None):
    global recs_message
    if category == UserWarning and "token_pattern' will not be used since 'tokenizer'" in str(message):
        recs_message = "Here are some recs"

warnings.showwarning = custom_warning

def preprocess(text):
    text = text.lower()
    text = re.sub(r"[.,\/#!$%\^\*;:{}=\_`~()@]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text):
    return text.split()

n_components = 42

# Create TF-IDF matrix
tfidf_vectorizer = TfidfVectorizer(stop_words='english', tokenizer=tokenize, max_df=0.8, min_df=5)


def svd_search(query, restaurants_df, p_r, l_c, t_d, k): 
  restaurants_df['combined_text'] = restaurants_df['name'] + ' ' + restaurants_df['comments']
  restaurants_df['processed_text'] = restaurants_df['combined_text'].apply(preprocess)
  
  tfidf_matrix = tfidf_vectorizer.fit_transform(restaurants_df['processed_text'])

  #print(tfidf_matrix)
  document_index = 0  # Index of the document you want to access
  nonzero_indices = tfidf_matrix[document_index].nonzero()[1]
  vocabulary = tfidf_vectorizer.get_feature_names_out()
  words_in_document = [vocabulary[idx] for idx in nonzero_indices]
  svd = TruncatedSVD(n_components, random_state=43)
  svd_matrix = svd.fit_transform(tfidf_matrix)

  svd_matrix_normalized = normalize(svd_matrix, axis=1)

  # Function to find closest restaurant names to a query
  query_text = preprocess(query)
  query_vector = tfidf_vectorizer.transform([query_text])
  query_svd_vector = svd.transform(query_vector)
  query_svd_vector_normalized = normalize(query_svd_vector)

  similarities = cosine_similarity(query_svd_vector_normalized, svd_matrix_normalized)

  top_indices = similarities.argsort(axis=1)[:, -k:][0][::-1]
  top_scores = np.sort(similarities[0])[-k:][::-1]

  temp = []
  for i in top_indices:
    document_index = i
    nonzero_indices = tfidf_matrix[document_index].nonzero()[1]
    vocabulary = tfidf_vectorizer.get_feature_names_out()
    words_in_document = [vocabulary[idx] for idx in nonzero_indices[:10]]
    temp.append(words_in_document)

  
  results = []
  for i in range(len(top_indices)):
    index = top_indices[i]
    if restaurants_df.iloc[index][t_d] == 1:
      if restaurants_df.iloc[index]['state_abbreviation'] == l_c:
        if restaurants_df.iloc[index]['price_range'] == p_r:
          name = restaurants_df.iloc[index]['name']
          type = restaurants_df.iloc[index]['type']
          price_range = restaurants_df.iloc[index]['price_range']
          street_address = restaurants_df.iloc[index]['street_address']
          locality = restaurants_df.iloc[index]['locality']
          trip_advisor_url = restaurants_df.iloc[index]['trip_advisor_url']
          comments = restaurants_df.iloc[index]['comments']
          score = top_scores[i]
          results.append((name, type, price_range, street_address, locality, trip_advisor_url, comments, score))

  return ((results[:5], temp, (query_vector.toarray()[0]), tfidf_matrix, tfidf_vectorizer))