from django.db.backends.mysql.base import DatabaseWrapper as MySQLDatabaseWrapper


class DatabaseWrapper(MySQLDatabaseWrapper):
    """Allow Django to work with older MariaDB servers used in this environment."""

    def check_database_version_supported(self):
        return None
