function(doc) { 
    if (doc.doc_type == "SyncLog") {
        // note that we don't have to convert this to iso because
        // it's already in JSON format
        emit([doc.chw_id, doc.date], 1);
    }
}