function(doc) { 
    // find encounters in patients 
    if (doc.doc_type == "CPatient")
    {
        for (i in doc.encounters) {
            enc = doc.encounters[i];
            emit(enc._id, enc);
        }
    }
}