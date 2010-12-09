from bhoma.apps.xforms.signals import xform_saved

def add_drug_information(sender, form, **kwargs):    
    """
    Find out if drug prescribed, identify types prescribed and formulation
    """
    from bhoma.apps.drugs.models import Drug
    from bhoma.apps.drugs.models import CDrugRecord
    if form.xpath("drugs/prescribed/med"):
        form.drugs_prescribed = []
        
        #need to put med object as list if only one, ok as dictionary if more
        def extract_drugs(doc):
            drugs = form.xpath("drugs/prescribed/med")
            # drugs is a dictionary if only one, otherwise a list of dictionaries
            # normalize this to a list of dictionaries always, in a hacky manner
            if "common_drug" in drugs:
                return [drugs]
            return drugs
        
        for each_drug in extract_drugs(form):

            #determine if common or uncommon
            if each_drug["common_drug"] != "enter_manually":
                #need to split drug string to get desired info
                # of form: name-formulation-dosage-freq-duration
                #aka, acetyl_salicylic_acid-tablet-600-3-3
                drug = each_drug["common_drug"].split('-')[0]
                formulation_prescribed = each_drug["common_drug"].split('-')[1]
            else:    
                #find drug from drill down options on xform
                drug = each_drug["uncommon"]["drug_prescribed"]
                formulation_prescribed = each_drug["uncommon"]["drug_formulation"]
                
            try:
                dbdrug = Drug.objects.get(slug=drug)
            except Drug.DoesNotExist:
                continue # no drug, do nothing
            
            #check the formulation prescribed is possible
            formulations_checked = []
            types_checked = []
            for formulation in dbdrug.formulations.all():
                if formulation_prescribed == formulation.name: 
                    formulations_checked = [formulation_prescribed]
                    break
                else:
                    formulations_checked = ["other"]
            for type in dbdrug.types.all(): types_checked.append(type.name)
            
            drug = CDrugRecord(name=dbdrug.slug, types=types_checked, formulations=formulations_checked)
            form.drugs_prescribed.append(drug.to_json())
            
        form.save()  
    
xform_saved.connect(add_drug_information)