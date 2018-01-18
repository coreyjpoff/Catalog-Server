#!/usr/bin/env python2.7
from flask import Flask, render_template, request, redirect, jsonify, \
    url_for, make_response, g
from flask import session as login_session
from flask_httpauth import HTTPBasicAuth
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import psycopg2
import httplib2
import json
import requests
import random
import string

# Global vars and constants
app = Flask(__name__)

app.secret_key = ''.join(
    random.choice(string.ascii_uppercase + string.digits)
    for x in xrange(32))

def getCategories():
    try:
        SQL = 'SELECT * FROM categories;'
        categories = query(SQL)
        return categories
    except:
        return []

def getLatestItems():
    try:
        SQL = 'SELECT * FROM categoryitems ORDER BY categoryitems.id DESC LIMIT 10;'
        items = query(SQL)
        return items
    except:
        return []

def createCategory(name):
    SQL = 'INSERT INTO categories (name) VALUES (%s)'
    execute(SQL, (name,))

def getCategory(id):
    try:
        SQL = 'SELECT * FROM categories WHERE categories.id = %s'
        category = query(SQL, (id,))
        return category[0]
    except:
        return []

def getItems(category_id):
    try:
        SQL = 'SELECT * FROM categoryitems WHERE categoryitems.category_id = %s'
        items = query(SQL, (category_id,))
        return items
    except:
        return []

def addItem(name, description, category_id, user_id):
    SQL = 'INSERT INTO categoryitems (name, description, category_id, user_id) VALUES (%s, %s, %s, %s)'
    execute(SQL, (name, description, category_id, user_id))
    return getItem(name, description, category_id, user_id)

def updateItem(item):
    SQL = 'UPDATE categoryitems SET name = %s, description = %s, category_id = %s WHERE id = %s'
    execute(SQL, (item[1], item[2], item[3], item[0]))
    return getItemById(item[0])

def getItem(name, description, category_id, user_id):
    try:
        SQL = 'SELECT * FROM categoryitems WHERE categoryitems.name = %s AND categoryitems.description = %s AND categoryitems.category_id = %s AND categoryitems.user_id = %s'
        item = query(SQL, (name, description, category_id, user_id))
        return item[0]
    except:
        return []

def getItemById(id):
    try:
        SQL = 'SELECT * FROM categoryitems WHERE categoryitems.id = %s'
        item = query(SQL, (id,))
        return item[0]
    except:
        return []

def removeItemFromDb(id):
    SQL = 'DELETE FROM categoryitems WHERE id = %s'
    execute(SQL, (id,))


@app.route('/catalog/')
@app.route('/')
def showHome():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    categories = getCategories()
    latestItems = getLatestItems()
    return render_template(
        'catalog.html',
        categories=categories,
        latestItems=latestItems,
        STATE=state
    )


@app.route('/category/new', methods=['GET', 'POST'])
def newCategory():
    if request.method == 'POST':
        createCategory(request.form['name'])
        return redirect(url_for('showHome'))
    else:
        return render_template('newCategory.html')


@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/items')
def showCategoryItems(category_id):
    allCategories = getCategories()
    selectedCategory = getCategory(category_id)
    items = getItems(category_id)
    return render_template(
        'categoryItems.html',
        allCategories=allCategories,
        selectedCategory=selectedCategory,
        items=items
    )


@app.route('/category/items/new/<init_category_id>', methods=['GET', 'POST'])
def newItem(init_category_id):
    if request.method == 'POST':
        item = addItem(
            request.form['name'],
            request.form['description'],
            request.form['category_id'],
            login_session['user_id']
        )
        return redirect(url_for(
            'showItem',
            item_id=item[0],
            category_id=item[3]
        ))
    else:
        categories = getCategories()
        if init_category_id == 'NONE' and len(categories) > 0:
            init_category_id = categories[0][0]
        return render_template(
            'newItem.html',
            categories=categories,
            init_category_id=init_category_id
        )


@app.route('/category/<int:category_id>/items/<int:item_id>')
def showItem(item_id, category_id):
    item = getItemById(item_id)
    allCategories = getCategories()
    return render_template(
        'itemDetails.html',
        item=item,
        allCategories=allCategories
    )


@app.route(
    '/category/<int:category_id>/items/<int:item_id>/edit',
    methods=['GET', 'POST']
)
def editItem(item_id, category_id):
    item = getItemById(item_id)
    if request.method == 'POST':
        item = list(item)
        if request.form['name']:
            item[1] = request.form['name']
        if request.form['description']:
            item[2] = request.form['description']
        if request.form['category_id']:
            item[3] = request.form['category_id']
        item = updateItem(tuple(item))
        return redirect(url_for(
            'showItem',
            item_id=item[0],
            category_id=item[3]
        ))
    else:
        allCategories = getCategories()
        return render_template(
            'editItem.html',
            item=item,
            allCategories=allCategories
        )


@app.route(
    '/category/<int:category_id>/items/<int:item_id>/delete',
    methods=['GET', 'POST'])
def deleteItem(item_id, category_id):
    item = getItemById(item_id)
    if request.method == 'POST':
        itemId = item[3]
        removeItemFromDb(item_id)
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
    conn = None
    try:
        conn = psycopg2.connect(database='catalog', user='catalog', password='catalog')
        cur = conn.cursor()
        cur.execute(SQL, params)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print error
    finally:
        if conn is not None:
            conn.close()

def query(SQL, params=None):
    try:
        conn = psycopg2.connect(database='catalog', user='catalog', password='catalog')
        cur = conn.cursor()
        if params is not None:
            cur.execute(SQL, params)
        else:
            cur.execute(SQL)
        results = cur.fetchall()
    except (Exception, psycopg2.DatabaseError) as error:
        print error
    finally:
        if conn is not None:
            conn.close()
    return results


if __name__ == '__main__':
    app.debug = True
    app.run()
