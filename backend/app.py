import json
import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
import foodies_rocchio as rocchio
import foodies_cossim as fc
import foodies_svd as svd 
from urllib.parse import unquote
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
    results = svd.svd_search(query, svd_df, price, location_city, time, k=80)
    top_restaurant_df = pd.DataFrame(results, columns=['name', 'type', 'price_range', 'street_address', 'locality', 'trip_advisor_url', 'comments', 'svd_score'])
    # matches = pd.merge(df,restaurants_df, on='name') 
    # matches_filtered = matches[['name','type', 'price_range', 'street_address', 'locality', "trip_advisor_url", "comments"]]
    # out = matches_filtered.sort_index()
    # matches_filtered_json = out.to_json(orient='records')
    # print(matches_filtered_json)
    matches_filtered_json = top_restaurant_df.to_json(orient='records')
    # print(matches_filtered_json)
    # print("return svd")
    return matches_filtered_json

@app.route("/")
def home():
    global recs_message
    return render_template('base.html', title="sample html", recs_message=recs_message)

def rocchio_search(query, restaurant_ids, location, price, time):
    rocchio_df = restaurants_df
    results = rocchio.rocchio_results(rocchio_df, query, restaurant_ids)
    print("results returned")
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
        print(result_restaurant_ids)
        print("restaurant ids")
        print("l_c:", location_city)
        results_rocchio = rocchio_search(query, result_restaurant_ids, location_city, price, time)
        return results_rocchio
    else:
        results_svd = svd_search(query, price, location_city, time)
        return results_svd
    
    
if 'DB_NAME' not in os.environ:
    app.run(debug=True,host="0.0.0.0",port=5000)