function(doc) { 
    if (doc.doc_type == "CPatient" && doc._conflicts) 
        emit(doc._id, null); 
}