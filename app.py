from flask import Flask, render_template, request, jsonify
import os
import numpy as np
from PIL import Image
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing.image import img_to_array
from bs4 import BeautifulSoup
import requests
from sklearn.svm import SVC
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from werkzeug.utils import secure_filename
import json
import re
import random  # Added for price variation

# Download NLTK data
nltk.download('vader_lexicon')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Ensure upload directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Initialize VGG16 model
try:
    model = VGG16(weights='imagenet')
except Exception as e:
    print(f"Error loading VGG16 model: {e}")
    model = None

# Initialize sentiment analyzer
sia = SentimentIntensityAnalyzer()

def predict_image(image_path):
    """Predict image content using VGG16"""
    try:
        img = Image.open(image_path)
        img = img.resize((224, 224))
        x = img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        predictions = model.predict(x)
        return decode_predictions(predictions, top=1)[0][0][1]
    except Exception as e:
        print(f"Error predicting image: {e}")
        return "Unknown"

def scrape_prices(product_name):
    """Scrape prices from e-commerce sites"""
    prices = []
    
    # Amazon scraping
    try:
        search_url = f"https://www.amazon.com/s?k={product_name.replace(' ', '+')}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        price_elements = soup.find_all('span', class_='a-price-whole')
        rating_elements = soup.find_all('span', class_='a-icon-alt')
        
        if price_elements and rating_elements:
            for price_elem, rating_elem in zip(price_elements[:3], rating_elements[:3]):
                try:
                    price = float(re.sub(r'[^\d.]', '', price_elem.text))
                    rating = float(rating_elem.text.split(' ')[0])
                    prices.append({
                        'site': 'Amazon',
                        'price': price,
                        'rating': rating
                    })
                except (ValueError, IndexError) as e:
                    print(f"Error parsing Amazon data: {e}")
    except Exception as e:
        print(f"Error scraping Amazon: {e}")

    # Flipkart scraping (mock data with variation)
    base_price = random.uniform(25, 45)
    prices.extend([
        {
            'site': 'Flipkart',
            'price': round(base_price * random.uniform(0.9, 1.1), 2),
            'rating': round(random.uniform(3.8, 4.8), 1)
        },
        {
            'site': 'Myntra',
            'price': round(base_price * random.uniform(0.95, 1.15), 2),
            'rating': round(random.uniform(3.9, 4.9), 1)
        }
    ])
    
    return prices

def rank_prices(prices):
    """Rank prices using SVM"""
    if len(prices) < 2:
        return prices
        
    try:
        X = np.array([[p['price'], p['rating']] for p in prices])
        X_normalized = (X - X.mean(axis=0)) / X.std(axis=0)
        
        svm = SVC(kernel='linear')
        y = np.array([1 if i == 0 else -1 for i in range(len(prices))])
        svm.fit(X_normalized, y)
        
        ranking_scores = svm.decision_function(X_normalized)
        ranked_indices = np.argsort(ranking_scores)[::-1]
        return [prices[i] for i in ranked_indices]
    except Exception as e:
        print(f"Error ranking prices: {e}")
        return prices

def analyze_sentiment(product_name):
    """Analyze sentiment from product reviews"""
    try:
        # Generate varied mock reviews
        review_templates = [
            ["Excellent product!", "Great quality!", "Highly recommended!", "Perfect fit!", "Amazing value!"],
            ["Good product", "Nice quality", "Worth the price", "Comfortable fit", "Decent value"],
            ["Average product", "Okay quality", "Bit pricey", "Fits okay", "Fair value"],
            ["Could be better", "Quality issues", "Too expensive", "Sizing issues", "Not worth it"]
        ]
        
        sentiment_level = random.randint(0, 3)
        reviews = random.sample(review_templates[sentiment_level], 3)
        
        sentiments = [sia.polarity_scores(review)['compound'] for review in reviews]
        avg_sentiment = sum(sentiments) / len(sentiments)
        
        return {
            'score': avg_sentiment,
            'reviews': reviews
        }
    except Exception as e:
        print(f"Error analyzing sentiment: {e}")
        return {'score': 0, 'reviews': []}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            product_name = predict_image(filepath)
            prices = scrape_prices(product_name)
            ranked_prices = rank_prices(prices)
            sentiment_analysis = analyze_sentiment(product_name)
            
            response = {
                'product': product_name.title(),
                'prices': ranked_prices,
                'sentiment': sentiment_analysis
            }
            
            os.remove(filepath)
            return jsonify(response)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)