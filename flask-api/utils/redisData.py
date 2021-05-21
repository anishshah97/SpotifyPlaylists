import os
import pickle

import redis

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# TODO: geenralize how to tell if data from redis was pickled and stored or just stored
def get_redis_data(data_path):
    data = r.get(data_path)
    if data:
        print(type(data))
        session_data = pickle.loads(data)
    else:
        session_data = data
    return session_data


# NOTE: 86400 seconds = 1 day
def set_redis_data(data_path, data, pkl=True, time_limit=86400):
    if pkl:
        r.set(
            data_path,
            pickle.dumps(data),
            ex=time_limit,
        )
    else:
        r.set(
            data_path,
            data,
            ex=time_limit,
        )
    return True
