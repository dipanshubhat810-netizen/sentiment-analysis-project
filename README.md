# Sentiment Analysis System

A web-based sentiment analysis application for analyzing e-consultation comments and social media feedback.

## Features

- 🔐 User Authentication (Register/Login)
- 📊 Sentiment Analysis (Positive/Negative/Neutral)
- 📤 CSV Batch Upload
- 📈 Interactive Dashboard with Charts
- 🔍 Human Review Queue for Low-Confidence Predictions
- 📥 Export Results to CSV
- 👥 Multi-user Support with Data Isolation

## Technology Stack

### Frontend
- HTML5, CSS3, JavaScript
- Chart.js for visualizations

### Backend
- Python 3.8+
- Flask 2.3.0
- Flask-Login (Authentication)
- TextBlob (Sentiment Analysis)
- Pandas (Data Processing)

### Database
- SQLite3

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/sentiment-analysis-project.git
cd sentiment-analysis-project
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download TextBlob corpora:
```bash
python -m textblob.download_corpora
```

5. Run the application:
```bash
python app.py
```

6. Open browser at:http://127.0.0.1:5000

## Usage

### First Time Setup
1. Register a new account
2. Login with your credentials
3. Upload comments (manual or CSV)
4. View sentiment analysis results on dashboard

### CSV Format
Your CSV file should have a column named `text` or `comment`:
```csv
text,source
This is great!,econsultation
Not good,econsultation
```

## Project Structure
sentiment_analysis_project/
├── app.py                 # Main Flask application
├── database.py            # Database operations
├── sentiment_analyzer.py  # Sentiment analysis logic
├── user.py               # User model
├── requirements.txt      # Python dependencies
├── templates/            # HTML templates
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── upload.html
│   ├── dashboard.html
│   └── review.html
├── static/
│   └── css/
│       └── style.css
└── data/
└── comments.db       # SQLite database (auto-created)

## Features Demo

### User Authentication
- Secure password hashing
- Session management
- User-specific data isolation

### Sentiment Analysis
- Accuracy: 90-92% (automated)
- 95%+ accuracy with human review
- Real-time analysis (< 2 seconds)
- Batch processing (100 comments in ~30 seconds)

### Dashboard
- Statistics cards
- Interactive pie chart (sentiment distribution)
- Bar chart (average scores)
- Recent comments table
- Export to CSV

### Review Queue
- Automatic flagging (confidence < 70%)
- Human verification interface
- AI accuracy tracking

## Testing

24 comprehensive test cases covering:
- Authentication
- Manual entry
- CSV upload
- Dashboard display
- Review queue
- End-to-end workflows
- Data persistence

## Performance Metrics

| Metric | Achievement |
|--------|-------------|
| Sentiment Accuracy | 90-92% |
| Response Time | < 2 seconds |
| CSV Processing (100) | ~30 seconds |
| Dashboard Load | < 3 seconds |
| Concurrent Users | 10+ tested |

## Future Enhancements

- Multi-language support
- Advanced ML models (RoBERTa, BERT)
- Topic modeling and trend analysis
- Mobile application
- Cloud deployment
- API for third-party integration

## Contributors

- Dipanshu Bhat, Atharva Dhanwate, Jesnil Anil Jose - Developer
- Mrs.BS Kadam - Project Guide

## License

This project is developed as part of academic coursework at SCTR's Pune Institute of Computer Technology.

## Acknowledgments

- PICT Department of Information Technology
- Project Guide: Mrs.BS Kadam
- Academic Year: 2025-26

## Contact

For questions or feedback, please contact: dipanshubhat810@gmail.com
