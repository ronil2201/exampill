
# 📘 Exampill – AI Powered Exam Preparation Platform

Exampill is an AI-based web application that helps students prepare for exams more effectively.
Students fill in basic exam details, and the system analyzes high‑weightage topics and recommends
the best YouTube videos using **Google Gemini AI**.

---

## 🚀 Features

- 📝 Simple exam details form
- 🤖 AI-powered topic weightage analysis
- 📊 Priority-based important topics
- 🎥 Best YouTube video recommendations
- 📱 Responsive and student-friendly UI
- ☁️ Ready for deployment

---

## 🛠️ Tech Stack

### Frontend
- HTML
- CSS

### Backend
- Python
- Flask

### AI
- Google Gemini API

---

## 📂 Project Structure

```
exam-buddy/
│
├── app.py                  # Main Flask application
├── requirements.txt        # Project dependencies
├── .env                    # API keys (not uploaded to GitHub)
├── Procfile                # Deployment configuration
│
├── templates/
│   ├── index.html          # Home & form page
│   ├── result.html         # Topic weightage page
│   ├── videos.html         # YouTube recommendations
│
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   └── images/
│
└── README.md
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository
```
git clone https://github.com/your-username/exam-buddy.git
cd exam-buddy
```

### 2️⃣ Create Virtual Environment (Optional but Recommended)
```
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3️⃣ Install Dependencies
```
pip install -r requirements.txt
```

### 4️⃣ Setup Environment Variables

Create a `.env` file in the root directory:

```
GEMINI_API_KEY=your_api_key_here
```

---

## ▶️ Run the Application

```
python app.py
```

Open browser and visit:
```
http://127.0.0.1:5000/
```

---

## 🌍 Deployment

This project can be deployed on:
- Render
- Railway
- Heroku

Gunicorn is included for production deployment.

---

## 🎯 Use Cases

- College and university exams
- Semester exams
- Smart exam preparation using AI

---

## ⭐ Future Enhancements

- User login and dashboard
- Exam history tracking
- PDF study planner
- Mock tests
- Multi-language support

---

## 👨‍💻 Author

**Ronil**  
Student Project – Exampill

---

## 📄 License

This project is created for **educational purposes only**.
