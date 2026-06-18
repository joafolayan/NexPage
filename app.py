from flask import Flask, render_template, flash, request, redirect, url_for, session
from models import db, User, Book, BorrowedBook, Librarian
# from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os

# --- Initialization ---
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

db.init_app(app)

# db = SQLAlchemy(app)

#helper classes

class FineCalculator:
    @staticmethod
    def calculate(due_date):
        today = datetime.now().date()
        if today > due_date:
            return (today - due_date).days * 10
        return 0

class FileHandler:
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

class AvailabilityUpdater:
    @staticmethod
    def update(book_id):
        book = db.session.get(Book, book_id)
        if book:
            borrowed_count = BorrowedBook.query.filter_by(book_id=book_id, return_date=None).count()
            book.available = book.quantity - borrowed_count
            db.session.commit()
            

#manages user authentication
class AuthenticationManager:
    @staticmethod
    def create_librarian():
        if not Librarian.query.filter_by(username='librarian').first():
            librarian = Librarian(username='librarian', password=generate_password_hash('library123'))
            db.session.add(librarian)
            db.session.commit()

    @staticmethod
    def user_login(username, password):
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            return user
        return None

    @staticmethod
    def librarian_login(username, password):
        librarian = Librarian.query.filter_by(username=username).first()
        if librarian and check_password_hash(librarian.password, password):
            return librarian
        return None
    
#bookManagement class
class BookManager:
    @staticmethod
    def add_book(title, author, file):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        book = Book(title=title, author=author, bookImage=filename)
        db.session.add(book)
        db.session.commit()

    @staticmethod
    def delete_book(book_id):
        book = Book.query.get(book_id)
        if not book:
            return False, 'Book not found'

        if BorrowedBook.query.filter_by(book_id=book_id, return_date=None).count() > 0:
            return False, 'Cannot delete: Book is currently borrowed'

        db.session.delete(book)
        db.session.commit()
        return True, 'Book deleted successfully'

#borrow book class
class BorrowManager:
    @staticmethod
    def borrow_book(user_id, book_id):
        user = db.session.get(User, user_id)
        book = db.session.get(Book, book_id)

        if not book:
            return False, 'Book not found'
        if BorrowedBook.query.filter_by(user_id=user.id, book_id=book_id, return_date=None).first():
            return False, 'You have already borrowed this book'
        if book.quantity < 1:
            return False, 'Book currently unavailable'

        borrow_date = datetime.now()
        due_date = borrow_date + timedelta(days=14)
        db.session.add(BorrowedBook(user_id=user.id, book_id=book_id, borrow_date=borrow_date, due_date=due_date))
        book.quantity -= 1
        db.session.commit()
        return True, 'Book borrowed successfully'

# Manages the return functionality
class ReturnManager:
    @staticmethod
    def return_book(user_id, book_id):
        borrowed = BorrowedBook.query.filter_by(user_id=user_id, book_id=book_id, return_date=None).first()
        if not borrowed:
            return False, 'This book has already been returned or was never borrowed'

        borrowed.return_date = datetime.now()
        book = db.session.get(Book, book_id)
        if book:
            book.quantity += 1
        db.session.commit()
        return True, 'Book returned successfully'

#Manages the search functionality
class SearchManager:
    @staticmethod
    def search_books(query):
        if query:
            return Book.query.filter(
                (Book.title.ilike(f'%{query}%')) |
                (Book.author.ilike(f'%{query}%'))
            ).all()
        return Book.query.limit(10).all()
    
    
#routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registration', methods=['GET','POST'])
def registration():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('registration'))

        if User.query.filter_by(email=email).first():
            flash('This email already exists!', 'error')
            return redirect(url_for('registration'))

        hashed_password = generate_password_hash(password)
        db.session.add(User(username=username, email=email, password=hashed_password))
        db.session.commit()
        flash("Registration completed, login to use the system!",'success')
        return redirect(url_for('login'))
    return render_template('registration.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        librarian = AuthenticationManager.librarian_login(username, password)
        if librarian:
            session['librarian'] = librarian.username
            return redirect(url_for('librarianPage'))

        user = AuthenticationManager.user_login(username, password)
        if user:
            session['user_id'] = user.id
            flash('Login successful!','success')
            return redirect(url_for('bookPage'))

        flash("Invalid Username or Password!",'error')
    return render_template('login.html')

@app.route('/add-book', methods=['GET','POST'])
def addBook():
    if 'librarian' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        BookManager.add_book(
            request.form['title'], 
            request.form['author'], 
            request.files['cover']
        )
        flash('Book has been added to the library','success')
        return redirect(url_for('librarianPage'))
    return render_template('addBook.html')

@app.route('/delete-book/<int:book_id>')
def deleteBook(book_id):
    if 'librarian' not in session:
        return redirect(url_for('login'))
    success, message = BookManager.delete_book(book_id)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('librarianPage'))

@app.route('/librarian')
def librarianPage():
    if 'librarian' not in session:
        return redirect(url_for('login'))
    books = Book.query.all()
    return render_template('librarian.html', books=books)

@app.route('/bookPage')
def bookPage():
    if 'user_id' not in session:
        flash('Please login to use the library system', 'error')
        return redirect(url_for('login'))
    query = request.args.get('search', '')
    books = SearchManager.search_books(query)
    for book in books:
        AvailabilityUpdater.update(book.id)
    return render_template('bookPage.html', books=books, search_query=query)

@app.route('/borrow/<int:book_id>')
def borrowBook(book_id):
    if 'user_id' not in session:
        flash('Login to the system to borrow a book', 'error')
        return redirect(url_for('login'))
    success, message = BorrowManager.borrow_book(session['user_id'], book_id)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('userPage'))

@app.route('/return/<int:book_id>')
def returnBook(book_id):
    if 'user_id' not in session:
        flash('Login to the system to borrow a book', 'error')
        return redirect(url_for('login'))
    success, message = ReturnManager.return_book(session['user_id'], book_id)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('userPage'))

@app.route('/user')
def userPage():
    if 'user_id' not in session:
        flash('Login to the system to access the dashboard','error')
        return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    borrowed = BorrowedBook.query.filter_by(user_id=user.id, return_date=None).all()
    fine = sum(FineCalculator.calculate(b.due_date) for b in borrowed)
    return render_template('userPage.html', borrowed=borrowed, fine=fine)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

#runs the application
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        AuthenticationManager.create_librarian()
    app.run(debug=True)