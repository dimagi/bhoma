class UnicodeMixIn(object):
    """
    Override objects so that str calls unicode and you only have to override
    unicode.
    """
    
    def __str__(self):
        return unicode(self).encode('utf-8')
    
