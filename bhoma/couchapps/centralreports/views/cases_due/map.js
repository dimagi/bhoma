
function(doc) { 
    // CommCareCases (for the phone) by clinic and zone and date due
    
    // !code util/dates.js
    // !code util/xforms.js
    
    var i, j, pat_case, cc_case, chosen_case, due_date;
    if (doc.doc_type == "CPatient") {
        for (i = 0; i < doc.cases.length; i++) {
            pat_case = doc.cases[i];
            if (!pat_case.closed && pat_case.send_to_phone) {
                for (j = 0; j < pat_case.commcare_cases.length; j++) {
                    cc_case = pat_case.commcare_cases[j];
                    if (!cc_case.closed) {
                        // if we ever find more than one open subcase, emit
                        // the most recently opened one
                        chosen_case = chosen_case ? 
                            (chosen_case.opened_on > cc_case.opened_on ? chosen_case : cc_case) :
                            cc_case;
                    }
                    if (chosen_case) {
                        due_date = parse_date(chosen_case.due_date);
                        emit([doc.address.clinic_id, doc.address.zone, due_date.getFullYear(), 
                              due_date.getMonth(), due_date.getDate()], 1);
                    }        
                    
                }
            }
        }
    }
}