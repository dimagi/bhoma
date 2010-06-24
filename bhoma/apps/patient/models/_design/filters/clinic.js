function(doc, req)
{   
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