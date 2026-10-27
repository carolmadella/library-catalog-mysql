-- schema.sql
-- Creates the Library Catalog database and its five related tables.
-- Safe to run more than once: nothing is created twice.

CREATE DATABASE IF NOT EXISTS library_catalog;
USE library_catalog;

-- One row per author
CREATE TABLE IF NOT EXISTS authors (
    author_id   INT AUTO_INCREMENT PRIMARY KEY,
    first_name  VARCHAR(50) NOT NULL,
    last_name   VARCHAR(50) NOT NULL
);

-- One row per genre. UNIQUE stops the same genre from being stored twice
-- (MySQL compares text without case, so 'Fantasy' and 'FAntasy' count as the same).
CREATE TABLE IF NOT EXISTS genres (
    genre_id  INT AUTO_INCREMENT PRIMARY KEY,
    name      VARCHAR(50) NOT NULL UNIQUE
);

-- One row per book. Each book belongs to one author and, optionally, one genre.
CREATE TABLE IF NOT EXISTS books (
    book_id           INT AUTO_INCREMENT PRIMARY KEY,
    title             VARCHAR(200) NOT NULL,
    author_id         INT NOT NULL,
    genre_id          INT NULL,
    year_published    INT NULL,
    copies_available  INT NOT NULL DEFAULT 1,
    FOREIGN KEY (author_id) REFERENCES authors(author_id),
    FOREIGN KEY (genre_id) REFERENCES genres(genre_id),
    CHECK (copies_available >= 0),
    CHECK (year_published IS NULL OR year_published BETWEEN 0 AND 2100)
);

-- One row per library member; email must be unique
CREATE TABLE IF NOT EXISTS members (
    member_id   INT AUTO_INCREMENT PRIMARY KEY,
    first_name  VARCHAR(50) NOT NULL,
    last_name   VARCHAR(50) NOT NULL,
    email       VARCHAR(100) NOT NULL UNIQUE,
    join_date   DATE NOT NULL
);

-- One row each time a member checks out a book.
-- return_date stays NULL until the book comes back.
CREATE TABLE IF NOT EXISTS loans (
    loan_id        INT AUTO_INCREMENT PRIMARY KEY,
    book_id        INT NOT NULL,
    member_id      INT NOT NULL,
    checkout_date  DATE NOT NULL,
    due_date       DATE NOT NULL,
    return_date    DATE NULL,
    late_fee       DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    FOREIGN KEY (book_id) REFERENCES books(book_id),
    FOREIGN KEY (member_id) REFERENCES members(member_id),
    CHECK (due_date >= checkout_date),
    CHECK (return_date IS NULL OR return_date >= checkout_date),
    CHECK (late_fee >= 0)
);