from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import pandas as pd
from sentiment_analyzer import SentimentAnalyzer
from database import Database
from user import User

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'  # Change this in production

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Initialize components
db = Database()
analyzer = SentimentAnalyzer()


@login_manager.user_loader
def load_user(user_id):
    user_data = db.get_user_by_id(int(user_id))
    if user_data:
        return User(user_data['id'], user_data['username'], user_data.get('email'))
    return None


# ===== AUTHENTICATION ROUTES =====

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')

        if not username or not password:
            flash('Username and password are required!', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return render_template('register.html')

        user_id = db.create_user(username, password, email)

        if user_id:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username already exists! Please choose another.', 'error')
            return render_template('register.html')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        user_data = db.verify_password(username, password)

        if user_data:
            user = User(user_data['id'], user_data['username'], user_data.get('email'))
            login_user(user, remember=remember)

            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'error')
            return render_template('login.html')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('login'))


# ===== PROTECTED ROUTES =====

@app.route('/')
@login_required
def index():
    """Home page"""
    return render_template('index.html', username=current_user.username)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Handle file uploads and manual entry"""
    if request.method == 'POST':
        try:
            # CSV upload
            if 'file' in request.files and request.files['file'].filename:
                file = request.files['file']
                df = pd.read_csv(file)

                text_column = None
                for col in ['text', 'comment', 'comments', 'Comment', 'Text']:
                    if col in df.columns:
                        text_column = col
                        break

                if not text_column:
                    return jsonify({
                        'error': 'CSV must have a column named "text" or "comment"'
                    }), 400

                processed = 0

                for _, row in df.iterrows():
                    text = str(row[text_column]).strip()

                    if not text or text.lower() == 'nan':
                        continue

                    comment_id = db.add_comment(text, current_user.id, source='csv_upload')

                    result = analyzer.analyze_with_confidence_check(text)

                    db.add_sentiment_result(
                        comment_id,
                        result['sentiment'],
                        result['positive_score'],
                        result['negative_score'],
                        result['neutral_score']
                    )

                    if result.get('needs_review', False):
                        db.add_to_review_queue(
                            comment_id,
                            current_user.id,
                            text,
                            result['sentiment'],
                            result['confidence']
                        )

                    processed += 1

                    if processed % 50 == 0:
                        print(f"Processed {processed} comments...")

                return jsonify({
                    'success': True,
                    'message': f'Successfully processed {processed} comments!'
                })

            # Manual entry
            elif 'text' in request.form:
                text = request.form.get('text', '').strip()

                if not text:
                    return jsonify({'error': 'Text cannot be empty'}), 400

                comment_id = db.add_comment(text, current_user.id, source='manual')

                result = analyzer.analyze_with_confidence_check(text)

                db.add_sentiment_result(
                    comment_id,
                    result['sentiment'],
                    result['positive_score'],
                    result['negative_score'],
                    result['neutral_score']
                )

                if result.get('needs_review', False):
                    db.add_to_review_queue(
                        comment_id,
                        current_user.id,
                        text,
                        result['sentiment'],
                        result['confidence']
                    )

                return jsonify({'success': True, 'result': result})

            else:
                return jsonify({'error': 'No data provided'}), 400

        except Exception as e:
            print(f"Error: {e}")
            return jsonify({'error': str(e)}), 500

    return render_template('upload.html', username=current_user.username)


@app.route('/dashboard')
@login_required
def dashboard():
    """Display sentiment analysis dashboard for current user"""
    results = db.get_all_results(current_user.id)
    stats = db.get_statistics(current_user.id)

    return render_template(
        'dashboard.html',
        results=results,
        stats=stats,
        username=current_user.username
    )


@app.route('/api/analyze', methods=['POST'])
@login_required
def api_analyze():
    """API endpoint for sentiment analysis"""
    data = request.get_json()

    if not data or 'text' not in data:
        return jsonify({'error': 'Missing text field'}), 400

    result = analyzer.analyze(data['text'])
    return jsonify(result)


@app.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for statistics"""
    stats = db.get_statistics(current_user.id)
    return jsonify(stats)


@app.route('/export')
@login_required
def export():
    """Export results as CSV for current user"""
    results = db.get_all_results(current_user.id)
    df = pd.DataFrame(results)
    csv = df.to_csv(index=False)

    return Response(
        csv,
        mimetype="text/csv",
        headers={
            "Content-disposition": f"attachment; filename={current_user.username}_sentiment_results.csv"
        }
    )


if __name__ == '__main__':
    app.run()
