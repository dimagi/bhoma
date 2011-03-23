function(doc) {
    // !code util/dates.js
    if (doc.doc_type == "SyncLog") {
        for (i in doc.cases) {
            emit([doc.chw_id, doc.cases[i]], iso_date_string(new Date(doc.date)));
        }
    }
}