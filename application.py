import os
import csv
from flask import Flask, session, request, render_template, flash, jsonify,abort
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import text
import requests
#from models import *

app = Flask(__name__)

# Check for environment variable
#if not os.getenv("DATABASE_URL"):
#    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(("postgresql://postgres:Lai1015@localhost:5433/postgres"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    if 'username' in session:
        username = session['username']
        return render_template('search.html', username=username)         
    return render_template("index.html")

 
@app.route("/login",methods=["POST"])
def login():
    username=request.form.get("username")
    password=request.form.get("password")
    if username == '' or password == '':
        flash("Error: username or password cannot be empty.")
        return render_template("index.html")
    exist = db.execute(text("SELECT * FROM users WHERE (username=:username)"),{"username": username}).fetchone()
    match = db.execute(text("SELECT * FROM users WHERE username=:username AND password=:password") , {"username":username, "password":password}).fetchone()
    if exist is not None:
        if match is not None:
            session['username'] = username
            flash("Logged in successfully. You can search your books now!")
            return render_template("search.html",username=username)
        else:
             flash("Error: password is incorrect.")
             return render_template("index.html")
    else:
        flash("Error: username doesn't exist.")
        return render_template("index.html")


@app.route("/register_form",methods=['GET'])
def register_form():
    return render_template("register.html")

    
@app.route("/register", methods=['POST'])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    email=request.form.get("email")
    taken = db.execute(text("SELECT * from users WHERE username=:username"),{"username":username}).fetchone()
    reg_status=db.execute(text("SELECT * from users WHERE email=:email"),{"email":email}).fetchone()
    if taken is not None:
       if reg_status is None: 
           flash("The username is used by other users. please pick a different username.")
           return render_template("register.html")
    elif reg_status is not None:
        flash ("The email is registered, please log in with the username related to this email.")
        return render_template("index.html")
    else:
        db.execute(text("INSERT INTO users (username, password, email) VALUES (:username, :password, :email)"),{"username": username, "password":password, "email":email})
        db.commit()
    session['username'] = username
    flash("Registration completed and log in successfully. You can search your books now!")
    return render_template("search.html",username=username)


@app.route("/logout", methods=['GET'])
def logout():
    if session.get('username') is None:
        return render_template('index.html')
    else:
        del session['username']
        flash("Logged out successfully.")
        return render_template("index.html")

@app.route("/search",methods=['POST'])
def search():
    if 'username' in session:
        username = session['username']
    content=[]      
    content="%"+request.form.get("content")+"%"
    content=content.title()
    content = db.execute(text("SELECT * FROM books WHERE (isbn LIKE :content OR title LIKE :content OR author LIKE :content)") , {"content":content}).fetchall()

    return render_template('search.html',results=content,username=username)

@app.route("/<isbn>",methods=['GET','POST'])
def book(isbn):
    if 'username' not in session:
        flash("You are not logged in!")
        return render_template("index.html")
    content = db.execute(text("SELECT * FROM books WHERE isbn = :isbn"), {"isbn": isbn}).fetchall()
    isbn = db.execute(text("SELECT isbn FROM books WHERE isbn = :isbn"), {"isbn": isbn}).fetchone()[0]
    
    reviews = db.execute(text("SELECT username, comment, rating FROM reviews WHERE isbn = :isbn"),{"isbn": isbn}).fetchall()
    res = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q": f"isbn:{isbn}"})
    book_info=(res.json())
    if book_info['totalItems']==0:
        average_rating = "Null"
        rating_count = "Null"
        description ="Null"
    else:
        average_rating = book_info['items'][0]['volumeInfo'].get('averageRating')
        rating_count = book_info['items'][0]['volumeInfo'].get('ratingsCount')
        description = book_info['items'][0]['volumeInfo'].get('description')

    if  request.method == "POST":
        check= db.execute(text("SELECT username FROM reviews WHERE (isbn=:isbn)"), {"isbn":isbn}).fetchall()
        if (session.get('username'),) in check:
            flash('You already make comment before.You cannot submit multiple reviews.') 
            return render_template("book.html",isbn=isbn, content=content,username=session["username"], reviews=reviews,rating_count=rating_count,average_rating=average_rating,description=description)
        else:
            username = session["username"]
            rating =  request.form.get("rating")
            comment = request.form.get("comment")
            db.execute(text("INSERT INTO reviews (username, isbn, comment, rating) VALUES (:username, :isbn, :comment, :rating)"), {"username": username,"isbn": isbn, "comment": comment, "rating": rating})
            db.commit()
            reviews = db.execute(text("SELECT username, comment, rating FROM reviews WHERE isbn = :isbn"),{"isbn": isbn}).fetchall()
            flash('Review submitted!')            
            return render_template("book.html",isbn=isbn, content=content,username=username, reviews=reviews,rating_count=rating_count,average_rating=average_rating,description=description)
#    else:
    username = session["username"]        
    return render_template("book.html",isbn=isbn, content=content,username=username, reviews=reviews,rating_count=rating_count,average_rating=average_rating,description=description)
    
@app.route('/api/<string:isbn>', methods=['GET'])
def api(isbn):    
    if 'username' not in session:
        flash("You are not logged in!")
        return render_template("index.html")
    isbn = db.execute(text("SELECT isbn FROM books WHERE isbn = :isbn"), {"isbn": isbn}).fetchone()[0]
    content = db.execute(text("SELECT * FROM books WHERE isbn = :isbn"), {"isbn": isbn}).fetchall()
    

    res = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q": f"isbn:{isbn}"})
    book_info=(res.json())
    if book_info['totalItems']==0:
        title="Null"
        author="Null"
        average_rating = "Null"
        rating_count = "Null"
        published_date ="Null"
        ISBN_10="Null"
        ISBN_13="Null"
    else:
        title=content[0].title
        author=content[0].author
        average_rating = book_info['items'][0]['volumeInfo'].get('averageRating')
        rating_count = book_info['items'][0]['volumeInfo'].get('ratingsCount')
    
        published_date = book_info['items'][0]['volumeInfo'].get('publishedDate')
        identifiers = book_info['items'][0]['volumeInfo'].get('industryIdentifiers')

        for identifier in identifiers:
            if identifier.get('type') == 'ISBN_10':
                ISBN_10 = identifier.get('identifier')
            if identifier.get('type') == 'ISBN_13':
                ISBN_13 = identifier.get('identifier')   
    
    response={
        "title":title,
        "author":author,
        "publishedDate": published_date,
        "ISBN_10":ISBN_10,
        "ISBN_13":ISBN_13,
        "reviewCount":rating_count,
        "averageRating": average_rating        
    }
    return jsonify(response)
    