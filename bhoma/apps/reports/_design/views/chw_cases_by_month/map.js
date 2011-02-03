function(doc) { 
    // !code util/xforms.js
    if (doc.doc_type == "CPatient") {
        for (i in doc.cases) {
            pat_case = doc.cases[i];
            for (j in pat_case.commcare_cases) {
                cc_case = pat_case.commcare_cases[j];
                date = parse_date(cc_case.due_date);
                emit([doc.address.clinic_id, doc.address.zone, date.getFullYear(), date.getMonth()], 1);
            }
        }
    }
}