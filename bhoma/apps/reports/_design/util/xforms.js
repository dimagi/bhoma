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
    try {
        return basestring && basestring.indexOf(searchstring) >= 0;
    } catch(err) {
        // oops.  this might not have been a string.
        log("There's a problem checking for " + searchstring + " in " + basestring + ". The searched string is likely not a string");
        return false;
    }
}

function get_date_string(xform_doc) {
	// check some expected places for a date
	if (xform_doc.encounter_date) return xform_doc.encounter_date;
	if (xform_doc.date) return xform_doc.date;
    if (xform_doc.meta && xform_doc.meta.TimeEnd) return xform_doc.meta.TimeEnd;
	if (xform_doc.meta && xform_doc.meta.TimeStart) return xform_doc.meta.TimeStart;
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

function get_encounter_date(xform_doc) {
    date_str = get_date_string(xform_doc);
    if (date_str) {
        return parse_date(date_str);
    }
    return null;
}

function get_form_filled_duration(xform_doc) {
    // in milliseconds
    if (xform_doc.meta && xform_doc.meta.TimeEnd && xform_doc.meta.TimeStart) 
        return new Date(xform_doc.meta.TimeEnd).getTime() - new Date(xform_doc.meta.TimeStart).getTime(); 
    return null;
}

function get_form_filled_date(xform_doc) {
    if (xform_doc.meta && xform_doc.meta.TimeEnd) return new Date(xform_doc.meta.TimeEnd);
    if (xform_doc.meta && xform_doc.meta.TimeStart) return new Date(xform_doc.meta.TimeStart);
    return null;
}