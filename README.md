# NutriScan AI 🍎

NutriScan AI is a Django-based web app that scans food product barcodes, fetches nutrition data, and analyzes whether the product suits the user based on their health profile.

## 🚀 Features
- User authentication (login/signup/profile)
- Scan food product barcode
- Fetch nutrition info using Open Food Facts API
- Personalized analysis using Generative AI (Ollama)
- MySQL database integration

## 🛠️ Tech Stack
- **Backend**: Django, MySQL.
- **Frontend**: HTML, CSS, JS
- **AI**: LLM(ollama), requests, PyMuPDF, OpenCV
- **API**:Openfoodfacts,llama-3

## ⚙️ How to Run Locally
```bash
git clone https://github.com/santosh6672/nutriscan.git
cd nutriscan
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
