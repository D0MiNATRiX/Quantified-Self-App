import os
import datetime
import pytz
import matplotlib.pyplot as plt
from flask import Flask,render_template,request,redirect
from flask_sqlalchemy import SQLAlchemy

current_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(current_dir, "finalproject.sqlite3") 
db = SQLAlchemy()
db.init_app(app)
app.app_context().push()

class users(db.Model):
  __tablename__='Users'
  user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
  user_name=db.Column(db.String,unique=True,nullable=False)
  password=db.Column(db.String,unique=True,nullable=False)

class trackers(db.Model):
  __tablename__='Trackers'
  tracker_id=db.Column(db.Integer,autoincrement=True,primary_key=True)
  tracker_name=db.Column(db.String,nullable=False)
  last_tracked=db.Column(db.String,nullable=False)
  user_name=db.Column(db.String,db.ForeignKey('Users.user_id'),nullable=False)
  tracker_description=db.Column(db.String)
  tracker_type=db.Column(db.String,nullable=False)
  tracker_settings=db.Column(db.String)

class logs(db.Model):
  __tablename__='Logs'
  log_id=db.Column(db.Integer,autoincrement=True,primary_key=True)
  tracker_id=db.Column(db.Integer,db.ForeignKey('Trackers.tracker_id'),nullable=False)
  log_time=db.Column(db.String,nullable=False)
  log_value=db.Column(db.String,nullable=False)
  log_notes=db.Column(db.String)
  
@app.route('/')
def home():
  return render_template('home.html')

@app.route('/login',methods=['GET','POST'])
def login():
  if(request.method=='GET'):
    return render_template('login.html')
  if(request.method=='POST'):
    uname=request.form.get('uname')
    passw=request.form.get('pass')
    us=users.query.filter_by(user_name=uname).first()
    if(us==None or us.password!=passw):
      return render_template('loginerror.html')
    else:
      url='/dashboard/'+uname
      return redirect(url)

@app.route('/new_user',methods=['GET','POST'])
def newuser():
  if(request.method=='GET'):
    return render_template('newuser.html')
  if(request.method=='POST'):
    uname=request.form.get('uname')
    psw=request.form.get('pass')
    us=users.query.filter_by(user_name=uname).all()
    if(len(us)==0):
      u=users(user_name=uname,password=psw)
      db.session.add(u)
      db.session.commit()
      return redirect('/login')
    else:
      return render_template('newusererror.html')

@app.route('/dashboard/<string:user_name>',methods=['GET','POST'])
def dashboard(user_name):
  if(request.method=='GET'):
    t=trackers.query.filter_by(user_name=user_name).all()
    return render_template('dashboard.html',name=user_name,trackers=t)
  if(request.method=='POST'):
    return redirect('/')

@app.route('/dashboard/<string:user_name>/add_tracker/',methods=['GET','POST'])
def addtracker(user_name):
  if(request.method=='GET'):
    return render_template('addtracker.html',name=user_name)
  if(request.method=='POST'):
    tname=request.form.get('tname')
    tdes=request.form.get('des')
    ttype=request.form.get('Type')
    tset=request.form.get('set')
    lt='Today'
    t=trackers(tracker_name=tname,last_tracked=lt,user_name=user_name,tracker_description=tdes,tracker_type=ttype,tracker_settings=tset)
    db.session.add(t)
    db.session.commit()
    url='/dashboard/'+user_name
    return redirect(url)

@app.route('/dashboard/<string:user_name>/edit_tracker/<int:tracker_id>',methods=['GET','POST'])
def edittraccker(user_name,tracker_id):
  if(request.method=='GET'):
    t=trackers.query.filter_by(tracker_id=tracker_id).first()
    return render_template('edittracker.html',name=user_name,tracker=t)
  if(request.method=='POST'):
    tname=request.form.get('tname')
    tdes=request.form.get('des')
    ttype=request.form.get('Type')
    tset=request.form.get('set')
    lt='Today'
    trackers.query.filter_by(tracker_id=tracker_id).update(dict(tracker_name=tname,last_tracked=lt,user_name=user_name,tracker_description=tdes,tracker_type=ttype,tracker_settings=tset))
    db.session.commit()
    url='/dashboard/'+user_name
    return redirect(url)

@app.route('/dashboard/<string:user_name>/delete_tracker/<int:tracker_id>')
def deletetracker(user_name,tracker_id):
  trackers.query.filter_by(tracker_id=tracker_id).delete()
  logs.query.filter_by(tracker_id=tracker_id).delete()
  db.session.commit()
  url='/dashboard/'+user_name
  return redirect(url)

@app.route('/dashboard/<string:user_name>/display_tracker/<int:tracker_id>')
def displaytracker(user_name,tracker_id):
  t=trackers.query.filter_by(tracker_id=tracker_id).first()
  l=logs.query.filter_by(tracker_id=tracker_id).all()
  d={}
  for i in l:
    d[i.log_time]=i.log_value
  dict={}
  for i in sorted(d.keys()):
    if(t.tracker_type=='num' or t.tracker_type=='td'):
      dict[i]=int(d[i])
    else:
      dict[i]=d[i]
  plt.plot(dict.keys(),dict.values())
  plt.xlabel('Timestamp →')
  plt.ylabel('Values →')
  plt.savefig('static/graph.png')
  plt.close()
  return render_template('displaytracker.html',name=user_name,tracker=t,logs=l)

@app.route('/dashboard/<string:user_name>/display_tracker/<int:tracker_id>/today')
def today(user_name,tracker_id):
  t=trackers.query.filter_by(tracker_id=tracker_id).first()
  l=logs.query.filter_by(tracker_id=tracker_id).all()
  today=str(datetime.datetime.now(pytz.timezone('Asia/Kolkata')))[:10]
  d={}
  for i in l:
    if(i.log_time[:10]==today[:10]):
      d[i.log_time]=i.log_value
  dict={}
  for i in sorted(d.keys()):
    dict[i]=int(d[i])
  plt.plot(dict.keys(),dict.values())
  plt.xlabel('Timestamp →')
  plt.ylabel('Values →')
  plt.savefig('static/graph.png')
  plt.close()
  return render_template('displaytracker.html',name=user_name,tracker=t,logs=l)

@app.route('/dashboard/<string:user_name>/display_tracker/<int:tracker_id>/this_week')
def thisweek(user_name,tracker_id):
  t=trackers.query.filter_by(tracker_id=tracker_id).first()
  l=logs.query.filter_by(tracker_id=tracker_id).all()
  dic={}
  today=str(datetime.datetime.now(pytz.timezone('Asia/Kolkata')))[:10]
  y=int(today[:4])
  m=int(today[5:7])
  d=int(today[8:10])
  for i in l:
    if(datetime.date(y,m,d).isocalendar()[1]==datetime.date(int(i.log_time[:4]),int(i.log_time[5:7]),int(i.log_time[8:10])).isocalendar()[1]):
      dic[i.log_time]=i.log_value
  dict={}
  for i in sorted(dic.keys()):
    dict[i]=int(dic[i])
  plt.plot(dict.keys(),dict.values())
  plt.xlabel('Timestamp →')
  plt.ylabel('Values →')
  plt.savefig('static/graph.png')
  plt.close()
  return render_template('displaytracker.html',name=user_name,tracker=t,logs=l)

@app.route('/dashboard/<string:user_name>/display_tracker/<int:tracker_id>/this_month')
def thismonth(user_name,tracker_id):
  t=trackers.query.filter_by(tracker_id=tracker_id).first()
  l=logs.query.filter_by(tracker_id=tracker_id).all()
  d={}
  thismonth=str(datetime.datetime.now(pytz.timezone('Asia/Kolkata')))[:7]
  for i in l:
    if(i.log_time[:7]==thismonth):
      d[i.log_time]=i.log_value
  dict={}
  for i in sorted(d.keys()):
    dict[i]=int(d[i])
  plt.plot(dict.keys(),dict.values())
  plt.xlabel('Timestamp →')
  plt.ylabel('Values →')
  plt.savefig('static/graph.png')
  plt.close()
  return render_template('displaytracker.html',name=user_name,tracker=t,logs=l)

@app.route('/dashboard/<string:user_name>/log_event/<int:tracker_id>',methods=['GET','POST'])
def logevent(user_name,tracker_id):
  if(request.method=='GET'):
    time=datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
    time=str(time)
    if(int(time[11:13])<12):
      time=time[:10]+' At '+time[11:13]+'am'
    else:
      time=time[:10]+' At '+str(int(time[11:13])-12)+'pm'
    t=trackers.query.filter_by(tracker_id=tracker_id).first()
    v=[]
    if(t.tracker_type!='num'):
      v=t.tracker_settings.split(',')
    return render_template('logevent.html',name=user_name,tracker=t,values=v,t=time)
  if(request.method=='POST'):
    ltime=request.form.get('time')
    lvalue=request.form.get('value')
    lnotes=request.form.get('notes')
    l=logs(tracker_id=tracker_id,log_time=ltime,log_value=lvalue,log_notes=lnotes)
    db.session.add(l)
    db.session.commit()
    url='/dashboard/'+user_name
    return redirect(url)

@app.route('/dashboard/<string:user_name>/<int:tracker_id>/edit_log/<int:log_id>',methods=['GET','POST'])
def editlog(user_name,log_id,tracker_id):
  if(request.method=='GET'):
    time=datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
    time=str(time)
    if(int(time[11:13])<12):
      time=time[:10]+' At '+time[11:13]+'am'
    else:
      time=time[:10]+' At '+str(int(time[11:13])-12)+'pm'
    l=logs.query.filter_by(log_id=log_id).first()
    t=trackers.query.filter_by(tracker_id=tracker_id).first()
    v=[]
    if(t.tracker_type!='num'):
      v=t.tracker_settings.split(',')
    return render_template('editlog.html',name=user_name,log=l,tracker=t,values=v,t=time)
  if(request.method=='POST'):
    ltime=request.form.get('time')
    lvalue=request.form.get('value')
    lnotes=request.form.get('notes')
    logs.query.filter_by(log_id=log_id).update(dict(tracker_id=tracker_id,log_time=ltime,log_value=lvalue,log_notes=lnotes))
    db.session.commit()
    url='/dashboard/'+user_name+'/display_tracker/'+str(tracker_id)
    return redirect(url)

@app.route('/dashboard/<string:user_name>/<int:tracker_id>/delete_log/<int:log_id>')
def deletelog(user_name,tracker_id,log_id):
  logs.query.filter_by(log_id=log_id).delete()
  db.session.commit()
  url='/dashboard/'+user_name+'/display_tracker/'+str(tracker_id)
  return redirect(url)

if __name__=='__main__':
  app.run(host='0.0.0.0')