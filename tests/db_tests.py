from literateApp.app import paand
import sqlalchemy


def init_db():
    db_user = "root"
    db_pass = "Prien-21."
    db_name = "mysql-testing"
    db_host = "localhost"
    db_port = 3306
    pool = sqlalchemy.create_engine(
        sqlalchemy.engine.url.URL.create(
            drivername="mysql+pymysql",
            username=db_user,
            password=db_pass,
            host=db_host,
            port=db_port,
            database=db_name,
        ),
        pool_size=5,
        max_overflow=2,
        pool_timeout=60,
        pool_recycle=1800,
    )
    return pool


testing_db = init_db()

