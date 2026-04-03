import os
for k,v in os.environ.items():
 if 'MEI' in k or 'PYI' in k:
  print(k, v)
