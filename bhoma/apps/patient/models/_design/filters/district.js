/*
 * Filter for district sync.  You query with a parameter
 * called clinic_ids which is a pipe ("|") separated list, 
 * and any document belonging to a clinic with one of those 
 * ids is matched.  The caller (district) is responsible for 
 * knowing their clinics.
 */
function(doc, req)
{   
    clinic_ids = req.query.clinic_ids.split("|");
    for (i in  clinic_ids) {
        req_clinic = clinic_ids[i];
        // check for a singular property called "clinic_id"
	    if (doc.clinic_id) {
	        if (req_clinic == doc.clinic_id) {
	            return true;
	        }
	    }
	    // or existence in a list property called "clinic_ids"
	    if(doc.clinic_ids) {
	        for (i in doc.clinic_ids) {
	            if(req_clinic == doc.clinic_ids[i]) {
	                return true;
	            }
	        }
	    }
	    
    }
    return false;
}