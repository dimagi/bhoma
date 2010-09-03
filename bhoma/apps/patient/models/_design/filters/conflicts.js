function(doc) { 
    return (doc.doc_type == "CPatient" && doc._conflicts); 
}