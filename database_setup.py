#!/usr/bin/env python3
import psycopg2

def create_tables():
    """create tables in database"""
    commands = (
    """
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL
    )
    """,
    """
    CREATE TABLE categories (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL
    )
    """,
    """
    CREATE TABLE categoryitems (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description VARCHAR(1000),
        category_id INTEGER,
        user_id INTEGER,
        FOREIGN KEY (category_id)
            REFERENCES categories (id)
            ON UPDATE CASCADE ON DELETE CASCADE,
        FOREIGN KEY (user_id)
            REFERENCES users (id)
            ON UPDATE CASCADE ON DELETE CASCADE
    )
    """
    )

    conn = None
    try:
        conn = psycopg2.connect(database="catalog", user="catalog", password="catalog")
        cur = conn.cursor()
        for command in commands:
            cur.execute(command)
            conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    create_tables()
