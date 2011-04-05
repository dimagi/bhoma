function(doc) { 
    // !code util/dates.js
    // !code util/reports.js
    // !code util/xforms.js
    
    var NAMESPACE = "http://cidrz.org/bhoma/chw_followup";
    
    if (xform_matches(doc, NAMESPACE))
    {   
        enc_date = get_encounter_date(doc);
        if (enc_date == null)  {
            log("encounter date not found in doc " + doc._id + ". Will not be counted in reports");
            return;
        }
        if (doc.case != null && doc.case.update != null)
        {
            emit([doc.meta.user_id, date.getFullYear(), date.getMonth(),
                  doc.case.update.bhoma_close, doc.case.update.bhoma_outcome], 1);
        }
    }
}