from flask import Flask, request, jsonify
import asyncpg,  asyncio
from config import DATABASE
import jwt 
import datetime as dt
from functools import wraps

app = Flask(__name__)
'''JWT Authentication'''
app.config['SECRET_KEY'] = 'your_secret_key'

def getToken(role):
    payload = {
        'role' : role,
        'exp' : dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def decodeToken(token):
    try:
        return jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidSignatureError:
        raise ValueError("Invalid signature - Secret key mismatch")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
    except Exception as e:
        raise ValueError(f"Failed to decode token: {str(e)}")

def roleRequired(role):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({'message': 'Token is missing'}), 401

            try:
                token = auth_header.split(" ")[1]
                print(token)
                decoded = decodeToken(token)
                if not decoded or decoded.get('role') != role:
                    return jsonify({'message': 'Permission denied'}), 403
            except Exception as e:
                print(str(e))
                return jsonify({'message': 'Invalid token'}), 401   

            return await func(*args, **kwargs)
        return wrapper
    return decorator


'''LOGIN Authentication'''
@app.route('/login', methods=['POST'])
async def login():
    data = request.json
    con = await getConnection()
    email = data.get('email')
    password = data.get('password')

    loginQuery = """
                SELECT * FROM users WHERE email = $1
            """
    record = await con.fetch(loginQuery,email)
    if len(record) == 0:
        return jsonify({'message': 'User Not Found'}),401
    userDetails = record[0]
    
    if userDetails["password"] != password:
        return jsonify({'message':'Password Incorrect'}),401
    role = userDetails["role"]
    return jsonify({'token': getToken(role)})  


db = None
'''Database Connection'''
async def getConnection():
    global db
    db = await asyncpg.connect(
        host = DATABASE['host'],
        database = DATABASE['database'],
        user = DATABASE['user'],
        password = DATABASE['password'],
        port = DATABASE['port']
    ) 
    return db


'''CRUD Operations on BOOKS
1. Add books'''

@app.route('/addBook', methods = ['POST'])
@roleRequired("admin")
async def addBooks():
    data = request.json
    con = await getConnection()
    try:
        for book in data:
            title = book['title']
            author = book['author']
            quantity = book['quantity']
            if quantity <= 0 :
                return jsonify({'message':"Invalid quantity"}),400

            query = """
            INSERT INTO books (title, author, quantity)
            VALUES ($1,$2,$3)
            """
            await con.execute(query, title, author, quantity)
    except asyncpg.exceptions.UniqueViolationError  as e:
         return jsonify({'message': 'Book already exists'}),409
    return jsonify({'message': 'Inserted Successfully'})


'''2. Show books'''

@app.route('/showBooks', methods = ['GET'])
async def getBooks():
    con = await getConnection()
    query = """
        SELECT * FROM books
    """
    rows = await con.fetch(query)
    books = [{"id": row["id"], "title": row["title"], "author": row["author"], "quantity": row["quantity"]} for row in rows]
    return jsonify(books)


'''3. Update Books'''

@app.route('/updateBooks', methods = ['POST'])
@roleRequired("admin")
async def updateBooks():
    data = request.json
    con = await getConnection()
    id = data['id']
    title = data['title']
    author = data['author']
    quantity = data['quantity']

    if quantity <= 0 :
            return jsonify({'message':"Invalid quantity"}),400
    
    query = """
        UPDATE books SET title = $2, author = $3, quantity = $4 WHERE id = $1
      """
    await con.execute(query, id, title, author, quantity)
    return jsonify({'message': 'Updated Successfully'})


'''4. Delete Books'''

@app.route('/deleteBooks', methods = ['POST'])
@roleRequired("admin")
async def deleteBooks():
    con = await getConnection()
    data = request.json
    try:
        id = data['id']
        
        query = """
            DELETE FROM books WHERE id = $1
        """
        await con.execute(query, id)
    except asyncpg.exceptions.ForeignKeyViolationError:
        return jsonify({'message': 'Book is currently borrowed'}),409
    return jsonify({'message': 'Deleted Successfully'})


'''OPTIONAL : SEARCH BOOKS BY AUTHOR/TITLE'''

@app.route('/searchBooks', methods = ['GET'])
async def searchBooks():
    con = await getConnection()
    search = request.args.get('search', '')
    query = """
        SELECT * FROM books WHERE author ILIKE $1 OR title ILIKE $1
    """
    rows = await con.fetch(query, f"%{search}%")
    books = [{"id": row["id"], "title": row["title"], "author": row["author"], "quantity": row["quantity"]} for row in rows]
    return jsonify(books)


'''Issue Book'''

@app.route('/issueBook', methods = ['POST'])
async def issueBooks():
    con = await getConnection()
    data = request.json

    for id in data:
        user_id = id["user_id"]
        book_id = id["book_id"]
        quantity = id["quantity"]

        if quantity <= 0 :
            return jsonify({'message':"Invalid quantity"}),400

    
        #Fetch quanity from books table
        fetchQuery = """
                    SELECT quantity from books where id = $1            
                """
        booksQty = await con.fetchval(fetchQuery,book_id)

        #Check if user is entering the quantity within the available range
        diff = int(booksQty) - quantity
        if diff >= 0 :
            query = """
                INSERT INTO issuedbooks(bid, uid, qty)
                VALUES($1,$2,$3)
            """
            await con.execute(query,book_id, user_id, quantity)

            updateQuery = """
                        UPDATE books set quantity = $2  WHERE id = $1
                    """
            await con.execute(updateQuery, book_id,diff)
           
        else:
            return jsonify({'message': 'Not enough books available'})
    return jsonify({'message': 'Book Issued Successfully'})


'''Return Book'''

@app.route('/returnBook', methods = ['POST'])
async def returnBooks():
    con = await getConnection()
    data = request.json
    for id in data:
        issue_id = id["issue_id"]
        book_id = id["book_id"]
        quantity = id["quantity"]

        if quantity <= 0 :
            return jsonify({'message':"Invalid quantity"}),400

        #Fetch the quantity from issued books table
        issueQtyQuery = """
                        SELECT qty from issuedbooks WHERE issueid = $1
                    """
        issueQty = await con.fetchval(issueQtyQuery,issue_id)

        #User should enter the amount less than or equal to the issued quantity
        if quantity <  issueQty:
            # fetchQuery = """
            #             SELECT quantity from books where id = $1            
            #         """
            # booksQty = await con.fetchval(fetchQuery,book_id)
            # add = int(booksQty) + quantity
    
            updateQuery = """
                        UPDATE books set quantity = quantity + $2  WHERE id = $1
                    """
            await con.execute(updateQuery, book_id,quantity)

            #Deduct the returned quantity in the issuedBooks table
            newIssueQty = int(issueQty) - quantity
            updateIssueQty = """
                            UPDATE issuedbooks SET qty = $2 WHERE issueid = $1
                """
            await con.execute(updateIssueQty,issue_id,newIssueQty)

        elif quantity == issueQty:
                # fetchQuery = """
                #         SELECT quantity from books where id = $1            
                #     """
                # booksQty = await con.fetchval(fetchQuery,book_id)
                # add = int(booksQty) + quantity
    
            updateQuery = """
                        UPDATE books set quantity = quantity + $2  WHERE id = $1
                    """
            await con.execute(updateQuery, book_id,quantity)
            deleteQuery = """
                        DELETE FROM issuedbooks WHERE issueid = $1
                    """
            await con.execute(deleteQuery,issue_id)
                

            return jsonify({'message': 'Book Returned Successfully'})
        else:
            return jsonify({'message': 'You borrowed less books'})
    


#-----------------------------------------------------------------------------------------------------------------------------------------------------------------    
'''CRUD Operations on Members
1. Add member'''

@app.route('/addUser', methods = ['POST'])
@roleRequired("admin")
async def addUser():
    data = request.json
    con = await getConnection()
   
    for user in data:
        email = user['email']
        password = user['password']
        role = user['role'] 

        query = """
            INSERT INTO users (email, password, role)
            VALUES ($1,$2,$3)
        """
        await con.execute(query, email, password, role)
    return jsonify({'message': 'Inserted Successfully'})


'''2. Show members'''

@app.route('/listUser', methods = ['GET'])
@roleRequired("admin")
async def listUsers():
    con = await getConnection()
    query = """
        SELECT * FROM users
    """
    users = await con.fetch(query)
    diplayUsers = [{"id": user["id"], "email": user["email"], "password": user["password"], "role":user["role"]} for user in users]
    return jsonify(diplayUsers)


'''3. Update member'''
@app.route('/updateUser', methods = ['POST'])
@roleRequired("admin")
async def updateUser():
    data = request.json
    con = await getConnection()
    id = data["id"]
    email = data['email']
    password = data['password']
    role = data['role'] 
    
    query = """
        UPDATE users SET  email = $2, password = $3, role = $4 WHERE id = $1
    """
    await con.execute(query, id, email, password, role)
    return jsonify({'message': 'Updated Successfully'})


'''4. Delete member'''

@app.route('/deleteUser', methods = ['POST'])
@roleRequired("admin")
async def deleteUser():
    con = await getConnection()
    data = request.json
    try:
        id = data['id']

        query = """
            DELETE FROM users WHERE id = $1
        """
        await con.execute(query, id)
    except asyncpg.exceptions.ForeignKeyViolationError:
        return jsonify({'message': 'User has borrowed books'}),409
    return jsonify({'message': 'Deleted Successfully'})



# '''5. User Issued Books'''
# @app.route('/user/{id}/books', methods = ['GET'])
# async def userBooks();
#     con = await getConnection()



#--------------------------------------------------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)

