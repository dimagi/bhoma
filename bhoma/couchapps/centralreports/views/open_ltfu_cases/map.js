function(doc) {
    /* 
       Cases by the date they are lost to follow up.
       This is useful for finding cases that should be marked
       lost to follow-up (e.g. by the cron job that cleans these 
       up each night)
     */
    if (doc.doc_type == "CPatient")
    {
        for (var i in doc.cases) {
            var pat_case = doc.cases[i];
            if (!pat_case.closed && pat_case.ltfu_date) {
                emit(pat_case.ltfu_date, pat_case);
            }
        }
    }
}