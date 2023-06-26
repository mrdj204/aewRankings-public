"""
Module for interacting with a SQL Server database using pymssql.

This module contains a class called SQLDatabase which allows for
interactions with a SQL Server database. The class can be used to
connect to the database, create tables, delete tables, and perform
other database operations.

Example:
    To use this module, first set the required environment variables
    (DATABASE_SERVER_NAME, DATABASE_NAME, DATABASE_USERNAME, DATABASE_PASSWORD),
    and then instantiate the SQLDatabase class:

    db = SQLDatabase()
    db.create_table("my_table", [("column1", "INT"), ("column2", "VARCHAR(255)")])
    db.close()
"""

import os

import pymssql
from dotenv import load_dotenv


class SQLDatabase:
    """
    A class used to represent and interact with a SQL Server database.

    ...

    Attributes
    ----------
    cnxn : pymssql.Connection
        A connection to the SQL Server database.
    cursor : pymssql.Cursor
        A cursor object used for executing SQL queries.

    Methods
    -------
    close():
        Close the database connection.
    delete_all_tables():
        Delete all tables in the database.
    create_table(table_name: str, columns: list, drop: bool = False):
        Create a new table in the database.
    list_tables() -> list:
        List all tables in the database.
    remake_user_activity_table():
        Create or re-create the UserActivity table.
    add_user_activity(server_ip: str, user: str, date: str, page: str):
        Add a new user activity to the UserActivity table.
    get_all_user_activity() -> str:
        Retrieve all user activity records from the UserActivity table.
    get_all_user_activity_html() -> str:
        Retrieve all user activity records from the UserActivity table in HTML format.
    remake_rankings_submissions_table():
        Create or re-create the RCV_submissions table for rankings submissions.
    clear_rankings_submissions(user: str) -> bool:
        Clear rankings submissions for a specific user, keeping only their submission.
    check_rankings_submission(user: str) -> bool:
        Check if a user has submitted rankings.
    add_rankings_submission(date: str, user: str, data: dict) -> bool:
        Add or update rankings submission for a user.
    update_rankings_submission(user: str, data: dict) -> bool:
        Update the rankings submission for a user.
    get_user_rankings_submission(user: str) -> dict:
        Retrieve the rankings submission for a specific user.
    get_all_rankings_submissions() -> dict:
        Retrieve all rankings submissions.
    get_all_rankings_submissions_html() -> str:
        Retrieve all rankings submissions in HTML format.
    """

    def __init__(self):
        """
        Initialize the database connection using environment variables.

        Raises:
            ValueError: If required database configuration environment variables are not set.
        """
        load_dotenv()
        # Define connection parameters
        server_name = os.environ.get("DATABASE_SERVER_NAME")
        database_name = os.environ.get("DATABASE_NAME")
        username = os.environ.get("DATABASE_USERNAME")
        password = os.environ.get("DATABASE_PASSWORD")

        # Check environment variables
        if not all([server_name, database_name, username, password]):
            raise ValueError("Database configuration environment variables are not set")

        # Establish database connection
        self.cnxn = pymssql.connect(server=server_name, user=username, password=password, database=database_name)

        # Create a cursor for executing SQL queries
        self.cursor = self.cnxn.cursor()

        self.rcv_cols = [
            # Columns for the RCV_submissions table
            ("datetime", "DATETIME"),
            ("username", "VARCHAR(255)"),
            ("AEW_World_Title_1", "VARCHAR(255)"),
            ("AEW_World_Title_2", "VARCHAR(255)"),
            ("AEW_World_Title_3", "VARCHAR(255)"),
            ("AEW_TNT_Title_1", "VARCHAR(255)"),
            ("AEW_TNT_Title_2", "VARCHAR(255)"),
            ("AEW_TNT_Title_3", "VARCHAR(255)"),
            ("AEW_International_Title_1", "VARCHAR(255)"),
            ("AEW_International_Title_2", "VARCHAR(255)"),
            ("AEW_International_Title_3", "VARCHAR(255)"),
            ("AEW_World_Tag_Team_Titles_1", "VARCHAR(255)"),
            ("AEW_World_Tag_Team_Titles_2", "VARCHAR(255)"),
            ("AEW_World_Tag_Team_Titles_3", "VARCHAR(255)"),
            ("AEW_World_Trios_Titles_1", "VARCHAR(255)"),
            ("AEW_World_Trios_Titles_2", "VARCHAR(255)"),
            ("AEW_World_Trios_Titles_3", "VARCHAR(255)"),
            ("AEW_Womens_World_Title_1", "VARCHAR(255)"),
            ("AEW_Womens_World_Title_2", "VARCHAR(255)"),
            ("AEW_Womens_World_Title_3", "VARCHAR(255)"),
            ("AEW_TBS_Title_1", "VARCHAR(255)"),
            ("AEW_TBS_Title_2", "VARCHAR(255)"),
            ("AEW_TBS_Title_3", "VARCHAR(255)")
        ]

    def close(self):
        """
        Close the database connection.
        """
        self.cnxn.close()

    def delete_all_tables(self):
        """
        Delete all tables in the database.
        """
        # SQL query to retrieve all table names in the database
        query = "SELECT table_name FROM information_schema.tables WHERE " \
                "table_type = 'BASE TABLE' AND table_schema = 'dbo'"

        # Call the execute_query function to execute the query and fetch all table names
        self.cursor.execute(query)
        table_names = self.cursor.fetchall()

        # Loop through the table names and drop each table
        for table_name in table_names:
            query = f"DROP TABLE {table_name[0]}"
            self.cursor.execute(query)
            self.cnxn.commit()

    def create_table(self, table_name, columns, drop=False):
        """
        Create a table in the database.

        Args:
            table_name (str): The name of the table to create.
            columns (list): List of tuples with column names and data types.
            drop (bool, optional): If True, drop the table if it exists. Defaults to False.
        """
        if drop:
            query = f"IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP TABLE {table_name};"
            self.cursor.execute(query)
            self.cnxn.commit()

        query = f"CREATE TABLE {table_name} ("
        for column in columns:
            column_name, column_type = column
            query += f"{column_name} {column_type}, "
        query = query.rstrip(", ")
        query += ")"

        self.cursor.execute(query)
        self.cnxn.commit()

    def list_tables(self) -> list:
        """
        List all tables in the database.

        Returns:
            list[str]: A list of table names.
        """
        query = "SELECT name FROM sys.tables"
        self.cursor.execute(query)
        result = self.cursor.fetchall()
        return [row.name for row in result]

    def remake_user_activity_table(self):
        """
        Create or re-create the UserActivity table.
        """
        cols = [
            ('id', 'INT IDENTITY(1,1) PRIMARY KEY'),
            ('SERVER_IP', "VARCHAR(255)"),
            ("activity_date", "VARCHAR(255)"),
            ("username", "VARCHAR(255)"),
            ("page", "VARCHAR(255)"),
        ]
        self.create_table("UserActivity", cols, True)

    def add_user_activity(self, server_ip, user, date, page):
        """
        Add a new user activity to the UserActivity table.

        Args:
            server_ip (str): The server IP associated with the activity.
            user (str): The username associated with the activity.
            date (str): The date of the activity.
            page (str): The page accessed during the activity.
        """
        # SQL query to insert a new row into UserActivity table
        query = f"INSERT INTO UserActivity (SERVER_IP, activity_date, username, page) " \
                f"VALUES ('{server_ip}', '{date}', '{user}', '{page}')"

        # Call the self.cursor.execute method with query and parameter values
        self.cursor.execute(query)

        # Commit the transaction to persist the changes
        self.cnxn.commit()

    def get_all_user_activity(self) -> str:
        """
        Retrieve all user activity records from the UserActivity table.

        Returns:
            str: A string representation of the user activity records.
        """
        # SQL query to select all rows from UserActivity table
        query = "SELECT * FROM UserActivity"

        # Call the self.cursor.execute method with query to execute the query
        self.cursor.execute(query)

        # Fetch all rows from the result set and return as a list of tuples
        rows = self.cursor.fetchall()

        # Return the fetched rows as a string
        return "\n".join(["\t".join(row[1:]) for row in rows])

    def get_all_user_activity_html(self) -> str:
        """
        Retrieve all user activity records from the UserActivity table in HTML format.

        Returns:
            str: An HTML representation of the user activity records.
        """
        # SQL query to select all rows from UserActivity table
        query = "SELECT * FROM UserActivity"

        # Call the self.cursor.execute method with query to execute the query
        self.cursor.execute(query)

        # Fetch all rows from the result set and return as a list of tuples
        rows = reversed(self.cursor.fetchall())

        # Generate an HTML table string from the fetched rows
        table_rows = "\n".join([f"<tr><td>{'</td><td>'.join(row[1:])}</td></tr>" for row in rows])
        table = f"""
        <div style="padding:15px">
            <table>
                <caption>Access Logs</caption>
                <tr><th>Server IP</th><th>Date</th><th>User</th><th>Path</th></tr>
                {table_rows}
            </table>
            <div class="centered" style="padding-top: 5px">
                <input type="checkbox" id="db_clear_cb">
                <a class="button" href="#" id="db_clear">Clear</a>
            </div>
        </div>
        """

        # Return the generated HTML string
        return table

    def remake_rankings_submissions_table(self):
        """
        Create or re-create the RCV_submissions table for rankings submissions.
        """
        self.create_table("RCV_submissions", self.rcv_cols, drop=True)

    def clear_rankings_submissions(self, user: str) -> bool:
        """
        Clear rankings submissions for a specific user, keeping only their submission.

        Args:
            user (str): The username for which to clear rankings submissions.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        if not user:
            return False
        query = "DELETE FROM RCV_submissions WHERE username != %s"
        self.cursor.execute(query, (user,))
        self.cnxn.commit()
        return True

    def check_rankings_submission(self, user: str) -> bool:
        """
        Check if a user has submitted rankings.

        Args:
            user (str): The username to check for rankings submission.

        Returns:
            bool: True if the user has submitted rankings, False otherwise.
        """
        # Check if user already exists in RCV_submissions table
        query = f"SELECT username FROM RCV_submissions WHERE username = '{user}'"
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        return bool(result)

    def add_rankings_submission(self, date: str, user: str, data: dict) -> bool:
        """
        Add or update rankings submission for a user.

        If the user has already submitted rankings, the existing submission will be updated.

        Args:
            date (str): The date of the rankings submission.
            user (str): The username associated with the rankings submission.
            data (dict): A dictionary containing the rankings data.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        if self.check_rankings_submission(user):
            return self.update_rankings_submission(user, data)

        # User does not exist, proceed with inserting a new row
        keys = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        values = tuple([date, user] + list(data.values()))
        query = f"INSERT INTO RCV_submissions (datetime, username, {keys}) VALUES (%s, %s, {placeholders})"
        self.cursor.execute(query, values)
        self.cnxn.commit()
        return True

    def update_rankings_submission(self, user: str, data: dict) -> bool:
        """
        Update the rankings submission for a user.

        Args:
            user (str): The username associated with the rankings submission.
            data (dict): A dictionary containing the updated rankings data.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        # Username exists, proceed with updating the row
        keys = ", ".join([f"{key} = %s" for key in data.keys()])
        values = tuple(data.values()) + (user,)
        query = f"UPDATE RCV_submissions SET {keys} WHERE username = %s"
        self.cursor.execute(query, values)
        self.cnxn.commit()
        return True

    def get_user_rankings_submission(self, user: str) -> dict:
        """
        Retrieve the rankings submission for a specific user.

        Args:
            user (str): The username associated with the rankings submission.

        Returns:
            dict: A dictionary containing the rankings submission data.
        """
        # SQL query to select all rows from UserActivity table
        query = f"SELECT * FROM RCV_submissions WHERE username = '{user}'"

        # Call the self.cursor.execute method with query to execute the query
        self.cursor.execute(query)

        # Fetch all rows from the result set and return as a list of tuples
        row = self.cursor.fetchall()[0]

        # Assuming 'rows' is a list of rows fetched from the 'RCV_submissions' table

        row_dict = {}  # Empty dictionary to store the formatted rows

        for col_idx, col_value in enumerate(row):
            col_name = self.rcv_cols[col_idx][0]  # Extract column name from 'rcv_cols' list
            row_dict[col_name] = str(col_value)

        return row_dict

    def get_all_rankings_submissions(self) -> dict:
        """
        Retrieve all rankings submissions.

        Returns:
            dict: A dictionary containing all rankings submissions, with usernames as keys and submission data as values.
        """
        # SQL query to select all rows from UserActivity table
        query = "SELECT * FROM RCV_submissions"

        # Call the self.cursor.execute method with query to execute the query
        self.cursor.execute(query)

        # Fetch all rows from the result set and return as a list of tuples
        rows = self.cursor.fetchall()

        # Assuming 'rows' is a list of rows fetched from the 'RCV_submissions' table

        result_dict = {}  # Empty dictionary to store the formatted rows

        for row in rows:
            user = row[1]  # Assuming 'username' is a column in the fetched rows
            row_dict = {}  # Nested dictionary to store the column names and their values

            for col_idx, col_value in enumerate(row):
                col_name = self.rcv_cols[col_idx][0]  # Extract column name from 'rcv_cols' list
                row_dict[col_name] = str(col_value)

            result_dict[user] = row_dict  # Add the nested dictionary to the result dictionary with 'username' as key

        return result_dict

    def get_all_rankings_submissions_html(self) -> str:
        """
        Retrieve all rankings submissions in HTML format.

        Returns:
            str: An HTML representation of all rankings submissions.
        """
        # SQL query to select all rows from UserActivity table
        query = "SELECT * FROM RCV_submissions"

        # Call the self.cursor.execute method with query to execute the query
        self.cursor.execute(query)

        # Fetch all rows from the result set and return as a list of tuples
        rows = reversed(self.cursor.fetchall())

        # Generate an HTML table string from the fetched rows
        table_rows = "\n".join([f"<tr><td>{'</td><td>'.join(row[1:])}</td></tr>" for row in rows])
        table = f"""
        <div style="padding:15px">
            <table>
                <caption>Rankings Submissions</caption>
                <tr><th>DateTime</th><th>Username</th><th>AEW World Title 1</th><th>AEW World Title 2</th>
                <th>AEW World Title 3</th><th>AEW TNT Title 1</th><th>AEW TNT Title 2</th><th>AEW TNT Title 3</th>
                <th>AEW International Title 1</th><th>AEW International Title 2</th><th>AEW International Title 3</th>
                <th>AEW World Tag Team Titles 1</th><th>AEW World Tag Team Titles 2</th>
                <th>AEW World Tag Team Titles 3</th><th>AEW World Trios Titles 1</th><th>AEW World Trios Titles 2</th>
                <th>AEW World Trios Titles 3</th><th>AEW Women's World Title 1</th>
                <th>AEW Women's World Title 2</th><th>AEW Women's World Title 3</th><th>AEW TBS Title 1</th>
                <th>AEW TBS Title 2</th><th>AEW TBS Title 3</th></tr>
                {table_rows}
            </table>
            <div class="centered" style="padding-top: 5px">
                <input type="checkbox" id="db_clear_cb">
                <a class="button" href="#" id="db_clear">Clear</a>
            </div>
        </div>
        """

        # Return the generated HTML string
        return table
