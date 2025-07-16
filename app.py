from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
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
    # create questions tables 
    conn.execute('''
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
        numeric_fields = [
         'Develop_courses', 'Prepare_file', 'Electronic_tests', 
        'Prepare_material_content', 'Use_learning_effectively',
        'teaching_methods', 'Methods_student', 'preparing_test_questions',
        'Provide_academic_guidance'
           ]

        data['aspests_sum'] = sum(int(data[field]) for field in numeric_fields)

        # Insert into database
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO Evaluation_aspects (
                user_id, Develop_courses, Prepare_file, Electronic_tests,
                 Prepare_material_content, Use_learning_effectively,teaching_methods,
                 Methods_student,preparing_test_questions,Provide_academic_guidance,aspests_sum
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', tuple(data.values()))
        conn.commit()
        conn.close()

        flash('Data added successfully!', 'success')
        return redirect(url_for('view_data'))

    return render_template('criteria_of_evaluation.html')


@app.route('/university_evaluation', methods=['GET', 'POST'])
@login_required
def university_evaluation():
    if request.method == 'POST':
        # Get form data
        data = {
            'user_id': session['user_id'],
            'department_load': request.form['department_load'],
            'workshop_develop': request.form['workshop_develop'],
            'program_bank': request.form['program_bank'],
            'medical_services': request.form['medical_services']
        }
        numeric_fields = [
         'department_load', 'workshop_develop', 'program_bank', 
        'medical_services'
           ]

        data['aspects_sum'] = sum(int(data[field]) for field in numeric_fields)

        # Insert into database
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO university_evaluation (
                user_id, department_load, workshop_develop, program_bank,
                 medical_services,aspects_sum
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', tuple(data.values()))
        conn.commit()
        conn.close()

        flash('Data added successfully!', 'success')
        return redirect(url_for('view_data'))

    return render_template('university_evaluation.html')



@app.route('/prticipation_add', methods=['GET', 'POST'])
@login_required
def prticipation_data():
    if request.method == 'POST':
        # Get form data
        data = {
            'user_id': session['user_id'],
            'location': request.form['location'],
            'type_part': request.form['type_part'],
            'year': request.form['year'],
            'place': request.form['place']
        }

        # Insert into database
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO participate_conference (
                user_id, location, type_part, place, year
            ) VALUES (?, ?, ?, ?, ? )
        ''', tuple(data.values()))
        conn.commit()
        conn.close()

        flash('Data added successfully!', 'success')
        return redirect(url_for('view_data'))

    return render_template('Participation_in_conferences.html')

@app.route('/university', methods=['GET', 'POST'])
@login_required
def University_Service():
    if request.method == 'POST':
        # Get form data
        data = {
            'user_id': session['user_id'],
            'task_level': request.form['task_level'],
            'task_type': request.form['task_type'],
            'notes': request.form['notes'],
        }

        # Insert into database
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO University_Service (
                user_id, task_level, task_type, notes
            ) VALUES (?, ?, ?, ? )
        ''', tuple(data.values()))
        conn.commit()
        conn.close()

        flash('Data added successfully!', 'success')
        return redirect(url_for('view_data'))

    return render_template('University_Service.html')


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
    return render_template('view_data.html', semseters=semseters,activity=activity)


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
    
    # Admin can see all data0
    Evaluation_aspects = conn.execute('''
        SELECT aspests_sum,evaluation_sum,user_id, users.username, users.full_name 
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
        
    conn.close()
    return render_template('view_data/view_criteria.html', Evaluation_aspects=Evaluation_aspects,activity=activity)


@app.route('/view/university_evaluation')
@login_required
@admin_required
def view_university_evaluation():
    conn = get_db_connection()
    
    # Admin can see all data0
    university_evaluation = conn.execute('''
        SELECT aspects_sum,evaluation_sum,user_id, users.username, users.full_name 
        FROM university_evaluation 
        JOIN users ON university_evaluation.user_id = users.id
        ORDER BY university_evaluation.created_at DESC
    ''').fetchall()
    conn.close()
    return render_template('view_data/view_university.html', university_evaluation=university_evaluation)


@app.route('/update/university/<int:id>', methods=['GET', 'POST'])
@login_required
def update_university(id):
    if session.get('role') == 'admin':
        if request.method == 'POST':
            # Get form data 
            department_load_Evaluation = request.form['department_load_Evaluation']
            workshop_develop_Evaluation = request.form['workshop_develop_Evaluation']
            medical_services_Evaluation = request.form['medical_services_Evaluation']
            program_bank_Evaluation = request.form['program_bank_Evaluation']

            evaluation_fields = [
            'department_load_Evaluation',
            'workshop_develop_Evaluation',
            'medical_services_Evaluation',
            'program_bank_Evaluation'
             ]

            # Calculate sum with error handling
            try:
                evaluation_sum = sum(int(request.form[field]) for field in evaluation_fields)
            except ValueError as e:
                # Handle case where a value can't be converted to int
                evaluation_sum = 0  # or raise an exception
                print(f"Error converting form values: {e}")

            # Insert into database
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()

            update_query = ''' UPDATE university_evaluation SET department_load_Evaluation == ?,
            workshop_develop_Evaluation == ?, medical_services_Evaluation == ? ,
            program_bank_Evaluation == ?, evaluation_sum == ?
            WHERE university_evaluation.user_id == ? '''

            cursor.execute(update_query, (department_load_Evaluation,workshop_develop_Evaluation,
            medical_services_Evaluation,program_bank_Evaluation,evaluation_sum,id))
            conn.commit()
            conn.close()
            flash('Data added successfully!', 'success')
            return redirect(url_for('view_data'))

        conn = get_db_connection()

        # Admin can see all data
        university_evaluation = conn.execute('''
            SELECT university_evaluation.*, users.username, users.full_name 
            FROM university_evaluation 
            JOIN users ON university_evaluation.user_id = users.id
            WHERE university_evaluation.user_id = ?
            ORDER BY university_evaluation.created_at DESC
        ''',(id,)).fetchone()
        conn.close()

        return render_template('admin/update_university.html',id=id, university_evaluation=university_evaluation)
    else:
        return render_template('page-404.html')




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
        users = conn.execute(''' 
        SELECT COUNT(*)
        FROM  users
        ''').fetchone()
        University_Service = conn.execute(''' 
        SELECT COUNT(*)
        FROM  University_Service
        ''').fetchone()
         # Admin can see all data

        activity = conn.execute('''
        SELECT activity_data.*, users.username, users.full_name 
        FROM activity_data 
        JOIN users ON activity_data.user_id = users.id
        ORDER BY activity_data.created_at DESC
        ''').fetchall()
        Scientific_research1 = conn.execute('''
        SELECT COUNT(*)
        FROM  Scientific_research
        WHERE research_type LIKE "%بحث%" AND Publisher LIKE "%مؤتمر%" ;
        ''').fetchone()

        Scientific_research2 = conn.execute('''
        SELECT COUNT(*)
        FROM  Scientific_research
        WHERE research_type LIKE "%بحث%" AND Publisher LIKE "%مجلة%" ;
        ''').fetchone()

        part_in_conf = conn.execute(''' 
        SELECT COUNT(DISTINCT user_id )
        FROM  participate_conference
        ''').fetchone()

        Evaluation_aspects = conn.execute(''' 
        SELECT SUM(evaluation_sum)
        FROM Evaluation_aspects
        ''').fetchone()

        university_evaluation = conn.execute(''' 
        SELECT SUM(evaluation_sum)
        FROM university_evaluation
        ''').fetchone()

        activity_percent = (activity_kpi[0]/(users[0]-1))*100
        research2_percent = (Scientific_research2[0]/(users[0]-1))*100
        research1_percent = (Scientific_research1[0]/(users[0]-1))*100
        conf_percent = (part_in_conf[0]/(users[0]-1))*100
        Evaluation_aspects_percent = (Evaluation_aspects[0]/(users[0]-1))
        university_evaluation_percent = (university_evaluation[0]/(users[0]-1))

        return render_template('view_kpis.html', academic_kpi=academic_kpi[0],activity_kpi=activity_kpi[0],
        activity_percent=int(activity_percent), University_Service=University_Service[0],
        Scientific_research1=Scientific_research1[0],Scientific_research2=Scientific_research2[0],
        research1_percent=int(research1_percent),research2_percent=int(research2_percent), conf_percent=int(conf_percent),
        Evaluation_aspects_percent=int(Evaluation_aspects_percent),university_evaluation_percent=int(university_evaluation_percent))

        
    conn.close()
    return render_template('view_data.html', semseters=semseters, activity=activity)

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
            return redirect(url_for('view_data'))

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
            Use_learning_Evaluation = request.form['Use_learning_Evaluation']
            teaching_methods_Evaluation = request.form['teaching_methods_Evaluation']
            Methods_student_Evaluation = request.form['Methods_student_Evaluation']
            preparing_test_Evaluation = request.form['preparing_test_Evaluation']
            Provide_academic_Evaluation = request.form['Provide_academic_Evaluation']

            evaluation_fields = [
            'Develop_courses_Evaluation',
            'Prepare_file_Evaluation',
            'Electronic_tests_Evaluation',
            'Prepare_material_Evaluation',
            'Use_learning_Evaluation',
            'teaching_methods_Evaluation',
            'Methods_student_Evaluation',
            'preparing_test_Evaluation',
            'Provide_academic_Evaluation'
             ]

            # Calculate sum with error handling
            try:
                evaluation_sum = sum(int(request.form[field]) for field in evaluation_fields)
            except ValueError as e:
                # Handle case where a value can't be converted to int
                evaluation_sum = 0  # or raise an exception
                print(f"Error converting form values: {e}")

            # Insert into database
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()

            update_query = ''' UPDATE Evaluation_aspects SET Develop_courses_Evaluation == ?,
            Prepare_file_Evaluation == ?, Electronic_tests_Evaluation == ? ,
            Prepare_material_Evaluation == ?, Use_learning_Evaluation == ?,
            teaching_methods_Evaluation == ?, Methods_student_Evaluation == ?,
            preparing_test_Evaluation == ?, Provide_academic_Evaluation == ? , evaluation_sum == ?
            WHERE Evaluation_aspects.user_id == ? '''

            cursor.execute(update_query, (Develop_courses_Evaluation,Prepare_file_Evaluation,
            Electronic_tests_Evaluation,Prepare_material_Evaluation,
            Use_learning_Evaluation,teaching_methods_Evaluation,
            Methods_student_Evaluation,preparing_test_Evaluation,Provide_academic_Evaluation,evaluation_sum,id))
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


@app.route('/add_Q', methods=['GET', 'POST'])
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
    init_db()
    app.run(debug=True)