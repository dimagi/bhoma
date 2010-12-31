
function wfGetPatient () {
  var flow = function (data) {
    var new_patient_rec = null;       //any new record created via registration form
    var existing_patient_rec = null;  //any existing record select by the user as belonging to the current patient
    //these fields are not mutually exclusive

    var q_form_type = qSelectReqd('What type of form is this?', ['Registration form', 'Other form']);
    yield q_form_type;
    var is_reg_form = (q_form_type.value == 1);
    
    var id_accepted = false;
    var need_to_fill_registration_upfront = is_reg_form;

    //we offer the option to correct a mistakenly entered ID, thus this loop
    while (!id_accepted) {

      //enter patient id
      var q_pat_id = new wfQuestion({caption: 'Patient ID', type: 'str', required: true,
                                     validation: function (x) { return x.length != 12 ? "A valid ID is 12 digits (this ID has " + x.length + ")" : null}, 
                                     domain: 'pat-id'});
      yield q_pat_id;
      var patient_id = q_pat_id.value;

      //retrieve existing matches for that id
      var qr_lookup_pat = new wfAsyncQuery(function (callback) { lookup(patient_id, callback); });
      yield qr_lookup_pat;
      var records_for_id = qr_lookup_pat.value;
      //for registration forms we always have them fill out the reg info upfront (but only once even if we re-ask patient id)
      if (need_to_fill_registration_upfront) {
        new_patient_rec = {} //new Patient();
        for (var q in ask_patient_info(new_patient_rec, true)) {
          yield q;
        }
        new_patient_rec.id = patient_id;
        need_to_fill_registration_upfront = false;
      }
      // save ourselves from having to do null checks all over
      if (records_for_id == null) {
        records_for_id = [];
      } 
      if (!is_reg_form && records_for_id.length == 0) {
        //if not a reg form, give them the option to bail if ID not found

        var q_no_record_found = qSelectReqd('No patient found for ID ' + patient_id,
                                            ['Register as new patient',
                                             'Wrong ID',
                                             'Start over']);
        yield q_no_record_found;
        var no_rec_ans = q_no_record_found.value;
        
        if (no_rec_ans == 3) {
          return; //start over
        } else if (no_rec_ans == 2) {
          continue; //re-enter id
        }
      } else if (records_for_id.length == 1) {
        //if one match, verify match
        if (is_reg_form) {
          var q_correct_patient = qSinglePatInfo('A patient is already registered with this ID. Is this the same patient?',
                                                 ['Yes, this is the same patient',
                                                  'No, I entered the wrong ID',
                                                  'No, continue registering my new patient with this ID',
                                                  'No, start over'],
                                                 records_for_id[0]);
        } else {
          var q_correct_patient = qSinglePatInfo('Is this the correct patient?', 
                                                 ['Yes',
                                                  'No, I entered the wrong ID',
                                                  'No, I will register a new patient with the same ID',
                                                  'No, start over'],
                                                 records_for_id[0]);
        }
        yield q_correct_patient;
        var corr_pat_ans = q_correct_patient.value;
        
        if (corr_pat_ans == 4) {
          return; //start over
        } else if (corr_pat_ans == 2) {
          continue; //re-enter id
        } else if (corr_pat_ans == 1) {
          existing_patient_rec = records_for_id[0];
        }
      } else if (records_for_id.length > 1) {
        //if many matches for that ID, pick one or none
        if (is_reg_form) {
          var q_choose_patient = qChooseAmongstPatients(records_for_id, 'Multiple patients found with that ID!',
                                                        'None of these is the same patient');
        } else {
          var q_choose_patient = qChooseAmongstPatients(records_for_id, 'Multiple patients found with that ID!',
                                                        'None of these is the correct patient');
        }        

        var chosen = false;
        while (!chosen) {
          yield q_choose_patient;
          var choose_pat_ans = q_choose_patient.value;
          if (choose_pat_ans < q_choose_patient.choices.length) {
            var chosen_rec = records_for_id[choose_pat_ans - 1];
            var q_correct_patient = qSinglePatInfo('Is this the ' + (is_reg_form ? 'same' : 'correct') + ' patient?', 
                                                   ['Yes',
                                                    'No, back to list'],
                                                   chosen_rec);
            yield q_correct_patient;
            var corr_pat_ans = q_correct_patient.value;
            if (corr_pat_ans == 1) {
              existing_patient_rec = chosen_rec;
              chosen = true;
            }
          } else {
            chosen = true;
          }
        }
        
        //picked none; offer option to bail or continue with new reg
        if (existing_patient_rec == null) {
          if (is_reg_form) {
            var q_not_found = qSelectReqd('No correct match found for ID ' + patient_id,
                                          ['Register as new patient with the same ID',
                                           'I entered the wrong ID',
                                           'Start over']);
          } else {
            var q_not_found = qSelectReqd('No correct match found for ID ' + patient_id,
                                          ['Register this new patient with the same ID',
                                           'I entered the wrong ID',
                                           'Start over']);
          }
          yield q_not_found;
          var not_found_ans = q_not_found.value;
          if (not_found_ans == 3) {
            return; //start over
          } else if (not_found_ans == 2) {
            continue; //re-enter id
          }
        }
      }  
      id_accepted = true;
    }

    //if no record has been chosen (for reg: a record that collides with current ID, for other: the patient lookup result)
    if (existing_patient_rec == null) {

      //for non-registration forms, optionally register the non-existent patient here
      if (new_patient_rec == null) {
        q_has_reg_form = qSelectReqd('Is there a registration form in the patient\'s file?', ['Yes, I will use this registration form', 'No']);
        yield q_has_reg_form;
        var has_reg_form = (q_has_reg_form.value == 1);
        
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
        var q_merge_dup = qSinglePatInfo('Similar patient found! Is this the same patient?',
                                         ['Yes, these are the same person',
                                          'No, this is a different person'],
                                         candidate_duplicate);
        yield q_merge_dup;
        merge = (q_merge_dup.value == 1);
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

function ask_patient_info (pat_rec, full_reg_form) {
  var q_fname = new wfQuestion({caption: 'First Name', type: 'str', required: true, domain: 'alpha'});
  yield q_fname;
  pat_rec['fname'] = q_fname.value;

  var q_lname = new wfQuestion({caption: 'Last Name', type: 'str', required: true, domain: 'alpha'});
  yield q_lname;
  pat_rec['lname'] = q_lname.value;
  
  if (pat_rec['fname'] == "WHITE" && pat_rec['lname'] == "MEAT") {
    yield qPork();
  }
  
  var q_sex = new wfQuestion({caption: 'Sex', type: 'select', choices: ['Male', 'Female'], required: full_reg_form});
  yield q_sex;
  pat_rec['sex'] = (q_sex.value == 1 ? 'm' : 'f');
  
  if (full_reg_form) {
    
    var q_dob = new wfQuestion({caption: 'Date of Birth', type: 'date', required: true,
                                meta: {maxdiff: 1.5, outofrangemsg: 'Birthdate cannot be in the future.'}});
    yield q_dob;
    pat_rec['dob'] = q_dob.value;
    
    var q_dob_est = new wfQuestion({caption: 'Date of Birth Estimated?', type: 'select', choices: ['Yes', 'No']});
    yield q_dob_est;
    pat_rec['dob_est'] = (q_dob_est.value != null ? (q_dob_est.value == 1) : null);
    
    var q_village = new wfQuestion({caption: 'Village', type: 'str', domain: 'alpha'});
    yield q_village;
    pat_rec['village'] = q_village.value;
    
    var q_contact = new wfQuestion({caption: 'Contact Phone #', type: 'str', domain: 'phone'});
    yield q_contact;
    pat_rec['phone'] = q_contact.value;
    
    var q_chwzone = qSelectReqd('CHW Zone', chwZoneChoices(CLINIC_NUM_CHW_ZONES));
    yield q_chwzone;
    if (q_chwzone.value.substring(0, 4) == 'zone') {
      pat_rec['chw_zone'] = +q_chwzone.value.substring(4);
      pat_rec['chw_zone_na'] = null;
    } else {
      pat_rec['chw_zone'] = null;
      pat_rec['chw_zone_na'] = q_chwzone.value;
    }

  } else {

    //ask age and deduce estimated birth date?
    
  }
}

function lookup (pat_id, callback) {
  jQuery.get('/patient/api/lookup', {'id': pat_id}, function (data) {
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
    choices.push(patLine(patrec[1]));
  }
  choices.push(noneCaption);
  
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
  return line;
}

function qSinglePatInfo (caption, choices, pat_rec, selected, help) {
  pat_content = get_server_content('single-patient', {'uuid': pat_rec['_id']});
  var BUTTON_SECTION_HEIGHT = '42%';

  return new wfQuestion({caption: caption, type: 'select', answer: selected, helptext: help, required: true, custom_layout: function (q) {
      var choiceLayout = new ChoiceSelect({choices: choices, selected: normalize_select_answer(q['answer'], false), multi: false});
      var markup = new Layout({id: 'patinfosplit', nrows: 2, heights: ['*', BUTTON_SECTION_HEIGHT], margins: '2.5%', spacings: '.5%', content: [
          new CustomContent(null, pat_content),
          choiceLayout
        ]});

      questionEntry.update(markup);
      activeInputWidget = choiceLayout.buttons;
    }});
}

function qPork () {
  return new wfQuestion({caption: 'PORK!', type: 'select', helptext: 'THERE IS ONLY PORK', custom_layout: function () {
      questionEntry.update(new CustomContent(null, '<table width="100%" height="100%"><tr><td align="center" valign="middle"><embed src="/static/webapp/352_pork3b.swf" \
           quality="high" width="550" height="400" align="middle" allowScriptAccess="sameDomain" allowFullScreen="false" play="true" type="application/x-shockwave-flash" /></td></tr></table>'));
      activeQuestionWidget = [];
    }});
}

function get_server_content (template, params) {
  //can't show waiting screen here, because synchronous request doesn't yield the thread
  return jQuery.ajax({url: '/patient/render/' + template + '/', type: 'POST', data: params, async: false}).responseText;
}