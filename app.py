import os
import json
import base64
from flask import Flask, render_template, request, redirect, url_for, Response, session, flash
import firebase_admin
from firebase_admin import credentials, firestore, auth
import datetime
import csv
import io

app = Flask(__name__)
# IMPORTANT: Change this to a strong, random key in production!
# You can generate one with `import os; print(os.urandom(24).hex())` in Python
app.secret_key = '2e61bb2576fe789a5f315b3bf4d26eb6e358c1820a3abe14'

# --- Firebase Initialization ---
# Ensure the Firebase app is initialized only once
if not firebase_admin._apps:
    # Try to get credentials from environment variable for deployment
    service_account_key_base64 = os.environ.get('SERVICE_ACCOUNT_KEY_BASE64')

    if service_account_key_base64:
        # Decode the key if found in environment variable
        try:
            service_account_info = json.loads(base64.b64decode(service_account_key_base64))
            cred = credentials.Certificate(service_account_info)
        except (json.JSONDecodeError, base64.binascii.Error) as e:
            print(f"Error decoding service account key from environment: {e}")
            # Fallback to ApplicationDefault if decoding fails (e.g., malformed env var)
            # This might cause issues if serviceAccountKey.json is truly gone and no GOOGLE_APPLICATION_CREDENTIALS set
            cred = credentials.ApplicationDefault()
    else:
        # Fallback for local development using GOOGLE_APPLICATION_CREDENTIALS or default ADC
        # This requires you to have GOOGLE_APPLICATION_CREDENTIALS env var pointing to your local key
        cred = credentials.ApplicationDefault()

    firebase_admin.initialize_app(cred)

db = firestore.client()

# --- Global Categories List ---
CATEGORIES = [
    "Food & Groceries", "Transport", "Housing (Rent/Mortgage)",
    "Utilities (Electricity, Water, Internet)", "Entertainment",
    "Salary", "Freelance Income", "Healthcare", "Education",
    "Shopping", "Savings", "Investments", "Miscellaneous", "Other"
]

# Define categories considered as income
INCOME_CATEGORIES = ["Salary", "Freelance Income", "Investments", "Savings"]

# --- Authentication Decorator ---
# This decorator will protect routes, redirecting unauthenticated users to login
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Flask Routes ---

@app.route('/')
@login_required # Protect this route
def index():
    user_id = session['user_id']
    transactions_query = db.collection('transactions').where('userId', '==', user_id) # Filter by userId

    # Get filter parameters
    selected_category = request.args.get('category', '')
    search_query = request.args.get('search', '').lower()
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')

    if selected_category:
        transactions_query = transactions_query.where('category', '==', selected_category)

    start_date_obj = None
    if start_date_str:
        try:
            start_date_obj = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
            transactions_query = transactions_query.where('date', '>=', start_date_obj)
        except ValueError:
            pass

    end_date_obj = None
    if end_date_str:
        try:
            end_date_obj = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
            transactions_query = transactions_query.where('date', '<=', end_date_obj.replace(hour=23, minute=59, second=59, microsecond=999999))
        except ValueError:
            pass

    # Order by date - crucial for efficient Firestore queries with range filters
    # This query combination (userId, category, date, __name__) requires a composite index
    transactions_query = transactions_query.order_by('date', direction=firestore.Query.DESCENDING)

    transactions = []
    total_income = 0.0
    total_expenses = 0.0
    category_expenses = {category: 0.0 for category in CATEGORIES}

    for doc in transactions_query.stream():
        transaction_data = doc.to_dict()
        transaction_data['id'] = doc.id

        amount = transaction_data.get('amount', 0.0)
        category = transaction_data.get('category', '').strip()

        if search_query and \
           (search_query not in transaction_data.get('description', '').lower() and \
            search_query not in category.lower()):
            continue

        if category in INCOME_CATEGORIES:
            total_income += amount
        else:
            total_expenses += amount
            if category in category_expenses:
                category_expenses[category] += amount
            else:
                category_expenses[category] = amount

        transactions.append(transaction_data)

    net_balance = total_income - total_expenses

    chart_labels = []
    chart_data = []
    sorted_categories = sorted(category_expenses.keys())
    for category in sorted_categories:
        expense = category_expenses[category]
        if expense > 0:
            chart_labels.append(category)
            chart_data.append(round(expense, 2))

    return render_template('index.html',
                           transactions=transactions,
                           total_income=total_income,
                           total_expenses=total_expenses,
                           net_balance=net_balance,
                           all_categories=CATEGORIES,
                           selected_category=selected_category,
                           search_query=search_query,
                           start_date_query=start_date_str,
                           end_date_query=end_date_str,
                           chart_labels=chart_labels,
                           chart_data=chart_data,
                           username=session.get('user_email')) # Pass username to template

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = auth.create_user(email=email, password=password)
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            # Firebase Admin SDK errors might need parsing to be user-friendly
            # e.g., auth/email-already-exists, auth/weak-password
            error_message = str(e)
            if 'EMAIL_ALREADY_EXISTS' in error_message:
                flash('That email is already in use. Please log in or use a different email.', 'danger')
            elif 'WEAK_PASSWORD' in error_message:
                flash('Password is too weak. Please use at least 6 characters.', 'danger')
            else:
                flash(f'Error creating account: {error_message}', 'danger')
            return render_template('signup.html', email=email)
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            # --- IMPORTANT SECURITY NOTE FOR TUTORIAL ---
            # This direct `get_user_by_email` and then assuming login is a SIMPLIFICATION for this tutorial.
            # In a production application, you would typically use a client-side Firebase SDK
            # (e.g., Firebase JS SDK in your HTML/JS) to perform `signInWithEmailAndPassword`.
            # Upon successful client-side sign-in, Firebase provides an ID token.
            # This ID token would then be sent to your Flask backend, which would verify it using `auth.verify_id_token`.
            # This method securely authenticates the user and provides their UID.
            # Direct password verification on the server with Admin SDK is generally not recommended
            # without proper hashing/salting, which Firebase handles client-side.
            # FOR THIS TUTORIAL'S PURPOSE, we rely on the Admin SDK's ability to fetch user data
            # to obtain the UID, assuming the email exists.
            # ----------------------------------------------

            user = auth.get_user_by_email(email)
            # For this tutorial, we will directly fetch the user by email and use their UID.
            # In a real app, you'd need to verify the password securely.

            session['user_id'] = user.uid
            session['user_email'] = user.email # Store email for display purposes
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('login.html', email=email)
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    session.pop('user_email', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/add', methods=['GET', 'POST'])
@login_required # Protect this route
def add_transaction():
    user_id = session['user_id']
    if request.method == 'POST':
        amount = float(request.form['amount'])
        description = request.form['description']
        category = request.form['category']
        date_str = request.form['date']
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')

        new_transaction = {
            'amount': amount,
            'description': description,
            'category': category,
            'date': date_obj,
            'userId': user_id # Store the user ID with the transaction
        }
        try:
            db.collection('transactions').add(new_transaction)
            flash('Transaction added successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"Error adding transaction: {e}", 'danger')
            return render_template('add.html', categories=CATEGORIES) # Pass categories even on error
    else:
        return render_template('add.html', categories=CATEGORIES)

@app.route('/edit/<id>', methods=['GET', 'POST'])
@login_required # Protect this route
def edit_transaction(id):
    user_id = session['user_id']
    transaction_ref = db.collection('transactions').document(id)

    # Before fetching, verify ownership (optional, but good for robust logic)
    # Firestore rules will prevent unauthorized access anyway, but this adds server-side check.
    doc = transaction_ref.get()
    if not doc.exists or doc.to_dict().get('userId') != user_id:
        flash("You don't have permission to edit this transaction.", 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        amount = float(request.form['amount'])
        description = request.form['description']
        category = request.form['category']
        date_str = request.form['date']
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')

        updated_transaction = {
            'amount': amount,
            'description': description,
            'category': category,
            'date': date_obj,
            'userId': user_id # Ensure userId is retained (or updated if user changes, though unlikely)
        }
        try:
            transaction_ref.update(updated_transaction)
            flash('Transaction updated successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"Error updating transaction: {e}", 'danger')
            transaction = transaction_ref.get().to_dict() # Re-fetch to populate form if error
            if isinstance(transaction.get('date'), datetime.datetime):
                transaction['date'] = transaction['date'].strftime('%Y-%m-%d')
            return render_template('edit.html', transaction=transaction, transaction_id=id, categories=CATEGORIES)
    else:
        try:
            transaction = transaction_ref.get().to_dict()
            if transaction:
                if isinstance(transaction.get('date'), datetime.datetime):
                    transaction['date'] = transaction['date'].strftime('%Y-%m-%d')
                return render_template('edit.html', transaction=transaction, transaction_id=id, categories=CATEGORIES)
            else:
                flash("Transaction not found.", 'danger')
                return redirect(url_for('index'))
        except Exception as e:
            flash(f"Error fetching transaction for edit: {e}", 'danger')
            return redirect(url_for('index'))

@app.route('/delete/<id>', methods=['GET', 'POST'])
@login_required # Protect this route
def delete_transaction(id):
    user_id = session['user_id']
    transaction_ref = db.collection('transactions').document(id)

    # Verify ownership before deleting
    doc = transaction_ref.get()
    if not doc.exists or doc.to_dict().get('userId') != user_id:
        flash("You don't have permission to delete this transaction.", 'danger')
        return redirect(url_for('index'))

    try:
        transaction_ref.delete()
        flash('Transaction deleted successfully!', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f"Error deleting transaction: {e}", 'danger')
        return redirect(url_for('index'))

@app.route('/export-csv')
@login_required # Protect this route
def export_csv():
    user_id = session['user_id']
    transactions_query = db.collection('transactions').where('userId', '==', user_id) # Filter by userId
    transactions_query = transactions_query.order_by('date', direction=firestore.Query.DESCENDING)

    si = io.StringIO()
    cw = csv.writer(si)

    headers = ['ID', 'Date', 'Amount', 'Description', 'Category']
    cw.writerow(headers)

    for doc in transactions_query.stream():
        transaction_data = doc.to_dict()

        date_value = transaction_data.get('date')
        if isinstance(date_value, datetime.datetime):
            formatted_date = date_value.strftime('%Y-%m-%d')
        else:
            formatted_date = str(date_value)

        row = [
            doc.id,
            formatted_date,
            f"₹{transaction_data.get('amount', 0.0):.2f}",
            transaction_data.get('description', ''),
            transaction_data.get('category', '')
        ]
        cw.writerow(row)

    output = si.getvalue()

    response = Response(output, mimetype='text/csv')
    response.headers["Content-Disposition"] = "attachment; filename=transactions.csv"
    return response

if __name__ == '__main__':
    # Get the port from the environment variable, default to 8080 if not set (Cloud Run sets it)
    port = int(os.environ.get("PORT", 8080))
    # Run the app, listening on all public IPs (0.0.0.0) and the specified port
    # Set debug=False for production!
    app.run(host="0.0.0.0", port=port, debug=False)
