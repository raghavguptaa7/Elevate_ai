from flask import render_template, request, jsonify, session
from . import study_bp
import sqlite3
import json
import re  # <-- IMPORTED FOR ROBUST JSON PARSING
from services.groq_client import GroqClient
from datetime import datetime, timedelta
from utils.logger import log_info, log_error, log_api_request

# Initialize Groq client
groq_client = GroqClient()

# Helper function to get database connection
def get_db_connection():
    conn = sqlite3.connect('database/database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Helper function to robustly extract JSON from AI response
def extract_json_from_response(raw_response, logger_func):
    """
    Finds the first '{' and the last '}' in the raw string
    to extract the JSON object, ignoring markdown fences.
    """
    match = re.search(r"\{.*\}", raw_response, re.DOTALL)
    if not match:
        logger_func(f"No JSON object found in Groq response: {raw_response[:200]}")
        return None
        
    json_string = match.group(0)
    return json_string

# Syllabus Routes
@study_bp.route('/syllabus', methods=['GET'])
def syllabus_page():
    return render_template('syllabus.html')

@study_bp.route('/syllabus/upload', methods=['POST'])
def upload_syllabus():
    log_api_request(request, 'syllabus_upload', 200)

    data = request.form
    subject = data.get('subject')
    syllabus_content = data.get('syllabus_content') # This is the raw text
    user_id = session.get('user_id', 'anonymous')

    if not subject or not syllabus_content:
        return jsonify({"error": "Missing subject or syllabus content"}), 400

    prompt = f"""
    You are a Syllabus Agent. Parse the following syllabus content for {subject}.
    Extract the main topics, subtopics, and learning objectives.

    Syllabus Content:
    {syllabus_content}

    Format your response STRICTLY as JSON with the following structure:
    {{
      "topics": [
        {{
          "name": "topic name",
          "subtopics": ["subtopic1", "subtopic2"],
          "learning_objectives": ["objective1", "objective2"]
        }}
      ]
    }}
    Return only valid JSON. Do not add explanations.
    """

    try:
        parsed_result_raw = groq_client.generate_response(prompt)

        # --- Robust JSON extraction ---
        clean_result = extract_json_from_response(parsed_result_raw, log_error)
        if not clean_result:
             return jsonify({"error": "Failed to extract JSON from AI response", "raw_response": parsed_result_raw}), 500

        # Try to parse the CLEANED string
        try:
            syllabus_json = json.loads(clean_result) # This is the parsed JSON
        except json.JSONDecodeError:
            log_error(f"Invalid JSON from Groq (raw): {parsed_result_raw[:200]}")
            log_error(f"Failed to parse extracted JSON: {clean_result[:200]}")
            return jsonify({"error": "Invalid JSON response from AI", "raw_response": parsed_result_raw}), 500

        # Store only if JSON is valid
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # --- START FINAL FIX (DATABASE): Insert BOTH content (raw text) AND parsed_topics (JSON) ---
        cursor.execute(
            "INSERT INTO syllabi (user_id, subject, content, parsed_topics) VALUES (?, ?, ?, ?)",
            (user_id, subject, syllabus_content, json.dumps(syllabus_json))
        )
        # --- END FINAL FIX ---
        
        syllabus_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return jsonify({"syllabus_id": syllabus_id, "parsed_syllabus": syllabus_json}), 200

    except Exception as e:
        log_error(f"Syllabus upload failed: {e}")
        return jsonify({"error": str(e)}), 500

# Quiz Routes
@study_bp.route('/quiz', methods=['GET'])
def quiz_page():
    return render_template('quiz.html')

@study_bp.route('/quiz/get', methods=['GET'])
def get_quiz():
    quiz_id = request.args.get('quiz_id')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT questions, syllabus_id FROM quizzes WHERE id = ?", (quiz_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({"error": "Quiz not found"}), 404
        
        syllabus_id = result['syllabus_id']
        questions_json = result['questions']
        
        # Get syllabus subject
        cursor.execute("SELECT subject FROM syllabi WHERE id = ?", (syllabus_id,))
        syllabus = cursor.fetchone()
        subject = syllabus['subject'] if syllabus else "Unknown Subject"
        
        conn.close()
        
        # Parse the JSON response
        try:
            quiz_data = json.loads(questions_json)
            return jsonify({"quiz_id": quiz_id, "syllabus_id": syllabus_id, "subject": subject, "quiz": quiz_data})
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid quiz data format"}), 500
    
    except Exception as e:
        log_error(f"Error fetching quiz: {e}")
        return jsonify({"error": str(e)}), 500

@study_bp.route('/study/quiz/generate', methods=['POST'])
@study_bp.route('/quiz/generate', methods=['POST'])
def generate_quiz():
    log_api_request(request, 'quiz_generate', 200)
    
    data = request.form
    syllabus_id = data.get('syllabus_id')
    difficulty = data.get('difficulty', 'medium')
    num_questions = int(data.get('num_questions', 5))
    topics = data.get('topics', '')  # Comma-separated list of topics
    user_id = session.get('user_id', 'anonymous')
    
    try:
        # Get syllabus content
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # This is correct: we need the PARSED JSON to generate the quiz
        cursor.execute("SELECT subject, parsed_topics, content FROM syllabi WHERE id = ?", (syllabus_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({"error": "Syllabus not found"}), 404
        
        subject = result['subject']
        syllabus_content = result['parsed_topics'] # Use the JSON data
        raw_syllabus = result['content']  # Get the raw syllabus content
        
        # Get user's previous quiz results to identify weak areas
        cursor.execute(
            "SELECT questions, answers, score FROM quizzes WHERE user_id = ? AND syllabus_id = ? ORDER BY created_at DESC LIMIT 5",
            (user_id, syllabus_id)
        )
        previous_quizzes = cursor.fetchall()
        
        # Extract weak topics from previous quizzes
        weak_topics = []
        if previous_quizzes:
            for quiz in previous_quizzes:
                try:
                    questions = json.loads(quiz['questions'])
                    answers = json.loads(quiz['answers'])
                    score = quiz['score']
                    
                    if score < 0.7:  # Less than 70%
                        for q in questions['questions']:
                            if q['topic'] not in weak_topics:
                                weak_topics.append(q['topic'])
                except (json.JSONDecodeError, KeyError):
                    continue
        
        # Prepare topics for the quiz
        selected_topics = []
        if topics:
            selected_topics = topics.split(',')
        elif weak_topics:
            selected_topics = weak_topics[:3]
        
        topics_str = ", ".join(selected_topics) if selected_topics else "all topics"
        
        # Call Groq API to generate quiz
        prompt = f"""You are a Quiz Generator Agent. Generate a quiz for {subject} with the following parameters:
        
        Syllabus Content: {raw_syllabus}
        Difficulty: {difficulty}
        Number of Questions: {num_questions}
        Topics to Focus on: {topics_str}
        
        Generate questions that test understanding and application of concepts, not just memorization.
        For each question, provide 4 options with one correct answer.
        
        Format your response as JSON with the following structure:
        {{"questions": [{{"id": 1, "question": "question text", "options": ["A. option1", "B. option2", "C. option3", "D. option4"], "correct_answer": "A", "topic": "topic name", "explanation": "explanation text"}}]}}
        """
        
        quiz_result_raw = groq_client.generate_response(prompt)

        # --- Robust JSON extraction ---
        quiz_result = extract_json_from_response(quiz_result_raw, log_error)
        if not quiz_result:
            return jsonify({"error": "Failed to extract JSON from AI response", "raw_response": quiz_result_raw}), 500
        
        # Store in database
        cursor.execute(
            "INSERT INTO quizzes (user_id, syllabus_id, questions, answers, score) VALUES (?, ?, ?, ?, ?)",
            (user_id, syllabus_id, quiz_result, '{}', 0.0)
        )
        quiz_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Parse the JSON response
        try:
            quiz_json = json.loads(quiz_result)
            return jsonify({"quiz_id": quiz_id, "quiz": quiz_json})
        except json.JSONDecodeError:
            log_error(f"Invalid JSON from Groq (raw): {quiz_result_raw[:200]}")
            return jsonify({"error": "Invalid JSON response from AI", "raw_response": quiz_result_raw})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@study_bp.route('/quiz/submit', methods=['POST'])
def submit_quiz():
    log_api_request(request, 'quiz_submit', 200)
    
    data = request.json
    quiz_id = data.get('quiz_id')
    user_answers = data.get('answers')
    
    try:
        # Get quiz questions
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT questions FROM quizzes WHERE id = ?", (quiz_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({"error": "Quiz not found"}), 404
        
        # Calculate score
        questions = json.loads(result['questions'])
        correct_count = 0
        total_questions = len(questions['questions'])
        
        for q in questions['questions']:
            q_id = str(q['id'])
            if q_id in user_answers and user_answers[q_id] == q['correct_answer']:
                correct_count += 1
        
        score = correct_count / total_questions if total_questions > 0 else 0
        
        # Update quiz with answers and score
        cursor.execute(
            "UPDATE quizzes SET answers = ?, score = ? WHERE id = ?",
            (json.dumps(user_answers), score, quiz_id)
        )
        
        # Update progress for topics in the quiz
        user_id = session.get('user_id', 'anonymous')
        cursor.execute("SELECT syllabus_id FROM quizzes WHERE id = ?", (quiz_id,))
        syllabus_id = cursor.fetchone()['syllabus_id']
        
        for q in questions['questions']:
            topic = q['topic']
            q_id = str(q['id'])
            status = "mastered" if q_id in user_answers and user_answers[q_id] == q['correct_answer'] else "needs_review"
            
            # Check if progress entry exists
            cursor.execute(
                "SELECT id FROM progress WHERE user_id = ? AND syllabus_id = ? AND topic = ?",
                (user_id, syllabus_id, topic)
            )
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute(
                    "UPDATE progress SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (status, existing['id'])
                )
            else:
                cursor.execute(
                    "INSERT INTO progress (user_id, syllabus_id, topic, status) VALUES (?, ?, ?, ?)",
                    (user_id, syllabus_id, topic, status)
                )
        
        conn.commit()
        
        # Prepare result with explanations
        result = {
            "score": score,
            "correct_count": correct_count,
            "total_questions": total_questions,
            "questions_with_explanations": []
        }
        
        for q in questions['questions']:
            q_id = str(q['id'])
            is_correct = q_id in user_answers and user_answers[q_id] == q['correct_answer']
            result["questions_with_explanations"].append({
                "id": q['id'],
                "question": q['question'],
                "user_answer": user_answers.get(q_id, ""),
                "correct_answer": q['correct_answer'],
                "is_correct": is_correct,
                "explanation": q['explanation'],
                "topic": q['topic']
            })
        
        conn.close()
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Study Plan Routes
@study_bp.route('/plan', methods=['GET'])
def plan_page():
    return render_template('plan.html')

@study_bp.route('/plan/get', methods=['GET'])
def get_plan():
    plan_id = request.args.get('plan_id')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT plan_content, syllabus_id, start_date, end_date FROM study_plans WHERE id = ?", (plan_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({"error": "Study plan not found"}), 404
        
        syllabus_id = result['syllabus_id']
        plan_content = result['plan_content']
        start_date = result['start_date']
        end_date = result['end_date']
        
        # Get syllabus subject
        cursor.execute("SELECT subject FROM syllabi WHERE id = ?", (syllabus_id,))
        syllabus = cursor.fetchone()
        subject = syllabus['subject'] if syllabus else "Unknown Subject"
        
        conn.close()
        
        # Parse the JSON response
        try:
            plan_data = json.loads(plan_content)
            return jsonify({
                "plan_id": plan_id, 
                "syllabus_id": syllabus_id, 
                "subject": subject, 
                "start_date": start_date,
                "end_date": end_date,
                "plan": plan_data
            })
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid plan data format"}), 500
    
    except Exception as e:
        log_error(f"Error fetching study plan: {e}")
        return jsonify({"error": str(e)}), 500

@study_bp.route('/study/plan/generate', methods=['POST'])
@study_bp.route('/plan/generate', methods=['POST'])
def generate_study_plan():
    log_api_request(request, 'plan_generate', 200)
    
    data = request.form
    syllabus_id = data.get('syllabus_id')
    duration_days = int(data.get('duration_days', 30))
    hours_per_day = float(data.get('hours_per_day', 2.0))
    user_id = session.get('user_id', 'anonymous')
    
    try:
        # Get syllabus content
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row   # ✅ important so we can use dict-style access
        cursor = conn.cursor()
        
        cursor.execute("SELECT subject, parsed_topics FROM syllabi WHERE id = ?", (syllabus_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({"error": "Syllabus not found"}), 404
        
        subject = result["subject"]
        syllabus_content = result["parsed_topics"]  # already JSON text from DB
        
        # Get user's progress to identify weak areas
        cursor.execute(
            "SELECT topic, status FROM progress WHERE user_id = ? AND syllabus_id = ?",
            (user_id, syllabus_id)
        )
        progress_results = cursor.fetchall()
        
        weak_topics = [row["topic"] for row in progress_results if row["status"] == "needs_review"]
        weak_topics_str = ", ".join(weak_topics) if weak_topics else "none identified yet"
        
        # Calculate dates
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=duration_days)).strftime("%Y-%m-%d")
        
        # Call Groq API to generate study plan
        prompt = f"""You are a Planner Agent. Generate a personalized study plan for {subject} with the following parameters:
        
        Syllabus: {syllabus_content}
        Duration: {duration_days} days
        Hours per day: {hours_per_day} hours
        Start date: {start_date}
        End date: {end_date}
        Weak topics to focus on: {weak_topics_str}
        
        Create a day-by-day study plan that:
        1. Allocates more time to weak topics
        2. Includes regular review sessions
        3. Incorporates practice exercises and self-assessment
        4. Builds concepts progressively
        5. Includes breaks and prevents burnout
        
        Format your response as JSON with the following structure:
        {{"plan": [{{"day": 1, "date": "YYYY-MM-DD", "topics": ["topic1", "topic2"], "activities": ["activity1", "activity2"], "duration_hours": 2.0, "resources": ["resource1", "resource2"]}}]}}
        """
        
        plan_result_raw = groq_client.generate_response(prompt)

        # --- Robust JSON extraction ---
        plan_result = extract_json_from_response(plan_result_raw, log_error)
        if not plan_result:
            return jsonify({"error": "Failed to extract JSON from AI response", "raw_response": plan_result_raw}), 500
        
        # Ensure we always have a string to insert in DB
        if isinstance(plan_result, dict):
            plan_str = json.dumps(plan_result)
            plan_json = plan_result
        elif isinstance(plan_result, str):
            try:
                plan_json = json.loads(plan_result)
                plan_str = plan_result
            except json.JSONDecodeError:
                log_error(f"Invalid JSON from Groq (raw): {plan_result_raw[:200]}")
                return jsonify({"error": "Invalid JSON response from AI", "raw_response": plan_result_raw}), 500
        else:
            return jsonify({"error": "Unexpected type from extract_json_from_response"}), 500

        # Store in database
        cursor.execute(
            "INSERT INTO study_plans (user_id, syllabus_id, plan_content, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            (user_id, syllabus_id, plan_str, start_date, end_date)
        )
        plan_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # ✅ Return clean JSON
        return jsonify({"plan_id": plan_id, "plan": plan_json})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Progress Routes
@study_bp.route('/progress', methods=['GET'])
def progress_page():
    return render_template('progress.html')

@study_bp.route('/progress/get', methods=['GET'])
def get_progress():
    syllabus_id = request.args.get('syllabus_id')
    days = request.args.get('days', 30, type=int)
    
    if not syllabus_id:
        return jsonify({"error": "Syllabus ID is required"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get syllabus info
        cursor.execute("SELECT subject FROM syllabi WHERE id = ?", (syllabus_id,))
        syllabus = cursor.fetchone()
        
        if not syllabus:
            conn.close()
            return jsonify({"error": "Syllabus not found"}), 404
        
        subject = syllabus['subject']
        
        # Get user ID from session
        user_id = session.get('user_id')
        if not user_id:
            conn.close()
            return jsonify({"error": "User not logged in"}), 401
        
        # Get progress data
        cursor.execute("""
            SELECT p.topic, p.mastery_level, p.created_at 
            FROM progress p
            WHERE p.user_id = ? AND p.syllabus_id = ?
            ORDER BY p.created_at DESC
        """, (user_id, syllabus_id))
        
        progress_data = cursor.fetchall()
        
        # Get quiz history
        cursor.execute("""
            SELECT q.id, q.score, q.total_questions, q.created_at, q.topics
            FROM quizzes q
            WHERE q.user_id = ? AND q.syllabus_id = ?
            ORDER BY q.created_at DESC
        """, (user_id, syllabus_id))
        
        quiz_history = cursor.fetchall()
        
        # Calculate overall mastery
        total_topics = 0
        mastered_topics = 0
        topic_mastery = {}
        
        for item in progress_data:
            topic = item['topic']
            mastery = item['mastery_level']
            
            topic_mastery[topic] = mastery
            total_topics += 1
            if mastery >= 80:  # Consider 80% or higher as mastered
                mastered_topics += 1
        
        overall_mastery = (mastered_topics / total_topics * 100) if total_topics > 0 else 0
        
        # Calculate study hours (estimate from quiz attempts)
        study_hours = len(quiz_history) * 0.5  # Assuming each quiz takes about 30 minutes
        
        # Identify weak topics (less than 60% mastery)
        weak_topics = [topic for topic, mastery in topic_mastery.items() if mastery < 60]
        
        # Format quiz history
        formatted_quizzes = []
        for quiz in quiz_history:
            formatted_quizzes.append({
                "id": quiz['id'],
                "score": quiz['score'],
                "total_questions": quiz['total_questions'],
                "percentage": round(quiz['score'] / quiz['total_questions'] * 100, 1),
                "date": quiz['created_at'],
                "topics": quiz['topics'].split(',') if quiz['topics'] else []
            })
        
        # Format progress data for chart
        chart_data = []
        for item in progress_data:
            chart_data.append({
                "topic": item['topic'],
                "mastery": item['mastery_level'],
                "date": item['last_updated']
            })
        
        conn.close()
        
        return jsonify({
            "subject": subject,
            "overall_mastery": round(overall_mastery, 1),
            "quizzes_completed": len(quiz_history),
            "study_hours": round(study_hours, 1),
            "topics_mastered": f"{mastered_topics}/{total_topics}",
            "topic_mastery": topic_mastery,
            "weak_topics": weak_topics,
            "quiz_history": formatted_quizzes,
            "chart_data": chart_data
        })
        
    except Exception as e:
        log_error(f"Error fetching progress data: {e}")
        return jsonify({"error": str(e)}), 500
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get syllabus info
        cursor.execute("SELECT subject FROM syllabi WHERE id = ?", (syllabus_id,))
        syllabus = cursor.fetchone()
        
        if not syllabus:
            conn.close()
            return jsonify({"error": "Syllabus not found"}), 404
        
        # Get progress data
        cursor.execute(
            "SELECT topic, status, notes, updated_at FROM progress WHERE user_id = ? AND syllabus_id = ? ORDER BY updated_at DESC",
            (user_id, syllabus_id)
        )
        progress_results = cursor.fetchall()
        
        # Get quiz history
        cursor.execute(
            "SELECT id, score, created_at FROM quizzes WHERE user_id = ? AND syllabus_id = ? ORDER BY created_at ASC",
            (user_id, syllabus_id)
        )
        quiz_results = cursor.fetchall()
        
        # Format results
        progress_data = {
            "subject": syllabus['subject'],
            "topics": [],
            "quiz_history": []
        }
        
        for progress in progress_results:
            progress_data["topics"].append({
                "topic": progress['topic'],
                "status": progress['status'],
                "notes": progress['notes'],
                "updated_at": progress['updated_at']
            })
        
        for quiz in quiz_results:
            progress_data["quiz_history"].append({
                "quiz_id": quiz['id'],
                "score": quiz['score'],
                "date": quiz['created_at']
            })
        
        conn.close()
        return jsonify(progress_data)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@study_bp.route('/progress/update', methods=['POST'])
def update_progress():
    log_api_request(request, 'progress_update', 200)
    
    data = request.json
    syllabus_id = data.get('syllabus_id')
    topic = data.get('topic')
    status = data.get('status')
    notes = data.get('notes', '')
    user_id = session.get('user_id', 'anonymous')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if progress entry exists
        cursor.execute(
            "SELECT id FROM progress WHERE user_id = ? AND syllabus_id = ? AND topic = ?",
            (user_id, syllabus_id, topic)
        )
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute(
                "UPDATE progress SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, notes, existing['id'])
            )
        else:
            cursor.execute(
                "INSERT INTO progress (user_id, syllabus_id, topic, status, notes) VALUES (?, ?, ?, ?, ?)",
                (user_id, syllabus_id, topic, status, notes)
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500