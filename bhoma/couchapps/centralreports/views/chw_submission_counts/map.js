function(doc) { 
    // !code util/dates.js
    // !code util/xforms.js
    
    function get_user_id(xform_doc) {
        if (xform_doc.meta) return xform_doc.meta.user_id; 
    }
    
    if (doc["#doc_type"] == "XForm" && get_user_id(doc) != null) {
        date = new Date(Date.parse(doc['#received_on']));
        if (date) {
            emit([get_user_id(doc), date.getFullYear(), date.getMonth(), date.getDate()], 1);    
        }
        
    } 
}