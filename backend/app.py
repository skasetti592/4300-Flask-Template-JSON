import json
import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
import foodies_rocchio as rocchio
import foodies_cossim as fc
import foodies_svd as svd 
from urllib.parse import unquote
import pandas as pd
import numpy as np
import warnings



# ROOT_PATH for linking with all your files.
os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..", os.curdir))

# Get the directory of the current script
current_directory = os.path.dirname(os.path.abspath(__file__))

# Specify the path to the JSON file relative to the current script
json_file_path = os.path.join(current_directory, 'csvjson.json')

# Assuming your JSON data is stored in a file named 'init.json'
with open(json_file_path, 'r', errors='ignore') as file:
    data = json.load(file)
    restaurants_df = pd.DataFrame(data['restaurants'])
    morning_df = restaurants_df[restaurants_df["morning"] == 1]
    evening_df = restaurants_df[restaurants_df["evening"] == 1]
    nightlife_df = restaurants_df[restaurants_df["nightlife"] == 1]


recs_message = "Here are some recs..."

app = Flask(__name__)
CORS(app)

def cossim_search(query): 
    results = fc.cossim_full(restaurants_df, query)
    df = pd.DataFrame(results, columns=['name'])
    matches = pd.merge(df,restaurants_df, on='name') 
    matches_filtered = matches[['name','type', 'price_range']]
    out = matches_filtered.sort_index()
    matches_filtered_json = out.to_json(orient='records')
    return matches_filtered_json 
    
def svd_search(query, price, location_city, time): 
    svd_df = restaurants_df
    results = svd.svd_search(query, svd_df, price, location_city, time, k=50)
    first = results[0]
    restaurant_names = [restaurant[0] for restaurant in first]
    best_words = results[1]
    num_restaurants = len(restaurant_names)
    query_tfidf = results[2]
    tfidf_matrix = results[3]
    tfidf_vectorizer = results[4]  # Extract tfidf_vectorizer
    top_restaurant_df = pd.DataFrame(first, columns=['name', 'type', 'price_range', 'street_address', 'locality', 'trip_advisor_url', 'comments', 'score_svd'])
    matches_filtered_json = top_restaurant_df.to_json(orient='records')
    return matches_filtered_json, best_words, tfidf_matrix, tfidf_vectorizer  # Return JSON results and other variables


def rocchio_search(query, restaurant_ids, location, price, time):
    rocchio_df = restaurants_df
    results = rocchio.rocchio_results(rocchio_df, query, restaurant_ids)
    #rocchio_top_df = pd.DataFrame(results, columns=['name', 'type', 'price_range', 'street_address', 'locality', 'trip_advisor_url', 'comments', 'score'])
    #final_df = rocchio_top_df[(rocchio_top_df["state_abbreviation"] == location) & (rocchio_top_df["price_range"] == price) & (rocchio_top_df[time] == 1)] 

    
    df = pd.DataFrame(results, columns=['name'])
    matches = pd.merge(df, rocchio_df, on='name')
    final_df = matches[(matches["state_abbreviation"] == location) & (matches["price_range"] == price) & (matches[time] == 1)] 
    final_df = final_df.head(5)
    matches_filtered = final_df[['name', 'type', 'price_range', 'street_address', 'locality', 'trip_advisor_url', 'comments']]
    out = matches_filtered.sort_index()
    
    matches_filtered_json = out.to_json(orient='records')
    return matches_filtered_json

def name_to_id(restaurant_names):
    df = restaurants_df
    name_to_id_map = df.set_index('name')['id'].to_dict()
    restaurant_ids = [name_to_id_map[name] for name in restaurant_names]
    return restaurant_ids

def visualize_restaurant_scores(restaurant_names, df, num_restaurants, best_words, tfidf_matrix, tfidf_vectorizer):
    temp_df = pd.DataFrame()
    for i in range(num_restaurants):
        words = best_words[i]  # Retrieve words for the current restaurant
        word_indices = [tfidf_vectorizer.vocabulary_.get(word, -1) for word in words]
        scores = []  # Initialize scores list inside the loop
        for j in range(len(word_indices)):
            doc = word_indices[j]
            feature_index = tfidf_matrix[doc,:].nonzero()[1]
            tfidf_scores = zip(feature_index, [tfidf_matrix[doc, x] for x in feature_index])
            feature_names = tfidf_vectorizer.get_feature_names_out()
            score_sum = 0
            for w, s in [(feature_names[i], s) for (i, s) in tfidf_scores]:
                score_sum += s
            scores.append(score_sum)
        scores_normalized = scores / np.linalg.norm(scores)  # Normalize scores
        df = pd.DataFrame({'best_words': words[:10], 'score': scores_normalized[:10]})
        df['restaurant'] = restaurant_names[i]
        #df['relevant_document'] = ["\n".join(doc) for doc in results[1][i]]
        temp_df = pd.concat([temp_df, df])
    
    print(temp_df)
    return temp_df

    

@app.route("/")
def home():
    global recs_message
    return render_template('base.html', title="sample html", recs_message=recs_message)

@app.route("/episodes")
def episodes_search():
    query = request.args.get("query")
    price_range = request.args.get("price_range")
    price = ""
    if price_range == "2":
        price = "$"
    elif price_range == "3":
        price = "$$"
    elif price_range == "4":
        price = "$$$"

    location_city = request.args.get("locality")
    time = request.args.get("time")
    restaurant_names = request.args.get("restaurant_names")

    if restaurant_names is not None:
        results_list = json.loads(restaurant_names)
        result_restaurant_ids = name_to_id(results_list)
        results_rocchio = rocchio_search(query, result_restaurant_ids, location_city, price, time)
        return results_rocchio
    else:
        results_svd_json, best_words, tfidf_matrix, tfidf_vectorizer = svd_search(query, price, location_city, time)  # Get JSON results and variables
        results_svd = json.loads(results_svd_json)
        if results_svd:
            print("if statement")
            restaurant_names = [restaurant['name'] for restaurant in results_svd]  # Extract restaurant names
            df_output = visualize_restaurant_scores(restaurant_names, restaurants_df, len(restaurant_names), best_words, tfidf_matrix, tfidf_vectorizer) 
            best_words = df_output['best_words']
            restaurant = df_output['restaurant']
            best_words = best_words.to_json(orient='records')
            restaurant = restaurant.to_json(orient='records')
            grouped = df_output.groupby('restaurant')

            result_dict = {name: {'best_words': group['best_words'].tolist(), 'score': group['score'].tolist()} for name, group in grouped}

            print(result_dict)            
            return jsonify(results_svd= results_svd, final = df_output)  # Return JSON data
      
        else:
            print("no if statement")
            return results_svd
    
    
if 'DB_NAME' not in os.environ:
    app.run(debug=True,host="0.0.0.0",port=5000)