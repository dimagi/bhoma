
function(doc) {
    /*
     * get a commcare case from a patient
     */ 
    if (doc.doc_type == "CPatient") {
        for (i in doc.cases) {
            pat_case = doc.cases[i];
            for (i in pat_case.commcare_cases) {
                emit(pat_case.commcare_cases[i]._id, pat_case.commcare_cases[i]);
            }
        }
    }
}