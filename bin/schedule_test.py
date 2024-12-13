from schedule import every, repeat, run_pending
import time
import datetime as dt

@repeat(every(1).minutes)
def job():
    print("I am a scheduled job at 1min {}".format(dt.datetime.utcnow()))

@repeat(every(10).seconds)
def job2():
    print("I am a scheduled job at 10s {}".format(dt.datetime.utcnow()))
    

while True:
    run_pending()
    time.sleep(1)