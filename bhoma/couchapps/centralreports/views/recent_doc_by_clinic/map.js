function(doc) { 
  // !code util/dates.js
  
  var parsedate = function (dt) {
    var dobj = parse_iso_date(dt);
    if (dobj) {
      return dobj.getTime() / 1000.;
    } else {
      return null;
    }
  }

  if (doc.doc_type == "ExceptionRecord") {
    var dt = parsedate(doc.date);
    if (dt) {
      emit(doc.clinic_id, dt);
    }
  } else if (doc.doc_type == "CXFormInstance") {
    if (!(doc.meta && doc.meta.DeviceID)) { //lame attempt to weed out commcare forms
      var dt = parsedate(doc['#received_on']);
      if (dt) {
        for (var i = 0; i < doc.clinic_ids.length; i++) {
          emit(doc.clinic_ids[i], dt);
        }
      }
    }
  }
}