from flask import Flask, render_template,request, send_from_directory, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import timedelta, timezone,datetime
import json
import os
import pytz
import random
import time

app = Flask(__name__)
# 初期設定
## 利用するDB設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///body.db'
## メモリ利用を抑える
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
## log出力
app.config['SQLALCHEMY_ECHO']=False

db = SQLAlchemy(app)

class Shelter(db.Model):
    def generate_random_id():
        return random.randint(1, 1000000)
    
    # id = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.Integer, primary_key=True, default=generate_random_id)
    shelter = db.Column(db.String(128), nullable=False)
    num = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.timezone("Asia/Tokyo")))
    user = db.Column(db.String(128), nullable=False)
    ## シェルターのユーザ情報を追加

class ShelterLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shelter = db.Column(db.String(128), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

class User_Info(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    age = db.Column(db.String(128), nullable=False)

@app.route('/')
def start():
	shelter_list = ShelterLocation.query.with_entities(ShelterLocation.shelter).distinct().all()
	return render_template('start.html', shelter_list=shelter_list)

@app.route('/init')
def init():
    return render_template('add_user.html')

@app.route('/add_user', methods=['POST'])
def add_user():
    print("test")
    name = request.form['name']
    age = request.form['age']
    # print(name)
    # print(age)
    Info=User_Info(name=name, age=age)
    db.session.add(Info)
    db.session.commit()
    # time.sleep(10)
    return render_template('start.html')

@app.route('/upload_data', methods=['POST'])
def upload_data():
    try:
        data = request.json
        shelter = data['shelter']
        uploaded_data = data['data']
        uploaded_data['created_at'] = datetime.strptime(uploaded_data['created_at'], '%Y-%m-%d %H:%M:%S.%f')
        user = data['user']
        print(data)
        # TODO: ここでデータを処理するための任意の処理を実装

        # データベースに保存
        new_entry = Shelter(shelter=shelter, num=uploaded_data['num'], created_at=uploaded_data['created_at'],user=user['name'])
        db.session.add(new_entry)
        db.session.commit()

        response = {'status': 'success', 'message': 'Data uploaded successfully'}
        return jsonify(response)

    except Exception as e:
        error_message = f'Error uploading data: {str(e)}'
        response = {'status': 'error', 'message': error_message}
        return jsonify(response), 500

@app.route('/home')
def index():
	# data = Shelter.query.all()
	# print(data)
    # 各 shelter ごとに一番新しいデータを選択
    # TODO
    # IDではなく、一番新しいデータをみろ。
    
    # 最新のShelter.created_atの時間を取得
    latest_data = db.session.query(
        Shelter.shelter,
        func.max(Shelter.created_at).label('latest_created_at')
    ).group_by(Shelter.shelter).all()

    # 対応する最新のデータを取得
    data = []
    for shelter, latest_created_at in latest_data:
        latest_entry = Shelter.query.filter_by(shelter=shelter, created_at=latest_created_at).first()
        data.append(latest_entry)
        
    location_data = ShelterLocation.query.all()
    return render_template('index.html',data=data,location_data=location_data)

@app.route('/add', methods=['POST'])
def add():
    created_at = datetime.now(pytz.timezone("Asia/Tokyo"))
    shelter = request.form['shelter']
    num = request.form['num']
    new_shelter = Shelter(shelter=shelter,num=num,created_at=created_at)
    db.session.add(new_shelter)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/del_body/<int:id>')
def del_body(id):
	del_data = Shelter.query.filter_by(id=id).first()
	db.session.delete(del_data)
	db.session.commit()
	return redirect(url_for('index'))

@app.route('/locations')
def locations():
    location_data = ShelterLocation.query.all()
    return render_template('locations.html', location_data=location_data)

@app.route('/add_location', methods=['GET', 'POST'])
def add_location():
    if request.method == 'POST':
        shelter = request.form['shelter']
        latitude = float(request.form['latitude'])
        longitude = float(request.form['longitude'])

        # 既存のデータがあれば更新、なければ新規追加
        existing_location = ShelterLocation.query.filter_by(shelter=shelter).first()
        if existing_location:
            existing_location.latitude = latitude
            existing_location.longitude = longitude
        else:
            new_location = ShelterLocation(shelter=shelter, latitude=latitude, longitude=longitude)
            db.session.add(new_location)

        db.session.commit()

        return redirect(url_for('locations'))

    return render_template('add_location.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8001)