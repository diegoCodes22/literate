import sqlalchemy


def access_secret_version(secret_version_id):
    from google.cloud import secretmanager

    client = secretmanager.SecretManagerServiceClient()
    response = client.access_secret_version(name=secret_version_id)

    return response.payload.data.decode('UTF-8')


def connect_unix_socket():
    db_user = access_secret_version("projects/431781277218/secrets/literate-db-user/versions/1")
    db_pass = access_secret_version("projects/431781277218/secrets/literate-db-pass/versions/1")
    db_name = "literate-db"
    db_socket_dir = "/cloudsql"
    cloud_sql_connection_name = "literate-c0532:us-central1:literate-db"

    pool = sqlalchemy.create_engine(
        sqlalchemy.engine.url.URL.create(
            drivername="mysql+pymysql",
            username=db_user,
            password=db_pass,
            database=db_name,
            query={"unix_socket": f"{db_socket_dir}/{cloud_sql_connection_name}"},
        ),
        # [START_EXCLUDE]
        # Pool size is the maximum number of permanent connections to keep.
        pool_size=15,

        # Temporarily exceeds the set pool_size if no connections are available.
        max_overflow=10,

        # The total number of concurrent connections for your application will be
        # a total of pool_size and max_overflow.

        # 'pool_timeout' is the maximum number of seconds to wait when retrieving a
        # new connection from the pool. After the specified amount of time, an
        # exception will be thrown.
        pool_timeout=60,  # 60 seconds

        # 'pool_recycle' is the maximum number of seconds a connection can persist.
        # Connections that live longer than the specified amount of time will be
        # re-established
        pool_recycle=1800,  # 30 minutes
        # [END_EXCLUDE]
        )
    return pool
