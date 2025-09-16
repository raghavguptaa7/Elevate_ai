from flask import render_template, request, jsonify, session, abort
from . import career_bp
import json
import re
import os  # <-- IMPORT THIS MODULE
from services.groq_client import GroqClient
from utils.db_utils import get_db_connection, query_db, insert_db, update_db
from utils.validators import sanitize_text, validate_email
from utils.logger import log_info, log_error, log_api_request
from utils.file_handlers import save_uploaded_file, extract_text_from_file
from utils.config import get_config

# Get configuration
config = get_config()

# Initialize Groq client
groq_client = GroqClient()

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

# Resume Analysis and Job Fit Routes
@career_bp.route('/resume', methods=['GET'])
def resume_page():
    return render_template('resume.html')

@career_bp.route('/resume/analyze', methods=['POST'])
def analyze_resume():
    log_api_request(request, 'resume_analyze', 200)
    
    data = request.form
    job_description = sanitize_text(data.get('job_description', ''))
    user_id = session.get('user_id', 'anonymous')
    
    resume_text = ""
    saved_filename = "N/A" # Initialize filename
    
    # 1. Prioritize file upload
    resume_file = request.files.get('resume_file')
    if resume_file and resume_file.filename:
        success, result = save_uploaded_file(resume_file, 'resume')

        if success:
            file_path = result
            # --- START FIX: Get the filename from the full path ---
            saved_filename = os.path.basename(file_path)
            # --- END FIX ---
            try:
                extracted_text = extract_text_from_file(file_path)
                if "Error" in extracted_text:
                    log_error(f"Text extraction failed for {file_path}: {extracted_text}")
                    return jsonify({"error": extracted_text}), 400
                
                if extracted_text:
                    resume_text = sanitize_text(extracted_text)

            except Exception as e:
                log_error(f"Critical error processing uploaded resume file: {str(e)}")
                return jsonify({"error": f"Error processing file: {str(e)}"}), 500
        else:
            error_message = result
            log_error(f"File upload failed: {error_message}")
            return jsonify({"error": error_message}), 400
    
    # 2. If no text came from file, fall back to the text area
    if not resume_text:
        resume_text = sanitize_text(data.get('resume_text', ''))
        saved_filename = "text_input" # Set a placeholder if it was text

    # 3. NOW, perform validation on the final values
    if not resume_text or not job_description:
        log_error("Missing required fields: No resume text (from file or text area) or no job description.")
        return jsonify({"error": "A resume (either as text or a file) and a job description are required"}), 400
    
    # Call Groq API for resume analysis
    prompt = f"""You are a Resume Analyzer Agent. Analyze the following resume for quality, structure, and content.
    Then compare it with the job description to evaluate fit.
    
    Resume:
    {resume_text}
    
    Job Description:
    {job_description}
    
    Provide a detailed analysis including:
    1. Resume Quality (structure, formatting, clarity)
    2. Content Evaluation (skills, experience, education)
    3. Job Fit Analysis (match percentage, key strengths, gaps)
    4. Improvement Suggestions
    
    Format your response as JSON with the following structure:
    {{"quality_score": 0-10, "content_score": 0-10, "job_fit_score": 0-10, "match_percentage": 0-100, "strengths": [list], "gaps": [list], "suggestions": [list]}}
    """
    
    try:
        log_info(f"Analyzing resume for user {user_id}")
        analysis_result_raw = groq_client.generate_response(prompt)
        
        analysis_result_json_string = extract_json_from_response(analysis_result_raw, log_error)
        if not analysis_result_json_string:
            return jsonify({"error": "Failed to extract JSON from AI response", "raw_response": analysis_result_raw}), 500

        # --- START FINAL FIX: Parse the JSON and map to ALL schema columns ---
        try:
            # Parse the JSON string into a Python dict FIRST
            result_json = json.loads(analysis_result_json_string)
        except json.JSONDecodeError:
            log_error(f"Failed to parse extracted JSON from AI: {analysis_result_json_string[:200]}")
            return jsonify({
                "error": "Invalid JSON response from AI after extraction",
                "raw_response": analysis_result_raw
            })

        # Build the data dictionary to match the database schema exactly
        resume_data = {
            "user_id": user_id,
            "filename": saved_filename,
            "content": resume_text,
            "job_description": job_description,
            "analysis": analysis_result_json_string,  # Store the full JSON blob in the 'analysis' column
            "match_score": result_json.get('match_percentage'), # Map AI key to DB column
            "strengths": json.dumps(result_json.get('strengths', [])), # Store lists as JSON strings
            "gaps": json.dumps(result_json.get('gaps', [])),
            "suggestions": json.dumps(result_json.get('suggestions', []))
        }
        
        # This insert will now work
        resume_id = insert_db("resumes", resume_data)
        
        # Return the original JSON object to the frontend
        return jsonify(result_json)
        # --- END FINAL FIX ---
    
    except Exception as e:
        log_error(f"Resume analysis failed: {e}")
        return jsonify({"error": str(e)}), 500

# Mock Interview Routes
@career_bp.route('/interview', methods=['GET'])
def interview_page():
    return render_template('interview.html')

@career_bp.route('/interview/start', methods=['POST'])
def start_interview():
    log_api_request(request, 'interview_start', 200)
    
    data = request.form
    job_title = sanitize_text(data.get('job_title', ''))
    experience_level = sanitize_text(data.get('experience_level', 'mid'))
    user_id = session.get('user_id', 'anonymous')
    
    if not job_title:
        log_error("Missing job title for interview")
        return jsonify({"error": "Job title is required"}), 400
    
    prompt = f"""You are a Mock Interviewer Agent for a {job_title} position at {experience_level} level.
    Generate 5 relevant technical and behavioral questions that would be asked in a real interview.
    
    Format your response as JSON with the following structure:
    {{"questions": [{{"id": 1, "question": "question text", "type": "technical|behavioral"}}]}}
    """
    
    try:
        log_info(f"Starting mock interview for {job_title} position at {experience_level} level for user {user_id}")
        questions_result_raw = groq_client.generate_response(prompt)
        
        questions_result = extract_json_from_response(questions_result_raw, log_error)
        if not questions_result:
            return jsonify({"error": "Failed to extract JSON from AI response", "raw_response": questions_result_raw}), 500

        try:
            questions_json = json.loads(questions_result)
            
            interview_data = {
                "user_id": user_id,
                "job_role": job_title,
                "questions": questions_result,
                "answers": '{}'
            }
            interview_id = insert_db("interviews", interview_data)
            
            log_info(f"Created interview ID {interview_id} with {len(questions_json.get('questions', []))} questions")
            return jsonify({"interview_id": interview_id, "questions": questions_json["questions"]})
        
        except json.JSONDecodeError as e:
            log_error(f"Invalid JSON response from AI for interview questions (post-extraction): {str(e)}")
            return jsonify({"error": "Invalid JSON response from AI", "raw_response": questions_result_raw}), 500
    
    except Exception as e:
        log_error(f"Error generating interview questions: {str(e)}")
        return jsonify({"error": str(e)}), 500

@career_bp.route('/interview/answer', methods=['POST'])
def submit_answer():
    log_api_request(request, 'interview_answer', 200)
    
    data = request.json
    interview_id = data.get('interview_id')
    question_id = data.get('question_id')
    answer_text = sanitize_text(data.get('answer', ''))
    
    if not interview_id or not question_id or not answer_text:
        log_error(f"Missing required fields for interview answer. Interview: {interview_id}, Q: {question_id}")
        return jsonify({"error": "Interview ID, question ID, and answer are required"}), 400
    
    try:
        result = query_db(
            "SELECT answers FROM interviews WHERE id = ?", 
            (interview_id,), 
            one=True
        )
        
        if not result:
            log_error(f"Interview not found with ID {interview_id}")
            return jsonify({"error": "Interview not found"}), 404
        
        try:
            answers = json.loads(result['answers']) if result['answers'] and result['answers'] != '{}' else {}
        except json.JSONDecodeError:
            answers = {}
        
        answers[str(question_id)] = answer_text
        
        # Proactive Fix: Using update_db correctly based on the utils file provided
        update_data = {"answers": json.dumps(answers)}
        condition_str = f"id = {int(interview_id)}" # Simple sanitation, assumes ID is int
        update_db("interviews", update_data, condition_str)
        
        log_info(f"Saved answer for question {question_id} in interview {interview_id}")
        return jsonify({"success": True})
    
    except Exception as e:
        log_error(f"Error saving interview answer: {str(e)}")
        return jsonify({"error": str(e)}), 500


@career_bp.route('/interview/feedback', methods=['POST'])
def get_feedback():
    log_api_request(request, 'interview_feedback', 200)
    
    data = request.form
    interview_id = data.get('interview_id')
    
    if not interview_id:
        log_error("Missing interview ID for feedback")
        return jsonify({"error": "Interview ID is required"}), 400
    
    try:
        result = query_db(
            f"SELECT job_role, questions, answers FROM interviews WHERE id = ?", 
            (interview_id,),
            one=True
        )
        
        if not result:
            log_error(f"Interview not found with ID {interview_id}")
            return jsonify({"error": "Interview not found"}), 404
        
        job_role = result['job_role']
        questions = json.loads(result['questions'])
        answers = json.loads(result['answers'])
        
        qa_pairs = []
        for q in questions['questions']:
            q_id = str(q['id'])
            if q_id in answers:
                qa_pairs.append({
                    "question": q['question'],
                    "answer": answers[q_id],
                    "type": q['type']
                })
        
        if not qa_pairs:
            log_error(f"No answers found for interview {interview_id}")
            return jsonify({"error": "No answers found for this interview"}), 400
        
        log_info(f"Generating feedback for interview {interview_id} with {len(qa_pairs)} answered questions")
        
        prompt = f"""You are a Feedback Agent for a {job_role} interview.
        Analyze the following question-answer pairs from a mock interview and provide detailed feedback.
        
        Interview for: {job_role}
        
        {json.dumps(qa_pairs, indent=2)}
        
        Provide a detailed feedback including:
        1. Overall impression
        2. Strengths in the answers
        3. Areas for improvement
        4. Specific suggestions for each answer
        5. Overall score (0-100)
        
        Format your response as JSON with the following structure:
        {{"overall_impression": "text", "overall_score": 0-100, "strengths": [list], "improvements": [list], "detailed_feedback": [{{"question_id": 1, "feedback": "text", "score": 0-10}}]}}
        """
        
        feedback_result_raw = groq_client.generate_response(prompt)
        
        feedback_result = extract_json_from_response(feedback_result_raw, log_error)
        if not feedback_result:
            return jsonify({"error": "Failed to extract JSON from AI response", "raw_response": feedback_result_raw}), 500

        # Proactive Fix: Using update_db correctly
        feedback_data = {"feedback": feedback_result}
        condition_str = f"id = {int(interview_id)}"
        update_db("interviews", feedback_data, condition_str)
        
        try:
            feedback_json = json.loads(feedback_result)
            log_info(f"Interview feedback completed with overall score {feedback_json.get('overall_score', 'N/A')}")
            return jsonify({"interview_id": interview_id, "feedback": feedback_json})
        except json.JSONDecodeError as e:
            log_error(f"Invalid JSON response from AI for interview feedback (post-extraction): {str(e)}")
            return jsonify({"error": "Invalid JSON response from AI", "raw_response": feedback_result_raw}), 500
    
    except Exception as e:
        log_error(f"Error generating interview feedback: {str(e)}")
        return jsonify({"error": str(e)}), 500