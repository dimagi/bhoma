function(doc) { 
    // patient docs without export tags
    if (doc.doc_type == "CPatient" && !doc['#export_tag']) {
        emit(doc._id, null);
    }
}