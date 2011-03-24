/* ISO Format our dates.
   Stolen from Mozilla.
   https://developer.mozilla.org/en/Core_JavaScript_1.5_Reference:Global_Objects:Date
 */
function iso_date_string(d){
    function pad(n){ return n<10 ? '0'+n : n}
    if (d) {
	   return d.getUTCFullYear()+'-'
		          + pad(d.getUTCMonth()+1)+'-'
			      + pad(d.getUTCDate())+'T'
			      + pad(d.getUTCHours())+':'
			      + pad(d.getUTCMinutes())+':'
			      + pad(d.getUTCSeconds())+'Z'
	}
	return null;
}
      
// parse a date in yyyy-mm-dd format
function parse_date(date_string) {
    // hat tip: http://stackoverflow.com/questions/2587345/javascript-date-parse
    if (date_string) {
        var parts = date_string.match(/(\d+)/g);
        // new Date(year, month [, date [, hours[, minutes[, seconds[, ms]]]]])
        return new Date(parts[0], parts[1]-1, parts[2]); // months are 0-based
    }
}


function parse_iso_date(str) {
    function parse_manual(str) {
	    // hat tip: http://anentropic.wordpress.com/2009/06/25/javascript-iso8601-parser-and-pretty-dates/
	    // we assume str is a UTC date ending in 'Z'
		
		var parts = str.split('T'),
			dateParts = parts[0].split('-'),
			timeParts = parts[1].split('Z'),
			timeSubParts = timeParts[0].split(':'),
			timeSecParts = timeSubParts[2].split('.'),
			timeHours = Number(timeSubParts[0]),
		    _date = new Date();
		
		_date.setUTCFullYear(Number(dateParts[0]));
		_date.setUTCMonth(Number(dateParts[1])-1);
		_date.setUTCDate(Number(dateParts[2]));
		_date.setUTCHours(Number(timeHours));
		_date.setUTCMinutes(Number(timeSubParts[1]));
		_date.setUTCSeconds(Number(timeSecParts[0]));
		if (timeSecParts[1]) _date.setUTCMilliseconds(Number(timeSecParts[1]));
		
		// by using setUTC methods the date has already been converted to local time(?)
		return _date;
	}
	if (isNaN(new Date(str))) {
	   return parse_manual(str);
	}
	return new Date(str);
}