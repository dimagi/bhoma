function(doc) { 
    // !code util/dates.js
    if (doc.doc_type == "CPatient") {
        for (var i in doc.cases) {
            var pat_case = doc.cases[i];
            for (j in pat_case.commcare_cases) {
                var cc_case = pat_case.commcare_cases[j];
                var date = parse_date(cc_case.due_date);
                emit([doc.address.clinic_id, doc.address.zone, date.getFullYear(), date.getMonth()], 1);
            }
        }
    }
}