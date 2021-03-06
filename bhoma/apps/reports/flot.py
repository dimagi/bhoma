from collections import defaultdict
import json
from dimagi.utils.parsing import string_to_datetime
import time

class PieChart(object):
    """Hold pie chart data"""
    
    def to_json(self):
        pass
    
    def to_html(self):
        pass
    

def date_to_flot_time(inputdate):
    return time.mktime(inputdate.timetuple()) * 1000
    
def get_cumulative_counts(data):
    # <3 python
    daily_data = sorted([[date_to_flot_time(item), data.count(item)] for item in set(data)], key=lambda x: x[0])
    cumulative_data = [[daily_data[i][0], sum([item[1] for item in daily_data[:i + 1]])] for i in range(len(daily_data))]
    return (json.dumps(daily_data),json.dumps(cumulative_data))
    
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