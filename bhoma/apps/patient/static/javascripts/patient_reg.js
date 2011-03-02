
ALLOW_OLD_FORMAT_IDS = true;

function wfGetPatient () {
  var flow = function (data) {
    var new_patient_rec = null;       //any new record created via registration form
    var existing_patient_rec = null;  //any existing record select by the user as belonging to the current patient
    //these fields are not mutually exclusive

    var q_form_type = qSelectReqd('What type of form is this?', zip_choices(['Registration form', 'Other form'], ['reg-form', 'other-form']));
    yield q_form_type;
    var is_reg_form = (q_form_type.value == 'reg-form');
    
    var id_accepted = false;
    var need_to_fill_registration_upfront = is_reg_form;

    //we offer the option to correct a mistakenly entered ID, thus this loop
    while (!id_accepted) {

      //enter patient id
      PATID_LEN = 13;
      var q_pat_id = new wfQuestion({caption: 'Patient ID', type: 'str', required: true,
                                     validation: function (x) { return x.length != PATID_LEN && !(ALLOW_OLD_FORMAT_IDS && x.length == PATID_LEN - 1) ?
                                                                "A valid ID is " + PATID_LEN + " digits (this ID has " + x.length + ")" : null}, 
                                     domain: 'numeric', meta: {mask: 'xxxx-xxx-xxxxx-x', prefix: '_clinic'}});
      yield q_pat_id;
      var patient_id = q_pat_id.value;
      //backwards compatibility: fix old-style 12-digit IDs
      if (patient_id.length == PATID_LEN - 1) {
        patient_id = patient_id.substring(0, 3) + '0' + patient_id.substring(3);
      }

      //retrieve existing matches for that id
      var qr_lookup_pat = new wfAsyncQuery(function (callback) { lookup(patient_id, callback); });
      yield qr_lookup_pat;
      var records_for_id = qr_lookup_pat.value || [];
      //for registration forms we always have them fill out the reg info upfront (but only once even if we re-ask patient id)
      if (need_to_fill_registration_upfront) {
        new_patient_rec = {} //new Patient();
        for (var q in ask_patient_info(new_patient_rec, true)) {
          yield q;
        }
        need_to_fill_registration_upfront = false;
      }
      if (new_patient_rec != null) {
        new_patient_rec.id = patient_id;
      }

      if (!is_reg_form && records_for_id.length == 0) {
        //if not a reg form, give them the option to bail if ID not found

        var q_no_record_found = qSelectReqd('No patient found for ID ' + formatPatID(patient_id), zip_choices(
                                            ['Register as new patient',
                                             'Wrong ID',
                                             'Start over'],
                                            ['register',
                                             'wrong-id',
                                             'start-over']));
        yield q_no_record_found;
        var no_rec_ans = q_no_record_found.value;
        
        if (no_rec_ans == 'start-over') {
          return;
        } else if (no_rec_ans == 'wrong-id') {
          continue;
        }
      } else if (records_for_id.length == 1) {
        //if one match, verify match
        var choicevals = ['same', 'wrong-id', 'dup-id', 'start-over'];
        if (is_reg_form) {
          var q_correct_patient = qSinglePatInfo('A patient is already registered with this ID. Is this the same patient?', zip_choices(
                                                 ['Yes, this is the same patient',
                                                  'No, I entered the wrong ID',
                                                  'No, continue registering my new patient with this ID',
                                                  'No, start over'],
                                                 choicevals),
                                                 records_for_id[0]);
        } else {
          var q_correct_patient = qSinglePatInfo('Is this the correct patient?', zip_choices(
                                                 ['Yes',
                                                  'No, I entered the wrong ID',
                                                  'No, I will register a new patient with the same ID',
                                                  'No, start over'],
                                                 choicevals),
                                                 records_for_id[0]);
        }
        yield q_correct_patient;
        var corr_pat_ans = q_correct_patient.value;
        
        if (corr_pat_ans == 'start-over') {
          return;
        } else if (corr_pat_ans == 'wrong-id') {
          continue;
        } else if (corr_pat_ans == 'same') {
          existing_patient_rec = records_for_id[0];
        }
      } else if (records_for_id.length > 1) {
        //if many matches for that ID, pick one or none
        if (is_reg_form) {
          var q_choose_patient = qChooseAmongstPatients(records_for_id, 'Multiple patients found with ID ' + formatPatID(patient_id) + '!',
                                                        'None of these is the same patient');
        } else {
          var q_choose_patient = qChooseAmongstPatients(records_for_id, 'Multiple patients found with ID ' + formatPatID(patient_id) + '!',
                                                        'None of these is the correct patient');
        }        

        var chosen = false;
        while (!chosen) {
          yield q_choose_patient;
          var choose_pat_ans = q_choose_patient.value;
          if (choose_pat_ans.substring(0, 3) == 'pat') {
            var chosen_rec = records_for_id[+choose_pat_ans.substring(3)];
            var q_correct_patient = qSinglePatInfo('Is this the ' + (is_reg_form ? 'same' : 'correct') + ' patient?',
                                                   zip_choices(['Yes', 'No, back to list'], [true, false]),
                                                   chosen_rec);
            yield q_correct_patient;
            var corr_pat_ans = q_correct_patient.value;
            if (corr_pat_ans) {
              existing_patient_rec = chosen_rec;
              chosen = true;
            }
          } else {
            chosen = true;
          }
        }
        
        //picked none; offer option to bail or continue with new reg
        if (existing_patient_rec == null) {
          var choicevals = ['reg-dup-id', 'wrong-id', 'start-over'];
          if (is_reg_form) {
            var q_not_found = qSelectReqd('No correct match found for ID ' + patient_id, zip_choices(
                                          ['Register as new patient with the same ID',
                                           'I entered the wrong ID',
                                           'Start over'],
                                          choicevals));
          } else {
            var q_not_found = qSelectReqd('No correct match found for ID ' + patient_id, zip_choices(
                                          ['Register this new patient with the same ID',
                                           'I entered the wrong ID',
                                           'Start over'],
                                          choicevals));
          }
          yield q_not_found;
          var not_found_ans = q_not_found.value;
          if (not_found_ans == 'start-over') {
            return;
          } else if (not_found_ans == 'wrong-id') {
            continue;
          }
        }
      }  
      id_accepted = true;
    }

    //if no record has been chosen (for reg: a record that collides with current ID, for other: the patient lookup result)
    if (existing_patient_rec == null) {

      //for non-registration forms, optionally register the non-existent patient here
      if (new_patient_rec == null) {
        q_has_reg_form = qSelectReqd('Is there a registration form in the patient\'s file?', zip_choices(['Yes, I will use this registration form', 'No'], [true, false]));
        yield q_has_reg_form;
        var has_reg_form = q_has_reg_form.value;
        
        new_patient_rec = {} //new Patient();
        for (var q in ask_patient_info(new_patient_rec, has_reg_form)) {
          yield q;
        }
        new_patient_rec.id = patient_id;
      }
      
      //check for similar record under a different ID
      var qr_dup_check = new wfAsyncQuery(function (callback) { fuzzy_match(new_patient_rec, callback); });
      yield qr_dup_check;
      var candidate_duplicate = qr_dup_check.value;
      
      if (candidate_duplicate != null) {
        var q_merge_dup = qSinglePatInfo('Similar patient found! Is this the same patient?', zip_choices(
                                         ['Yes, these are the same person',
                                          'No, this is a different person'],
                                         [true, false]),
                                         candidate_duplicate);
        yield q_merge_dup;
        merge = q_merge_dup.value;
        if (merge) {
          existing_patient_rec = candidate_duplicate;
          yield new wfAlert('Remember to merge the two paper records for this patient');
        }
      }
    }
    //summarize result of workflow
    data['new'] = (new_patient_rec != null);
    if (data['new']) {
      data['patient'] = new_patient_rec;
      if (existing_patient_rec != null)
        data['merge_with'] = existing_patient_rec['_id'];
    } else {
      data['patient'] = existing_patient_rec;
    }
  }

  var onFinish = function (data) {
    submit_redirect({result: JSON.stringify(data)})
  }

  return new Workflow(flow, onFinish);
}

function wfEditPatient (pat_uuid) {
  var flow = function (data) {
    var qr_lookup_pat = new wfAsyncQuery(function (callback) { lookup(pat_uuid, callback, true); });
    yield qr_lookup_pat;
    var patient = mkpatrec(qr_lookup_pat.value);
    
    while (true) {
      var q_overview = qPatientEdit(patient);
      yield q_overview;
      var choice = q_overview.value;

      var path = null;
      if (choice == null) {
        break;
      } else if (choice == 'sex') {
        path = ask_patient_field(patient, choice);
      } else if (choice == 'fname') {
        path = ask_patient_field(patient, choice, true);
      } else if (choice == 'lname') {
        path = ask_patient_field(patient, choice, true);
      } else if (choice == 'dob') {
        path = ask_patient_field(patient, choice, true);
      } else if (choice == 'village') {
        path = ask_patient_field(patient, choice);
      } else if (choice == 'phone') {
        path = ask_patient_field(patient, choice);
      } else if (choice == 'chwzone') {
        path = ask_patient_field(patient, choice);
      }

      for (var q in path) {
        yield q;
      }
    }

    data.patient = patient;
  }
  
  var onFinish = function (data) {
    data._id = pat_uuid;
    submit_redirect({result: JSON.stringify(data)})
  }
  
  return new Workflow(flow, onFinish);
}

function mkpatrec (patient_info) {
  var patrec = {
    fname: patient_info.first_name,
    lname: patient_info.last_name,
    sex: patient_info.gender,
    dob: patient_info.birthdate,
    dob_est: patient_info.birthdate_estimated,
    id: patient_info.patient_id,
    deceased: patient_info.is_deceased,
    _id: patient_info._id
  }
  if (patient_info.phones && patient_info.phones.length > 0) {
    patrec.phone = patient_info.phones[0].number;
  }
  if (patient_info.address) {
    patrec.village = patient_info.address.village;
    patrec.address = patient_info.address.address;
    patrec.chw_zone = patient_info.address.zone;
    patrec.chw_zone_na = patient_info.address.zone_empty_reason;
  }
  return patrec;
}

function ask_patient_info (pat_rec, full_reg_form) {
  for (var q in ask_patient_field(pat_rec, 'sex', full_reg_form)) { yield q; }
  for (var q in ask_patient_field(pat_rec, 'fname', true)) { yield q; }
  for (var q in ask_patient_field(pat_rec, 'lname', true)) { yield q; }

  if (pat_rec['fname'] == "WHITE" && pat_rec['lname'] == "MEAT") {
    yield qPork();
  }
  
  if (full_reg_form) {
    for (var q in ask_patient_field(pat_rec, 'dob', true)) { yield q; }
    for (var q in ask_patient_field(pat_rec, 'village')) { yield q; }
    if (POP_DENSITY != 'rural') {
      for (var q in ask_patient_field(pat_rec, 'address')) { yield q; }
    }
    for (var q in ask_patient_field(pat_rec, 'phone')) { yield q; }
    for (var q in ask_patient_field(pat_rec, 'chwzone')) { yield q; }
  } else {

    //ask age and deduce estimated birth date?
    
  }
}

function ask_patient_field (pat_rec, field, reqd) {
  var ask = function (args, field, reqd) {
    args.required = reqd;
    args.answer = pat_rec[field];
    var q = new wfQuestion(args);
    yield q;
    pat_rec[field] = q.value;
  }

  if (field == 'sex') {
    for (var q in ask({caption: 'Sex', type: 'select', choices: zip_choices(['Male', 'Female'], ['m', 'f'])}, 'sex', reqd)) { yield q };
  } else if (field == 'fname') {
    var domain = 'firstname';
    if (pat_rec.sex) {
      domain += '-' + (pat_rec.sex == 'm' ? 'male' : 'female');
    }
    for (var q in ask({caption: 'First Name', type: 'str', domain: domain, meta: {autocomplete: true}}, 'fname', reqd)) { yield q };
  } else if (field == 'lname') {
    for (var q in ask({caption: 'Last Name', type: 'str', domain: 'lastname', meta: {autocomplete: true}}, 'lname', reqd)) { yield q };
  } else if (field == 'dob') {
    for (var q in ask({caption: 'Date of Birth', type: 'date', meta: {maxdiff: 1.5, outofrangemsg: 'Birthdate cannot be in the future.'}}, 'dob', reqd)) { yield q };
    for (var q in ask({caption: 'Date of Birth Estimated?', type: 'select', choices: zip_choices(['Yes', 'No'], [true, false])}, 'dob_est')) { yield q };
  } else if (field == 'village') {
    var caption = {
      'rural': 'Village',
      'urban': 'Neighborhood / Compound',
      'mixed': 'Village (rural area) or Neighborhood (urban area)'
    }[POP_DENSITY];
    for (var q in ask({caption: caption, type: 'str', domain: 'village', meta: {autocomplete: true}}, 'village')) { yield q };
  } else if (field == 'address') {
    for (var q in ask({caption: 'Address where patient lives / Directions to residence (skip if in rural area \u2014 see help)', type: 'str', helptext: 'Enter the patient\'s address so that the CHW can find the patient for follow-up visits. Or enter a description or directions for how to find the patient if the exact address is not available. If knowing just the patient\'s name and village is enough for the CHW to find where they live (like in a rural area), skip this question.'}, 'address')) { yield q };
  } else if (field == 'phone') {
    for (var q in ask({caption: 'Contact Phone #', type: 'str', domain: 'phone'}, 'phone')) { yield q };
  } else if (field == 'chwzone') {    
    var zoneans = (pat_rec.chw_zone != null ? 'zone' + pat_rec.chw_zone : pat_rec.chw_zone_na);
    var q_chwzone = qSelectReqd('CHW Zone', chwZoneChoices(CLINIC_NUM_CHW_ZONES), null, zoneans);
    yield q_chwzone;
    if (q_chwzone.value.substring(0, 4) == 'zone') {
      pat_rec.chw_zone = +q_chwzone.value.substring(4);
      pat_rec.chw_zone_na = null;
    } else {
      pat_rec.chw_zone = null;
      pat_rec.chw_zone_na = q_chwzone.value;
    }
  }
}

function lookup (pat_id, callback, is_uuid) {
  jQuery.get('/patient/api/lookup', is_uuid ? {'uuid': pat_id} : {'id': pat_id}, function (data) {
      callback(data);
    }, "json");
}

function fuzzy_match (patient_rec, callback) {
  jQuery.post('/patient/api/match/', patient_rec, function (data) {
      callback(data);
    }, "json");
}

function qChooseAmongstPatients (records, qCaption, noneCaption) {
  var choices = [];
  for (patrec in Iterator(records)) {
    choices.push({lab: patLine(patrec[1]), val: 'pat' + patrec[0]});
  }
  choices.push({lab: noneCaption, val: 'none'});
  
  return qSelectReqd(qCaption, choices);
}

function parseISODate (dt) {
  y = parseInt(dt.substring(0, 4));
  m = parseInt(dt.substring(5, 7));
  d = parseInt(dt.substring(8, 10));
  return new Date(y, m - 1, d);
}

function patLine (pat) {
  var line = pat['first_name'] + " " + pat['last_name'] + " ";
  if (pat['birthdate'] != null) {
    line += Math.floor((new Date() - parseISODate(pat['birthdate']))/(1000.*86400*365.2425));
  } else {
    line += '??';
  }
  line += "/" + (pat['gender'] != null ? pat['gender'].toUpperCase() : "?");
  if (pat["is_deceased"]) {
    line += " (deceased)";
    //line += " \u2620";
    //line += " \u26b0";
  }
  return line;
}

function qSinglePatInfo (caption, choices, pat_rec, selected, help) {
  var pat_content = get_server_content('single-patient', {'uuid': pat_rec['_id']});
  var BUTTON_SECTION_HEIGHT = '42%';

  return new wfQuestion({caption: caption, answer: selected, helptext: help, required: true, custom_layout: function (q) {
      var PatientDetailEntry = function () {
        inherit(this, new SingleSelectEntry({choices: choices}));

        this.load = function () {
          var choiceLayout = this.makeChoices();
          var markup = new Layout({id: 'patinfosplit', nrows: 2, heights: ['*', BUTTON_SECTION_HEIGHT], margins: '2.5%', spacings: '.5%', content: [
              new CustomContent(null, pat_content),
              choiceLayout
            ]});
          questionEntry.update(markup);
          this.buttons = choiceLayout.buttons;
        }
      }
      return new PatientDetailEntry();
    }});
}

function qPatientEdit (patient) {
  if (patient.chw_zone) {
    patient.chw_zone_display = 'Zone ' + patient.chw_zone;
  } else if (patient.chw_zone_na == 'outside_catchment_area') {
    patient.chw_zone_display = 'outside catchment area';
  } else {
    patient.chw_zone_display = 'unknown';
  }
  var pat_content = get_server_content('single-patient-edit', JSON.stringify(patient));

  return new wfQuestion({caption: 'Edit patient ' + formatPatID(patient.id), custom_layout: function (q) {
      var PatientEditOverview = function () {
        var fields = ['fname', 'lname', 'dob', 'sex', 'village', 'phone', 'chwzone'];
        var captions = [];
        for (var i = 0; i < fields.length; i++) {
          captions.push('EDIT');
        }

        inherit(this, new SingleSelectEntry({choices: captions, choicevals: fields}));

        var action = this.selectFunc();
        this.load = function () {
          var choiceLayout = this.makeChoices();
          //override render function to render buttons directly into slots created by django template
          choiceLayout.render = function () {
            this.buttons = [];
            for (var i = 0; i < fields.length; i++) {
              var button = make_button('EDIT', {value: fields[i], textsize: .7, action: action});
              button.render($('#button' + (i + 1))[0]);
              this.buttons.push(button);
            }
          }

          var markup = new Layout({margins: ['0', '0', '3%', '*'], content: [new CustomContent(null, pat_content)]});
          questionEntry.update(markup);
          choiceLayout.render();
          this.buttons = choiceLayout.buttons;
        }
      }
      return new PatientEditOverview();
    }});
}

function qPork () {
  return new wfQuestion({caption: 'PORK!', helptext: 'THERE IS ONLY PORK', custom_layout: function (q) {
      var PorkEntry = function () {
        inherit(this, new SimpleEntry());

        this.load = function () {
          questionEntry.update(new CustomContent(null, '<table width="100%" height="100%"><tr><td align="center" valign="middle"><embed src="/static/webapp/352_pork3b.swf" \
             quality="high" width="550" height="400" align="middle" allowScriptAccess="sameDomain" allowFullScreen="false" play="true" type="application/x-shockwave-flash" /></td></tr></table>'));
        }

        this.getAnswer = function () { return null; }
        this.setAnswer = function (answer) { }
      }
      return new PorkEntry();
    }});
}

function get_server_content (template, params) {
  //can't show waiting screen here, because synchronous request doesn't yield the thread
  return jQuery.ajax({url: '/patient/render/' + template + '/', type: 'POST', data: params, async: false}).responseText;
}

function formatPatID (patid) {
  return patid.substring(0, 4) + '-' + patid.substring(4, 7) + '-' + patid.substring(7, 12) + '-' + patid.substring(12);
}