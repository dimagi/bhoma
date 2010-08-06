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
        
        

function get_encounter_date(xform_doc) {
    return new Date(Date.parse(xform_doc.encounter_date));
}