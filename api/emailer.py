import os,smtplib,ssl
from email.message import EmailMessage
from jinja2 import Environment, FileSystemLoader, select_autoescape
SMTP_HOST=os.getenv('SMTP_HOST',''); SMTP_PORT=int(os.getenv('SMTP_PORT','587'))
SMTP_USER=os.getenv('SMTP_USER',''); SMTP_PASS=os.getenv('SMTP_PASS','')
SMTP_FROM=os.getenv('SMTP_FROM','no-reply@example.com')
SMTP_STARTTLS=os.getenv('SMTP_STARTTLS','1')=='1'
env=Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__),'templates')),autoescape=select_autoescape(['html','xml']))
def render(name,**ctx): return env.get_template(name).render(**ctx)
def send_mail(subject,to,html,text=None):
  if not SMTP_HOST or not to: return False
  msg=EmailMessage(); msg['Subject']=subject; msg['From']=SMTP_FROM; msg['To']=to
  if text: msg.set_content(text)
  msg.add_alternative(html,subtype='html')
  if SMTP_STARTTLS:
    ctx=ssl.create_default_context();
    with smtplib.SMTP(SMTP_HOST,SMTP_PORT,timeout=10) as s:
      s.ehlo(); s.starttls(context=ctx); s.login(SMTP_USER,SMTP_PASS); s.send_message(msg)
  else:
    with smtplib.SMTP(SMTP_HOST,SMTP_PORT,timeout=10) as s:
      s.ehlo();
      if SMTP_USER and SMTP_PASS: s.login(SMTP_USER,SMTP_PASS)
      s.send_message(msg)
  return True
