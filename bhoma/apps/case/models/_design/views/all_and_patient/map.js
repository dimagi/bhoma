function(doc) {
    /* Lists case documents that are found both within patients and as a part
       of freestanding documents 
     */
    
    // Root case documents
    if (doc.doc_type == "CCase") {
        emit(doc.case_id, doc);
    }
    // patients 
    else if (doc.doc_type == "CPatient")
    {
        for (i in doc.cases) {
            pat_case = doc.cases[i];
            emit(pat_case.case_id, pat_case)
        }
    }
}