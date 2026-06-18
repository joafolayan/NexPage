### NexPage ###

NexPage is a Flask-based web application that provides a library management system. 
It allows users to browse, borrow, and return books, while librarians can manage the book inventory. 
The system includes features like user authentication, book search, borrowing management,book management and fine calculation for overdue books.

### Features ###
- User Features 

    - User registration and login

    - Browse available books

    - Search books by title or author

    - Borrow and return books

    - View borrowed books and due dates

    - See calculated fines for overdue books

- Librarian Features
    - Add new books to the library
    - Remove books from the library
    - View all books in the system

- System Components

    - Models
        - User: Stores user information (username, email, password)

        - Librarian: Special admin accounts for library management

        - Book: Contains book details (title, author, quantity, cover image)

        - BorrowedBook: Tracks borrowing transactions

    - Helper Classes
        - AuthenticationManager: Handles user and librarian authentication

        - BookManager: Manages book addition and deletion

        - BorrowManager: Handles book borrowing logic

        - ReturnManager: Manages book returns

        - SearchManager: Provides book search functionality

        - FineCalculator: Calculates fines for overdue books

        - AvailabilityUpdater: Updates book availability status

        - FileHandler: Manages file uploads for book covers

### Installation

    - Clone the repository
    - Create and activate a virtual environment:
        python -m venv venv
        source venv/bin/activate  - for use on Mac `venv\Scripts\activate` - for use on Windows
    - Install dependencies:
        pip install flask flask-sqlalchemy werkzeug
    - Run the application using;
            python app.py
    - Access the application at http://localhost:5000

### Usage
    Default Accounts
        For the Librarian;
        Username: librarian
        Password: library123

### System File Structure
/static
  /uploads - Book cover images storage

  /images - Static images

  style.css - CSS stylesheet

/templates

  addBook.html - Add book form

  base.html - Base template

  bookPage.html - Book browsing page

  index.html - Home page

  librarian.html - Librarian dashboard

  login.html - Login page

  registration.html - User registration

  userPage.html - User dashboard

app.py - Main application file

models.py - Database models
