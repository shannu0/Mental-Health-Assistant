from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import json
import os
import re
import nltk
import numpy as np
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import pairwise_distances
import pandas as pd
from datetime import datetime
import uuid

# Download NLTK data
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

app = Flask(__name__)
app.secret_key = 'mental_health_app_secret_key'

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

# Create necessary directories
os.makedirs('static/data', exist_ok=True)

# Define paths
USERS_FILE = 'static/data/users.json'
JSON_FILE = 'static/data/mentalhealth.json'
CSV_FILE = 'static/data/mentalhealth.csv'

# Create users.json if it doesn't exist
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({"users": []}, f)

# Function to load users
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {"users": []}

# Function to save users
def save_users(users_data):
    with open(USERS_FILE, 'w') as f:
        json.dump(users_data, f, indent=4)

# Load mental health JSON data
def load_mental_health_json():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r') as file:
            return json.load(file)
    return {"intents": []}

# Load mental health CSV data
def load_mental_health_csv():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    return pd.DataFrame(columns=['Questions', 'Answers'])

# Function for text normalization
def text_normalization(text):
    text = str(text).lower()
    spl_char_text = re.sub(r'[^ a-z]', '', text)
    tokens = nltk.word_tokenize(spl_char_text)
    lema = WordNetLemmatizer()
    tags_list = nltk.pos_tag(tokens, tagset=None)
    lema_words = []
    
    for token, pos_token in tags_list:
        if pos_token.startswith('V'):
            pos_val = 'v'
        elif pos_token.startswith('J'):
            pos_val = 'a'
        elif pos_token.startswith('R'):
            pos_val = 'r'
        else:
            pos_val = 'n'
        
        lema_token = lema.lemmatize(token, pos_val)
        lema_words.append(lema_token)
    
    return " ".join(lema_words)

# Load and preprocess data
mental_health_data = load_mental_health_json()
mental_health_csv = load_mental_health_csv()

# Preprocess the mental health data for intent matching
intents_data = []
for intent in mental_health_data['intents']:
    for pattern in intent['patterns']:
        intents_data.append({
            'pattern': pattern,
            'lemmatized': text_normalization(pattern),
            'tag': intent['tag'],
            'response': intent['responses'][0]
        })

# Create DataFrame for intents
intent_df = pd.DataFrame(intents_data) if intents_data else pd.DataFrame(columns=['pattern', 'lemmatized', 'tag', 'response'])

# Create vectorizer for intent patterns if data exists
if not intent_df.empty:
    cv = CountVectorizer()
    X = cv.fit_transform(intent_df['lemmatized']).toarray()
    intent_bow = pd.DataFrame(X, columns=cv.get_feature_names_out())
else:
    cv = CountVectorizer()
    intent_bow = pd.DataFrame()

# Preprocess CSV data if it exists
if not mental_health_csv.empty and 'Questions' in mental_health_csv.columns:
    mental_health_csv['lemmatized_text'] = mental_health_csv['Questions'].apply(text_normalization)
    csv_cv = CountVectorizer()
    X_csv = csv_cv.fit_transform(mental_health_csv['lemmatized_text']).toarray()
    csv_bow = pd.DataFrame(X_csv, columns=csv_cv.get_feature_names_out())
else:
    csv_cv = CountVectorizer()
    csv_bow = pd.DataFrame()

# Function to find the best intent match
def get_intent_response(query):
    query_lemma = text_normalization(query)
    
    # Default response if no match is found
    default_response = "I'm sorry, I don't have information on that topic. Please try asking something about mental health."
    default_score = 0.0
    
    # Check if we have intent data
    if not intent_df.empty:
        query_bow = cv.transform([query_lemma]).toarray()
        
        # Calculate cosine similarity with intent patterns
        cosine_values = 1 - pairwise_distances(intent_bow, query_bow, metric='cosine')
        max_index = cosine_values.argmax()
        similarity_score = cosine_values[max_index][0]
        
        # If similarity is too low, search in CSV data
        if similarity_score < 0.2 and not mental_health_csv.empty and 'Questions' in mental_health_csv.columns:
            query_csv_bow = csv_cv.transform([query_lemma]).toarray()
            csv_cosine_values = 1 - pairwise_distances(csv_bow, query_csv_bow, metric='cosine')
            csv_max_index = csv_cosine_values.argmax()
            csv_similarity_score = csv_cosine_values[csv_max_index][0]
            
            if csv_similarity_score > similarity_score:
                return mental_health_csv['Answers'].iloc[csv_max_index], csv_similarity_score
        
        # Return intent response if similarity is good enough
        if similarity_score > 0.1:
            return intent_df['response'].iloc[max_index], similarity_score
    
    # If we have CSV data but no intent data
    elif not mental_health_csv.empty and 'Questions' in mental_health_csv.columns:
        query_csv_bow = csv_cv.transform([query_lemma]).toarray()
        csv_cosine_values = 1 - pairwise_distances(csv_bow, query_csv_bow, metric='cosine')
        csv_max_index = csv_cosine_values.argmax()
        csv_similarity_score = csv_cosine_values[csv_max_index][0]
        
        if csv_similarity_score > 0.1:
            return mental_health_csv['Answers'].iloc[csv_max_index], csv_similarity_score
    
    return default_response, default_score

# Function to get search suggestions
def get_suggestions(query, max_results=5):
    if not query:
        return []
    
    # Combine questions from both datasets
    all_questions = []
    
    if not intent_df.empty:
        all_questions.extend(list(intent_df['pattern']))
    
    if not mental_health_csv.empty and 'Questions' in mental_health_csv.columns:
        all_questions.extend(list(mental_health_csv['Questions']))
    
    # Calculate similarity for each question
    suggestions = []
    for question in all_questions:
        if query.lower() in question.lower():
            suggestions.append(question)
            if len(suggestions) >= max_results:
                break
    
    return suggestions

# Function to save user search history
def save_search(username, query, response):
    users_data = load_users()
    
    for user in users_data['users']:
        if user['username'] == username:
            if 'search_history' not in user:
                user['search_history'] = []
            
            user['search_history'].append({
                'id': str(uuid.uuid4()),
                'query': query,
                'response': response,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            save_users(users_data)
            break

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users_data = load_users()
        
        for user in users_data['users']:
            if user['username'] == username and user['password'] == password:
                session['username'] = username
                return redirect(url_for('dashboard'))
        
        flash('Invalid username or password')
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users_data = load_users()
        
        # Check if username already exists
        for user in users_data['users']:
            if user['username'] == username:
                flash('Username already exists')
                return redirect(url_for('signup'))
        
        # Add new user
        users_data['users'].append({
            'username': username,
            'password': password,
            'search_history': []
        })
        
        save_users(users_data)
        
        session['username'] = username
        return redirect(url_for('dashboard'))
    
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', username=session['username'])

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/search', methods=['POST'])
def search():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'})
    
    query = request.form.get('query', '')
    response, score = get_intent_response(query)
    
    # Save to user's search history
    save_search(session['username'], query, response)
    
    return jsonify({
        'response': response,
        'score': float(score)
    })

@app.route('/suggest', methods=['GET'])
def suggest():
    query = request.args.get('query', '')
    suggestions = get_suggestions(query)
    return jsonify(suggestions)

@app.route('/history')
def history():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    users_data = load_users()
    search_history = []
    
    for user in users_data['users']:
        if user['username'] == session['username']:
            if 'search_history' in user:
                search_history = user['search_history']
            break
    
    return render_template('history.html', search_history=search_history)

@app.route('/clear_history', methods=['POST'])
def clear_history():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    users_data = load_users()
    
    for user in users_data['users']:
        if user['username'] == session['username']:
            user['search_history'] = []
            save_users(users_data)
            break
    
    return redirect(url_for('history'))

if __name__ == '__main__':
    app.run(debug=True)

