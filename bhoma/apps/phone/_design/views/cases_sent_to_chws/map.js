function(doc) {
    if (doc.doc_type == "SyncLog") {
        for (i in doc.cases) {
            if (doc.date) {
                emit([doc.chw_id, doc.cases[i]], doc.date);
            }
        }
    }
}