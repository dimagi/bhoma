function(doc) { 
    if (doc.doc_type == "CPatient") {
        emit([doc.last_name.toUpperCase(), doc.first_name.toUpperCase()], null);
    }
}
