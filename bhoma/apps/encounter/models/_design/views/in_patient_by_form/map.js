function(doc) { 
    // find encounters in patients, by form id 
    if (doc.doc_type == "CPatient")
    {
        for (i in doc.encounters) {
            enc = doc.encounters[i];
            emit(enc.xform_id, enc);
        }
    }
}