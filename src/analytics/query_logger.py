import sqlite3

from datetime import datetime


class QueryLogger:


    def __init__(self):

        self.conn = sqlite3.connect(
            "query_logs.db",
            check_same_thread=False
        )

        self.create_table()


    def create_table(self):

        cursor = self.conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS query_logs(

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                question TEXT,

                document TEXT,

                timestamp TEXT
            )
            """
        )

        self.conn.commit()


    def log_query(
        self,
        question,
        document
    ):

        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT INTO query_logs
            (
                question,
                document,
                timestamp
            )
            VALUES
            (
                ?,
                ?,
                ?
            )
            """,

            (
                question,
                document,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
        )

        self.conn.commit()


    def get_total_queries(self):

        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM query_logs
            """
        )

        return cursor.fetchone()[0]


    def get_recent_queries(
        self,
        limit=5
    ):

        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT
                question,
                timestamp

            FROM query_logs

            ORDER BY id DESC

            LIMIT ?
            """,

            (limit,)
        )

        return cursor.fetchall()


    def get_document_count(self):

        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(DISTINCT document)
            FROM query_logs
            """
        )

        return cursor.fetchone()[0]


    def get_most_queried_document(self):

        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT
                document,
                COUNT(*) as total

            FROM query_logs

            GROUP BY document

            ORDER BY total DESC

            LIMIT 1
            """
        )

        result = cursor.fetchone()

        return result


    def get_all_logs(self):

        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT
                question,
                document,
                timestamp

            FROM query_logs

            ORDER BY id DESC
            """
        )

        return cursor.fetchall()