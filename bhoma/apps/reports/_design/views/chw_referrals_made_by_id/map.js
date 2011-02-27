function(doc) {
    // !code util/xforms.js
    // !code util/referrals.js
    if (might_have_referral(doc)) {
        var ref_ids = get_referral_ids(doc);
        for (i in ref_ids) {
            if (ref_ids[i]) {
                emit([clean_referral_id(ref_ids[i])], null);
            }
        }
    }
}