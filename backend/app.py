import json
import os
from flask import Flask, render_template, request
from flask_cors import CORS
from helpers.MySQLDatabaseHandler import MySQLDatabaseHandler
import pandas as pd
import foodies_cossim as fc
import foodies_svd as svd 

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
    
def svd_search(query): 
    #cossims_sorted = fc.cossim_mat(restaurants_df, query)
    ##types = fc.types_set(restaurants_df)
    #qtypes = fc.tokenize_types(types, query)
    results = svd.cossim_full(restaurants_df, query)
    #print(results)
    df = pd.DataFrame(results, columns=['name'])
    #matches = pd.merge(restaurants_df,df) 
    #df['id'] = range(1, len(df)+1) 
    matches = pd.merge(df,restaurants_df, on='name') 
    matches_filtered = matches[['name','type', 'price_range']]
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

    

@app.route("/")
def home():
    return render_template('base.html',title="sample html")

@app.route("/episodes")
def episodes_search():
    text = request.args.get("title")
    return svd_search(text)

if 'DB_NAME' not in os.environ:
    app.run(debug=True,host="0.0.0.0",port=5000)