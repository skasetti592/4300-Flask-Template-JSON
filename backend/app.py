import json
import os
from flask import Flask, render_template, request
from flask_cors import CORS
from helpers.MySQLDatabaseHandler import MySQLDatabaseHandler
import pandas as pd
import foodies_cossim as fc
import foodies_svd as svd 
import foodies_rocchio as rocchio

# ROOT_PATH for linking with all your files. 
# Feel free to use a config.py or settings.py with a global export variable
os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..",os.curdir))

# Get the directory of the current script
current_directory = os.path.dirname(os.path.abspath(__file__))

# Specify the path to the JSON file relative to the current script
json_file_path = os.path.join(current_directory, 'csvjson.json')

# Assuming your JSON data is stored in a file named 'init.json'
with open(json_file_path, 'r', errors='ignore') as file:
    data = json.load(file)
    restaurants_df = pd.DataFrame(data['restaurants'])
    restaurants_df = restaurants_df.drop_duplicates(subset=['name', 'comments'], ignore_index=True)
    
   #reviews_df = pd.DataFrame(data['reviews'])

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
    
def svd_search(filtered_df, query): 

    results = svd.svd_results(filtered_df, query)
    df = pd.DataFrame(results, columns=['name'])
    matches = pd.merge(df,filtered_df, on='name') 
    matches_filtered = matches[['name','type', 'price_range', 'street_address', 'locality', "trip_advisor_url", "comments"]]
    out = matches_filtered.sort_index()
    matches_filtered_json = out.to_json(orient='records')
    print(matches_filtered_json)
    return matches_filtered_json 

def rocchio_search(query, price_range): 
    results = rocchio.rocchio_results(restaurants_df, query, price_range)
    #print(results)
    df = pd.DataFrame(results, columns=['name'])
    matches = pd.merge(df,restaurants_df, on='name') 
    matches_filtered = matches[['name','type', 'price_range', 'street_address', 'locality', "trip_advisor_url", "comments"]]
    out = matches_filtered.sort_index()
    matches_filtered_json = out.to_json(orient='records')
    return matches_filtered_json 

    
# Sample search using json with pandas
def json_search(query):
    matches = []
    #merged_df = pd.merge(episodes_df, reviews_df, left_on='id', right_on='id', how='inner')
    
    #m_e = restaurants_df['Morning']
    matches = restaurants_df[restaurants_df['type'].str.lower().str.contains(query.lower())]
    tags = []

    matches_filtered = matches[['name','type', 'price_range']]
    matches_filtered_json = matches_filtered.to_json(orient='records')
    return matches_filtered_json

def filter_data(time, price, locality, df):
    print(time + "filter")
    if time == "morning":
        new_df = df[df["morning"] == 1]
    elif time == "evening":
        new_df= df[df["evening"] == 1]
    elif time == "nightlife":
        new_df = df[df["nightlife"] == 1]
        
    filtered = new_df[(new_df[new_df["price_range"] == price]) & (new_df[new_df["locality"] == locality])]
    return filtered
        

@app.route("/")
def home():
    return render_template('base.html',title="sample html")

@app.route("/episodes")
def episodes_search():
    text = request.args.get("title")
    time = request.args.get("time")
    print(time + "in epi")
    price_range = request.args.get("price_range")
    price = ""
    if price_range == "2":
        price = "$"
    elif price_range == "3":
        price = "$$"
    elif price_range == "4":
        price = "$$$"
    locality = request.args.get("locality")
    print('here')
    filtered_df = filter_data(time, price, locality, restaurants_df)
    #return svd_search(text, time, price)
    
    return svd_search(filtered_df,text)
    

if 'DB_NAME' not in os.environ:
    app.run(debug=True,host="0.0.0.0",port=5000)