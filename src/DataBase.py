import mysql.connector as sql


class Database:

    class SELECT:
        def __init__(self, cols: tuple) -> None:
            self.query = "SELECT " + ", ".join(cols)

        def FROM(self, table_name: str):
            self.query += "\nFROM " + table_name
            return self

        def WHERE(self, condition: str):
            self.query += "\nWHERE " + condition
            return self

        def GROUP_BY(self, cols: tuple):
            self.query += "\nGROUP BY " + ", ".join(cols)
            return self

        def HAVING(self, condition: str):
            self.query += "\nHAVING " + condition
            return self

        def ORDER_BY(self, cols: tuple):
            self.query += "\nORDER BY " + ", ".join(cols)
            return self

    def __init__(self, host: str, user: str,
                 password: str, database: str) -> None:
        self.connection = sql.connect(
            host=host, user=user,
            password=password, database=database)

    def CREATE_TABLE(self, table_name: str, *args):
        cols = [" ".join(i) for i in args]
        create_table_query = "CREATE TABLE {0}({1})".format(
            table_name, ",\n".join(cols))
        with self.connection.cursor() as cursor:
            cursor.execute(create_table_query)
            self.connection.commit()

    def DESCRIBE(self, table_name: str):
        show_table_query = "DESCRIBE " + table_name
        with self.connection.cursor() as cursor:
            cursor.execute(show_table_query)
            result = cursor.fetchall()
            for row in result:
                print(row)

    def DROP_TABLE(self, table_name: str):
        drop_table_query = "DROP TABLE " + table_name
        with self.connection.cursor() as cursor:
            cursor.execute(drop_table_query)

    def REPLACE(self, table_name: str, cols: tuple, *args):
        values = ",\n".join([str(i) for i in args])
        cols = "(" + ", ".join(cols) + ")"
        insert_movies_query = "REPLACE INTO {0} {1} VALUES {2}".format(
            table_name, cols, values)
        with self.connection.cursor() as cursor:
            cursor.execute(insert_movies_query)
            self.connection.commit()

    def DELETE(self, table_name: str, where: str):
        query = "DELETE FROM " + table_name + \
            " " + " WHERE " + where
        with self.connection.cursor() as cursor:
            cursor.execute(query)
            self.connection.commit()

    def get_SELECT(self, query: SELECT) -> list:
        with self.connection.cursor() as cursor:
            cursor.execute(query.query)
            return list(cursor.fetchall())