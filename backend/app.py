import json
import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
import foodies_rocchio as rocchio  # Import your Rocchio module
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

app = Flask(__name__)
CORS(app)

def cossim_search(query): 
    #cossims_sorted = fc.cossim_mat(restaurants_df, query)
    ##types = fc.types_set(restaurants_df)
    #qtypes = fc.tokenize_types(types, query)
    results = fc.cossim_full(restaurants_df, query)
    #print(results)
    df = pd.DataFrame(results, columns=['name'])
    #matches = pd.merge(restaurants_df,df) 
    #df['id'] = range(1, len(df)+1) 
    matches = pd.merge(df,restaurants_df, on='name') 
    matches_filtered = matches[['name','type', 'price_range']]
    out = matches_filtered.sort_index()
    matches_filtered_json = out.to_json(orient='records')
    return matches_filtered_json 
    
def svd_search(query, price_range): 
    results = svd.svd_results(restaurants_df, query)
    #print(results)
    df = pd.DataFrame(results, columns=['name'])
    matches = pd.merge(df,restaurants_df, on='name') 
    matches_filtered = matches[['name','type', 'price_range', 'street_address', 'locality', "trip_advisor_url", "comments", "id"]]
    out = matches_filtered.sort_index()
    matches_filtered_json = out.to_json(orient='records')
    print(matches_filtered_json)
    return matches_filtered_json 


def json_search(query):
    matches = []
    #merged_df = pd.merge(episodes_df, reviews_df, left_on='id', right_on='id', how='inner')
    
    #m_e = restaurants_df['Morning']
    matches = restaurants_df[restaurants_df['type'].str.lower().str.contains(query.lower())]
    tags = []

    matches_filtered = matches[['name','type', 'price_range']]
    matches_filtered_json = matches_filtered.to_json(orient='records')
    return matches_filtered_json

@app.route("/")
def home():
    return render_template('base.html',title="sample html")

# Rocchio algorithm to receive feedback and update
#@app.route('/feedback', methods=['POST'])
#def collect_feedback():
#    data = request.json
#    morning_restaurant_ids = data.get('morningRestaurantIds', [])
#    evening_restaurant_ids = data.get('eveningRestaurantIds', [])

    # Update the Rocchio algorithm with the received feedback
#    rocchio.rocchio_results(restaurants_df, "", "", morning_restaurant_ids)

    # Return a response
#    return jsonify({"message": "Feedback received and processed"})

def rocchio_search(query, price_range, restaurant_ids):
    results = rocchio.rocchio_results(restaurants_df, query, price_range, restaurant_ids)
    df = pd.DataFrame(results, columns=['name'])
    matches = pd.merge(df, restaurants_df, on='name') 
    matches_filtered = matches[['name', 'type', 'price_range', 'street_address', 'locality', 'trip_advisor_url', 'comments', 'id']]
    out = matches_filtered.sort_index()
    matches_filtered_json = out.to_json(orient='records')
    return matches_filtered_json

@app.route("/episodes")
def episodes_search():
    text = request.args.get("title")
    price_range = request.args.get("price_range")
    morning_restaurant_ids = request.args.get("morning_restaurant_ids")
    evening_restaurant_ids = request.args.get("evening_restaurant_ids")

    if morning_restaurant_ids or evening_restaurant_ids:
        results_morn_list = json.loads(morning_restaurant_ids)
        results_even_list = json.loads(evening_restaurant_ids)

        morning_restaurant_ids = [json.loads(id) for id in results_morn_list]
        evening_restaurant_ids = [json.loads(id) for id in results_even_list]

        results_morn = rocchio_search(text, price_range, morning_restaurant_ids)
        results_even = rocchio_search(text, price_range, evening_restaurant_ids)        

        combined_results = results_morn + results_even
        results = json.dumps(combined_results)

    else:
        results = svd_search(text, price_range)

    return results    

if 'DB_NAME' not in os.environ:
    app.run(debug=True,host="0.0.0.0",port=5000)