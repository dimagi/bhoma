function (keys, values, rereduce) {
    if (!rereduce) {
        return {"sum" : sum(values), "count" : values.length};
    }
    else {
		count = 0;
		sum = 0;
		for (i in values) {
		  count += values[i]['count'];
		  sum += values[i]['sum'];
		}
		return {"sum" : sum, "count" : count};
    }
}