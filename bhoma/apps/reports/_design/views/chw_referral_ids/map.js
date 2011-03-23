function(doc) {
    // !code util/dates.js
    // !code util/xforms.js
    // !code util/referrals.js
    
    if (might_have_referral(doc)) {
        var date = get_encounter_date(doc);
        if (!date) {
            date = Date();
        }
        var ref_ids = get_referral_ids(doc);
        for (i in ref_ids) {
            if (ref_ids[i]) {
                emit([doc.meta.user_id, date.getFullYear(), date.getMonth()], clean_referral_id(ref_ids[i]));
            }
        }
    }
}