import hashlib

def hash(filename, alg=hashlib.md5, block_size=2**20):
    file = open(filename, "rb")
    try:
        alg_instance = alg()
        while True:
            data = file.read(block_size)
            if not data:
                break
            alg_instance.update(data)
        return alg_instance
    finally:
        file.close()
