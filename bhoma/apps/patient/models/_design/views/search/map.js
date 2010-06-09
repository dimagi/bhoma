function(doc) { 
    if (doc.doc_type == "CPatient") {
        emit(doc.last_name.toLowerCase(), null);
        emit(doc.first_name.toLowerCase(), null);
    }
}