function(doc) {
    if (doc["#doc_type"] == "XForm" && doc["@xmlns"] == "http://cidrz.org/bhoma/new_clinic_referral") {
        emit([doc.chw_referral_id.replace(/-/g, "")], null);
    }
}