import json
import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity
import warnings

def custom_warning(message, category, filename, lineno, file=None, line=None):
    if category == UserWarning and "token_pattern' will not be used since 'tokenizer'" in str(message):
        print("Here are some recs")

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
    n_components = min(n_components, min_dimension)
    n_components = int(round(n_components))
    return n_components
  #  print(n_components)
  #  print("before return")

def svd_search(query, restaurants_df, k=5): 
  restaurants_df['combined_text'] = restaurants_df['name'] + ' ' + restaurants_df['comments']

  def tokenize(text):
      return text.split()
  
  # n_components = determine_n_component(restaurants_df)
  # print(n_components)
  # print("after return")

  # Create TF-IDF matrix
  tfidf_vectorizer = TfidfVectorizer(stop_words='english', tokenizer=tokenize, max_df=0.7, min_df=2)
  tfidf_matrix = tfidf_vectorizer.fit_transform(restaurants_df['combined_text'])
  # print("TF-IDF matrix shape:", tfidf_matrix.shape)

  n_components = determine_n_component(tfidf_matrix)
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

  top_restaurant_names = [((restaurants_df.iloc[i]['name']),
                          (restaurants_df.iloc[i]['type']), 
                          (restaurants_df.iloc[i]['price_range']),
                          (restaurants_df.iloc[i]['street_address']), 
                          (restaurants_df.iloc[i]['locality']), 
                          (restaurants_df.iloc[i]['trip_advisor_url']), 
                          (restaurants_df.iloc[i]['comments']))
                          for i in top_indices]
  
  results = []

  for i in range(len(top_restaurant_names)):
    name = top_restaurant_names[i][0]
    type = top_restaurant_names[i][1]
    price_range = top_restaurant_names[i][2]
    street_address = top_restaurant_names[i][3]
    locality = top_restaurant_names[i][4]
    trip_advisor_url = top_restaurant_names[i][5]
    comments = top_restaurant_names[i][6]
    results.append((name,type,price_range,street_address,locality,trip_advisor_url, comments))
  return results
