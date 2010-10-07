import os
from bhoma.apps.zscore.models import Zscore

class LoaderException(Exception):
    pass

def load_zscore(file_path, log_to_console=True):
    if log_to_console: print "loading zscore table from %s" % file_path
    # give django some time to bootstrapp itself
    if not os.path.exists(file_path):
        raise LoaderException("Invalid file path: %s." % file_path)
    
    csv_file = open(file_path, 'r')
    try:
        Zscore.objects.all().delete()
        
        count = 0    
        for line in csv_file:
            #leave out first line
            if "gender" in line.lower():
                continue
    
            gender, age_months, l_value, m_value, s_value, sd_three_neg, sd_two_neg, sd_one_neg, sd_zero = \
               [item.strip() for item in line.split(",")]
            
            #create zscore table
            table = Zscore()    
            table.gender = "m" if gender == "Male" else "f"
            table.age = age_months
            table.l_value = l_value
            table.m_value = m_value
            table.s_value = s_value
            table.sd_three_neg = sd_three_neg
            table.sd_two_neg = sd_two_neg
            table.sd_one_neg = sd_one_neg
            table.sd_zero = sd_zero
                    
            table.save()
            
            count += 1
    
        if log_to_console: print "Successfully processed %s lines to make zscore table." % count
    finally:
        csv_file.close()

