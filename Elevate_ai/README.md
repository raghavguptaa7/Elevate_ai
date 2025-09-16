# Elevate.AI

Elevate.AI is a multi-agent, AI-powered system that guides users in their career readiness and academic learning journey. The platform leverages the Groq API to provide intelligent assistance through specialized agents.

## Project Overview

Elevate.AI consists of two major modules:

### Career Readiness Coach

- **Resume Analyzer Agent**: Evaluates resume quality for a given job description
- **Job Fit Agent**: Compares resume with job role & provides alignment suggestions
- **Mock Interviewer Agent**: Conducts role-specific mock interviews (Q&A)
- **Feedback Agent**: Analyzes user answers & gives structured feedback

### Smart Study Coach

- **Syllabus Agent**: Parses uploaded syllabus/subject list
- **Weak Topic Detector Agent**: Identifies user's weak areas from quiz performance
- **Quiz Generator Agent**: Creates adaptive quizzes from syllabus
- **Planner Agent**: Generates personalized study plans (daily/weekly)
- **Progress Memory Agent**: Tracks learning history & adjusts future recommendations

## Tech Stack

- **Backend**: Python Flask
- **AI Models**: Groq API (LLM-based agents)
- **Frontend**: HTML + CSS (with JavaScript for interactivity)
- **Database**: SQLite for storing resumes, quiz results, study progress

## Project Structure

```
Elevate_ai/
├── app.py                  # Main application entry point
├── run.py                  # Application runner script
├── init_db.py              # Database initialization script
├── blueprints/             # Flask blueprints for different modules
│   ├── career/             # Career Readiness Coach module
│   │   ├── __init__.py
│   │   └── routes.py       # Career-related routes
│   └── study/              # Smart Study Coach module
│       ├── __init__.py
│       └── routes.py       # Study-related routes
├── services/               # Service modules
│   └── groq_client.py      # Groq API wrapper
├── utils/                  # Utility modules
│   ├── __init__.py         # Package initialization
│   ├── config.py           # Configuration management
│   ├── db_utils.py         # Database utilities
│   ├── error_handlers.py   # Error handling utilities
│   ├── file_handlers.py    # File upload and processing
│   ├── logger.py           # Logging utilities
│   └── validators.py       # Input validation utilities
├── templates/              # HTML templates
│   ├── base.html           # Base template with common elements
│   ├── error.html          # Error page template
│   ├── index.html          # Homepage
│   ├── resume.html         # Resume analysis page
│   ├── interview.html      # Mock interview page
│   ├── syllabus.html       # Syllabus upload page
│   ├── quiz.html           # Quiz page
│   ├── plan.html           # Study plan page
│   └── progress.html       # Progress tracking page
├── static/                 # Static assets
│   ├── css/
│   │   └── styles.css      # Main stylesheet
│   ├── js/
│   │   └── main.js         # Main JavaScript file
│   └── images/             # Image assets
├── database/               # Database directory
│   └── database.db         # SQLite database
├── requirements.txt        # Project dependencies
├── setup.sh               # Setup script for Unix/macOS
├── setup.bat              # Setup script for Windows
├── Procfile               # Heroku deployment configuration
├── DEPLOYMENT.md          # Detailed deployment instructions
└── README.md               # Project documentation
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Groq API key (sign up at [groq.com](https://groq.com))

### Local Development Setup

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/elevate-ai.git
cd elevate-ai
```

2. **Run the setup script**

```bash
# On macOS/Linux
chmod +x setup.sh
./setup.sh

# On Windows
setup.bat
```

This will:
- Create a virtual environment->python -m venv venv   ,  source venv/bin/activate
- Install required dependencies    -> pip install -r requirements.txt
- Set up the database
- Create a .env file (if not exists)

4. **Set up environment variables**

Create a `.env` file in the project root with the following content:

```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
GROQ_API_KEY=your_groq_api_key_here
```

5. **Run the application**

```bash
python run.py
```

The application will be available at `http://127.0.0.1:5000/`.

## Deployment

### Deploying to Render

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Configure the service:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
4. Add environment variables (GROQ_API_KEY, SECRET_KEY)
5. Deploy the service

### Deploying to Heroku

1. Install the Heroku CLI and log in
2. Create a `Procfile` with the content: `web: gunicorn app:app`
3. Add `gunicorn` to requirements.txt
4. Run the following commands:

```bash
heroku create elevate-ai
heroku config:set GROQ_API_KEY=your_groq_api_key_here
heroku config:set SECRET_KEY=your_secret_key_here
git push heroku main
```

### Deploying to Railway

1. Create a new project on Railway
2. Connect your GitHub repository
3. Add environment variables (GROQ_API_KEY, SECRET_KEY)
4. Railway will automatically detect the Python project and deploy it

## Usage

### Career Readiness Coach

1. **Resume Analysis**:
   - Upload your resume and a job description
   - Get a detailed analysis of your resume's match with the job
   - Receive suggestions for improvement

2. **Mock Interview**:
   - Select a job role for the interview
   - Answer a series of role-specific questions
   - Receive detailed feedback on your answers

### Smart Study Coach

1. **Syllabus Upload**:
   - Upload a syllabus or enter subject topics
   - The system will parse and organize the content

2. **Quiz Generation**:
   - Generate quizzes based on the syllabus
   - Take adaptive quizzes that focus on your weak areas

3. **Study Planning**:
   - Get personalized daily/weekly study plans
   - Track your progress over time

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Groq](https://groq.com) for providing the AI API
- [Flask](https://flask.palletsprojects.com/) for the web framework
- All contributors to the project