function(doc) {
    // !code util/dates.js
    // !code util/xforms.js
    
    // for now incude all non-device-reports in this report
    if (doc["#doc_type"] == "XForm" && 
        doc["@xmlns"] != "http://code.javarosa.org/devicereport")
    {   
        date = get_encounter_date(doc);
        if (!date) {
            date = Date();
        }
        emit([doc.meta.user_id, doc["@xmlns"], date.getFullYear(), date.getMonth(), date.getDate()], 1);
    }
}