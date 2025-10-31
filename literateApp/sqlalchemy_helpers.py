from sqlalchemy import create_engine, engine


# def sqlalchemy_db_init(driver_name, user, password, host, port, db_name, pool_size=5, max_overflow=2, pool_timeout=60,
#                        pool_recycle=1800):
#     pool = create_engine(
#         engine.url.URL.create(
#             drivername=driver_name,
#             username=user,
#             password=password,
#             host=host,
#             port=port,
#             database=db_name,
#         ),
#         pool_size=pool_size,
#         max_overflow=max_overflow,
#         pool_timeout=pool_timeout,
#         pool_recycle=pool_recycle,
#     )
#     return pool


def sqlalchemy_db_init(
    driver_name,
    user,
    password,
    host,
    port,
    db_name,
    pool_size=5,
    max_overflow=2,
    pool_timeout=60,
    pool_recycle=1800,
):
    url = engine.URL.create(
        drivername=driver_name,
        username=user,
        password=password,
        host=host,
        port=port,
        database=db_name,
        query={"sslmode": "require"}  # <-- add this
    )

    pool = create_engine(
        url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
    )
    return pool

def return_dict(query):
    return [q.__dict__ for q in query]