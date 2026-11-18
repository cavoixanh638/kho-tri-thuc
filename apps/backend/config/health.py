from django.db import connection


def check_database():
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
