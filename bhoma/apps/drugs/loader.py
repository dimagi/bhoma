import os
import re
from bhoma.apps.drugs.models import DrugType, DrugFormulation, Drug

class LoaderException(Exception):
    pass

def load_drugs(file_path, log_to_console=True):
    if log_to_console: print "loading static drugs from %s" % file_path
    # give django some time to bootstrapp itself
    if not os.path.exists(file_path):
        raise LoaderException("Invalid file path: %s." % file_path)
    
    csv_file = open(file_path, 'r')
    try:
        count = 0    
        for line in csv_file:
            #leave out first line
            if "name of drug" in line.lower():
                continue
    
            #not currently using strength or units, but may in future
            drug_name, drug_formulation, drug_strength, drug_units, drug_type, drug_slug = \
               [item.strip() for item in line.split(",")]
            
            #create/load drug formulation, can be multiple per line entry
            formulation_list = []
            drug_formulation_list = drug_formulation.lower().split(";")
            for formulation in drug_formulation_list:
                formulation = formulation.strip()
                if formulation:
                    try:
                        formulation = DrugFormulation.objects.get(name=formulation)
                    except DrugFormulation.DoesNotExist:
                        formulation = DrugFormulation.objects.create(name=formulation)
                    formulation_list.append(formulation)
            
            #create/load drug type, can be multiple per line entry
            classification_list = []
            drug_type_list = drug_type.lower().split(";")
            for type in drug_type_list:
                type = type.strip()
                if type:
                    try:
                        classification = DrugType.objects.get(name=type)
                    except DrugType.DoesNotExist:
                        classification = DrugType.objects.create(name=type)
                    classification_list.append(classification)
                
            #create slug
            try:
                drug = Drug.objects.get(slug=drug_slug)
                for formulation in formulation_list:
                    if formulation not in drug.formulations.all() :
                        drug.formulations.add(formulation)
                for type in classification_list:
                    if type not in drug.types.all():
                        drug.types.add(type)
            except Drug.DoesNotExist:
                drug = Drug.objects.create(slug=drug_slug)    
                drug.name = drug_name
                drug.types = classification_list
                drug.formulations = formulation_list
            
            drug.save()
            
            count += 1
    
        if log_to_console: print "Successfully processed %s drugs." % count
    
    finally:
        csv_file.close()

        
def _clean(name):
    truncated_name = name.lower().strip().replace(" ", "_")[:30]
    return re.sub(r'\W+', '', truncated_name)