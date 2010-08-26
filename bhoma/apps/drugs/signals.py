from bhoma.apps.xforms.signals import xform_saved

def add_drug_information(sender, form, **kwargs):    
    """
    Find out if drug prescribed, identify types prescribed and formulation
    """
    print "========\nadding drug information\n==========="
    from bhoma.apps.drugs.models import Drug
    from bhoma.apps.drugs.models import CDrugRecord
    if form.xpath("drugs/prescribed/med"):
        form.drugs_prescribed = []
        
        #need to put med object as list if only one, ok as dictionary if more
        def extract_drugs(doc):
            drugs = form.xpath("drugs/prescribed/med")
            # drugs is a dictionary if only one, otherwise a list of dictionaries
            # normalize this to a list of dictionaries always, in a hacky manner
            if "duration" in drugs:
                return [drugs]
            return drugs
        
        for each_drug in extract_drugs(form):

            #find drug from drill down options on xform
            drug = each_drug["drug_prescribed"]
            formulation_prescribed = each_drug["drug_formulation"]
            dbdrug = Drug.objects.get(slug=drug)
            
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
            
        print "========\nadding drug information: %s\n===========" % form.get_id
        form.save()  
    
xform_saved.connect(add_drug_information)