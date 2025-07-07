from flask import Flask, render_template, request, redirect, url_for, flash, abort
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database setup
def get_db_connection():
    conn = sqlite3.connect('questions.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT NOT NULL,
            topic TEXT NOT NULL,
            main_slo TEXT NOT NULL,
            enabling_slos TEXT NOT NULL,
            complexity_level TEXT NOT NULL,
            student_level TEXT NOT NULL,
            options TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return redirect(url_for('add_question'))

@app.route('/add', methods=['GET', 'POST'])
def add_question():
    if request.method == 'POST':
        # Get form data
        topic = request.form['topic'].strip()
        main_slo = request.form['main_slo'].strip()
        enabling_slos = request.form['enabling_slos'].strip()
        complexity = request.form['complexity'].strip()
        student_level = request.form['student_level'].strip()
        question_text = request.form['question_text'].strip()
        options = request.form['options'].strip()
        correct_answer = request.form['correct_answer'].strip().upper()

        # Validate inputs
        if not all([topic, main_slo, complexity, student_level, question_text, options, correct_answer]):
            flash('All fields are required!', 'error')
            return render_template('add_question.html', form_data=request.form)

        # Process options and validate correct answer
        options_list = [opt.strip() for opt in options.split('\n') if opt.strip()]
        if len(options_list) < 2:
            flash('At least two options are required!', 'error')
            return render_template('add_question.html', form_data=request.form)

        valid_answers = [opt[0].upper() for opt in options_list if opt]
        if correct_answer not in valid_answers:
            flash('Correct answer must match one of the option letters!', 'error')
            return render_template('add_question.html', form_data=request.form)

        # Save to database
        try:
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO questions (
                    question_text, topic, main_slo, enabling_slos, 
                    complexity_level, student_level, options, correct_answer
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                question_text, topic, main_slo, enabling_slos, 
                complexity, student_level, options, correct_answer
            ))
            conn.commit()
            conn.close()
            
            flash('Question added successfully!', 'success')
            return redirect(url_for('add_question'))
            
        except Exception as e:
            flash(f'Failed to add question: {str(e)}', 'error')
    
    return render_template('add_question.html')

@app.route('/search', methods=['GET', 'POST'])
def search_questions():
    if request.method == 'POST':
        search_term = request.form.get('search_term', '').strip()
        complexity = request.form.get('complexity', '').strip()

        conn = get_db_connection()
        
        query = '''
            SELECT id, topic, main_slo, complexity_level, substr(question_text, 1, 100) as question_preview
            FROM questions 
            WHERE 1=1
        '''
        params = []
        
        if search_term:
            query += " AND (question_text LIKE ? OR topic LIKE ? OR main_slo LIKE ?)"
            params.extend([f"%{search_term}%"] * 3)
        
        if complexity:
            query += " AND complexity_level = ?"
            params.append(complexity)
        
        query += " ORDER BY id DESC"
        
        questions = conn.execute(query, params).fetchall()
        conn.close()
        
        return render_template('search.html', questions=questions, search_term=search_term, complexity=complexity)
    
    return render_template('search.html')

@app.route('/view_all')
def view_all():
    conn = get_db_connection()
    questions = conn.execute('''
        SELECT id, topic, main_slo, complexity_level, student_level, 
               strftime('%Y-%m-%d', created_at) as created_at
        FROM questions 
        ORDER BY id DESC
    ''').fetchall()
    conn.close()
    return render_template('view_all.html', questions=questions)

@app.route('/question/<int:question_id>')
def question_detail(question_id):
    conn = get_db_connection()
    question = conn.execute('''
        SELECT *
        FROM questions 
        WHERE id = ?
    ''', (question_id,)).fetchone()
    conn.close()
    
    if question is None:
        abort(404)
    
    return render_template('question_detail.html', question=question)

@app.route('/edit/<int:question_id>', methods=['GET', 'POST'])
def edit_question(question_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        # Get form data
        topic = request.form['topic'].strip()
        main_slo = request.form['main_slo'].strip()
        enabling_slos = request.form['enabling_slos'].strip()
        complexity = request.form['complexity'].strip()
        student_level = request.form['student_level'].strip()
        question_text = request.form['question_text'].strip()
        options = request.form['options'].strip()
        correct_answer = request.form['correct_answer'].strip().upper()

        # Validate inputs
        if not all([topic, main_slo, complexity, student_level, question_text, options, correct_answer]):
            flash('All fields are required!', 'error')
            conn.close()
            return render_template('edit_question.html', question=request.form)

        # Process options and validate correct answer
        options_list = [opt.strip() for opt in options.split('\n') if opt.strip()]
        if len(options_list) < 2:
            flash('At least two options are required!', 'error')
            conn.close()
            return render_template('edit_question.html', question=request.form)

        valid_answers = [opt[0].upper() for opt in options_list if opt]
        if correct_answer not in valid_answers:
            flash('Correct answer must match one of the option letters!', 'error')
            conn.close()
            return render_template('edit_question.html', question=request.form)

        # Update database
        try:
            conn.execute('''
                UPDATE questions SET
                    question_text = ?,
                    topic = ?,
                    main_slo = ?,
                    enabling_slos = ?,
                    complexity_level = ?,
                    student_level = ?,
                    options = ?,
                    correct_answer = ?
                WHERE id = ?
            ''', (
                question_text, topic, main_slo, enabling_slos, 
                complexity, student_level, options, correct_answer,
                question_id
            ))
            conn.commit()
            conn.close()
            
            flash('Question updated successfully!', 'success')
            return redirect(url_for('question_detail', question_id=question_id))
            
        except Exception as e:
            flash(f'Failed to update question: {str(e)}', 'error')
            conn.close()
    
    # GET request - load existing question
    question = conn.execute('''
        SELECT *
        FROM questions 
        WHERE id = ?
    ''', (question_id,)).fetchone()
    conn.close()
    
    if question is None:
        abort(404)
    
    return render_template('edit_question.html', question=question)

@app.route('/delete/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM questions WHERE id = ?', (question_id,))
    conn.commit()
    conn.close()
    
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('view_all'))

if __name__ == '__main__':
    app.run(debug=True)