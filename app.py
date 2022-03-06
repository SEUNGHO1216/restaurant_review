import math
import os

import bcrypt
import pymongo
from bson import json_util
from bson.objectid import ObjectId
from bson.json_util import dumps
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, send_file
from flask_bcrypt import Bcrypt
import time
from PIL import Image
import re
from werkzeug.utils import secure_filename
from pytz import timezone
from datetime import datetime


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
        if boardsAll != "":
            print(boardsAll)
            return jsonify({'boards': dumps(boardsAll)})


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
                {'noTagCon':{'$regex': textbox}},
                {'category':{'$regex': textbox}}]
        }).skip((page-1)*limit).limit(limit).sort([(sortbox, pymongo.DESCENDING),('_id', pymongo.DESCENDING)]))
        resultLength = list(db.boards.find({
            '$or': [
                {'title': {'$regex': textbox}},
                {'noTagCon': {'$regex': textbox}},
                {'category':{'$regex': textbox}}]
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
@app.route('/loginReply', methods=["POST"])
def loginReply():
    if request.method=="POST":
        input_id = request.form['id']
        input_pw = request.form['pw']
        if input_id=="" or input_pw=="":
            msg='아이디와 비밀번호를 입력하세요!'
            return jsonify({'msg':msg})

        user_info = db.users.find_one({'id': input_id})

        if not user_info :
            msg='아이디 정보가 없습니다.'
            return jsonify({'msg':msg})
        else:
            id = user_info["id"]
            pw = user_info["pw"]
            if bcrypt.checkpw(input_pw.encode('utf-8'),pw):
                session['id'] = id
                msg = '로그인이 완료되었습니다!'
                return jsonify({'msg':msg})
            else:
                msg = '비밀번호를 잘못 입력하셨습니다.'
            return jsonify({'msg':msg})
@app.route('/addReply/<idx>/<page>',methods=['POST'])
def addReply(idx,page):
    if request.method=="POST":
        context = request.form['con']
        context=context.replace("\n","   ")
        print(list(context))
        doc={
            'writer': session['id'],
            'context': context,
            'pubdate' : datetime.now(timezone('Asia/Seoul')).strftime('%y%m%d_%H:%M:%S')
        }
        replyInfo = db.replies.insert_one(doc)
        db.boards.update_one({'_id':ObjectId(idx)},{'$addToSet':{'rid':replyInfo.inserted_id}})
        db.users.update_one({'id':session['id']},{'$addToSet':{'rid':replyInfo.inserted_id}})
        return jsonify({'msg': '댓글 추가 완료했습니다.'})

@app.route('/editReply',methods=['POST'])
def editReply():
    if request.method=="POST":
        context = request.form['con']
        context = context.replace("\n", "   ")
        rid = request.form['rid']
        print(context, rid)
        replyInfo=db.replies.find_one({'_id':ObjectId(rid)})
        doc={
            'writer': session['id'],
            'context': context,
            'pubdate' : replyInfo.get('pubdate'),
            'updateDt' : datetime.now(timezone('Asia/Seoul')).strftime('%y%m%d_%H:%M:%S')
        }
        db.replies.update_one({'_id':ObjectId(rid)},{'$set':doc})
        return jsonify({'msg': '댓글 수정 완료했습니다.'})

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
            category = request.form['category']
            print('category:', request.form['category'])
            if category:
                categ=category
            else:
                categ='미선택'

            a= re.findall("(<img[^>]+src\s*=\s*[\"']?([^>\"']+)[\"']?[^>]*>)",contents)
            if len(a)==0:
                image="https://missioninfra.net/img/noimg/noimg_fac.gif"
            else:
                image=a[0][1]
            comment=request.form['comment']
            con = re.sub('<(/)?([a-zA-Z0-9]*)(\\s[a-zA-Z0-9]*=[^>]*)?(\\s)*(/)?>','',contents)
            con = re.sub('&nbsp;', ' ', con)
            print(con)
            pubdate=datetime.now(timezone('Asia/Seoul')).strftime('%y%m%d_%H:%M:%S')
            print('pubdate:',pubdate)

            file=request.files.getlist("file")
            print(file)
            files = os.listdir('./static/files')
            insertFile=[]
            if len(file)!=0:
                for i in file:
                    if i.filename:
                        i.save('./static/files/' + i.filename)
                        insertFile.append(i.filename)
                    else:
                        print('empty file list')
            else:
                print('no inserted file')
            mapPlace=request.form['inputPlace']
            mapAddress=request.form['inputAddress']
            mapUrl=request.form['inputUrl']
            map={}
            map['place']=mapPlace
            map['address']=mapAddress
            map['url']=mapUrl
            print(map)
            # dbUser=db.users.find_one({'id':session['id']})
            # userId=dbUser.get('_id')
            # print(userId)

            if title =="" or contents =="<p><br></p>":
                return jsonify({'msg':'입력오류'})
            print(type(title),writer,type(contents),pubdate)
            doc={

                'title':title,
                'writer':writer,
                'comment':comment,
                'content':contents,
                'category':categ,
                'image': image,
                'noTagCon':con,
                'view_cnt': 0,
                'likey':[],
                'pubdate':pubdate,
                'file':insertFile,
                'map':map,
                # 'userId': userId
            }
            boardsInsert=db.boards.insert_one(doc)

            db.users.update_one({'id':session['id']},{'$addToSet': {'bid':boardsInsert.inserted_id}})

            return redirect(url_for('detail',idx = boardsInsert.inserted_id,page=1))

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

@app.route('/detail/<idx>/<page>',methods=['GET'])
def detail(idx,page):
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
                'pubdate' : boards_data.get('pubdate'),
                'uptdate': boards_data.get('uptdate'),
                'file' : boards_data.get('file'),
                'map': boards_data.get('map'),
                'category':boards_data.get('category')
            }
        if boards_data.get('rid'):
            reply_list=list(db.replies.find({'_id':{'$in': boards_data.get('rid')}}))
            print(reply_list)
            return render_template('detail.html', doc=doc, page=page, replies=reply_list)
        return render_template('detail.html', doc=doc, page=page)
    if not request.args.get("idx"):
        msg='게시물 정보 오류로 페이지 전환 이상 발생'
        return render_template('result.html',msg=msg)


@app.route('/likey/<idx>/<page>')
def likey(idx, page):
    db.boards.update_one({'_id':ObjectId(idx)},{'$push' : {'likey':session['id']}})
    boards_data = db.boards.find_one({'_id': ObjectId(idx)})
    view=boards_data.get('view_cnt')
    view-=1
    db.boards.update_one({'_id': ObjectId(idx)}, {'$set': {'view_cnt': view}})

    # likey_cnt=len(db.boards.find_one({'_id':ObjectId(idx)})['likey'])
    # return jsonify({'likey_cnt':likey_cnt})
    return redirect(url_for('detail', idx=idx, page=page))

@app.route('/unlikey/<idx>/<page>')
def unlikey(idx, page):
    db.boards.update_one({'_id':ObjectId(idx)},{'$pull':{'likey':session['id']}})
    boards_data = db.boards.find_one({'_id': ObjectId(idx)})
    view = boards_data.get('view_cnt')
    view -= 1
    db.boards.update_one({'_id': ObjectId(idx)}, {'$set': {'view_cnt': view}})
    return redirect(url_for('detail', idx=idx, page=page))

@app.route('/update/<idx>/<page>', methods=["GET", "POST"])
def update(idx, page):
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
        pubdate = datetime.now(timezone('Asia/Seoul')).strftime('%y%m%d_%H:%M:%S')
        file = request.files.getlist('file')
        filename= request.form.getlist('filename')
        print('file:',file)
        print('filename:',filename)
        insertFile = []
        if len(filename) != 0: #기존 파일 정보가 있는 상태에서 수정x(다른 파일 추가 x)
            files = os.listdir('./static/files')
            for i in filename:
                if i in files:
                    insertFile.append(i)
            if len(file) != 0:
                for i in file:
                    if i.filename:
                        i.save('./static/files/' + i.filename)
                        insertFile.append(i.filename)
                    else:
                        print('empty file list')
            else:
                print('no inserted file')

        else: #기존 파일 정보 지움
            if len(file)==0: #기존거 지우고 새로운거 추가 x
                insertFile=[]
            else: #기존거 지우고 새로운거 추가 o
                if len(file) != 0:
                    for i in file:
                        if i.filename:
                            i.save('./static/files/' + i.filename)
                            files = os.listdir('./static/files')
                            if i.filename in files:
                                insertFile.append(i.filename)
                            else:
                                print('no inserted file')
                        else:
                            print('empty file list')
                else:
                    print('no file')
        category = request.form['category']
        if category:
            categ=category
        else:
            categ='미선택'
        mapPlace = request.form['inputPlace']
        mapAddress = request.form['inputAddress']
        mapUrl = request.form['inputUrl']
        map = {}
        map['place'] = mapPlace
        map['address'] = mapAddress
        map['url'] = mapUrl
        print(map)

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
            'pubdate': boards_data.get('pubdate'),
            'uptdate':'수정:'+pubdate,
            'file':insertFile,
            'map': map,
            'category': categ
        }
        db.boards.update_one({'_id': ObjectId(idx)},{'$set':doc})
        return render_template('detail.html', doc=doc, page=page)
    doc = { #get방식일 경우
        'id': boards_data.get('_id'),
        'title': boards_data.get('title'),
        'writer': boards_data.get('writer'),
        'comment': boards_data.get('comment'),
        'content': boards_data.get('content'),
        'noTagCon': boards_data.get('noTagCon'),
        'view_cnt': boards_data.get('view_cnt'),
        'likey': boards_data.get('likey'),
        'pubdate': boards_data.get('pubdate'),
        'uptdate': boards_data.get('uptdate'),
        'file': boards_data.get('file'),
        'map': boards_data.get('map'),
        'category': boards_data.get('category')
    }
    return render_template('update.html',doc=doc, page=page)

@app.route("/deleteUser")
def deleteUser():
    userinfo=db.users.find_one({'id':session['id']})
    if userinfo.get('bid'):
        print(userinfo.get('bid'))
        bidList=db.boards.remove({'_id':{'$in':userinfo.get('bid')}}) #여기까지만 하면 나중에 사용자 게시물 전체지우기 가능
        db.users.delete_one({'id':session['id']})
    if userinfo.get('rid'):
        print(userinfo.get('rid'))
        db.replies.remove({'_id': {'$in': userinfo.get('rid')}})  # 여기까지만 하면 나중에 사용자 댓글 전체지우기 가능
        db.users.delete_one({'id': session['id']})
    logout()
    return redirect(url_for('index'))

@app.route("/delete/<idx>/<page>")
def delete(idx,page):
    userinfo=db.users.find_one({'id':session['id']})
    boardinfo=db.boards.find_one({'_id':ObjectId(idx)})
    print('boardinfo:',boardinfo)
    replyinfo=list(db.replies.find({'_id':{'$in':boardinfo.get('rid')}}))
    print('replyinfo:',replyinfo)
    if userinfo.get('bid'): #게시물 지우면 그 작성자자 게시물 리스트에서 지움
        db.users.update_one({'id':session['id']},{'$pull':{'bid':ObjectId(idx)}})
    if boardinfo.get('rid'): #게시물 지우면 거기에 달려있던 댓글 정보 db에서 지움
        for i in replyinfo:
            db.users.update_one({'id': i.get('writer')}, {'$pull': {'rid': i.get('_id')}}) # 유저에게 등록돼있던 댓글 정보도 db에서 제거
        db.replies.remove({'_id':{'$in': boardinfo.get('rid')}})
    db.boards.delete_one({'_id': ObjectId(idx)}) #게시글 삭제
    return redirect(url_for('index', page=page))

@app.route("/deleteReply/<idr>/<idb>/<page>") #댓글 id와 댓글이 속한 게시물 id 가져옴
def deleteReply(idr,idb, page):
    db.boards.update_one({'_id':ObjectId(idb)},{'$pull':{'rid':ObjectId(idr)}}) #게시글에 저장돼있던 댓글 리스트에서 제거
    replyInfo = db.replies.find_one({'_id':ObjectId(idr)})
    writer = replyInfo.get('writer')
    db.users.update_one({'id':writer},{'$pull':{'rid':ObjectId(idr)}}) #유저에 저장돼있던 댓글 리스트에서 제거
    db.replies.delete_one({'_id':ObjectId(idr)}) #댓글삭제
    return redirect(url_for('detail',idx=idb,page=page))

@app.route("/filedown", methods=["POST"])
def filedown():
    if request.method=="POST":
        files=os.listdir('./static/files')
        print('filename',request.form['file'])
        # for i in files:
        if request.form['file'] in files:
            # if i == request.form['file']:
                # print(i)
            path="./static/files/"
            return send_file(path+request.form['file'],
                             attachment_filename= request.form['file'],
                             as_attachment=True)
        else:
            msg='파일이 존재하지 않습니다.'
            return render_template('result.html', msg=msg)

@app.route('/deleteFile/<idx>', methods=['POST'])
def deleteFile(idx):
    print(idx)
    if request.method=="POST":
        files = os.listdir('./static/files')
        for i in files:
            if i == request.form['filename']:
                print(request.form['filename'])
                db.boards.update_one({'_id': ObjectId(idx)},{'$pull':{'file': i }})
                os.remove('./static/files/'+request.form['filename'])
                return jsonify({'msg':'삭제완료'})





if __name__=="__main__":
    app.run('0.0.0.0', port=5000, debug=True)
