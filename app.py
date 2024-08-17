from flask import Flask, request, render_template, redirect, url_for
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)

# Constants for file paths
EMPLOYEES_FILENAME = 'employees.csv'
PAYMENTS_FILENAME = 'payments.csv'

# Initialize or load data from CSV files
def load_data():
    if os.path.exists(EMPLOYEES_FILENAME):
        employees_df = pd.read_csv(EMPLOYEES_FILENAME)
    else:
        employees_df = pd.DataFrame(columns=['Employee Name', 'Joining Date', 'Payment Date'])

    if os.path.exists(PAYMENTS_FILENAME):
        payments_df = pd.read_csv(PAYMENTS_FILENAME)
    else:
        payments_df = pd.DataFrame(columns=['Employee Name', 'Payment Date', 'Amount'])

    return employees_df, payments_df

employees_df, payments_df = load_data()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/view_employee', methods=['GET', 'POST'])
def view_employee():
    global employees_df

    if request.method == 'POST':
        selected_employee = request.form.get('employee_name')
        if selected_employee:
            return redirect(url_for('employee_page', name=selected_employee))

    employees_list = employees_df['Employee Name'].unique()
    return render_template('view_employee.html', employees_list=employees_list)

@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    global employees_df  # Global declaration should be at the start
    if request.method == 'POST':
        name = request.form.get('employee_name')
        joining_date = request.form.get('joining_date')
        payment_date = request.form.get('payment_date')
        
        if not name:
            return "Employee name is required", 400

        # Check if the employee already exists
        if name in employees_df['Employee Name'].values:
            return "Employee with this name already exists", 400
        
        new_employee = pd.DataFrame({
            'Employee Name': [name], 
            'Joining Date': [joining_date], 
            'Payment Date': [payment_date]
        })
        employees_df = pd.concat([employees_df, new_employee], ignore_index=True)
        employees_df.to_csv(EMPLOYEES_FILENAME, index=False)
        
        return redirect(url_for('home'))
    
    return render_template('add_employee.html')

@app.route('/remove_employee', methods=['POST'])
def remove_employee():
    global employees_df  # Global declaration should be at the start
    name = request.form.get('employee_name')
    
    if not name:
        return "Employee name is required", 400
    
    employees_df = employees_df[employees_df['Employee Name'] != name]
    employees_df.to_csv(EMPLOYEES_FILENAME, index=False)
    
    return redirect(url_for('home'))

@app.route('/record_payment', methods=['GET', 'POST'])
def record_payment():
    global payments_df  # Global declaration should be at the start
    if request.method == 'POST':
        name = request.form.get('employee_name')
        payment_date = request.form.get('payment_date')
        amount = request.form.get('amount')

        if not name or not amount:
            return "Employee name and amount are required", 400
        
        try:
            amount = float(amount)
        except ValueError:
            return "Invalid amount", 400
        
        new_payment = pd.DataFrame({
            'Employee Name': [name], 
            'Payment Date': [payment_date], 
            'Amount': [amount]
        })
        payments_df = pd.concat([payments_df, new_payment], ignore_index=True)
        payments_df.to_csv(PAYMENTS_FILENAME, index=False)
        
        return redirect(url_for('record_payment'))
    
    employees_list = employees_df['Employee Name'].unique()
    return render_template('record_payment.html', employees_list=employees_list)

@app.route('/view_payments', methods=['GET'])
def view_payments():
    global employees_df, payments_df  # Global declaration should be at the start
    selected_employee = request.args.get('name', '')
    employees_list = employees_df['Employee Name'].unique()

    if selected_employee:
        employee_info = employees_df[employees_df['Employee Name'] == selected_employee]
        
        if employee_info.empty:
            return "Employee not found", 404

        employee_payments = payments_df[payments_df['Employee Name'] == selected_employee]

        filter_option = request.args.get('filter', 'none')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        current_month = datetime.now().strftime('%Y-%m')
        last_month = (datetime.now().replace(day=1) - pd.DateOffset(days=1)).strftime('%Y-%m')

        if filter_option == 'current':
            employee_payments = employee_payments[
                pd.to_datetime(employee_payments['Payment Date']).dt.to_period('M').astype(str) == current_month]
        elif filter_option == 'last':
            employee_payments = employee_payments[
                pd.to_datetime(employee_payments['Payment Date']).dt.to_period('M').astype(str) == last_month]
        elif filter_option == 'custom' and start_date and end_date:
            employee_payments['Payment Date'] = pd.to_datetime(employee_payments['Payment Date'])
            employee_payments = employee_payments[
                (employee_payments['Payment Date'] >= start_date) & 
                (employee_payments['Payment Date'] <= end_date)
            ]

        total_payments = employee_payments['Amount'].sum()

        employee_info_html = employee_info.to_html(classes='table table-striped', index=False)
        employee_payments_html = employee_payments.to_html(classes='table table-striped', index=False)
        
        return render_template('view_payments.html', 
                               employees_list=employees_list, 
                               selected_employee=selected_employee,
                               employee_info=employee_info_html, 
                               employee_payments=employee_payments_html,
                               total_payments=total_payments)
    
    return render_template('view_payments.html', employees_list=employees_list)

@app.route('/employee/<name>', methods=['GET'])
def employee_page(name):
    global employees_df, payments_df

    # Get employee info
    employee_info = employees_df[employees_df['Employee Name'] == name]

    if employee_info.empty:
        return "Employee not found", 404

    # Get employee payments
    employee_payments = payments_df[payments_df['Employee Name'] == name]

    # Handle filtering
    filter_option = request.args.get('filter', 'none')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    current_month = datetime.now().strftime('%Y-%m')
    last_month = (datetime.now().replace(day=1) - pd.DateOffset(days=1)).strftime('%Y-%m')

    if filter_option == 'current':
        employee_payments = employee_payments[
            pd.to_datetime(employee_payments['Payment Date']).dt.to_period('M').astype(str) == current_month]
    elif filter_option == 'last':
        employee_payments = employee_payments[
            pd.to_datetime(employee_payments['Payment Date']).dt.to_period('M').astype(str) == last_month]
    elif filter_option == 'custom' and start_date and end_date:
        try:
            start_date_parsed = pd.to_datetime(start_date, format='%Y-%m-%d')
            end_date_parsed = pd.to_datetime(end_date, format='%Y-%m-%d')
            employee_payments.loc[:, 'Payment Date'] = pd.to_datetime(employee_payments['Payment Date'])
            employee_payments = employee_payments[
                (employee_payments['Payment Date'] >= start_date_parsed) & 
                (employee_payments['Payment Date'] <= end_date_parsed)
            ]
        except Exception as e:
            return f"Error in date format: {e}", 400

    # Calculate total payments
    total_payments = employee_payments['Amount'].sum()

    # Convert DataFrames to HTML
    employee_info_html = employee_info.to_html(classes='table table-striped', index=False)
    employee_payments_html = employee_payments.to_html(classes='table table-striped', index=False)

    return render_template('employee_page.html', 
                          employee_info=employee_info_html, 
                          employee_payments=employee_payments_html,
                          total_payments=total_payments,
                          employee_name=name,
                          filter_option=filter_option,
                          start_date=start_date,
                          end_date=end_date)




if __name__ == '__main__':
    app.run(debug=True)
