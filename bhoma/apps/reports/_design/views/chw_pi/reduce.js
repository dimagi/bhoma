function (keys, values) {
    totals = {};
    for (var i = 0; i < values.length; i++) {
        result = values[i];
        for (var prop in result) {
            if (result.hasOwnProperty(prop)) {
                if (!totals.hasOwnProperty(prop)) {
                    totals[prop] = 0;
                }
                if (result[prop]) {
                    totals[prop] += 1;
                }
            }
        }
    }
    return totals;
}