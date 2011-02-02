    function(doc) {
    // these lines magically import our other javascript files.  DON'T REMOVE THEM!
    // !code util/xforms.js
    
    // for now incude all non-device-reports in this report
    if (doc["#doc_type"] == "XForm" && 
        doc["@xmlns"] != "http://code.javarosa.org/devicereport")
    {
        emit([doc.meta.user_id, get_encounter_date(doc), ], 1);
    }
}