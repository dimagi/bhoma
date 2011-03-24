function(doc) {
    // !code util/dates.js
    if (doc.doc_type == "SyncLog") {
        for (i in doc.cases) {
            emit([doc.chw_id, doc.cases[i]], doc.date);
        }
    }
}