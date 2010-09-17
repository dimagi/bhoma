function(doc) { 
    if (doc.doc_type == "ExceptionRecord" && !doc.archived)
    {
        emit([doc.clinic_id, new Date(doc.date)], doc);
    }
}