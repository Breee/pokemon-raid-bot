def replace_quotes(string):
    """
    >>> test_string =  '„Kyogre HBF Freiburg“'
    >>> replace_quotes(test_string)
    '"Kyogre HBF Freiburg"$$$'

    """
    string = string.replace('„', '"')
    string = string.replace('“','"$$$')
    return string
