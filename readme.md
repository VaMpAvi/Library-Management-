# Library Management System - Flask API  

## Project Description  
The Library Management System is a Flask-based API designed to manage a library's operations by allowing CRUD (Create, Read, Update, Delete) operations for books and members. The system includes optional features like search functionality, pagination, and token-based authentication to enhance usability and security.  

The API is built without the use of third-party libraries, adhering to the given constraints. It is designed to interact with a PostgreSQL database and demonstrates structured coding practices, use of typed parameters, and automated tests to ensure correctness and quality.  

---

## Features  
### Core Features:  
1. **CRUD operations** for books and members.  
2. **Association of books with members** through issuing and returning functionalities.  

### Bonus Features (Optional):  
1. **Search Functionality**: Search books by title or author.  
2. **Pagination**: Manage large datasets efficiently.  
3. **Token-based Authentication**: Secure the API endpoints.  

---

## Prerequisites  

### 1. Install Required Software  
- Python 3.10 or above  
- PostgreSQL  

### 2. Setup PostgreSQL Database  
- Create a new database:  
  ```sql
  CREATE DATABASE library_management;

  Create the users, books, and issuedbooks tables
  CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100) NOT NULL,
    password VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(100) NOT NULL
);

CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(100) NOT NULL,
    quantity int NOT NULL
);

CREATE TABLE issuedbooks (
    issueid SERIAL PRIMARY KEY,
    uid INT REFERENCES users(id),
    bid INT REFERENCES books(id),
);

### 3. Install Python Dependencies
pip install flask
pip install asyncpg
pip install pyjwt


### 4. Steps to Run the Application
Clone it from git reporistory 
git clone https://github.com/VaMpAvi/Library-Management-.git

### 5. Run the Application
python app.py

### 6. Access the API
The API will be accessible at http://localhost:5000.

### 7. Design Choices
Flask Framework: Chosen for its simplicity and flexibility.
PostgreSQL: Used for its robustness and compliance with relational database standards.
API Structure: Endpoints are organized for scalability and maintenance.
Typed Parameters: Used to ensure parameter validation and consistency.
Automated Tests: Created to verify API functionality and edge cases.

### 8. Assumptions and Limitations
Authentication: If implemented, token-based authentication assumes the use of HTTP headers for secure token exchange.
Database Constraints: Primary and foreign key relationships are enforced for data integrity.
Error Handling: Basic error handling is implemented, but edge-case handling may require further iteration.
Search Functionality: Limited to searching by book title and author.




  

