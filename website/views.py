from flask import Blueprint, render_template, request, flash, jsonify, redirect,url_for, session, make_response
from flask_login import login_required, current_user
from .import db, tables_dict, mysql, oauth
from .models import Users, Admins
import MySQLdb.cursors
import json
from datetime import datetime
import re
import os
from functools import wraps

views = Blueprint('views', __name__) 
@views.route('/',methods=['GET','POST'])
def index():
  return render_template("index.html",user = current_user)


@views.route("/display")
@login_required
def display():
        return render_template('display.html', user=current_user, usertype="Admins")

@views.route("/searchby")
@login_required
def search_by():
  return render_template('searchby.html')
@views.route("/where_display")
@login_required
def where_display():
  return render_template('where_display.html', tables_dict = tables_dict, user = current_user)

@views.route("/rename_display")
@login_required
def rename_display():
  return render_template('rename_display.html', tables_dict = tables_dict,user = current_user, usertype="Admin")

@views.route("/update_display")
@login_required
def update_display():
  return render_template('update_display.html', tables_dict = tables_dict,user = current_user, usertype="Admin")

@views.route("/delete_display")
@login_required
def delete_display():
  return render_template('delete_display.html',  tables_dict = tables_dict, keys=tables_dict.keys(),user = current_user, usertype="Admin")

@views.route("/insert", methods=['GET','POST'])
@login_required
def insert():
  msg =''
  table_data = {}
  cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
  for table_name in tables_dict:
    sql_query = "select * from {}".format(table_name)
    resultValue = cursor.execute(sql_query)

    current_table_data = []
    if resultValue > 0:
      current_table_data = cursor.fetchall()
      table_data[table_name] = list(current_table_data)
    mysql.connection.commit()

  if request.method == 'POST':
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    table_name = request.form.get('keyaa')
    pattern = r'^[a-zA-Z0-9\s_]*$'
    cursor.execute(f"LOCK TABLES {table_name} WRITE")
    column_name =tables_dict[table_name]
    data = []

    sql_query_insert = "INSERT INTO "+table_name+" VALUES ("+"% s,"*(len(column_name)-1)+"% s)"
    for i in column_name:
      data_val = request.form[i]
      data_val1 = bool(re.match(pattern, data_val)  )
      if data_val1 != True:
        flash("This input can put our website at risk. You are allowed to use only alphabets, integers, underscores and spaces", 'danger')
        # flash("<script> alert('This input is not allowed')</script>")
        return render_template('insert.html', tables_dict = tables_dict, keys=tables_dict.keys(), table_data = table_data, user = current_user, msg =msg,usertype="Admin")
      data.append(data_val)

    data = tuple(data)
    
    try:
      cursor.execute(sql_query_insert,data)
      mysql.connection.commit()
      flash("Data succesfully inserted", 'success')     
    except:
      flash("Data cannot be entered", 'danger')  
    cursor.execute(f"UNLOCK TABLES")
  return render_template('insert.html', tables_dict = tables_dict, keys=tables_dict.keys(), table_data = table_data, user = current_user, msg =msg,usertype="Admin")

@views.route('/delete/<string:table_name>', methods=['GET', 'POST'])
@login_required
def delete(table_name):
  if request.method == 'GET':
    args = request.args
    field_lst = []
    for attr in tables_dict[table_name]:
        field_name = attr
        field_value = args[field_name]
        if (field_value == 'None' or field_value == None):
          field_value = None
        field_lst.append([attr, field_value])
    try:
      cur = mysql.connection.cursor()
      sql_query = 'delete from {} where '.format(table_name)
      for i in range(len(field_lst) - 1):
        if (field_lst[i][1]):
          sql_query = sql_query + field_lst[i][0] + '=' + '"' + field_lst[i][1] + '"' + ' and '
      if (field_lst[-1][1]):
        sql_query = sql_query + field_lst[-1][0] + '=' + '"' + field_lst[-1][1] + '";'
      elif (len(sql_query) > 4):
        sql_query = sql_query[:-5]
      cur.execute(sql_query)
      mysql.connection.commit()
      cur.close()
      flash("Data deleted successfully", 'success')
      return redirect('/insert#' + str(table_name))
    except Exception as e:
      flash('There was an issue adding the entry:' + str(e), 'danger')
  return redirect('/insert#' + str(table_name))

@views.route('/update', methods=['POST','GET'])
@login_required
def update():
    msg = ''
    table_data = {}
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    for table_name in tables_dict:
        sql_query = "select * from {}".format(table_name)
        resultValue = cursor.execute(sql_query)

        current_table_data = []
        if resultValue > 0:
            current_table_data = cursor.fetchall()
            table_data[table_name] = list(current_table_data)
        mysql.connection.commit()

    if request.method == 'POST':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        table_name = request.form.get('keyaa')
        pattern = r'^[a-zA-Z0-9\s_]*$'
        table_name = re.sub('<[^>]*>', '', table_name)

        column_name = tables_dict[table_name]
        data = []
        cursor.execute(f"LOCK TABLES {table_name} WRITE")
        condition = request.form.get('condition')
        update_columns = [f"{col}=%s" for col in column_name]
        update_query = f"UPDATE {table_name} SET {', '.join(update_columns)} WHERE {condition}"

        for i in column_name:
            data_val = request.form[i]
            data_val1 = bool(re.match(pattern, data_val) )
            if data_val1 != True:
              flash("This input can put our website at risk. You are allowed to use only alphabets, integers, underscores and spaces", 'danger')
              return render_template('update.html', tables_dict=tables_dict, keys=tables_dict.keys(),table_data=table_data, user=current_user, msg=msg, usertype="Admin")
            data.append(data_val)

        data = tuple(data)
        try:
            cursor.execute(update_query, data)
            mysql.connection.commit()
            flash("Data update successfull", 'success')
        except Exception as e:
            flash("Data update unsuccessfull. Please check and re-enter", 'danger')
        cursor.execute(f"UNLOCK TABLES")
    return render_template('update.html', tables_dict=tables_dict, keys=tables_dict.keys(),
                           table_data=table_data, user=current_user, msg=msg, usertype="Admin")

@views.route('/rename/<string:key>', methods=['GET', 'POST'])
@login_required
def rename(key):
  print(key)
  msg = ''
  if request.method == 'POST':
    new_name = request.form['name']
    pattern = r'^[a-zA-Z0-9\s_]*$'
    new_name1 = bool(re.match(pattern, new_name) )
    if new_name1!= True:
      flash("This input can put our website at risk. You are allowed to use only alphabets, integers, underscores and spaces", 'danger')
      return render_template('rename.html', msg = msg, key = key, user=current_user)
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(f"LOCK TABLES {key} WRITE")
    sql_query = 'alter table {0} rename {1};'.format(key, new_name)

    try:
      cur.execute(sql_query)
      tables_dict[new_name] = tables_dict[key]
      del tables_dict[key]
      with open('website/tables.json', 'w') as json_file:
        json.dump(tables_dict, json_file)
      mysql.connection.commit()
      cur.execute(f"UNLOCK TABLES")
      cur.close()
      flash("Rename successful", 'success')
      return redirect('/rename/' + str(new_name))
    except:
      cur.execute(f"UNLOCK TABLES")
      flash("Rename unsuccessful", 'danger')
      return redirect(request.url)
    
  return render_template('rename.html', msg = msg, key = key, user=current_user)

@views.route('/where/<string:key>', methods =['GET', 'POST'])
@login_required
def where(key):
  print(key)
  msg = ''
  try:
    if request.method == 'POST':
      column_name = request.form['Column_Name']
      pattern = r'^[a-zA-Z0-9\s_]*$'
      column_name1 = bool(re.match(pattern, column_name) )
      if column_name1 != True:
        flash("This input can put our website at risk. You are allowed to use only alphabets, integers, underscores and spaces", 'danger')
        return render_template('where.html', msg = msg, key = key, user=current_user)
      value = request.form['Value']
      value1 = bool(re.match(pattern, value) )
      if value1 != True:
        flash("This input can put our website at risk. You are allowed to use only alphabets, integers, underscores and spaces", 'danger')
        return render_template('where.html', msg = msg, key = key, user=current_user)
      cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
      query1 = "SELECT * FROM {0} WHERE {1} = '{2}'".format(key,column_name,value)
      print(query1)
      resultValue =cursor.execute(query1)
      # mysql.connection.commit()
      msg = 'You have successfully executed where clause on the table !!'
      # return redirect('/display#' + str(key))
      if resultValue > 0:
          userDetails = cursor.fetchall()
          print(userDetails)
          print(tables_dict[key])
          flash("Fetch successfull", 'success')
          return render_template('output.html',userDetails=userDetails,cols = tables_dict[key],table = key,query = query1, user=current_user,usertype="Admin")
      else:
          msg = "No values found"
  except Exception as e:
     return 'There was an ERROR : ' + str(e) 
  return render_template('where.html', msg = msg, key = key, user=current_user)

@views.route('/user-profile',methods=['GET','POST'])
@login_required
def profile():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    sql_query = "select user_name,email, address, linkedin, phone from Users where user_id={}".format(current_user.get_id())
    result = cursor.execute(sql_query)
    if result>0:
      user_data = list(cursor.fetchall())
      print(user_data)
    mysql.connection.commit()
    
    if request.method == 'POST':
      cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
      data = []
      sql_query_insert = "Update Users Set user_name =%s,email=%s, address = %s, linkedin = %s, phone = %s where user_id ={}".format(current_user.get_id())
      user_name_val = request.form["user_name"]
      pattern = r'^[a-zA-Z0-9\s_]*$'
      user_name_val1 = re.sub('<[^>]*>', '', user_name_val)
      email_val = request.form["email"]
      email_val1 = re.sub('<[^>]*>', '', email_val)
      address_val = request.form["address"]
      address_val1 = re.sub('<[^>]*>', '', address_val)
      linkedin_val = request.form["linkedin"]
      linkedin_val1 = re.sub('<[^>]*>', '', linkedin_val)
      phone_val = request.form["phone"]
      phone_val1 = re.sub('<[^>]*>', '', phone_val)
      if user_name_val1 != user_name_val or email_val1 != email_val or address_val1 != address_val or linkedin_val1 != linkedin_val or phone_val1 != phone_val:
        flash("This input can put our website at risk. You are not allowed to use HTML tags", category='error')
        return render_template("user_profile.html",user=current_user,uname = user_data[0]["user_name"],usermail=user_data[0]["email"],uaddress=user_data[0]["address"],ulinkedin=user_data[0]["linkedin"],uphone=user_data[0]["phone"],usertype="User")
      data = [user_name_val,email_val, address_val, linkedin_val, phone_val]
      
      data = tuple(data)
      if(data[0] != user_data[0]["user_name"] or data[1] != user_data[0]["email"] or data[2] != user_data[0]["address"] or data[3] != user_data[0]["linkedin"] or data[4] != user_data[0]["phone"]):
        cursor.execute(sql_query_insert,data)
        msg = "Profile Updated"
        flash(msg,"success")
        user_data[0]["user_name"] =data[0] 
        user_data[0]["email"] = data[1]
        user_data[0]["address"] =data[2] 
        user_data[0]["linkedin"] = data[3]
        user_data[0]["phone"] =data[4] 
      else:
        msg = "No changes detected"
        flash(msg,"danger")
      print(msg)
      mysql.connection.commit()
      
    return render_template("user_profile.html",user=current_user,uname = user_data[0]["user_name"],usermail=user_data[0]["email"],uaddress=user_data[0]["address"],ulinkedin=user_data[0]["linkedin"],uphone=user_data[0]["phone"],usertype="User")


@views.route("/testsearch", methods = ["POST", "GET"])
@login_required
def testsearch():
    # Retrieve search query from form
    search_query = request.form.get('search_query')
    print(search_query)
    search_by = request.form.get('search_by')
    print(search_by)
    pattern = r'^[a-zA-Z0-9\s_]*$'
    if search_query != None and search_by != None:
      search_query1 = bool(re.match(pattern, search_query) )
      search_by1 = bool(re.match(pattern, search_by) )
      if search_query1 != True or search_by1 != True:
        flash("This input can put our website at risk. You are allowed to use only alphabets, integers, underscores and spaces", category='error')
        return render_template("testsearch.html", user = current_user)
    # Initialize cursor
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Define the search type logic
    if search_by == "Name":
      print("Hi1")
          # Use the query_param to handle partial matches
      query_param = f'%{search_query}%'
      # Define your SQL query based on the search type and parameter
      sql_query = "SELECT first_name, last_name, degree, branch, year_of_graduation, current_profession, personal_email, date_of_birth FROM alumni WHERE first_name LIKE %s OR middle_name LIKE %s OR last_name LIKE %s"
      # Execute the SQL query
      
      cursor.execute(sql_query, (query_param, query_param, query_param))
    elif search_by == "Graduation Year":
        # Use the query_param to handle partial matches
        
        # Define your SQL query based on the search type and parameter
        sql_query = "SELECT first_name, last_name, degree, branch, year_of_graduation, current_profession, personal_email, date_of_birth FROM alumni WHERE year_of_graduation =" + search_query
        # Execute the SQL query
        cursor.execute(sql_query)
        # print(sql_query, (search_query,))

    elif search_by == "Discipline":
        # Use the query_param to handle partial matches
        query_param = f'%{search_query}%'
        # Define your SQL query based on the search type and parameter
        sql_query = "SELECT first_name, last_name, degree, branch, year_of_graduation, current_profession, personal_email, date_of_birth FROM alumni WHERE branch LIKE %s"
        # Execute the SQL query
        cursor.execute(sql_query, (query_param,))
    elif search_by == "Program":
        # Use the query_param to handle partial matches
        # Define your SQL query based on the search type and parameter
        sql_query = "SELECT first_name, last_name, degree, branch, year_of_graduation, current_profession, personal_email, date_of_birth FROM alumni WHERE degree = %s"
        # Execute the SQL query
        cursor.execute(sql_query, (search_query,))
    elif search_by == "Other Institutions":
        # Use the query_param to handle partial matches
        # Define your SQL query based on the search type and parameter
        query_param = f'%{search_query}%'
        sql_query = "SELECT alumni.first_name, alumni.last_name, alumni.degree, alumni.branch, other_studies.institute, alumni.year_of_graduation, alumni.current_profession, alumni.personal_email, alumni.date_of_birth FROM alumni INNER JOIN other_studies ON alumni.roll_number  = other_studies.roll_number WHERE institute LIKE %s"
        # Execute the SQL query
        cursor.execute(sql_query, (query_param,))
    elif search_by == "Current profession":
        # Use the query_param to handle partial matches
        # Define your SQL query based on the search type and parameter
        query_param = f'%{search_query}%'
        sql_query = "SELECT first_name, last_name, degree, branch, year_of_graduation, current_profession, personal_email, date_of_birth FROM alumni WHERE current_profession LIKE %s"
        # Execute the SQL query
        cursor.execute(sql_query, (query_param,))
    else:
      return render_template("testsearch.html", user = current_user)
    # Fetch all the results
    results = cursor.fetchall()
    
    # Close the cursor
    cursor.close()
    flash("search successful", 'success')
    # Render the output template and pass results to the template
    return render_template('testsearch.html',userDetails=results,search_key = search_by,cols = ["first_name", "last_name", "degree", "branch", "year_of_graduation", "current_profession", "personal_email", "date_of_birth"],table = "alumni",query = sql_query, user=current_user,usertype="Admin")


