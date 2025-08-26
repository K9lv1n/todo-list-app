from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date # Import date as well for comparison
import os

app = Flask(__name__)
# Configure the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db' # Path to the database file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # To suppress a warning
db = SQLAlchemy(app)

# Define the Task model with new fields
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    # New fields:
    category = db.Column(db.String(50), default='General') # Category for the task
    deadline = db.Column(db.DateTime, nullable=True) # Optional deadline date and time
    location = db.Column(db.String(200), nullable=True) # Optional location string for map
    completed = db.Column(db.Boolean, default=False) # New field to track completion status

    def __repr__(self):
        # This is for debugging, helps to see task objects clearly
        return f'<Task {self.id}: {self.content}>'

# --- Routes and Views ---

@app.route('/')
def home():
    # Fetch all tasks from the database to display on the home page
    tasks = Task.query.order_by(Task.completed, Task.deadline).all() # Order by completion status (incomplete first), then by deadline
    # Pass datetime.now() to the template for highlighting overdue/due today tasks
    return render_template('index.html', tasks=tasks, today=datetime.now())


@app.route('/add', methods=['POST'])
def add_task():
    # Extract data from the submitted form
    task_content = request.form['task_content']
    task_category = request.form['task_category']
    task_deadline_str = request.form['task_deadline']
    task_location = request.form['task_location']

    # Convert deadline string from 'YYYY-MM-DD' to a datetime object
    task_deadline = None
    if task_deadline_str:
        try:
            task_deadline = datetime.strptime(task_deadline_str, '%Y-%m-%d')
        except ValueError:
            # Handle cases where the date format might be wrong, though HTML 'date' input helps prevent this
            pass 

    # Create a new Task object with the collected data
    new_task = Task(
        content=task_content,
        category=task_category,
        deadline=task_deadline,
        location=task_location
    )
    
    # Add the new task to the database session and commit the changes
    db.session.add(new_task)
    db.session.commit()
    
    # Redirect back to the home page to show the updated list
    return redirect(url_for('home'))

@app.route('/delete/<int:id>')
def delete_task(id):
    # Find the task by its ID, or return a 404 error if not found
    task_to_delete = Task.query.get_or_404(id)
    
    # Delete the task from the database session and commit the changes
    db.session.delete(task_to_delete)
    db.session.commit()
    
    # Redirect back to the home page
    return redirect(url_for('home'))

@app.route('/complete/<int:id>')
def complete_task(id):
    task_to_toggle = Task.query.get_or_404(id)
    task_to_toggle.completed = not task_to_toggle.completed # Toggle the completed status
    db.session.commit()
    return redirect(url_for('home'))
        
# --- Application Entry Point ---
if __name__ == '__main__':
    # Ensure database tables are created before running the app
    # This block runs only when you execute app.py directly
    with app.app_context():
        db.create_all()
    # Run the Flask development server
    app.run(debug=True)
