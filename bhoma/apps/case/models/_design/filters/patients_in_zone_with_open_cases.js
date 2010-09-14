function(doc, req)
{   
    
    if(!req.query.clinic_id) {
        throw("Please provide a query parameter 'clinic_id'.");
    }
    if(!req.query.zone) {
        throw("Please provide a query parameter 'zone'.");
    }

    if (doc.doc_type == "CPatient") {
        
        matches_clinic = function(doc, clinic_id) {
            if(clinic_id && doc.clinic_ids) {
                for (i in doc.clinic_ids) {
                    if(req.query.clinic_id == doc.clinic_ids[i]) {
                        return true;
                    }
                }
            }
            return false;
        }
        
        matches_zone = function(doc, zone) {
            return zone && doc.address.zone == zone;
        }
        
        has_open_case = function(doc) {
	        for (i in doc.cases) {
	            pat_case = doc.cases[i];
	            if (!pat_case.closed) {
	                return true;
	            }
	        }
	        return false;
        }
        
        zone = req.query.zone;
        clinic_id = req.query.clinic_id;
        return (matches_clinic(doc, clinic_id) && matches_zone(doc, zone) && has_open_case(doc));
    }
    return false;
}