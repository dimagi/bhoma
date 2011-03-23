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

      