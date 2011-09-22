function(doc) { 
    /*
     * The search function keys everything very specifically and only
     * returns a match if all terms in the search match. The current
     * list of fields is: gender, lastname, firstname, date of birth,
     * phone number (in that order).
     *  
     * The key you pass in should be any number of these parameters
     * for varying degrees of specificity.
     * 
     * Everything is stripped leading/trailing whitespace and converted
     * to lowercase.
     */
    
    var prepare = function(item) {
        if (item) {
            return item.trim().toLowerCase();
        }
    }
    if (doc.doc_type == "CPatient") {
        
        emit([prepare(doc.gender), 
              prepare(doc.last_name),
              prepare(doc.first_name),
              prepare(doc.birthdate),
              prepare(doc.phones ? doc.phones[0] : "")],
             null);
              
    }
}