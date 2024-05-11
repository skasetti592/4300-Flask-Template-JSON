import json
import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
import foodies_rocchio as rocchio
import foodies_cossim as fc
import foodies_svd as svd 
from urllib.parse import unquote

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
    
def svd_search(query, filtered_df): 
    svd_df = filtered_df
    results = svd.svd_search(query, svd_df, k=5)
    top_restaurant_df = pd.DataFrame(results, columns=['name', 'type', 'price_range', 'street_address', 'locality', 'trip_advisor_url', 'comments'])
    '''matches = pd.merge(df,restaurants_df, on='name') 
    matches_filtered = matches[['name','type', 'price_range', 'street_address', 'locality', "trip_advisor_url", "comments"]]
    out = matches_filtered.sort_index()
    matches_filtered_json = out.to_json(orient='records')
    print(matches_filtered_json)'''
    matches_filtered_json = top_restaurant_df.to_json(orient='records')
    # print(matches_filtered_json)
    # print("return svd")

    return matches_filtered_json

@app.route("/")
def home():
    return render_template('base.html',title="sample html")

def rocchio_search(filtered_df, query, restaurant_ids):
    rocchio_df = filtered_df
    results = rocchio.rocchio_results(rocchio_df, query, restaurant_ids)
    df = pd.DataFrame(results, columns=['name'])
    df = df.head(5)
    matches = pd.merge(df, rocchio_df, on='name') 
    matches_filtered = matches[['name', 'type', 'price_range', 'street_address', 'locality', 'trip_advisor_url', 'comments']]
    out = matches_filtered.sort_index()
    matches_filtered_json = out.to_json(orient='records')
    return matches_filtered_json

def name_to_id(restaurant_names):
    df = filtered_df
    name_to_id_map = df.set_index('name')['id'].to_dict()

    restaurant_ids = [name_to_id_map[name] for name in restaurant_names]

    return restaurant_ids


def filter_df(price_range, location_city, time):
    if time == "morning":
        new_df = morning_df
    elif time == "evening":
        new_df = evening_df
        
    elif time == "nightlife":
        new_df = nightlife_df
       
    final_df = new_df[(new_df["state_abbreviation"] == location_city) & (new_df["price_range"] == price_range)] 
    final_df = final_df.reset_index(drop=True)
    final_df['id'] = final_df.index + 1

    return final_df
    
filtered_df = None

def let_filter(restaurant_names, price, location_city, time):
    global filtered_df
    if restaurant_names is None:
        filtered_df = filter_df(price, location_city, time)
    global_df = filtered_df
    return global_df


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

    
    episodes_df = let_filter(restaurant_names, price, location_city, time)


    if restaurant_names is not None:
        results_list = json.loads(restaurant_names)


        result_restaurant_ids = name_to_id(results_list)
        results_rocchio = rocchio_search(episodes_df, query, result_restaurant_ids)

        return results_rocchio

    else:
        results_svd = svd_search(query, episodes_df)
        return results_svd
    
    
if 'DB_NAME' not in os.environ:
    app.run(debug=True,host="0.0.0.0",port=5000)