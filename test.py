from datetime import datetime


while(1):
       t = datetime.now().strftime('%S')
       print(t)
       if t == "30":
              print("DONE")