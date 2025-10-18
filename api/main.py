from fastapi import FastAPI,Depends,HTTPException,WebSocket,WebSocketDisconnect,Header,BackgroundTasks
from pydantic import BaseModel,Field,EmailStr
from typing import List,Optional
from datetime import timedelta,datetime as dt
import json,os,requests
from sqlalchemy.orm import Session
from .database import SessionLocal,engine,Base
from .models import MenuItem,MenuCategory,Order,OrderItem,OrderStatus,User
from .utils import now_zrh
from .auth import hash_password,verify_password,create_token,decode_token
from .emailer import send_mail,render
app=FastAPI(title='Asia Restaurant API')
Base.metadata.create_all(bind=engine)
kitchen_clients:set[WebSocket]=set()

def get_db():
  db=SessionLocal()
  try: yield db
  finally: db.close()
class RegisterIn(BaseModel):
  email:EmailStr; password:str; name:Optional[str]=None; phone:Optional[str]=None
class LoginIn(BaseModel):
  email:EmailStr; password:str
class OrderItemIn(BaseModel):
  menu_item_id:int; qty:int=Field(ge=1)
class OrderIn(BaseModel):
  items:List[OrderItemIn]; pickup_at:str; notes:Optional[str]=None
async def get_current_user(authorization:Optional[str]=Header(None),db:Session=Depends(get_db)):
  if not authorization: return None
  try:
    scheme,token=authorization.split(' ',1)
    if scheme.lower()!='bearer': return None
    email=decode_token(token).get('sub');
    if not email: return None
    return db.query(User).filter(User.email==email).first()
  except Exception: return None
@app.post('/auth/register')
def register(body:RegisterIn,db:Session=Depends(get_db)):
  if db.query(User).filter(User.email==body.email).first(): raise HTTPException(400,'email exists')
  u=User(email=body.email,password_hash=hash_password(body.password),name=body.name,phone=body.phone)
  db.add(u); db.commit(); token=create_token(u.email); return {'token':token,'email':u.email,'name':u.name}
@app.post('/auth/login')
def login(body:LoginIn,db:Session=Depends(get_db)):
  u=db.query(User).filter(User.email==body.email).first()
  if not u or not verify_password(body.password,u.password_hash): raise HTTPException(401,'invalid')
  token=create_token(u.email); return {'token':token,'email':u.email,'name':u.name}
@app.get('/menu/items')
def list_menu(db:Session=Depends(get_db)):
  items=db.query(MenuItem).filter(MenuItem.is_active==1).all()
  return [{'id':i.id,'name':i.name,'description':i.description,'price_chf':i.price_chf,'category_id':i.category_id} for i in items]
@app.post('/dev/seed')
def seed(db:Session=Depends(get_db)):
  if db.query(MenuItem).count(): return {'ok':True}
  cat=MenuCategory(name='Beliebt',position=1); db.add(cat)
  db.add_all([
    MenuItem(category=cat,name='Pad Thai',description='Reisnudeln',price_chf=18.5),
    MenuItem(category=cat,name='Chicken Curry',description='Gelbes Curry',price_chf=19.0),
    MenuItem(category=cat,name='Veggie Dumplings (6)',description='Gedämpft',price_chf=9.5),
  ]); db.commit(); return {'ok':True}
async def notify_kitchen(payload:dict):
  dead=[]
  for ws in list(kitchen_clients):
    try: await ws.send_text(json.dumps(payload))
    except Exception: dead.append(ws)
  for d in dead: kitchen_clients.discard(d)
MATOMO_URL=os.getenv('MATOMO_URL',''); MATOMO_SITE_ID=os.getenv('MATOMO_SITE_ID',''); MATOMO_TOKEN=os.getenv('MATOMO_TOKEN','')
def track_order_matomo(order_id:int,total:float):
  if not MATOMO_URL or not MATOMO_SITE_ID: return
  try:
    params={'idsite':MATOMO_SITE_ID,'rec':1,'ecommerce':1,'idgoal':0,'ec_id':str(order_id),'revenue':total,'url':'https://restaurant.bibabau.ch/checkout-success','action_name':'Order Completed (Server)'}
    if MATOMO_TOKEN: params['token_auth']=MATOMO_TOKEN
    requests.get(MATOMO_URL,params=params,timeout=3)
  except Exception: pass
@app.post('/orders')
async def create_order(order:OrderIn,background:BackgroundTasks,db:Session=Depends(get_db),user:User|None=Depends(get_current_user)):
  try: pickup_dt=dt.fromisoformat(order.pickup_at)
  except Exception: raise HTTPException(422,'pickup_at must be ISO8601 with timezone')
  if pickup_dt < (now_zrh()+timedelta(minutes=30)): raise HTTPException(422,'pickup_at must be at least 30 minutes from now')
  ids=[it.menu_item_id for it in order.items]
  menu_map={m.id:m for m in db.query(MenuItem).filter(MenuItem.id.in_(ids)).all()}
  if len(menu_map)!=len(ids): raise HTTPException(400,'unknown menu_item_id')
  new=Order(status=OrderStatus.NEW,pickup_at=pickup_dt,notes=order.notes or '',user_id=user.id if user else None)
  total=0.0; lines=[]
  for oi in order.items:
    m=menu_map[oi.menu_item_id]; new.items.append(OrderItem(menu_item_id=m.id,name_snapshot=m.name,unit_price_chf=m.price_chf,qty=oi.qty))
    total+=m.price_chf*oi.qty; lines.append({'name':m.name,'unit_price':m.price_chf,'qty':oi.qty})
  new.total_chf=round(total,2); db.add(new); db.commit(); db.refresh(new)
  payload={'type':'order_created','order':{'id':new.id,'status':new.status.value,'pickup_at':new.pickup_at.isoformat(),'total_chf':new.total_chf}}
  await notify_kitchen(payload)
  def _mail():
    try:
      pickup_local=new.pickup_at.astimezone(now_zrh().tzinfo).strftime('%d.%m.%Y %H:%M')
      ctx={'order':{'id':new.id,'pickup_at_local':pickup_local,'total':new.total_chf,'notes':new.notes},'items':lines,'customer':{'email':getattr(user,'email',None),'name':getattr(user,'name',None)} if user else None}
      to=os.getenv('KITCHEN_EMAIL','');
      if to: send_mail(f'NEUE BESTELLUNG #{new.id}',to,render('order_kitchen.html',**ctx),'Neue Bestellung')
      if user and user.email: send_mail(f'Deine Bestellung #{new.id}',user.email,render('order_customer.html',**ctx),'Bestellbestätigung')
    except Exception: pass
  background.add_task(_mail); track_order_matomo(new.id,new.total_chf); return payload['order']
@app.get('/orders')
def list_orders(status:OrderStatus|None=None,db:Session=Depends(get_db)):
  q=db.query(Order); q=q.filter(Order.status==status) if status else q
  q=q.order_by(Order.created_at.desc())
  return [{'id':o.id,'status':o.status.value,'pickup_at':o.pickup_at.isoformat(),'total_chf':o.total_chf} for o in q.all()]
@app.get('/orders/me')
def my_orders(db:Session=Depends(get_db),user:User|None=Depends(get_current_user)):
  if not user: raise HTTPException(401,'auth required')
  q=db.query(Order).filter(Order.user_id==user.id).order_by(Order.created_at.desc())
  return [{'id':o.id,'status':o.status.value,'pickup_at':o.pickup_at.isoformat(),'total_chf':o.total_chf} for o in q.all()]
@app.patch('/orders/{order_id}/status')
async def update_status(order_id:int,status:OrderStatus,db:Session=Depends(get_db)):
  o=db.get(Order,order_id)
  if not o: raise HTTPException(404,'order not found')
  o.status=status; db.commit(); await notify_kitchen({'type':'order_status','order_id':order_id,'status':status.value}); return {'ok':True}
@app.websocket('/ws/kitchen')
async def ws_kitchen(ws:WebSocket):
  await ws.accept(); kitchen_clients.add(ws)
  try:
    while True: await ws.receive_text()
  except WebSocketDisconnect: kitchen_clients.discard(ws)
@app.get('/')
def root(): return {'ok':True}
HEALTH_MAIL_TOKEN=os.getenv('HEALTH_MAIL_TOKEN','')
@app.post('/health/mail')
def health_mail(to:str,x_health_token:str=Header(None)):
  if not HEALTH_MAIL_TOKEN or x_health_token!=HEALTH_MAIL_TOKEN: raise HTTPException(401,'unauthorized')
  ok=send_mail('SMTP Health',to,'<b>SMTP ok</b>','SMTP ok'); return {'sent':bool(ok)}
