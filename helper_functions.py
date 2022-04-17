# helper function to return key for any value
def get_key(dict, val):
    for key, value in dict.items():
         if val == value:
             return key
 
    return "key doesn't exist"
