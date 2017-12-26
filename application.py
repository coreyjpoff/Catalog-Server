#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, jsonify, \
    url_for, make_response, g
from flask import session as login_session
from flask_httpauth import HTTPBasicAuth
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from psycopg2 import connect
import httplib2
import json
import requests
import random
import string

# XCJP see above--change the flask login_session to just session?

# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from database_setup import Base, User, Category, CategoryItem

# Global vars and constants
app = Flask(__name__)
auth = HTTPBasicAuth()

# engine = create_engine('sqlite:///catalog.db')
# Base.metadata.bind = engine

# DBSession = sessionmaker(bind=engine)
# session = DBSession()

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read()
)['web']['client_id']


# JSON APIs
@app.route('/catalog/JSON')
def categoriesJSON():
    # XCJP
    # categories = session.query(Category).all()
    returnList = []
    for c in categories:
        returnObj = c.serialize
        # XCJP
        # items = session.query(CategoryItem).filter_by(category_id=c.id).all()
        returnObj['Item'] = []
        for item in items:
            returnObj['Item'].append(item.serialize)
        returnList.append(returnObj)
        # XCJP
    # return jsonify(Category=returnList)


# page renders
@app.route('/oauth/<provider>', methods=['POST'])
def login(provider):
    # Validate state token
    if request.args.get('state') != login_session.get('state'):
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    auth_code = request.data
    if provider == 'google':
        return googleLogin(auth_code)
    else:
        response = make_response(
            json.dumps('Unrecognized Provider'), 401
        )
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/oauth/logout')
def logout():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected'), 401
        )
        response.headers['Content-Type'] = 'application/json'
        return response
    if login_session.get('provider') == 'google':
        return googleLogout(access_token)
    else:
        response = make_response(
            json.dumps('Unrecognized Provider'), 401
        )
        response.headers['Content-Type'] = 'application/json'
        return response


def googleLogin(auth_code):
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets(
            'client_secrets.json',
            scope=''
        )
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(auth_code)
    except FlowExchangeError:
        response = make_response(json.dumps(
            'Failed to upgrade the authorization code'),
            401
        )
        response.headers['Content-Type'] = 'application/json'
        return response
    # Check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Verify that the access token is used for the intended user
    g_id = credentials.id_token['sub']
    if result['user_id'] != g_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match user ID"),
            401
        )
        response.headers['Content-Type'] = 'application/json'
        return response
    # Verify that the access token is valid for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app client ID"),
            401
        )
        response.headers['Content-Type'] = 'application/json'
        return response
    # See if user is already connected
    stored_access_token = login_session.get('access_token')
    stored_g_id = login_session.get('g_id')
    if stored_access_token is not None and g_id == stored_g_id:
        response = make_response(
            json.dumps('Current user is already connected'),
            200
        )
        response.headers['Content-Type'] = 'application/json'
        return response
    # Store the access token in session
    login_session['access_token'] = credentials.access_token
    login_session['g_id'] = g_id
    # Get user info and store in session
    url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    result = requests.get(url, params=params)
    data = result.json()
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'
    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    return login_session['username']


def googleLogout(access_token):
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['g_id']
        del login_session['provider']
        del login_session['user_id']
        del login_session['username']
        del login_session['email']
        return redirect(url_for('showHome'))
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user'),
            400
        )
        response.headers['Content-Type'] = 'applicatin/json'
        return response


def createUser(login_session):
    SQL = 'INSERT INTO users VALUES (%s, %s)'
    execute(SQL, (login_session['username'], login_session['email']))
    return getUserID(email)


def getUserID(email):
    try:
        SQL = 'SELECT id FROM users WHERE email = %s'
        user = query(SQL, email)
        return user[0]
    except:
        return None


@app.route('/catalog/')
@app.route('/')
def showHome():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # XCJP
    # categories = session.query(Category).all()
    # latestItems = session.query(CategoryItem).join(CategoryItem.category) \
    #     .order_by(CategoryItem.id.desc()).limit(10).all()
    return render_template(
        'catalog.html',
        # categories=categories,
        # latestItems=latestItems,
        # STATE=state
    )


@app.route('/category/new', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect(url_for('showHome'))
    if request.method == 'POST':
        # newCategory = Category(name=request.form['name'])
        # XCJP
        # session.add(newCategory)
        # session.commit()
        return redirect(url_for('showHome'))
    else:
        return render_template('newCategory.html')


@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/items')
def showCategoryItems(category_id):
    # XCJP
    # allCategories = session.query(Category).all()
    # selectedCategory = session.query(Category).filter_by(id=category_id).one()
    # items = session.query(CategoryItem).filter_by(category_id=category_id). \
    #     all()
    return render_template(
        'categoryItems.html',
        allCategories=allCategories,
        selectedCategory=selectedCategory,
        items=items
    )


@app.route('/category/items/new/<init_category_id>', methods=['GET', 'POST'])
def newItem(init_category_id):
    if 'username' not in login_session:
        return redirect(url_for('showHome'))
    if request.method == 'POST':
        # newItem = CategoryItem(
        #     name=request.form['name'],
        #     description=request.form['description'],
        #     category_id=request.form['category_id'],
        #     user_id=login_session['user_id']
        # )
        # XCJP
        # session.add(newItem)
        # session.commit()
        return redirect(url_for(
            'showItem',
            item_id=newItem.id,
            category_id=newItem.category_id
        ))
    else:
        # XCJP
        # categories = session.query(Category).all()
        if init_category_id == 'NONE' and len(categories) > 0:
            init_category_id = categories[0].id
        return render_template(
            'newItem.html',
            categories=categories,
            init_category_id=init_category_id
        )


@app.route('/category/<int:category_id>/items/<int:item_id>')
def showItem(item_id, category_id):
    # XCJP
    # item = session.query(CategoryItem).filter_by(id=item_id).one()
    # allCategories = session.query(Category).all()
    allowEdit = item.user_id == login_session.get('user_id')
    return render_template(
        'itemDetails.html',
        item=item,
        allCategories=allCategories,
        allowEdit=allowEdit
    )


@app.route(
    '/category/<int:category_id>/items/<int:item_id>/edit',
    methods=['GET', 'POST']
)
def editItem(item_id, category_id):
    # XCJP
    # item = session.query(CategoryItem).filter_by(id=item_id).one()
    if item.user_id != login_session.get('user_id'):
        return redirect(url_for('showHome'))
    if request.method == 'POST':
        if request.form['name']:
            item.name = request.form['name']
        if request.form['description']:
            item.description = request.form['description']
        if request.form['category_id']:
            item.category_id = request.form['category_id']
        # XCJP
        # session.add(item)
        # session.commit()
        return redirect(url_for(
            'showItem',
            item_id=item.id,
            category_id=item.category_id
        ))
    else:
        # XCJP
        # allCategories = session.query(Category).all()
        return render_template(
            'editItem.html',
            item=item,
            allCategories=allCategories
        )


@app.route(
    '/category/<int:category_id>/items/<int:item_id>/delete',
    methods=['GET', 'POST'])
def deleteItem(item_id, category_id):
    # XCJP
    # item = session.query(CategoryItem).filter_by(id=item_id).one()
    if item.user_id != login_session.get('user_id'):
        return redirect(url_for('showHome'))
    if request.method == 'POST':
        itemId = item.category_id
        # XCJP
        # session.delete(item)
        # session.commit()
        return redirect(url_for(
            'showCategoryItems',
            category_id=itemId
        ))
    else:
        return render_template(
            'deleteItem.html',
            item=item,
        )

def execute(SQL, params):
    try:
        conn = psycopg2.connect(database="catalog", user="catalog", password="catalog")
        cur = conn.cursor()
        cur.execute(SQL, params)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

def query(SQL, params):
    try:
        conn = psycopg2.connect(database="catalog", user="catalog", password="catalog")
        cur = conn.cursor()
        cur.execute(SQL, params)
        results = cur.fetchall()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return results

# openCon() XCJP implement this?


if __name__ == '__main__':
    app.secret_key = ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for x in xrange(32))
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
