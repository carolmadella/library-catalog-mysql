-- sample_data.sql
-- Adds sample authors, genres, books, members, and loans to the
-- library_catalog database so every feature and report has data to show.
-- Safe to run more than once: rows that already exist are skipped.

USE library_catalog;

-- Authors (added only if they are not already in the table)
INSERT INTO authors (first_name, last_name)
SELECT 'J.R.R.', 'Tolkien' FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM authors WHERE last_name = 'Tolkien');

INSERT INTO authors (first_name, last_name)
SELECT 'Jane', 'Austen' FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM authors WHERE last_name = 'Austen');

INSERT INTO authors (first_name, last_name)
SELECT 'George', 'Orwell' FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM authors WHERE last_name = 'Orwell');

INSERT INTO authors (first_name, last_name)
SELECT 'Harper', 'Lee' FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM authors WHERE last_name = 'Lee');

INSERT INTO authors (first_name, last_name)
SELECT 'Agatha', 'Christie' FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM authors WHERE last_name = 'Christie');

-- Genres: INSERT IGNORE skips a genre that already exists (name is UNIQUE)
INSERT IGNORE INTO genres (name) VALUES
    ('Classic'),
    ('Dystopian'),
    ('Fantasy'),
    ('Mystery'),
    ('Romance');

-- Books: the author_id and genre_id are looked up by name
INSERT INTO books (title, author_id, genre_id, year_published, copies_available)
SELECT 'The Hobbit', a.author_id, g.genre_id, 1937, 3 FROM authors AS a, genres AS g
WHERE a.last_name = 'Tolkien' AND g.name = 'Fantasy'
  AND NOT EXISTS (SELECT 1 FROM books WHERE title = 'The Hobbit');

INSERT INTO books (title, author_id, genre_id, year_published, copies_available)
SELECT 'The Lord of the Rings', a.author_id, g.genre_id, 1954, 5 FROM authors AS a, genres AS g
WHERE a.last_name = 'Tolkien' AND g.name = 'Fantasy'
  AND NOT EXISTS (SELECT 1 FROM books WHERE title = 'The Lord of the Rings');

INSERT INTO books (title, author_id, genre_id, year_published, copies_available)
SELECT 'The Silmarillion', a.author_id, g.genre_id, 1977, 0 FROM authors AS a, genres AS g
WHERE a.last_name = 'Tolkien' AND g.name = 'Fantasy'
  AND NOT EXISTS (SELECT 1 FROM books WHERE title = 'The Silmarillion');

INSERT INTO books (title, author_id, genre_id, year_published, copies_available)
SELECT 'Pride and Prejudice', a.author_id, g.genre_id, 1813, 2 FROM authors AS a, genres AS g
WHERE a.last_name = 'Austen' AND g.name = 'Romance'
  AND NOT EXISTS (SELECT 1 FROM books WHERE title = 'Pride and Prejudice');

INSERT INTO books (title, author_id, genre_id, year_published, copies_available)
SELECT 'Emma', a.author_id, g.genre_id, 1815, 1 FROM authors AS a, genres AS g
WHERE a.last_name = 'Austen' AND g.name = 'Romance'
  AND NOT EXISTS (SELECT 1 FROM books WHERE title = 'Emma');

INSERT INTO books (title, author_id, genre_id, year_published, copies_available)
SELECT '1984', a.author_id, g.genre_id, 1949, 2 FROM authors AS a, genres AS g
WHERE a.last_name = 'Orwell' AND g.name = 'Dystopian'
  AND NOT EXISTS (SELECT 1 FROM books WHERE title = '1984');

INSERT INTO books (title, author_id, genre_id, year_published, copies_available)
SELECT 'Animal Farm', a.author_id, g.genre_id, 1945, 2 FROM authors AS a, genres AS g
WHERE a.last_name = 'Orwell' AND g.name = 'Dystopian'
  AND NOT EXISTS (SELECT 1 FROM books WHERE title = 'Animal Farm');

INSERT INTO books (title, author_id, genre_id, year_published, copies_available)
SELECT 'To Kill a Mockingbird', a.author_id, g.genre_id, 1960, 2 FROM authors AS a, genres AS g
WHERE a.last_name = 'Lee' AND g.name = 'Classic'
  AND NOT EXISTS (SELECT 1 FROM books WHERE title = 'To Kill a Mockingbird');

INSERT INTO books (title, author_id, genre_id, year_published, copies_available)
SELECT 'Murder on the Orient Express', a.author_id, g.genre_id, 1934, 1 FROM authors AS a, genres AS g
WHERE a.last_name = 'Christie' AND g.name = 'Mystery'
  AND NOT EXISTS (SELECT 1 FROM books WHERE title = 'Murder on the Orient Express');

INSERT INTO books (title, author_id, genre_id, year_published, copies_available)
SELECT 'And Then There Were None', a.author_id, g.genre_id, 1939, 2 FROM authors AS a, genres AS g
WHERE a.last_name = 'Christie' AND g.name = 'Mystery'
  AND NOT EXISTS (SELECT 1 FROM books WHERE title = 'And Then There Were None');

-- Members: INSERT IGNORE skips a member whose email already exists
INSERT IGNORE INTO members (first_name, last_name, email, join_date) VALUES
    ('Ana', 'Silva', 'ana.silva@example.com', '2026-09-01'),
    ('Bruno', 'Costa', 'bruno.costa@example.com', '2026-09-01'),
    ('Carla', 'Mendes', 'carla.mendes@example.com', '2026-09-03');

-- Loans: five returned (two of them late) and two still checked out.
-- Each book and member is looked up by title and email.
INSERT INTO loans (book_id, member_id, checkout_date, due_date, return_date, late_fee)
SELECT b.book_id, m.member_id, '2026-09-02', '2026-09-16', '2026-09-14', 0.00
FROM books AS b, members AS m
WHERE b.title = '1984' AND m.email = 'ana.silva@example.com'
  AND NOT EXISTS (SELECT 1 FROM loans WHERE checkout_date = '2026-09-02');

INSERT INTO loans (book_id, member_id, checkout_date, due_date, return_date, late_fee)
SELECT b.book_id, m.member_id, '2026-09-05', '2026-09-19', '2026-09-18', 0.00
FROM books AS b, members AS m
WHERE b.title = 'Murder on the Orient Express' AND m.email = 'bruno.costa@example.com'
  AND NOT EXISTS (SELECT 1 FROM loans WHERE checkout_date = '2026-09-05');

INSERT INTO loans (book_id, member_id, checkout_date, due_date, return_date, late_fee)
SELECT b.book_id, m.member_id, '2026-09-20', '2026-10-04', '2026-10-09', 1.25
FROM books AS b, members AS m
WHERE b.title = 'To Kill a Mockingbird' AND m.email = 'ana.silva@example.com'
  AND NOT EXISTS (SELECT 1 FROM loans WHERE checkout_date = '2026-09-20');

INSERT INTO loans (book_id, member_id, checkout_date, due_date, return_date, late_fee)
SELECT b.book_id, m.member_id, '2026-09-25', '2026-10-09', '2026-10-19', 2.50
FROM books AS b, members AS m
WHERE b.title = 'And Then There Were None' AND m.email = 'bruno.costa@example.com'
  AND NOT EXISTS (SELECT 1 FROM loans WHERE checkout_date = '2026-09-25');

INSERT INTO loans (book_id, member_id, checkout_date, due_date, return_date, late_fee)
SELECT b.book_id, m.member_id, '2026-10-01', '2026-10-15', '2026-10-12', 0.00
FROM books AS b, members AS m
WHERE b.title = 'Animal Farm' AND m.email = 'carla.mendes@example.com'
  AND NOT EXISTS (SELECT 1 FROM loans WHERE checkout_date = '2026-10-01');

INSERT INTO loans (book_id, member_id, checkout_date, due_date)
SELECT b.book_id, m.member_id, '2026-10-10', '2026-10-24'
FROM books AS b, members AS m
WHERE b.title = '1984' AND m.email = 'carla.mendes@example.com'
  AND NOT EXISTS (SELECT 1 FROM loans WHERE checkout_date = '2026-10-10');

INSERT INTO loans (book_id, member_id, checkout_date, due_date)
SELECT b.book_id, m.member_id, '2026-10-20', '2026-11-03'
FROM books AS b, members AS m
WHERE b.title = 'The Silmarillion' AND m.email = 'ana.silva@example.com'
  AND NOT EXISTS (SELECT 1 FROM loans WHERE checkout_date = '2026-10-20');