import sqlite3

DB_NAME = "chat_history.db"


# =====================================
# INITIALIZE DATABASE
# =====================================

def init_db():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chats (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        title TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        chat_id INTEGER,

        role TEXT,

        content TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(chat_id)
        REFERENCES chats(id)

    )
    """)

    conn.commit()
    conn.close()



# =====================================
# CREATE CHAT
# =====================================

def create_chat():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM chats"
    )

    count = cursor.fetchone()[0]

    title = f"Chat {count + 1}"

    cursor.execute(
        """
        INSERT INTO chats(title)
        VALUES(?)
        """,
        (title,)
    )

    chat_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return chat_id


# =====================================
# GET ALL CHATS
# =====================================

def get_chats():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, title
        FROM chats
        ORDER BY id DESC
        """
    )

    chats = cursor.fetchall()

    conn.close()

    return chats


# =====================================
# SAVE MESSAGE
# =====================================

def save_message(
    chat_id,
    role,
    content
):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO messages
        (
            chat_id,
            role,
            content
        )
        VALUES
        (
            ?,
            ?,
            ?
        )
        """,
        (
            chat_id,
            role,
            content
        )
    )

    conn.commit()
    conn.close()


# =====================================
# LOAD CHAT MESSAGES
# =====================================

def load_chat_messages(
    chat_id
):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            role,
            content
        FROM messages
        WHERE chat_id = ?
        ORDER BY id
        """,
        (chat_id,)
    )

    rows = cursor.fetchall()

    conn.close()

    return rows


# =====================================
# DELETE CHAT
# =====================================

def delete_chat(
    chat_id
):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM messages
        WHERE chat_id = ?
        """,
        (chat_id,)
    )

    cursor.execute(
        """
        DELETE FROM chats
        WHERE id = ?
        """,
        (chat_id,)
    )

    conn.commit()
    conn.close()


# =====================================
# CLEAR ALL
# =====================================

def clear_all_chats():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM messages"
    )

    cursor.execute(
        "DELETE FROM chats"
    )

    conn.commit()
    conn.close()