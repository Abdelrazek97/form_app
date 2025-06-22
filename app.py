from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this in production!
DATABASE = 'academic.db'

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
def init_db():
    conn = get_db_connection()
    
    # Create users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            full_name TEXT
        )
    ''')
    
    # Update academic_data table to include user_id
    conn.execute('''
        CREATE TABLE IF NOT EXISTS academic_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            semester TEXT NOT NULL,
            course_code TEXT NOT NULL,
            num_students INTEGER,
            teaching_load TEXT,
            course_name TEXT,
            theoretical_hours INTEGER,
            practical_hours INTEGER,
            credit_hours INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS activity_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_title TEXT,
            activity_date TEXT,
            duration TEXT,
            participation_type TEXT,
            place TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create admin user if not exists
    admin_exists = conn.execute('SELECT 1 FROM users WHERE username = ?', ('admin',)).fetchone()
    if not admin_exists:
        conn.execute(
            'INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)',
            ('admin', generate_password_hash('admin123'), 'admin', 'Administrator')
        )
    
    conn.commit()
    conn.close()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('view_data'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Login successful!', 'success')
            return redirect(url_for('view_data'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        
        if not username or not password:
            flash('Username and password are required', 'danger')
        else:
            conn = get_db_connection()
            try:
                conn.execute(
                    'INSERT INTO users (username, password, full_name) VALUES (?, ?, ?)',
                    (username, generate_password_hash(password), full_name)
                )
                conn.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Username already exists', 'danger')
            finally:
                conn.close()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/semester_add', methods=['GET', 'POST'])
@login_required
def semester_data():
    if request.method == 'POST':
        # Get form data
        data = {
            'user_id': session['user_id'],
            'semester': request.form['semester'],
            'course_code': request.form['course_code'],
            'num_students': int(request.form['num_students']) if request.form['num_students'] else None,
            'teaching_load': request.form['teaching_load'],
            'course_name': request.form['course_name'],
            'semester_type': request.form['semester_type'] ,
            'credit_hours': int(request.form['credit_hours']) if request.form['credit_hours'] else None,
            
        }

        # Insert into database
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO academic_data (
                user_id, semester, course_code, num_students, teaching_load,
                course_name, semester_type, credit_hours
                
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ? )
        ''', tuple(data.values()))
        conn.commit()
        conn.close()

        flash('Data added successfully!', 'success')
        return redirect(url_for('view_data'))

    return render_template('add_semester.html')



@app.route('/Scientific_production', methods=['GET', 'POST'])
@login_required
def Scientific_production_data():
    if request.method == 'POST':
        # Get form data
        data = {
            'user_id': session['user_id'],
            'Scientific_research': request.form['Scientific_research'],
            'supervision_Graduation': request.form['supervision_Graduation'],
        }

        # Insert into database
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO Scientific_production (
                user_id, Scientific_research, supervision_Graduation
            ) VALUES (?, ?, ?)
        ''', tuple(data.values()))
        conn.commit()
        conn.close()

        flash('Data added successfully!', 'success')
        return redirect(url_for('view_data'))

    return render_template('Scientific_production.html')

@app.route('/cirteria_add', methods=['GET', 'POST'])
@login_required
def cirteria_data():
    if request.method == 'POST':
        # Get form data
        data = {
            'user_id': session['user_id'],
            'Develop_courses': request.form['Develop_courses'],
            'Prepare_file': request.form['Prepare_file'],
            'Electronic_tests': request.form['Electronic_tests'],
            'Prepare_material_content': request.form['Prepare_material_content'],
            'Use_learning_effectively': request.form['Use_learning_effectively'],
            'teaching_methods': request.form['teaching_methods'],
            'Methods_student': request.form['Methods_student'],
            'preparing_test_questions': request.form['preparing_test_questions'],
            'Provide_academic_guidance': request.form['Provide_academic_guidance']
        }

        # Insert into database
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO Evaluation_aspects (
                user_id, Develop_courses, Prepare_file, Electronic_tests,
                 Prepare_material_content, Use_learning_effectively,teaching_methods,
                 Methods_student,preparing_test_questions,Provide_academic_guidance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', tuple(data.values()))
        conn.commit()
        conn.close()

        flash('Data added successfully!', 'success')
        return redirect(url_for('view_data'))

    return render_template('criteria_of_evaluation.html')



@app.route('/prticipation_add', methods=['GET', 'POST'])
@login_required
def prticipation_data():
    if request.method == 'POST':
        # Get form data
        data = {
            'user_id': session['user_id'],
            'activity_title': request.form['activity_title'],
            'activity_date': request.form['date'],
            'duration': request.form['duration'],
            'participation_type': request.form['participation_type'],
            'place': request.form['place']
        }

        # Insert into database
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO activity_data (
                user_id, activity_title, activity_date, duration, participation_type, place
            ) VALUES (?, ?, ?, ?, ?, ? )
        ''', tuple(data.values()))
        conn.commit()
        conn.close()

        flash('Data added successfully!', 'success')
        return redirect(url_for('view_data'))

    return render_template('Participation_in_conferences.html')


@app.route('/activity_add', methods=['GET', 'POST'])
@login_required
def activity_data():
    if request.method == 'POST':
        # Get form data
        data = {
            'user_id': session['user_id'],
            'activity_title': request.form['activity_title'],
            'activity_date': request.form['date'],
            'duration': request.form['duration'],
            'participation_type': request.form['participation_type'],
            'place': request.form['place']
        }

        # Insert into database
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO activity_data (
                user_id, activity_title, activity_date, duration, participation_type, place
            ) VALUES (?, ?, ?, ?, ?, ? )
        ''', tuple(data.values()))
        conn.commit()
        conn.close()

        flash('Data added successfully!', 'success')
        return redirect(url_for('view_data'))

    return render_template('add_activity.html')



@app.route('/program_add', methods=['GET', 'POST'])
@login_required
def program_data():
    if request.method == 'POST':
        # Get form data
        data = {
            'user_id': session['user_id'],
            'scientific_output': request.form['scientific_output'],
            'Authors_names': request.form['Authors_names'],
            'Publisher': request.form['Publisher'],
            'Agency': request.form['Agency'],
            'year': request.form['year'],
            'research_type': request.form['research_type']
        }

        # Insert into database
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO Scientific_research (
                user_id, scientific_output, Authors_names, Publisher, Agency,
                year, research_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', tuple(data.values()))
        conn.commit()
        conn.close()

        flash('Data added successfully!', 'success')
        return redirect(url_for('view_data'))

    return render_template('add_program.html')

@app.route('/view')
@login_required
def view_data():
    conn = get_db_connection()
    
    if session.get('role') == 'admin':
        # Admin can see all data
        semseters = conn.execute('''
            SELECT academic_data.*, users.username, users.full_name 
            FROM academic_data 
            JOIN users ON academic_data.user_id = users.id
            ORDER BY academic_data.created_at DESC
        ''').fetchall()
        activity = conn.execute('''
            SELECT activity_data.*, users.username, users.full_name 
            FROM activity_data 
            JOIN users ON activity_data.user_id = users.id
            ORDER BY activity_data.created_at DESC
        ''').fetchall()
        
    else:
        # Regular users can only see their own data
        semseters = conn.execute('''
            SELECT academic_data.*, users.username, users.full_name 
            FROM academic_data 
            JOIN users ON academic_data.user_id = users.id
            WHERE academic_data.user_id = ?
            ORDER BY academic_data.created_at DESC
        ''', (session['user_id'],)).fetchall()

        activity = conn.execute('''
            SELECT activity_data.*, users.username, users.full_name 
            FROM activity_data 
            JOIN users ON activity_data.user_id = users.id
            WHERE activity_data.user_id = ?
            ORDER BY activity_data.created_at DESC
        ''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('view_data/view_semester.html', semseters=semseters,activity=activity)


@app.route('/view/Scientific_production')
@login_required
@admin_required
def view_Scientific_production():
    conn = get_db_connection()
    
    # Admin can see all data
    Scientific_production = conn.execute('''
        SELECT Scientific_production.*, users.username, users.full_name 
        FROM Scientific_production 
        JOIN users ON Scientific_production.user_id = users.id
        ORDER BY Scientific_production.created_at DESC
    ''').fetchall()

    conn.close()
    return render_template('view_data/view_Scientific_production.html', Scientific_production=Scientific_production)
 
@app.route('/view/criteria_of_evaluation')
@login_required
@admin_required
def view_criteria_of_evaluation():
    conn = get_db_connection()
    
    # Admin can see all data
    Evaluation_aspects = conn.execute('''
        SELECT Evaluation_aspects.*, users.username, users.full_name 
        FROM Evaluation_aspects 
        JOIN users ON Evaluation_aspects.user_id = users.id
        ORDER BY Evaluation_aspects.created_at DESC
    ''').fetchall()

    activity = conn.execute('''
        SELECT activity_data.*, users.username, users.full_name 
        FROM activity_data 
        JOIN users ON activity_data.user_id = users.id
        ORDER BY activity_data.created_at DESC
    ''').fetchall()
        
    # else:
    #     # Regular users can only see their own data
    #     semseters = conn.execute('''
    #         SELECT academic_data.*, users.username, users.full_name 
    #         FROM academic_data 
    #         JOIN users ON academic_data.user_id = users.id
    #         WHERE academic_data.user_id = ?
    #         ORDER BY academic_data.created_at DESC
    #     ''', (session['user_id'],)).fetchall()

    #     activity = conn.execute('''
    #         SELECT activity_data.*, users.username, users.full_name 
    #         FROM activity_data 
    #         JOIN users ON activity_data.user_id = users.id
    #         WHERE activity_data.user_id = ?
    #         ORDER BY activity_data.created_at DESC
    #     ''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('view_data/view_criteria.html', Evaluation_aspects=Evaluation_aspects,activity=activity)


@app.route('/kpis')
@login_required
def view_kpis():
    conn = get_db_connection()
    
    if session.get('role') == 'admin':
        # Admin can see all data
        academic_kpi = conn.execute(''' 
        SELECT COUNT(*)
        FROM academic_data
        ''').fetchone()
        activity_kpi = conn.execute(''' 
        SELECT COUNT(*)
        FROM  activity_data
        ''').fetchone()
        return render_template('view_kpis.html', academic_kpi=academic_kpi[0],activity_kpi=activity_kpi[0])

        
    conn.close()
    return render_template('view_data.html', semseters=semseters,activity=activity)

@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    if session.get('role') == 'admin':
        if request.method == 'POST':
            # Get form data
            Scientific_research_Evaluation = request.form['Scientific_research_Evaluation']
            supervision_Graduation_Evaluation = request.form['supervision_Graduation_Evaluation']
            data = {
                'supervision_Graduation_Evaluation' : request.form['supervision_Graduation_Evaluation'],
                'user_id' : id
            }
            # Insert into database
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()

            update_query = " UPDATE Scientific_production SET Scientific_research_Evaluation == ?, supervision_Graduation_Evaluation == ? WHERE Scientific_production.user_id == ? "
            cursor.execute(update_query, (Scientific_research_Evaluation,supervision_Graduation_Evaluation,id))
            conn.commit()
            conn.close()
            flash('Data added successfully!', 'success')
            return redirect(url_for('view_Scientific_production'))

        conn = get_db_connection()

        # Admin can see all data
        Scientific_production = conn.execute('''
            SELECT Scientific_production.*, users.username, users.full_name 
            FROM Scientific_production 
            JOIN users ON Scientific_production.user_id = users.id
            WHERE Scientific_production.user_id = ?
            ORDER BY Scientific_production.created_at DESC
        ''',(id,)).fetchone()
        conn.close()

        return render_template('admin/update.html',id=id, Scientific_production=Scientific_production)
    else:
        return render_template('page-404.html')


@app.route('/update/criteria/<int:id>', methods=['GET', 'POST'])
@login_required
def update_criteria(id):
    if session.get('role') == 'admin':
        if request.method == 'POST':
            # Get form data 
            Develop_courses_Evaluation = request.form['Develop_courses_Evaluation']
            Prepare_file_Evaluation = request.form['Prepare_file_Evaluation']
            Electronic_tests_Evaluation = request.form['Electronic_tests_Evaluation']
            Prepare_material_Evaluation = request.form['Prepare_material_Evaluation']
            Use_learning__Evaluation = request.form['Use_learning_Evaluation']
            teaching_methods_Evaluation = request.form['teaching_methods_Evaluation']
            Methods_student_Evaluation = request.form['Methods_student_Evaluation']
            preparing_test_Evaluation = request.form['preparing_test_Evaluation']
            Provide_academic_Evaluation = request.form['Provide_academic_Evaluation']
        
            # Insert into database
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()

            update_query = ''' UPDATE Evaluation_aspects SET Develop_courses_Evaluation == ?,
            Prepare_file_Evaluation == ?, Electronic_tests_Evaluation == ? ,
            Prepare_material_Evaluation == ?, Use_learning_Evaluation == ?,
            teaching_methods_Evaluation == ?, Methods_student_Evaluation == ?,
            preparing_test_Evaluation == ?, Provide_academic_Evaluation == ?
            WHERE Evaluation_aspects.user_id == ? '''

            cursor.execute(update_query, (Develop_courses_Evaluation,Prepare_file_Evaluation,
            Electronic_tests_Evaluation,Prepare_material_Evaluation,
            Use_learning__Evaluation,teaching_methods_Evaluation,
            Methods_student_Evaluation,preparing_test_Evaluation,Provide_academic_Evaluation,id))
            conn.commit()
            conn.close()
            flash('Data added successfully!', 'success')
            return redirect(url_for('view_data'))

        conn = get_db_connection()

        # Admin can see all data
        Evaluation_aspects = conn.execute('''
            SELECT Evaluation_aspects.*, users.username, users.full_name 
            FROM Evaluation_aspects 
            JOIN users ON Evaluation_aspects.user_id = users.id
            WHERE Evaluation_aspects.user_id = ?
            ORDER BY Evaluation_aspects.created_at DESC
        ''',(id,)).fetchone()
        conn.close()

        return render_template('admin/criteria_of_evaluation.html',id=id, Evaluation_aspects=Evaluation_aspects)
    else:
        return render_template('page-404.html')










if __name__ == '__main__':
    init_db()
    app.run(debug=True)