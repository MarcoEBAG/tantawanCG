from datetime import datetime
import pytz
ZRH=pytz.timezone('Europe/Zurich')
def now_zrh():
  return datetime.now(tz=ZRH)
