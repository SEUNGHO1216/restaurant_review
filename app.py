import math

import bcrypt
import pymongo
from bson import json_util
from bson.objectid import ObjectId
from bson.json_util import dumps
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_bcrypt import Bcrypt
import time
from PIL import Image
import re
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

from pymongo import MongoClient
client = MongoClient('mongodb+srv://test:sparta@cluster0.okxdx.mongodb.net/Cluster0?retryWrites=true&w=majority')
db = client.dbreview

app.secret_key = '19wjsck!!'

@app.route('/index', methods=["GET"])
@app.route('/', methods=["GET"])
def index():
    page = request.args.get('page', 1, type=int)
    limit = 8
    result = list(db.boards.find().skip((page-1)*limit).limit(limit).sort('_id', -1))
    resultLength = list(db.boards.find().sort('_id', -1))

    total_cnt=len(resultLength)
    last_page=math.ceil(total_cnt/limit)
    block_size = 5
    block_num = int((page - 1) / block_size)  # 페이지가 속한 블럭(통)이 여러개 중 몇번째 블럭인지
    block_start = (block_size * block_num) + 1
    block_end = block_start + (block_size - 1)
    return render_template('index.html',result=result,limit=limit, page=page,
                               block_start=block_start, block_end=block_end, last_page=last_page)

@app.route('/boards')
def boards():
        boardsAll = list(db.boards.find().sort('_id',-1))
        # boardsAll = list(db.boards.find({}).sort({'_id':-1}))
        # json.loads(json_util.dumps(data))
        # db.getCollection('wow').find({}).sort({_id: -1}) 내림차순 조회
        if boardsAll != "":
            print(boardsAll)
            return jsonify({'boards': dumps(boardsAll)})
# @app.route('/searchmain')
# def searchmain():
#     return render_template('search.html')

@app.route('/search', methods=["GET"])
def search():
    selectbox = request.args.get('selectbox')
    textbox = request.args.get('textbox')
    sortbox = request.args.get('sorting')
    page = request.args.get('page',1,type=int)
    limit = 8
    block_size=5
    block_num=int((page-1)/block_size) #페이지가 속한 블럭(통)이 여러개 중 몇번째 블럭인지
    block_start=(block_size*block_num)+1
    block_end=block_start+(block_size-1)
    if selectbox != "전체" and textbox !="":
        result = list(db.boards.find({selectbox: {'$regex': textbox}}).skip((page-1)*limit).limit(limit).sort([(sortbox, pymongo.DESCENDING),('_id', pymongo.DESCENDING)])) #like와 같은기능 정규표현식
        resultLenght = list(db.boards.find({selectbox: {'$regex': textbox}}).sort([(sortbox, pymongo.DESCENDING),('_id', pymongo.DESCENDING)])) #like와 같은기능 정규표현식
        print(result)
        total_count=len(resultLenght)
        last_page=math.ceil(total_count/limit)
        print(page, block_start, block_end, total_count,last_page)
        if total_count==0:
            return render_template('result.html',msg='검색 결과가 없습니다.')
        return render_template('search.html',result=result,limit=limit, page=page,
                               block_start=block_start, block_end=block_end, last_page=last_page,
                               selectbox=selectbox, textbox=textbox, sortbox=sortbox)

    elif selectbox == "전체" and textbox !="": #전체로 검색한 경우
        result = list(db.boards.find({
            '$or':[
                {'title': {'$regex':textbox}},
                {'noTagCon':{'$regex': textbox}}]
        }).skip((page-1)*limit).limit(limit).sort([(sortbox, pymongo.DESCENDING),('_id', pymongo.DESCENDING)]))
        resultLength = list(db.boards.find({
            '$or': [
                {'title': {'$regex': textbox}},
                {'noTagCon': {'$regex': textbox}}]
        }).sort([(sortbox, pymongo.DESCENDING), ('_id', pymongo.DESCENDING)]))
        print(result)
        total_count = len(resultLength)
        last_page = math.ceil(total_count / limit)
        if total_count == 0:
            return render_template('result.html', msg='검색 결과가 없습니다.')
        return render_template('search.html', result=result, limit=limit, page=page,
                               block_start=block_start, block_end=block_end, last_page=last_page,
                               selectbox=selectbox, textbox=textbox, sortbox=sortbox)

    else: #검색어 입력 안했을시
        result = list(db.boards.find().skip((page-1)*limit).limit(limit).sort([(sortbox, pymongo.DESCENDING),('_id', pymongo.DESCENDING)]))
        resultLength = list(db.boards.find().sort([(sortbox, pymongo.DESCENDING),('_id', pymongo.DESCENDING)]))
        total_count = len(resultLength)
        last_page = math.ceil(total_count / limit)
        return render_template('search.html', result=result, limit=limit, page=page,
                               block_start=block_start, block_end=block_end, last_page=last_page,
                               selectbox=selectbox, textbox=textbox, sortbox=sortbox)

@app.route('/register', methods=["POST","GET"])
def register():
    if 'id' in session:
        return redirect(url_for('index'))
    msg = ''
    if request.method == "POST":
        id = request.form['id']
        pw = request.form['password']
        if id == "" or pw == "":
            return redirect(url_for('register'))
        result = db.users.find_one({'id': id})
        if result:
            msg='동일한 아이디가 존재합니다.'
            return render_template('register.html', msg=msg)
        else:
            hashed=bcrypt.hashpw(pw.encode('utf-8'),bcrypt.gensalt())
            doc = {
                'id': id,
                'pw': hashed
            }
            db.users.insert_one(doc)
            msg = id + '님 회원가입을 축하합니다!!'
            return render_template('result.html', msg=msg)
    return render_template('register.html')

@app.route('/idCheck', methods=["POST"])
def idCheck():
    if request.method == "POST":
        id = request.form['id']
        if id == "":
            return redirect(url_for('register'))
        result = db.users.find_one({'id': id})
        if result:
            msg = '동일한 아이디가 이미 있습니다'
            return jsonify({'msg':msg})
        else:
            msg = '사용가능한 아이디입니다.'
            return jsonify({'msg':msg})

@app.route('/login', methods=["POST", "GET"])
def login():
    if 'id' in session:
        return redirect(url_for('index'))
    msg=''
    if request.method=="POST":
        input_id = request.form['id']
        input_pw = request.form['password']
        if input_id=="" or input_pw=="":
            return redirect(url_for('login'))

        user_info = db.users.find_one({'id': input_id})
        print(user_info)

        if not user_info :
            msg='아이디 정보가 없습니다.'
            return render_template('login.html',msg=msg)
        else:
            id = user_info["id"]
            pw = user_info["pw"]

            if bcrypt.checkpw(input_pw.encode('utf-8'),pw):
                session['id'] = id
                msg = '로그인 성공!'
                return redirect(url_for('index'))
            else:
                msg = '비밀번호를 잘못 입력하셨습니다.'
            return render_template('login.html',msg=msg)

    return render_template('login.html',msg=msg)

@app.route('/logout')
def logout():
    if 'id' in session:
        session.pop('id', None)
        return redirect(url_for('index'))
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
def upload():
    if 'id' not in session:
        msg='로그인 후 작성가능합니다'
        return jsonify({'msg':msg})
    else:
        print(session)
        if request.method=="POST":
            title=request.form['title']
            writer=session['id']
            contents=request.form['contents']

            a= re.findall("(<img[^>]+src\s*=\s*[\"']?([^>\"']+)[\"']?[^>]*>)",contents)
            if len(a)==0:
                image="https://missioninfra.net/img/noimg/noimg_fac.gif"
            else:
                image=a[0][1]
            print(image)
            # , {'src': re.compile("<img[^>]*src=[\"']?([^>\"']+)[\"']?[^>]*>")}
            comment=request.form['comment']
            # con = re.sub(pattern='(<([^>]+)>)', repl='', string=contents)
            con = re.sub('<(/)?([a-zA-Z0-9]*)(\\s[a-zA-Z0-9]*=[^>]*)?(\\s)*(/)?>','',contents)
            con = re.sub('&nbsp;', ' ', con)
            print(con)
            pubdate=time.strftime('%y%m%d_%H:%M:%S')
            if title =="" or contents =="<p><br></p>":
                return jsonify({'msg':'입력오류'})
            print(type(title),writer,type(contents),pubdate)
            doc={
                'title':title,
                'writer':writer,
                'comment':comment,
                'content':contents,
                'image': image,
                'noTagCon':con,
                'view_cnt': 0,
                'likey':[],
                'pubdate':pubdate
            }
            boardsInsert=db.boards.insert_one(doc)
            return redirect(url_for('detail',idx = boardsInsert.inserted_id))

        # return redirect(url_for('upload'))

@app.route('/upload', methods=['GET'])
def upload_get():
    if 'id' not in session:
        return redirect(url_for('login',next='/upload'))
    else:
        return render_template('upload.html')

@app.route("/addImgSummer", methods=["POST"])
def addImgSummer():
    img = request.files["file"]
    image=Image.open(img)
    # form=img.filename.split('.')[1]
    # print(form, img.filename)
    image.save('./static/'+img.filename)
    imgURL = 'http://sparta-restaurant.shop/static/'+img.filename
    # db.boards.update_one({'_id':},{'$set':{'img':imgURL}})
    print(imgURL)
    return jsonify(url = imgURL)

@app.route('/detail/<idx>',methods=['GET'])
def detail(idx):
    if db.boards.find_one({'_id':ObjectId(idx)}):
        boards_data = db.boards.find_one({'_id': ObjectId(idx)})
        view = boards_data.get('view_cnt')
        view += 1
        db.boards.update_one({'_id': ObjectId(idx)},{'$set':{'view_cnt':view}})
        if boards_data != "":
            doc = {
                'id':boards_data.get('_id'),
                'title':boards_data.get('title'),
                'writer' : boards_data.get('writer'),
                'comment' : boards_data.get('comment'),
                'content' : boards_data.get('content'),
                'noTagCon' : boards_data.get('noTagCon'),
                'view_cnt' : boards_data.get('view_cnt'),
                'likey' : boards_data.get('likey'),
                'pubdate' : boards_data.get('pubdate')
            }
            return render_template('detail.html', doc=doc)
        # return render_template("detail.html")
    if not request.args.get("idx"):
        msg='게시물 정보 오류로 페이지 전환 이상 발생'
        return render_template('result.html',msg=msg)


@app.route('/likey/<idx>')
def likey(idx):
    db.boards.update_one({'_id':ObjectId(idx)},{'$push' : {'likey':session['id']}})
    boards_data = db.boards.find_one({'_id': ObjectId(idx)})
    view=boards_data.get('view_cnt')
    view-=1
    db.boards.update_one({'_id': ObjectId(idx)}, {'$set': {'view_cnt': view}})

    # likey_cnt=len(db.boards.find_one({'_id':ObjectId(idx)})['likey'])
    # return jsonify({'likey_cnt':likey_cnt})
    return redirect(url_for('detail', idx=idx))

@app.route('/unlikey/<idx>')
def unlikey(idx):
    db.boards.update_one({'_id':ObjectId(idx)},{'$pull':{'likey':session['id']}})
    boards_data = db.boards.find_one({'_id': ObjectId(idx)})
    view = boards_data.get('view_cnt')
    view -= 1
    db.boards.update_one({'_id': ObjectId(idx)}, {'$set': {'view_cnt': view}})
    return redirect(url_for('detail', idx=idx))

@app.route('/update/<idx>', methods=["GET", "POST"])
def update(idx):
    boards_data = db.boards.find_one({'_id': ObjectId(idx)})
    if request.method == "POST":
        title=request.form['title']
        comment=request.form['comment']
        content=request.form['contents']
        a = re.findall("(<img[^>]+src\s*=\s*[\"']?([^>\"']+)[\"']?[^>]*>)", content)
        if len(a) == 0:
            image = "https://missioninfra.net/img/noimg/noimg_fac.gif"
        else:
            image = a[0][1]
        con = re.sub('<(/)?([a-zA-Z0-9]*)(\\s[a-zA-Z0-9]*=[^>]*)?(\\s)*(/)?>', '', content)
        con = re.sub('&nbsp;', ' ', con)
        pubdate = time.strftime('%y%m%d_%H:%M:%S')
        print(type(pubdate))
        print(title, comment, pubdate)
        if title == "" or content == "<p><br></p>":
            return jsonify({'msg': '입력오류'})
        doc = {
            'id': boards_data.get('_id'),
            'title': title,
            'writer': boards_data.get('writer'),
            'comment': comment,
            'content': content,
            'image': image,
            'noTagCon': con,
            'view_cnt': boards_data.get('view_cnt'),
            'likey': boards_data.get('likey'),
            'pubdate': pubdate
        }
        db.boards.update_one({'_id': ObjectId(idx)},{'$set':doc})
        return render_template('detail.html', doc=doc)
    doc = {
        'id': boards_data.get('_id'),
        'title': boards_data.get('title'),
        'writer': boards_data.get('writer'),
        'comment': boards_data.get('comment'),
        'content': boards_data.get('content'),
        'noTagCon': boards_data.get('noTagCon'),
        'view_cnt': boards_data.get('view_cnt'),
        'likey': boards_data.get('likey'),
        'pubdate': boards_data.get('pubdate')
    }
    return render_template('update.html',doc=doc)

@app.route("/delete/<idx>")
def delete(idx):
    db.boards.delete_one({'_id': ObjectId(idx)})
    return redirect(url_for('index'))



if __name__=="__main__":
    app.run('0.0.0.0', port=5000, debug=True)
