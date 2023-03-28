CREATE TABLE users(
 username VARCHAR PRIMARY KEY,
 password VARCHAR NOT NULL,
 email VARCHAR NOT NULL
);

CREATE TABLE books (
  isbn VARCHAR PRIMARY KEY UNIQUE,
  title TEXT,
  author TEXT,
  year INTEGER
);

CREATE TABLE reviews (
  id SERIAL PRIMARY KEY,
  isbn VARCHAR NOT NULL,
  rating INTEGER NOT NULL,
  comment TEXT,
  username VARCHAR NOT NULL
);

INSERT INTO reviews(isbn,rating,comment,username) VALUES ('1416949658','3','Good.','Gloria');
INSERT INTO reviews(isbn,rating,comment,username) VALUES ('1416949658','2','Overrated','Kelsey');