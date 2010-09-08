
function(doc) { 
    if (doc.doc_type == "CPatient") {
        for (i in doc.cases) {
            pat_case = doc.cases[i];
            if (!pat_case.closed) {
                emit(doc._id, pat_case);
            }
        }
    }
}