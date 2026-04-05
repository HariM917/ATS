import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)
CORS(app)

# Global variable for the model
model = None

def get_model():
    global model
    if model is None:
        print("Loading ultra-lightweight AI model...")
        # 'paraphrase-albert-small-v2' is even smaller than MiniLM
        model = SentenceTransformer('paraphrase-albert-small-v2')
    return model

@app.route('/')
def home():
    return "ATS Backend is Live!"

@app.route('/api/score', methods=['POST'])
def score_resume():
    try:
        data = request.json
        jd = data.get('job_description', '')
        resume = data.get('resume_text', '')

        if not jd or not resume:
            return jsonify({"error": "Missing input"}), 400

        # Load model only when needed to save startup memory
        nlp = get_model()
        
        emb1 = nlp.encode(jd, convert_to_tensor=True)
        emb2 = nlp.encode(resume, convert_to_tensor=True)
        
        score = float(util.cos_sim(emb1, emb2)[0][0]) * 100

        return jsonify({
            "score": round(score, 2),
            "match_level": "High" if score > 70 else "Medium" if score > 40 else "Low"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)