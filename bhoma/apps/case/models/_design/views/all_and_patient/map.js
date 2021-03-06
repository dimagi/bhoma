function(doc) {
    /* Lists case documents that are found both within patients and as a part
       of freestanding documents 
     */
    
    // Root case documents
    if (doc.doc_type == "CommCareCase") {
        emit(doc._id, doc);
    }
    // patients 
    else if (doc.doc_type == "CPatient")
    {
        for (i in doc.cases) {
            pat_case = doc.cases[i];
            emit(pat_case._id, pat_case);
        }
    }
}