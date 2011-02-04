function(doc) { 
    // !code util/xforms.js
    CLINIC_REFERRAL_NAMESPACES = ["http://cidrz.org/bhoma/general", 
                                  "http://cidrz.org/bhoma/sick_pregnancy",
                                  "http://cidrz.org/bhoma/underfive",
                                  "http://cidrz.org/bhoma/delivery"];
    if (doc["#doc_type"] == "XForm" && CLINIC_REFERRAL_NAMESPACES.indexOf( doc["@xmlns"] ) != -1) {
        if (doc.chw_referral_id) {
            emit(doc.chw_referral_id, 1);    
        }
    } 
}