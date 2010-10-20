from collections import defaultdict
import json
from bhoma.utils.parsing import string_to_datetime
import time

def date_to_flot_time(inputdate):
    return time.mktime(inputdate.timetuple()) * 1000
    
def get_sparkline_json(data):
    """
    Gets a sparkline plot json data
    """
    # flot expects [[timestamp1, value1], [timestamp2, value2], ...]
    ret_avgs = []
    ret_totals = []
    for date, data_dict in data.items():
        ts = date_to_flot_time(string_to_datetime(date))
        ret_avgs.append([ts, (data_dict["sum"] / data_dict["count"]) / (1000)])
        ret_totals.append([ts, data_dict["count"]])
    ret_avgs = sorted(ret_avgs, key=lambda x: x[0])
    ret_totals = sorted(ret_totals, key=lambda x: x[0])
    return (json.dumps(ret_totals), json.dumps(ret_avgs))

def get_sparkline_extras(data):
    """
    Gets a sparkline plot json extras
    """
    # flot expects [[timestamp1, value1], [timestamp2, value2], ...]
    ret = defaultdict(lambda: defaultdict(lambda: 0))
    for date, data_dict in data.items():
        ret[int(date_to_flot_time(string_to_datetime(date)))] = data_dict
    return json.dumps(ret)