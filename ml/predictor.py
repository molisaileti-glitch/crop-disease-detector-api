# ml/predictor.py
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Loads the trained CNN model and makes predictions.
# This is the bridge between Django and TensorFlow.
# The model is loaded ONCE when Django starts
# not on every request — much faster.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import os
import json
import numpy as np
from PIL import Image
from tensorflow import keras

# ── DISEASE INFORMATION ──────────────────────────────
# Friendly names shown to farmers in the app
DISEASE_FRIENDLY_NAMES = {
    'Pepper__bell___Bacterial_spot':    'Pepper — Bacterial Spot',
    'Pepper__bell___healthy':           'Pepper — Healthy',
    'Potato___Early_blight':            'Potato — Early Blight',
    'Potato___Late_blight':             'Potato — Late Blight',
    'Potato___healthy':                 'Potato — Healthy',
    'Tomato_Bacterial_spot':            'Tomato — Bacterial Spot',
    'Tomato_Early_blight':              'Tomato — Early Blight',
    'Tomato_Late_blight':               'Tomato — Late Blight',
    'Tomato_Leaf_Mold':                 'Tomato — Leaf Mold',
    'Tomato_Septoria_leaf_spot':        'Tomato — Septoria Leaf Spot',
    'Tomato_Spider_mites_Two_spotted_spider_mite': 'Tomato — Spider Mites',
    'Tomato__Target_Spot':              'Tomato — Target Spot',
    'Tomato__Tomato_YellowLeaf__Curl_Virus': 'Tomato — Yellow Leaf Curl Virus',
    'Tomato__Tomato_mosaic_virus':      'Tomato — Mosaic Virus',
    'Tomato_healthy':                   'Tomato — Healthy',
}

# Treatment recommendations for each disease
DISEASE_TREATMENTS = {
    'Pepper__bell___Bacterial_spot':
        'Remove infected leaves immediately. Apply copper-based bactericide. Avoid overhead watering. Rotate crops next season.',
    'Pepper__bell___healthy':
        'Your pepper plant looks healthy! Continue regular watering and monitoring.',
    'Potato___Early_blight':
        'Apply fungicide containing chlorothalonil or mancozeb. Remove infected leaves. Ensure good air circulation.',
    'Potato___Late_blight':
        'URGENT: Spreads very fast. Remove and destroy all infected plants immediately. Apply metalaxyl fungicide. Do not compost infected material.',
    'Potato___healthy':
        'Your potato plant looks healthy! Monitor regularly for any signs of disease.',
    'Tomato_Bacterial_spot':
        'Apply copper-based bactericide. Remove infected leaves. Avoid working with plants when wet.',
    'Tomato_Early_blight':
        'Apply mancozeb or chlorothalonil fungicide. Remove lower infected leaves. Mulch around base of plant.',
    'Tomato_Late_blight':
        'URGENT: Apply metalaxyl fungicide immediately. Remove infected plant parts. This disease can destroy entire crop within days.',
    'Tomato_Leaf_Mold':
        'Improve air circulation. Reduce humidity. Apply fungicide with chlorothalonil. Remove infected leaves.',
    'Tomato_Septoria_leaf_spot':
        'Remove infected leaves. Apply mancozeb fungicide. Avoid overhead watering. Rotate crops.',
    'Tomato_Spider_mites_Two_spotted_spider_mite':
        'Apply miticide or insecticidal soap. Spray undersides of leaves. Increase humidity around plants.',
    'Tomato__Target_Spot':
        'Apply fungicide with azoxystrobin. Remove infected leaves. Improve air circulation.',
    'Tomato__Tomato_YellowLeaf__Curl_Virus':
        'No cure available. Remove and destroy infected plants. Control whitefly population which spreads this virus.',
    'Tomato__Tomato_mosaic_virus':
        'No cure available. Remove infected plants. Wash hands and tools. Control aphids which spread this virus.',
    'Tomato_healthy':
        'Your tomato plant looks healthy! Continue regular watering, fertilizing and monitoring.',
}

# Severity levels
DISEASE_SEVERITY = {
    'Pepper__bell___Bacterial_spot': 'medium',
    'Pepper__bell___healthy':        'none',
    'Potato___Early_blight':         'medium',
    'Potato___Late_blight':          'high',
    'Potato___healthy':              'none',
    'Tomato_Bacterial_spot':         'medium',
    'Tomato_Early_blight':           'medium',
    'Tomato_Late_blight':            'high',
    'Tomato_Leaf_Mold':              'low',
    'Tomato_Septoria_leaf_spot':     'medium',
    'Tomato_Spider_mites_Two_spotted_spider_mite': 'medium',
    'Tomato__Target_Spot':           'medium',
    'Tomato__Tomato_YellowLeaf__Curl_Virus': 'high',
    'Tomato__Tomato_mosaic_virus':   'high',
    'Tomato_healthy':                'none',
}


class CropDiseasePredictor:
    """
    Loads the trained CNN model and predicts
    the disease in a given leaf image.

    The model is loaded once when Django starts
    using the singleton pattern — fast and efficient.
    """

    # Class variable — shared across all instances
    # Model loads only once when server starts
    _model = None
    _class_labels = None

    @classmethod
    def get_model(cls):
        """
        Returns the loaded model.
        Loads it on first call — cached after that.
        """
        if cls._model is None:
            # Path to the trained model file
            model_path = os.path.join(
                os.path.dirname(__file__),
                'crop_disease_model.h5'
            )

            # Path to class labels JSON
            labels_path = os.path.join(
                os.path.dirname(__file__),
                'class_labels.json'
            )

            print("Loading crop disease ML model...")

            # Load the trained model
            cls._model = keras.models.load_model(model_path)

            # Load class labels
            with open(labels_path, 'r') as f:
                cls._class_labels = json.load(f)

            print(
                f"Model loaded successfully. "
                f"{len(cls._class_labels)} disease classes."
            )

        return cls._model, cls._class_labels

    @classmethod
    def predict(cls, image_file):
        """
        Takes an uploaded image file and returns
        the disease prediction with confidence score.

        Returns a dictionary with:
        - disease_name: raw class name
        - friendly_name: human readable name
        - confidence: percentage 0-100
        - treatment: what to do
        - severity: none/low/medium/high
        - crop_type: Tomato/Potato/Pepper
        """

        # Load model (cached after first load)
        model, class_labels = cls.get_model()

        # ── PREPROCESS IMAGE ─────────────────────────
        # Open image from uploaded file
        img = Image.open(image_file)

        # Convert to RGB (handles grayscale and RGBA)
        img = img.convert('RGB')

        # Resize to 224x224 — same size used in training
        img = img.resize((224, 224))

        # Convert to numpy array
        img_array = np.array(img)

        # Scale pixels from 0-255 to 0-1
        # Must match preprocessing used during training
        img_array = img_array / 255.0

        # Add batch dimension — model expects (1, 224, 224, 3)
        img_array = np.expand_dims(img_array, axis=0)

        # ── MAKE PREDICTION ──────────────────────────
        # Get probability for each of 15 disease classes
        predictions = model.predict(img_array, verbose=0)

        # Get the class with highest probability
        predicted_index = int(np.argmax(predictions[0]))
        confidence = float(predictions[0][predicted_index]) * 100

        # Get disease name from class labels
        disease_name = class_labels[str(predicted_index)]

        # ── PREPARE RESPONSE ─────────────────────────
        # Extract crop type from disease name
        if 'Tomato' in disease_name:
            crop_type = 'Tomato'
        elif 'Potato' in disease_name:
            crop_type = 'Potato'
        elif 'Pepper' in disease_name:
            crop_type = 'Pepper'
        else:
            crop_type = 'Unknown'

        return {
            'disease_name':  disease_name,
            'friendly_name': DISEASE_FRIENDLY_NAMES.get(
                disease_name, disease_name
            ),
            'confidence':    round(confidence, 2),
            'treatment':     DISEASE_TREATMENTS.get(
                disease_name,
                'Consult an agricultural officer.'
            ),
            'severity':      DISEASE_SEVERITY.get(
                disease_name, 'unknown'
            ),
            'crop_type':     crop_type,
            # Warn if model is not very confident
            'low_confidence_warning': confidence < 70,
        }