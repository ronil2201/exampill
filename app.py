"""
AI Study Planner - Pure Python Version
No web framework, just command line
"""

from flask import Flask, render_template, request, redirect, url_for, session
import google.generativeai as genai
import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime

app = Flask(__name__)
app.secret_key = "students" 

# Site-wide name used in templates and meta
app.config['SITE_NAME'] = "Exampill"

@app.context_processor
def inject_site_name():
    return dict(site_name=app.config.get('SITE_NAME', 'Exampill'))

# Load environment variables from .env
load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

if not GEMINI_API_KEY:
    print("⚠️ GEMINI_API_KEY not set in environment (check .env)")
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
    except Exception as e:
        print(f"⚠️ Failed to configure Gemini client: {e}")


def call_model(prompt):
    """Attempt multiple ways to call the installed GenAI client and return text or None."""
    try:
        # If the model object exposes generate_content (original code expectation)
        if hasattr(model, 'generate_content'):
            resp = model.generate_content(prompt)
            text = getattr(resp, 'text', None)
            if text is None and isinstance(resp, str):
                text = resp
            return text.strip() if isinstance(text, str) else None

        # If the genai module exposes a generate(...) function returning dict/object
        if hasattr(genai, 'generate'):
            try:
                resp = genai.generate(prompt=prompt)
            except TypeError:
                # older signatures might accept positional
                resp = genai.generate(prompt)

            if isinstance(resp, dict):
                text = resp.get('text') or resp.get('content') or resp.get('output') or None
            else:
                text = getattr(resp, 'text', None)
            return text.strip() if isinstance(text, str) else None

        # If the module exposes generate_text
        if hasattr(genai, 'generate_text'):
            try:
                # try to pass model info if available
                model_name = model if isinstance(model, str) else getattr(model, 'name', None)
                resp = genai.generate_text(prompt=prompt, model=model_name) if model_name else genai.generate_text(prompt=prompt)
            except Exception:
                resp = genai.generate_text(prompt=prompt)

            text = getattr(resp, 'text', None)
            if text is None and isinstance(resp, dict):
                text = resp.get('text')
            return text.strip() if isinstance(text, str) else None

        # Last resort: if model is a string name, try passing it to genai.generate
        if isinstance(model, str) and hasattr(genai, 'generate'):
            try:
                resp = genai.generate(model=model, prompt=prompt)
                if isinstance(resp, dict):
                    text = resp.get('text') or resp.get('content')
                else:
                    text = getattr(resp, 'text', None)
                return text.strip() if isinstance(text, str) else None
            except Exception:
                pass

        print('DEBUG: no compatible genai method found; model type:', type(model))
        return None

    except Exception as e:
        print('DEBUG: call_model exception:', e)
        return None

def print_header(text):
    """Print a nice header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")


def generate_study_plan(exam_name, semester, university, exam_date):
    """Generate study plan using Gemini"""
    
    print("🤖 Asking Gemini AI to generate study plan...")
    
    prompt = f"""You are an education expert.

Create a study plan for:
Exam: {exam_name}
Level: {semester}
Board: {university}
Exam Date: {exam_date}

List 8–10 important topics.
For each topic include:
- name
- weightage (HIGH/MEDIUM/LOW)
- estimated_hours
- 3 key concepts

Return ONLY valid JSON in this format:
{{
  "topics": [{{
      "name": "",
      "weightage": "",
      "estimated_hours": 0,
      "key_concepts": ["", "", ""]}}
  ]
}}"""

    
    try:
        text = call_model(prompt)

        if text:
            # Clean markdown
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()

            plan = json.loads(text)
            print(f"✅ Generated {len(plan['topics'])} topics\n")
            return plan

        # If AI didn't return valid text, fallback
        print('⚠️ AI backend unavailable or returned no text — falling back to static plan')
        fallback = {
            'topics': [
                {'name': 'Important Topic 1', 'weightage': 'HIGH', 'estimated_hours': 12, 'key_concepts': ['Concept A','Concept B','Concept C']},
                {'name': 'Important Topic 2', 'weightage': 'HIGH', 'estimated_hours': 10, 'key_concepts': ['Concept D','Concept E','Concept F']},
                {'name': 'Topic 3', 'weightage': 'MEDIUM', 'estimated_hours': 8, 'key_concepts': ['Concept G','Concept H','Concept I']},
                {'name': 'Topic 4', 'weightage': 'LOW', 'estimated_hours': 5, 'key_concepts': ['Concept J','Concept K','Concept L']},
                {'name': 'Topic 5', 'weightage': 'MEDIUM', 'estimated_hours': 6, 'key_concepts': ['Concept M','Concept N','Concept O']}
            ]
        }
        return fallback

    except Exception as e:
        print(f"❌ Error while generating study plan: {e}")
        return None


def search_youtube(topic_name, exam_name):
    """Search YouTube for videos"""
    
    print(f"🔍 Searching YouTube for: {topic_name}")
    
    query = f"{topic_name} {exam_name} tutorial"
    url = "https://www.googleapis.com/youtube/v3/search"
    
    params = {
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'maxResults': 10,
        'videoDuration': 'medium',
        'order': 'relevance',
        'key': YOUTUBE_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        videos = []
        for item in data.get('items', []):
            videos.append({
                'video_id': item['id']['videoId'],
                'title': item['snippet']['title'],
                'channel': item['snippet']['channelTitle'],
                'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            })
        
        print(f"✅ Found {len(videos)} videos\n")
        return videos
        
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return []


def rank_videos(topic_name, exam_name, videos):
    """Rank videos using Gemini"""
    
    if not videos:
        return []
    
    print(f"🤖 Ranking videos with Gemini AI...")
    
    prompt = f"""Rank YouTube videos for topic "{topic_name}" and exam "{exam_name}".

Videos:
{json.dumps(videos)}

Pick TOP 5.

Return ONLY valid JSON:
{{
  "ranked_videos": [
    {{
      "video_id": "",
      "rank": 1,
      "reasoning": ""
    }}
  ]
}}"""

    
    try:
        text = call_model(prompt)

        if text:
            print('DEBUG: raw ranking output from model:\n', text)
            # Clean markdown
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()

            # Try to extract JSON object/array embedded in the response
            import re
            json_text = None
            # look for a JSON object
            m_obj = re.search(r"\{[\s\S]*\}", text)
            m_arr = re.search(r"\[[\s\S]*\]", text)
            if m_obj:
                json_text = m_obj.group(0)
            elif m_arr:
                json_text = m_arr.group(0)

            if json_text:
                try:
                    result = json.loads(json_text)
                    ranked = result.get('ranked_videos', []) if isinstance(result, dict) else result
                    print(f"✅ Ranked {len(ranked)} videos (parsed JSON)\n")
                    return ranked[:5]
                except Exception as e:
                    print('DEBUG: failed to parse extracted JSON:', e)

            # If JSON parsing failed, attempt heuristic: match video_ids in the raw text
            # and order by their first occurrence index
            id_positions = []
            for v in videos:
                vid = v.get('video_id')
                if not vid:
                    continue
                pos = text.find(vid)
                if pos != -1:
                    # try to extract a short reasoning near the id (few chars around)
                    start = max(0, pos - 120)
                    end = min(len(text), pos + 200)
                    reasoning = text[start:end].strip()
                    id_positions.append((vid, pos, reasoning))

            if id_positions:
                # sort by position (earlier means higher rank)
                id_positions.sort(key=lambda x: x[1])
                ranked = []
                for i, (vid, pos, reasoning) in enumerate(id_positions[:5]):
                    ranked.append({'video_id': vid, 'rank': i+1, 'reasoning': reasoning})
                print(f"✅ Ranked {len(ranked)} videos (heuristic by id match)\n")
                return ranked

            # else fall through to fallback

        print(f"⚠️ Ranking failed or AI returned no text, using first 5 videos\n")
        return [{'video_id': v['video_id'], 'rank': i+1} for i, v in enumerate(videos[:5])]

    except Exception as e:
        print(f"⚠️ Ranking failed with exception: {e} — using first 5 videos\n")
        return [{'video_id': v['video_id'], 'rank': i+1} for i, v in enumerate(videos[:5])]


def display_study_plan(exam_name, semester, university, exam_date, topics):
    """Display the study plan nicely"""
    
    print_header("📚 YOUR PERSONALIZED STUDY PLAN")
    
    print(f"📖 Exam: {exam_name}")
    print(f"📅 Semester: {semester}")
    print(f"🏫 University: {university}")
    print(f"📆 Exam Date: {exam_date}")
    
    print_header(f"📋 {len(topics)} TOPICS TO STUDY")
    
    for i, topic in enumerate(topics, 1):
        print(f"\n{'='*60}")
        print(f"Topic {i}: {topic['name']}")
        print(f"{'='*60}")
        
        # Topic details
        print(f"⚡ Priority: {topic['weightage']}")
        print(f"⏱️  Estimated Hours: {topic['estimated_hours']}")
        
        # Key concepts
        print(f"\n🎯 Key Concepts:")
        for concept in topic['key_concepts']:
            print(f"   • {concept}")
        
        # Videos
        if 'videos' in topic and topic['videos']:
            print(f"\n🎥 Recommended Videos ({len(topic['videos'])}):")
            for video in topic['videos']:
                print(f"\n   #{video['rank']} - {video['title']}")
                print(f"       📺 {video['channel']}")
                print(f"       🔗 {video['url']}")
                if 'reasoning' in video:
                    print(f"       💡 {video['reasoning']}")
        else:
            print(f"\n🎥 No videos found for this topic")


def main():
    """Main function"""
    
    print_header("🎓 AI-POWERED STUDY PLANNER")
    
    # Get user input
    print("Let's create your personalized study plan!\n")
    
    exam_name = session.get("exam_name")
    semester = session.get("semester")
    university = session.get("university")
    exam_date = session.get("exam_date")
    
    print(f"Exam: {exam_name}")
    print(f"Semester: {semester}")
    print(f"University: {university}")
    print(f"Exam Date: {exam_date}\n")
    if not all([exam_name, semester, university, exam_date]):
        print(exam_name, semester, university, exam_date,"hello")
        return
    
    # Generate study plan
    print_header("GENERATING STUDY PLAN")
    study_plan = generate_study_plan(exam_name, semester, university, exam_date)
    
    if not study_plan or not study_plan.get('topics'):
        print("❌ Failed to generate study plan")
        return
    
    # Process each topic (limit to 5 for demo)
    topics_with_videos = []
    
    for topic in study_plan['topics'][:5]:
        print(f"\n{'─'*60}")
        print(f"Processing: {topic['name']}")
        print(f"{'─'*60}")
        
        # Search YouTube
        videos = search_youtube(topic['name'], exam_name)
        
        # Rank with Gemini
        ranked = rank_videos(topic['name'], exam_name, videos)
        
        # Merge data
        topic['videos'] = []
        for ranked_video in ranked:
            full_video = next((v for v in videos if v['video_id'] == ranked_video['video_id']), None)
            if full_video:
                full_video['rank'] = ranked_video['rank']
                full_video['reasoning'] = ranked_video.get('reasoning', '')
                topic['videos'].append(full_video)
        
        topics_with_videos.append(topic)
    
    # Display final result
    display_study_plan(exam_name, semester, university, exam_date, topics_with_videos)
    
    print_header("✅ STUDY PLAN GENERATED SUCCESSFULLY")
    print("Good luck with your exam preparation! 🎯\n")
    return topics_with_videos

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/Submit", methods=["POST"])
def submit():
    session["semester"] = request.form.get("semester")
    session["exam_name"] = request.form.get("subject")
    session["university"] = request.form.get("university")
    session["exam_date"] = request.form.get("examDate")
    print(session["semester"], session["exam_name"], session["university"], session["exam_date"])

    # Generate the study plan (topics only) and save to session
    study_plan = generate_study_plan(session.get("exam_name"), session.get("semester"), session.get("university"), session.get("exam_date"))
    if not study_plan or not study_plan.get('topics'):
        return render_template("result.html")

    # Save topics (without videos) into session for later per-topic video lookup
    session['study_plan'] = study_plan
    session['topics'] = study_plan.get('topics')

    # Redirect to dashboard so user sees the generated plan summary
    return redirect(url_for('dashboard'))


@app.route('/topics')
def topics_page():
    topics = session.get('topics')
    if not topics:
        return redirect(url_for('index'))

    # Normalize topic keys (handle variations from AI output) and ensure consistent structure
    normalized = []
    for t in topics:
        name = t.get('name') or t.get('topic') or t.get('title') or ''
        weight = (t.get('weightage') or t.get('weight') or t.get('priority') or '').upper()
        if weight not in ('HIGH', 'MEDIUM', 'LOW'):
            # try to detect from text
            if 'high' in weight.lower():
                weight = 'HIGH'
            elif 'med' in weight.lower():
                weight = 'MEDIUM'
            elif 'low' in weight.lower():
                weight = 'LOW'
            else:
                weight = 'MEDIUM'

        est = t.get('estimated_hours') if t.get('estimated_hours') is not None else t.get('estimatedHours') if t.get('estimatedHours') is not None else t.get('hours') if t.get('hours') is not None else ''
        key_concepts = t.get('key_concepts') or t.get('keyConcepts') or t.get('concepts') or []
        # Ensure list
        if not isinstance(key_concepts, list):
            try:
                key_concepts = list(key_concepts)
            except Exception:
                key_concepts = [str(key_concepts)]

        normalized.append({
            'name': name,
            'weightage': weight,
            'estimated_hours': est,
            'key_concepts': key_concepts
        })

    # Sort by weightage (HIGH -> MEDIUM -> LOW)
    order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
    normalized.sort(key=lambda x: order.get(x.get('weightage', 'MEDIUM'), 1))

    # Save normalized topics back to session so /videos/<idx> sees same order
    session['topics'] = normalized

    return render_template('topics.html', topics=normalized)


@app.route('/form')
def form_page():
    return render_template('form.html')


@app.route('/about')
def about_page():
    return render_template('about.html')


@app.route('/faq')
def faq_page():
    return render_template('faq.html')


@app.route('/dashboard')
def dashboard():
    topics = session.get('topics')
    if not topics:
        return redirect(url_for('index'))

    return render_template('dashboard.html', topics=topics, exam_name=session.get('exam_name'), university=session.get('university'), exam_date=session.get('exam_date'))


@app.route('/videos/<int:idx>')
def topic_videos(idx):
    topics = session.get('topics')
    if not topics:
        return redirect(url_for('index'))

    if idx < 0 or idx >= len(topics):
        return redirect(url_for('topics_page'))

    topic = topics[idx]

    # Perform YouTube search and ranking for this single topic
    videos = search_youtube(topic['name'], session.get('exam_name'))
    ranked = rank_videos(topic['name'], session.get('exam_name'), videos)

    # Merge ranked metadata into full video entries
    topic['videos'] = []
    for ranked_video in ranked:
        full_video = next((v for v in videos if v['video_id'] == ranked_video['video_id']), None)
        if full_video:
            full_video['rank'] = ranked_video['rank']
            full_video['reasoning'] = ranked_video.get('reasoning', '')
            topic['videos'].append(full_video)

    return render_template('videos.html', topics=[topic])

if __name__ == '__main__':
    app.run(debug=True)