function(doc) { 
    if (doc.doc_type == "Encounter")
        emit(doc.patient._id, null); 
}