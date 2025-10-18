from sqlalchemy import Column,Integer,String,Float,DateTime,ForeignKey,Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import enum
class OrderStatus(str, enum.Enum):
  NEW='NEW';IN_PROGRESS='IN_PROGRESS';READY='READY';PICKED_UP='PICKED_UP';CANCELLED='CANCELLED'
class User(Base):
  __tablename__='users'
  id=Column(Integer,primary_key=True)
  email=Column(String,unique=True,nullable=False)
  password_hash=Column(String,nullable=False)
  name=Column(String)
  phone=Column(String)
  orders=relationship('Order',back_populates='user')
class MenuCategory(Base):
  __tablename__='menu_categories'
  id=Column(Integer,primary_key=True)
  name=Column(String,nullable=False)
  position=Column(Integer,default=0)
  items=relationship('MenuItem',back_populates='category')
class MenuItem(Base):
  __tablename__='menu_items'
  id=Column(Integer,primary_key=True)
  category_id=Column(Integer,ForeignKey('menu_categories.id'))
  name=Column(String,nullable=False)
  description=Column(String,default='')
  price_chf=Column(Float,nullable=False)
  is_active=Column(Integer,default=1)
  category=relationship('MenuCategory',back_populates='items')
class Order(Base):
  __tablename__='orders'
  id=Column(Integer,primary_key=True)
  user_id=Column(Integer,ForeignKey('users.id'))
  status=Column(Enum(OrderStatus),default=OrderStatus.NEW)
  pickup_at=Column(DateTime(timezone=True))
  total_chf=Column(Float,default=0.0)
  notes=Column(String,default='')
  created_at=Column(DateTime(timezone=True),default=datetime.utcnow)
  items=relationship('OrderItem',back_populates='order',cascade='all, delete-orphan')
  user=relationship('User',back_populates='orders')
class OrderItem(Base):
  __tablename__='order_items'
  id=Column(Integer,primary_key=True)
  order_id=Column(Integer,ForeignKey('orders.id'))
  menu_item_id=Column(Integer,ForeignKey('menu_items.id'))
  name_snapshot=Column(String,nullable=False)
  unit_price_chf=Column(Float,nullable=False)
  qty=Column(Integer,nullable=False)
  order=relationship('Order',back_populates='items')
