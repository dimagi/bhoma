function(keys, values, rereduce) {
  // !code util/dates.js
    
  // according to https://developer.mozilla.org/en/JavaScript/Reference/Global_Objects/Date
  // and http://stackoverflow.com/questions/3009810/php-mysql-javascript-mindate-and-maxdate
  // this is the biggest date in javascript.  we probably could get away with 9999
  var cur_min = new Date( 100000000*86400000);  
  for (i in values) {
     dt = parse_iso_date(values[i]);
     if (dt < cur_min) {
        cur_min = dt;
     }
  }
  return cur_min;
}