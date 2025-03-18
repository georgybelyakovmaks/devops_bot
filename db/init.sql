-- Создаем пользователя для репликации
CREATE USER repl_user WITH REPLICATION ENCRYPTED PASSWORD '1234';


-- Подключаемся к базе данных ptstart, если она существует
\c ptstart

-- Создаем таблицу emails, если она не существует
CREATE TABLE IF NOT EXISTS emails (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL
);

-- Создаем таблицу phone_numbers, если она не существует
CREATE TABLE IF NOT EXISTS phone_numbers (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL
);

