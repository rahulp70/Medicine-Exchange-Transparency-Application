from flask import Flask, render_template, redirect, url_for, request, jsonify 
from flask_sqlalchemy import SQLAlchemy 
from flask_wtf import FlaskForm 
from wtforms import StringField, SelectField, PasswordField, SubmitField , IntegerField, FloatField 
from wtforms.validators import InputRequired, Email, NumberRange , ValidationError
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user 
from flask_migrate import Migrate 
app = Flask(__name__) 
app.config['SECRET_KEY'] = 'your_secret_key' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///patient.db' 

db = SQLAlchemy(app) 
login_manager = LoginManager() 
login_manager.init_app(app) 
migrate = Migrate(app, db) 
# Create a User model for the database 


class User(UserMixin, db.Model): 
    id = db.Column(db.Integer, primary_key=True) 
    email = db.Column(db.String(80), unique=True) 
    password = db.Column(db.String(80)) 
    account_type = db.Column(db.String(10)) 
    # Define the relationship between User and HospitalDetails 
    hospital_details = db.relationship('HospitalDetails', backref='patient', lazy='dynamic') 
    pharmacy_medicines = db.relationship('PharmacyMedicineDetails', backref='patient')
    


@login_manager.user_loader 
def load_user(user_id): 
    return User.query.get(int(user_id)) 

# HospitalDetails model 
class HospitalDetails(db.Model): 
    id = db.Column(db.Integer, primary_key=True) 
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id')) 
    disease_name = db.Column(db.String(255)) 
    medicine_name = db.Column(db.String(255)) 
    quantity = db.Column(db.String(50)) 
    duration = db.Column(db.String(50)) 
    
    
    
# WTForms for registration and login 
class RegistrationForm(FlaskForm): 
    email = StringField('Email', validators=[InputRequired()]) 
    password = PasswordField('Password', validators=[InputRequired()]) 
    confirm = PasswordField('Confirm Password', validators=[InputRequired()]) 
    account_type = SelectField('Account Type', choices=[('hospital', 'Hospital'), ('pharmacy', 'Pharmacy'), ('patient', 'Patient')]) 


class HospitalDetailsForm(FlaskForm): 
    email = StringField('Patient Email', validators=[InputRequired(), Email()]) 
    disease_name = StringField('Disease Name', validators=[InputRequired()]) 
    medicine_name = StringField('Name of Medicine', validators=[InputRequired()]) 
    quantity = StringField('Quantity', validators=[InputRequired()]) 
    duration = StringField('Duration', validators=[InputRequired()]) 


# WTForms for login 
class LoginForm(FlaskForm): 
    email = StringField('Email', validators=[InputRequired()]) 
    password = PasswordField('Password', validators=[InputRequired()]) 
# MedicineDetails model 


class MedicineDetails(db.Model): 
    id = db.Column(db.Integer, primary_key=True) 
    hospital_details_id = db.Column(db.Integer, db.ForeignKey('hospital_details.id')) 
    medicine_name = db.Column(db.String(255)) 
    quantity = db.Column(db.String(50)) 
    duration = db.Column(db.String(50)) 
    
    
# Routes 
@app.route('/') 
def home(): 
    return render_template('home.html') 


@app.route('/registration', methods=['GET', 'POST']) 
def registration(): 
    form = RegistrationForm() 
    if form.validate_on_submit(): 
        email = form.email.data 
        password = form.password.data 
        account_type = form.account_type.data 
        user = User(email=email, password=password, account_type=account_type) 
        db.session.add(user) 
        db.session.commit() 
        return redirect(url_for('login')) 
    return render_template('registration.html', form=form) 


@app.route('/login', methods=['GET', 'POST']) 
def login(): 
    form = LoginForm() 
    if form.validate_on_submit(): 
        user = User.query.filter_by(email=form.email.data, password=form.password.data).first() 
        if user: 
            login_user(user) 
            if user.account_type == 'hospital': 
                return redirect(url_for('hospital_details', email=user.email)) 
            elif user.account_type == 'pharmacy': 
                return redirect(url_for('pharmacy_details', email=user.email))
            elif user.account_type == 'patient': 
                return redirect(url_for('patient_details')) 
    return render_template('login.html', form=form) 


@app.route('/hospital_details/<email>', methods=['GET', 'POST']) 
@login_required 
def hospital_details(email): 
    form = HospitalDetailsForm() 
    patient_email = None  # Default value for patient_email 
    if form.validate_on_submit(): 
        patient_email = form.email.data 
        disease_name = form.disease_name.data 
        medicine_name = form.medicine_name.data 
        quantity = form.quantity.data 
        duration = form.duration.data 
        # Get the patient's user object from the database 
        patient = User.query.filter_by(email=patient_email).first() 
        if patient: 
            # Create a new HospitalDetails object and associate it with the patient 
            hospital_details = HospitalDetails( 
                patient_id=patient.id,  # Use patient_id to associate hospital details with the patient 
                disease_name=disease_name, 
                medicine_name=medicine_name, 
                quantity=quantity, 
                duration=duration 
            ) 
            # Save hospital details to the database 
            db.session.add(hospital_details) 
            db.session.commit() 
            return jsonify({"message": "Data saved successfully"}) 
    return render_template('hospitalDetails.html', email=email, form=form) 


#@app.route('/pharmacy_details') 
#@login_required 
#def pharmacy_details(): 
#    return render_template('pharmacyDetails.html') 


@app.route('/patient_details', methods=['GET', 'POST'])
@login_required
def patient_details():
    patient_email = current_user.email
    patient = User.query.filter_by(email=patient_email).first()
    if patient:
        # Retrieve the associated hospital details for the patient
        hospital_details = HospitalDetails.query.filter_by(patient_id=patient.id).all()
        pharmacy_medicine = PharmacyMedicineDetails.query.filter_by(patient_id=patient.id).all()
        
        return render_template('patientDetails.html', patient=patient, hospital_details=hospital_details, pharmacy_medicine=pharmacy_medicine)
    return render_template('patientDetails.html', patient=current_user)


 
@app.route('/logout') 
@login_required 
def logout(): 
    logout_user() 
    return redirect(url_for('home')) 


#Pharmacy wale ka hai yaha se 

class PharmacyMedicineDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    patient_email = db.Column(db.String(255))
    medicine_name = db.Column(db.String(255))
    quantity = db.Column(db.String(50))
    rate = db.Column(db.String(50))



class PatientEmailForm(FlaskForm):
    patient_email = StringField('Enter Patient Email', validators=[InputRequired(), Email()])
    submit = SubmitField('Get Medicine Details')

class PharmacyMedicineForm(FlaskForm):
    patient_email = StringField('Patient Email', validators=[InputRequired(), Email()])
    medicine_name = StringField('Medicine Name', validators=[InputRequired()])
    quantity = StringField('Quantity', validators=[InputRequired()])
    rate = StringField('Rate', validators=[InputRequired()])
    submit = SubmitField('Add Medicine')

@app.route('/pharmacy_details/<email>', methods=['GET', 'POST'])
@login_required
def pharmacy_details(email):
    pharmacy_medicine_form = PharmacyMedicineForm()
    patient_email = None
    patient_details = []
    patient_email_form = PatientEmailForm() #
    
    if patient_email_form.validate_on_submit():#
        patient_email = patient_email_form.patient_email.data #
        patient = User.query.filter_by(email=patient_email).first() #
        if patient:
            patient_details = HospitalDetails.query.filter_by(patient_id=patient.id).all() #

    if pharmacy_medicine_form.validate_on_submit(): 
        
        patient_email = pharmacy_medicine_form.patient_email.data 
        medicine_name = pharmacy_medicine_form.medicine_name.data 
        quantity = pharmacy_medicine_form.quantity.data 
        rate = pharmacy_medicine_form.rate.data  
        patient = User.query.filter_by(email=patient_email).first()      
        if patient: 
            
            pharmacy_medicine = PharmacyMedicineDetails(
                patient_id=patient.id, #current_user.id
                patient_email=patient_email,
                medicine_name=medicine_name,
                quantity=quantity,
                rate=rate
            ) 
            db.session.add(pharmacy_medicine)
            db.session.commit()
    
    return render_template('pharmacyDetails.html', patient_email_form=patient_email_form, pharmacy_medicine_form=pharmacy_medicine_form, patient_details=patient_details)




#end of pharmacy wala 
if __name__ == '__main__': 
    db.create_all() 
    app.run(debug=True) 

#Ignore all changes
    
    
# class PharmacyMedicineDetails(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     patient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
#     patient_email = db.Column(db.String(255))
#     medicine_name = db.Column(db.String(255))
#     quantity = db.Column(db.String(50))
#     rate = db.Column(db.String(50))



# class PatientEmailForm(FlaskForm):
#     patient_email = StringField('Enter Patient Email', validators=[InputRequired(), Email()])
#     submit = SubmitField('Get Medicine Details')

# class PharmacyMedicineForm(FlaskForm):
#     email = StringField('Patient Email', validators=[InputRequired(), Email()])
#     medicine_name = StringField('Medicine Name', validators=[InputRequired()])
#     quantity = StringField('Quantity', validators=[InputRequired()])
#     rate = StringField('Rate', validators=[InputRequired()])
#     submit = SubmitField('Add Medicine')

# @app.route('/pharmacy_details/<email>', methods=['GET', 'POST'])
# @login_required
# def pharmacy_details(email):
#     pharmacy_medicine_form = PharmacyMedicineForm()
#     patient_email = None
#     patient_details = []
#     patient_email_form = PatientEmailForm()
    
#     if patient_email_form.validate_on_submit():
#         patient_email = patient_email_form.patient_email.data
#         patient = User.query.filter_by(email=patient_email).first()
#         if patient:
#             patient_details = HospitalDetails.query.filter_by(patient_id=patient.id).all()

#     if pharmacy_medicine_form.validate_on_submit(): 
        
#         patient_email = patient_email_form.patient_email.data 
#         medicine_name = pharmacy_medicine_form.medicine_name.data 
#         quantity = pharmacy_medicine_form.quantity.data 
#         rate = pharmacy_medicine_form.rate.data  
#         patient = User.query.filter_by(email=patient_email).first()      
#         if patient: 
            
#             pharmacy_medicine = PharmacyMedicineDetails(
#                 patient_id=patient.id, #current_user.id
#                 patient_email=patient_email,
#                 medicine_name=medicine_name,
#                 quantity=quantity,
#                 rate=rate
#             ) 
#             db.session.add(pharmacy_medicine)
#             db.session.commit()
    
#     return render_template('pharmacyDetails.html', patient_email_form=patient_email_form, pharmacy_medicine_form=pharmacy_medicine_form, patient_details=patient_details)
    
