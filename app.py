from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta, time as TimeClass # Alias time as TimeClass
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24) # IMPORTANT: Keep this for flash messages!
db = SQLAlchemy(app)

# --- Removed Gemini API Configuration and call_gemini_api function ---

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), default='General')
    deadline = db.Column(db.DateTime, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    completed = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Task {self.id}: {self.content}>'

@app.route('/')
def home():
    tasks = Task.query.order_by(Task.completed, Task.deadline).all()
    print(f"Home route fetched {len(tasks)} tasks from DB.")
    for task in tasks:
        print(f"  - Task ID: {task.id}, Content: '{task.content}', Completed: {task.completed}, Deadline: {task.deadline}")
    return render_template('index.html', tasks=tasks, today=datetime.now())

@app.route('/add', methods=['POST'])
def add_task():
    print(f"Full form data received: {request.form}")

    task_content = request.form.get('task_content', '').strip()
    task_category = request.form.get('task_category', 'General').strip()
    task_date_str = request.form.get('task_date')
    task_time_str = request.form.get('task_time')
    task_location = request.form.get('task_location', '').strip()

    # --- Manual Validation ---
    if not task_content or len(task_content) < 3:
        flash('Please provide a descriptive task activity (at least 3 characters). 🧐', 'error')
        print("Validation failed: Task content too short or empty.")
        return redirect(url_for('home'))

    if not task_date_str:
        flash('Please select a deadline date for your task. 🗓️', 'error')
        print("Validation failed: No deadline date provided.")
        return redirect(url_for('home'))

    task_deadline = None
    try:
        parsed_date = datetime.strptime(task_date_str, '%Y-%m-%d').date()
        if task_time_str:
            parsed_time = datetime.strptime(task_time_str, '%H:%M').time()
            task_deadline = datetime.combine(parsed_date, parsed_time)
        else:
            # If date is provided but no time, default to 5 PM
            task_deadline = datetime.combine(parsed_date, TimeClass(17, 0, 0))
            print("Defaulting time to 5 PM as no time was provided.")

        # Ensure the deadline is not in the past (unless it's today and the time is still valid)
        if task_deadline < datetime.now() and task_deadline.date() < datetime.now().date():
             flash('The deadline cannot be in the past. Please select a future date or time. ⏰', 'error')
             print("Validation failed: Deadline is in the past.")
             return redirect(url_for('home'))
        elif task_deadline < datetime.now() and task_deadline.date() == datetime.now().date() and task_deadline.time() < datetime.now().time():
             flash('The deadline time is in the past for today. Please select a future time. ⏰', 'error')
             print("Validation failed: Deadline time is in the past for today.")
             return redirect(url_for('home'))


    except ValueError:
        flash('Invalid date or time format. Please use the provided pickers. ⏳', 'error')
        print(f"Validation failed: Invalid date/time format for {task_date_str} {task_time_str}")
        return redirect(url_for('home'))

    new_task = Task(
        content=task_content,
        category=task_category,
        deadline=task_deadline,
        location=task_location
    )
    db.session.add(new_task)
    db.session.commit()
    flash(f"Task '{new_task.content}' added successfully! 🎉", 'success')
    print(f"Successfully added task: '{new_task.content}' (ID: {new_task.id}, Deadline: {new_task.deadline})")
            
    return redirect(url_for('home'))

@app.route('/delete/<int:id>')
def delete_task(id):
    task_to_delete = Task.query.get_or_404(id)
    db.session.delete(task_to_delete)
    db.session.commit()
    flash(f"Task '{task_to_delete.content}' deleted. 👋", 'info')
    print(f"Deleted task with ID: {id}")
    return redirect(url_for('home'))

@app.route('/complete/<int:id>', methods=['POST'])
def complete_task(id):
    task_to_toggle = Task.query.get_or_404(id)
    task_to_toggle.completed = not task_to_toggle.completed
    db.session.commit()
    status = "completed" if task_to_toggle.completed else "unmarked"
    flash(f"Task '{task_to_toggle.content}' {status}! ✅", 'success')
    print(f"Toggled completion for task with ID: {id}. New status: {task_to_toggle.completed}")
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)