import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# ऐप कॉन्फ़िगरेशन
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_very_secret_key_for_probank'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'bank.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- डेटाबेस मॉडल ---
class Account(db.Model):
    """बैंक खाता मॉडल"""
    id = db.Column(db.Integer, primary_key=True) # खाता संख्या
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    account_type = db.Column(db.String(50), nullable=False) # जैसे 'Savings', 'Current'
    balance = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Account {self.id}: {self.name}>'

# --- रूट्स (Routes) ---

@app.route('/')
def index():
    """डैशबोर्ड / होम पेज"""
    accounts = Account.query.all()
    total_accounts = len(accounts)
    total_balance = sum(account.balance for account in accounts)
    return render_template('index.html', 
                           total_accounts=total_accounts, 
                           total_balance=total_balance,
                           accounts=accounts)

@app.route('/create', methods=['GET', 'POST'])
def create_account():
    """नया खाता बनाने का पेज"""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        account_type = request.form['account_type']
        initial_deposit = float(request.form['initial_deposit'])

        if initial_deposit < 0:
            flash('शुरुआती जमा राशि नेगेटिव नहीं हो सकती!', 'danger')
            return redirect(url_for('create_account'))

        new_account = Account(name=name, email=email, account_type=account_type, balance=initial_deposit)
        try:
            db.session.add(new_account)
            db.session.commit()
            flash('खाता सफलतापूर्वक बना दिया गया है!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'खाता बनाने में त्रुटि हुई: {e}', 'danger')
            return redirect(url_for('create_account'))

    return render_template('create_account.html')

@app.route('/transaction', methods=['GET', 'POST'])
def transaction():
    """जमा/निकासी का पेज"""
    if request.method == 'POST':
        account_id = int(request.form['account_id'])
        amount = float(request.form['amount'])
        transaction_type = request.form['transaction_type']

        account = db.session.get(Account, account_id)

        if not account:
            flash('खाता संख्या मौजूद नहीं है!', 'danger')
            return redirect(url_for('transaction'))

        if amount <= 0:
            flash('राशि 0 से अधिक होनी चाहिए!', 'danger')
            return redirect(url_for('transaction'))
        
        if transaction_type == 'deposit':
            account.balance += amount
            flash(f'₹{amount:.2f} सफलतापूर्वक जमा किए गए। नई शेष राशि: ₹{account.balance:.2f}', 'success')
        elif transaction_type == 'withdraw':
            if account.balance >= amount:
                account.balance -= amount
                flash(f'₹{amount:.2f} सफलतापूर्वक निकाले गए। नई शेष राशि: ₹{account.balance:.2f}', 'success')
            else:
                flash('अपर्याप्त शेष राशि!', 'danger')
        
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('transaction.html')

@app.route('/search', methods=['GET', 'POST'])
def search_account():
    """खाता खोजने का फॉर्म पेज"""
    if request.method == 'POST':
        account_id = request.form['account_id']
        account = db.session.get(Account, account_id)
        if account:
            return redirect(url_for('account_details', account_id=account_id))
        else:
            flash('इस नंबर का कोई खाता नहीं मिला!', 'danger')
            return redirect(url_for('search_account'))
            
    return render_template('account_details_form.html')

@app.route('/details/<int:account_id>')
def account_details(account_id):
    """खाते की जानकारी का पेज"""
    account = db.session.get(Account, account_id)
    if not account:
        flash('खाता नहीं मिला!', 'danger')
        return redirect(url_for('index'))
    return render_template('account_details.html', account=account)

@app.route('/close', methods=['GET', 'POST'])
def close_account():
    """खाता बंद करने का पेज"""
    if request.method == 'POST':
        account_id = int(request.form['account_id'])
        account = db.session.get(Account, account_id)

        if not account:
            flash('खाता संख्या मौजूद नहीं है!', 'danger')
            return redirect(url_for('close_account'))

        db.session.delete(account)
        db.session.commit()
        flash(f'खाता संख्या {account_id} सफलतापूर्वक बंद कर दिया गया है।', 'success')
        return redirect(url_for('index'))

    return render_template('close_account.html')

# मुख्य रनर
if __name__ == '__main__':
    with app.app_context():
        db.create_all() # ऐप शुरू होने पर डेटाबेस टेबल बनाता है
    app.run(debug=True)