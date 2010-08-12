/*
 * use this to make sure you loaded the reports module properly
 */

function hello_reports() {
    log("hello reports!");
}

/*
 * Function/Class to represent a report
 */
 
function report(name, values) {
    this.name = name;
    this.values = values;
}

 
/*
 * Function/Class to represent a value in a report
 */

function reportValue(num, denom, slug, hidden, display_name) {
    this.num = num;
    this.denom = denom;
    this.slug = slug;
    // this param is optional, defaulting to false
    if (hidden!=null) {
        this.hidden = hidden;
    } else {
        this.hidden = false;
    }
    // the display name defaults to the slug
    if (display_name != null) {
        this.display_name = display_name;
    } else {
        this.display_name = slug;
    }
    
}


/*
 * Performs reduce aggregation and adds the report name.
 */
function reduce_common(keys, values, rereduce, report_name) {
    totals = {};
    for (var i = 0; i < values.length; i++) {
        result = rereduce ? values[i].values : values[i];
        for (var j = 0; j < result.length; j++) {
            rep_val = result[j];
            if (!totals.hasOwnProperty(rep_val.slug)) {
                totals[rep_val.slug] = rep_val;
            } else {
                old_val = totals[rep_val.slug]
                old_val.num += rep_val.num;
                old_val.denom += rep_val.denom;
            }
        }
    }
    // convert back to an array
    ret = [];
    for (key in totals) {
        ret.push(totals[key]);
    }
    return new report(report_name, ret);
}

/*
 * Returns boolean for whether a drug prescribed matches an intended type
 */
function check_drug_type(drugs_prescribed, type_to_check) {
log(drugs_prescribed);
log(type_to_check);
log(drugs_prescribed["formulation"]);
log(drugs_prescribed["types"][0]);
    for (var i = 0; i < drugs_prescribed.length; i++) {
   		for (var j = 0; j < drugs_prescribed["types"].length; j++) {
   			if (exists(drugs_prescribed["types"],type_to_check)) {
   				return 1;
   				log("return 1 from func");
   			} else {
   				return 0;
   				log("return 0 from func");
   			}
   		}
   	}	
}
	    