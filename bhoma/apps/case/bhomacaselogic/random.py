import math

MAX = math.pow(2, 32)
    
def predictable_random(hash, probability):
    """
    From a hex hash (e.g. sha1) map to a function that returns true
    with probability equal to what is passed in. 
    
    probability is an argument between 0 and 1.
    """
    assert(0 <= probability and probability <= 1)
    assert(len(hash) >= 8)
    tail = hash[-8:]
    inttail = int(tail, 16)
    return inttail / MAX < probability