function(doc) {
    // !code util/xforms.js
    if (doc["#doc_type"] == "XForm" && doc["@xmlns"] == "http://cidrz.org/bhoma/new_clinic_referral") {
        date = get_encounter_date(doc);
        if (!date) {
            date = Date();
        }
        // we remove hyphens because the clinic system doesn't expect them        
        emit([doc.meta.user_id, date.getFullYear(), date.getMonth()], doc.chw_referral_id.replace(/-/g, ""));            
    }
}