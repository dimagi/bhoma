from bhoma.apps.xforms.signals import xform_saved
import logging

def chw_referral_num(sender, form, **kwargs):    
    """
    Process CHW referral num; link to any existing referral
    """
    if form.xpath("chw_referral_id"):
        ref_num = form.xpath("chw_referral_id")

        if len(ref_num) not in (7, 8):
            logging.info('received non-conformant chw referral # [%s]' % ref_num)

        #allow 7-digit IDs for backwards compatibility
        if len(ref_num) == 7:
            ref_num = ref_num[:4] + '0' + ref_num[4:]

        #TODO: do something with this referral #
        #cross-reference with original referral... create a doc... index it somehow?
    
xform_saved.connect(chw_referral_num)
