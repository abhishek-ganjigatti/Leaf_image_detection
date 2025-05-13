# Import necessary libraries
from flask import Flask, render_template, request, jsonify
import os
import tensorflow as tf
from PIL import Image
import numpy as np
import pandas as pd

# App setup
app = Flask(
    __name__,
    template_folder='D:/pythonn alll/plf_dl/Plant_Identification_App/templates',
    static_folder='D:/pythonn alll/plf_dl/Plant_Identification_App/frontend/static'
)

# Define upload folder path
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'backend', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load model
model_path = os.path.join('backend', 'model', '4th_year_final_project_10-02-25_14-55.h5')
print(f"Loading model from: {model_path}")
try:
    model = tf.keras.models.load_model(model_path)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    raise e

# Load class labels (plant types)
labels_path = os.path.join('backend', 'data', 'tree_names.csv')
print(f"Loading class labels from: {labels_path}")
try:
    df_labels = pd.read_csv(labels_path, header=None)
    class_labels = df_labels.iloc[0].tolist()
    print(f"Class labels loaded: {class_labels}")
except Exception as e:
    print(f"Error loading class labels: {e}")
    raise e

# Load plant info (additional details)
plant_info_path = os.path.join('backend', 'data', 'plant_info.csv')
print(f"Loading plant info from: {plant_info_path}")
try:
    df_info = pd.read_csv(plant_info_path)
    df_info['Scientific Name Normalized'] = df_info['Scientific Name'].str.strip().str.lower()
    print("Plant info loaded successfully.")
except Exception as e:
    print(f"Error loading plant info: {e}")
    raise e

# Routes
@app.route('/')
def index():
    """Route for the homepage."""
    print("Index route accessed.")
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Route for making plant predictions."""
    print("Predict route accessed.")
    
    if 'image' not in request.files:
        print("No image in request.")
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    
    if file.filename == '':
        print("Empty filename in image upload.")
        return jsonify({'error': 'Empty filename'}), 400

    img_path = os.path.join(UPLOAD_FOLDER, file.filename)
    try:
        file.save(img_path)
        print(f"Image saved to {img_path}")
    except Exception as e:
        print(f"Error saving image: {e}")
        return jsonify({'error': 'Error saving image'}), 500

    try:
        img = Image.open(img_path).convert('RGB')
        img = img.resize((224, 224))
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        print(f"Image preprocessed: shape {img_array.shape}")
    except Exception as e:
        print(f"Error during image preprocessing: {e}")
        return jsonify({'error': 'Error during image preprocessing'}), 500

    try:
        predictions = model.predict(img_array)
        predicted_idx = np.argmax(predictions, axis=1)[0]
        predicted_label = class_labels[predicted_idx]
        confidence = np.max(predictions) * 100
        print(f"Prediction: {predicted_label}, Confidence: {confidence:.2f}%")
    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({'error': 'Error during prediction'}), 500

    try:
        label_norm = predicted_label.strip().lower()
        match = df_info[df_info['Scientific Name Normalized'] == label_norm]
        print(f"Matching plant info: {match}")
    except Exception as e:
        print(f"Error during plant info matching: {e}")
        return jsonify({'error': 'Error during plant info matching'}), 500

    # Prepare the response with flattened, frontend-compatible structure
    if not match.empty:
        plant_data = match.iloc[0]

        result = {
            "common_name": plant_data["Common Name"],
            "scientific_name": plant_data["Scientific Name"],
            "lifetime": "N/A",
            "water": {
                "description": plant_data.get("Water Required Per Day", "No data"),
                "level": "Moderate",
                "percentage": 60
            },
            "soil": {
                "description": plant_data.get("Soil Types Suitable for Plant", "No data"),
                "level": "Well-drained",
                "percentage": 70
            },
            "light": {
                "description": "Prefers partial to full sunlight",
                "level": "Medium",
                "percentage": 65
            },
            "temperature": plant_data.get("Temperature for Plant", "No data"),
            "season": plant_data.get("Best Season to Plant", "No data"),
            "edible": plant_data.get("Edible (Yes/No) & Edible Parts", "No data"),
            "use_case": plant_data.get("Industrial/Domestic Use Case", "No data"),
            "regions": plant_data.get("Commonly Grown Regions", "No data"),
            "propagation": plant_data.get("Propagation Method", "No data"),
            "tips": [
                {"icon": "fa-tint", "text": "Water moderately as needed."},
                {"icon": "fa-sun", "text": "Place in indirect sunlight."},
                {"icon": "fa-seedling", "text": "Use well-drained soil mix."}
            ],
            "costs": {
                "maintenance": "₹500",
                "fertilizer": "₹200",
                "pesticide": "₹100",
                "life": "10 yrs"
            }
        }
    else:
        result = {
            "error": "No plant data found for prediction."
        }

    print(f"Response prepared: {result}")
    return jsonify(result)


# Start the Flask app
if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(debug=True)
