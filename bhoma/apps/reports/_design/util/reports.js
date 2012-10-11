/*
 * use this to make sure you loaded the reports module properly
 */

function hello_reports() {
    log("hello reports!");
}


/*
 * Performs reduce aggregation and adds the report name.
 */
function reduce_common(keys, values, rereduce) {
    var ret = [0,0];
    for (var i in values) {
        ret[0] = ret[0] + values[i][0];
        ret[1] = ret[1] + values[i][1];
    }
    return ret;
}

/*
 * Check for name existing within drugs prescribed
 */
function check_drug_name(drugs_prescribed, name_to_check) {
	bool_name_good = 0;
	for (var i = 0; i < drugs_prescribed.length && !bool_name_good; i++) {
        this_drug = drugs_prescribed[i];
        if (exists(this_drug["name"],name_to_check)) {
        	bool_name_good =  1;
        } else {
        	bool_name_good =  0;
        }
    }
    return bool_name_good;
}
/*
 * Check if all drugs on form are in stock
 */
function check_drug_stock(prescriptions) {
	bool_in_stock = 1;
	for (var i = 0; i < prescriptions.length && bool_in_stock; i++) {
        this_drug = prescriptions[i];
        if (this_drug["stock"] != "not_in_stock") {
        	bool_in_stock =  1;
        } else {
        	bool_in_stock =  0;
        }
    }
    return bool_in_stock;
}
/*
 * Returns boolean for whether a drug prescribed matches an intended type and formulation
 */
function check_drug_type(drugs_prescribed, type_to_check, formulation_to_check) {
    bool_check_good = 0;
    if (drugs_prescribed) {
	    for (var i = 0; i < drugs_prescribed.length && !bool_check_good; i++) {
	        this_drug = drugs_prescribed[i];
	        
	   		for (var j = 0; j < this_drug["types"].length && !bool_check_good; j++) {
	   			if (exists(this_drug["types"],type_to_check) && (formulation_to_check == null)) {
	   				bool_check_good =  1;
	   			} else if (exists(this_drug["types"],type_to_check) && formulation_to_check) {
	   			   	if(exists(this_drug["formulations"],formulation_to_check)) {
	   					bool_check_good =  1;
	   				} else {
	   					bool_check_good =  0;
	   				}  			
	   			} else {
	   				bool_check_good =  0;
	   			}
	   		}
	   	}	
   	}
   	return bool_check_good
}

var get_age_in_days = function (doc) {
   // doesn't exist yet but might one day.
   //if (doc.age_in_months) {
   //    return doc.age_in_months;
   //}
   var enc_date = get_encounter_date(doc);
   if (doc.dob_raw && enc_date) {
       var dob = parse_date(doc.dob_raw);
       return days_between(dob, enc_date);
   } else if (doc.age) {
       // this is the best proxy we have.
       return doc.age * 365.25;
   } else if (doc.age_raw) {
       // this is the best proxy we have.
       return doc.age_raw * 365.25;
   } else {
       return null;
   }
};
