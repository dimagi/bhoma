function(doc) {
    /** List XForm Ids that contain cases, by case id **/
    if (doc["#doc_type"] == "XForm") {
        // TODO: make this recursive
        if (doc["case"]) {
            case_obj = doc["case"];
            emit(case_obj.case_id, doc._id);
        }
    }
}