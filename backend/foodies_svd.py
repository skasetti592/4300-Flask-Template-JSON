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


def determine_n_component(df, variance_ratio=0.5):
  #  print(n_features)
  #  print("this is features")
  #  print(n_samples)
    n_samples, n_features = df.shape
    min_dimension = min(n_samples, n_features)
    n_components = min_dimension * variance_ratio 
    n_components = max(n_components, 1)  # Ensure n_components is at least 1
    n_components = min(n_components, min_dimension)
    n_components = int(round(n_components))
    return n_components

  #  print(n_components)
  #  print("before return")

def svd_search(query, restaurants_df, k=5): 
  restaurants_df['combined_text'] = restaurants_df['name'] + ' ' + restaurants_df['comments']

  def tokenize(text):
      return text.split()

  try:
    tfidf_vectorizer = TfidfVectorizer(stop_words='english', tokenizer=tokenize, max_df=0.7, min_df=2)
    tfidf_matrix = tfidf_vectorizer.fit_transform(restaurants_df['combined_text'])
  # print("TF-IDF matrix shape:", tfidf_matrix.shape)
  except ValueError as e:
    # print("Error:", e)
    # print("Adjusting max_df and min_df parameters...")
    max_df_adjusted = 1.0  # Set max_df to a value that works
    min_df_adjusted = 1    # Set min_df to a value that works
    tfidf_vectorizer = TfidfVectorizer(stop_words='english', tokenizer=tokenize, max_df=max_df_adjusted, min_df=min_df_adjusted)
    tfidf_matrix = tfidf_vectorizer.fit_transform(restaurants_df['combined_text'])

  n_components = int(determine_n_component(tfidf_matrix))
  # print("Number of components:", n_components)

  svd = TruncatedSVD(n_components, random_state=43)
  svd_matrix = svd.fit_transform(tfidf_matrix)
  # print("SVD matrix shape:", svd_matrix.shape)

  svd_matrix_normalized = normalize(svd_matrix, axis=1)

  # Function to find closest restaurant names to a query
  query_text = preprocess(query)
  query_vector = tfidf_vectorizer.transform([query_text])
  query_svd_vector = svd.transform(query_vector)
  query_svd_vector_normalized = normalize(query_svd_vector)

  similarities = cosine_similarity(query_svd_vector_normalized, svd_matrix_normalized)
  
  top_indices = similarities.argsort(axis=1)[:, -k:][0][::-1]
  top_scores = np.sort(similarities[0])[-k:][::-1]
  results = []
  for i in range(len(top_indices)):
    index = top_indices[i]
    name = restaurants_df.iloc[index]['name']
    type = restaurants_df.iloc[index]['type']
    price_range = restaurants_df.iloc[index]['price_range']
    street_address = restaurants_df.iloc[index]['street_address']
    locality = restaurants_df.iloc[index]['locality']
    trip_advisor_url = restaurants_df.iloc[index]['trip_advisor_url']
    comments = restaurants_df.iloc[index]['comments']
    svd_score = top_scores[i]
    results.append((name, type, price_range, street_address, locality, trip_advisor_url, comments, svd_score))
  return results