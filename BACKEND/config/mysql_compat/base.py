from django.db.backends.mysql.base import DatabaseWrapper as BaseDatabaseWrapper
from django.db.backends.mysql.features import DatabaseFeatures as MySQLDatabaseFeatures


class DatabaseFeatures(MySQLDatabaseFeatures):
    can_return_id_from_insert = False
    can_return_ids_from_bulk_insert = False
    can_return_columns_from_insert = False


class DatabaseWrapper(BaseDatabaseWrapper):
    """Allow Django to work with older MariaDB servers used in this environment."""
    features_class = DatabaseFeatures

    def check_database_version_supported(self):
        return None
