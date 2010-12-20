/*
 * Filter for clinic sync.  You query with a parameter
 * called clinic_id and any document belonging to a clinic
 * with that id is matched.  
 */
function(doc, req)
{   
    // HACK: don't sync Exception records back to clinics
    if (doc.doc_type == "ExceptionRecord") {
        return false;
    }
    // check for a singular property called "clinic_id"
    if (doc.clinic_id) {
        if (req.query.clinic_id == doc.clinic_id) {
            return true;
        }
    }
    // or existence in a list property called "clinic_ids"
    if(doc.clinic_ids) {
        for (i in doc.clinic_ids) {
            if(req.query.clinic_id == doc.clinic_ids[i]) {
                return true;
            }
        }
    }
    return false;
}