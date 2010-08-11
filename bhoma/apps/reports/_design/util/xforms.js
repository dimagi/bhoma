/*
 * This module has utilities for working with xforms
 */


/*
 * use this to make sure you loaded the reports module properly
 */

function hello_xforms() {
    log("hello xforms!");
}

function xform_matches(doc, namespace) {
    return doc["#doc_type"] == "XForm" && doc["@xmlns"] == namespace;
}

var exists = function(basestring, searchstring) {
    return basestring && basestring.indexOf(searchstring) >= 0;
}

// parse a date in yyyy-mm-dd format
function parse_date(date_string) {
    // hat tip: http://stackoverflow.com/questions/2587345/javascript-date-parse    
    var parts = date_string.match(/(\d+)/g);
    // new Date(year, month [, date [, hours[, minutes[, seconds[, ms]]]]])
    return new Date(parts[0], parts[1]-1, parts[2]); // months are 0-based
}
     

function get_encounter_date(xform_doc) {
    return parse_date(xform_doc.encounter_date);
}