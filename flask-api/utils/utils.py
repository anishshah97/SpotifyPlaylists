import argparse
import logging

log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(format=log_fmt)
logger = logging.getLogger("spotifyApp")
logger.setLevel("DEBUG")


def chunk(data, n):
    return [data[x : x + n] for x in range(0, len(data), n)]


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")
