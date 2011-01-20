function(doc) { 
  if (doc.doc_type == "CPatient") {
    if (doc.first_name && doc.gender) {
      emit(['firstname-' + {m: 'male', f: 'female'}[doc.gender], doc.first_name], 1);
    }
    if (doc.last_name) {
      emit(['lastname', doc.last_name], 1);
    }
    if (doc.address && doc.address.village) {
      emit(['village', doc.address.village], 1);
    }
  }
}
