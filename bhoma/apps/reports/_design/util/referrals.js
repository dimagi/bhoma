function clean_referral_id(ref_id) {
        // we remove hyphens because the clinic system doesn't expect them        
        return ref_id.replace(/-/g, "");
}

function might_have_referral(doc) {
    var VALID_NAMESPACES = ["http://cidrz.org/bhoma/new_clinic_referral",
                            "http://cidrz.org/bhoma/household_survey",
                            "http://cidrz.org/bhoma/chw_followup"]; 
    return doc["#doc_type"] == "XForm" && VALID_NAMESPACES.indexOf( doc["@xmlns"] ) != -1; 
}

function get_referral_ids(doc) {
    var ref_ids = [];
    if (doc["@xmlns"] == "http://cidrz.org/bhoma/new_clinic_referral") {
        ref_ids.push(doc.chw_referral_id);
    } else if (doc["@xmlns"] == "http://cidrz.org/bhoma/chw_followup") {
        ref_ids.push(doc.chw_referral_id);
    } else if (doc["@xmlns"] == "http://cidrz.org/bhoma/household_survey") {
        var ppl_sick = extract_repeats[doc.any_sick];
        for (i in ppl_sick) {
            ref_ids.push(ppl_sick[i].chw_referral_id);
        }
    }
    return ref_ids;
}
    
    