import os, datetime
from flask import Flask,render_template, request, redirect, url_for, session,flash
from flask_sqlalchemy import SQLAlchemy
import matplotlib.pyplot as plt
import matplotlib
from sqlalchemy import func
matplotlib.use("Agg")
from datetime import datetime, timezone
from flask import send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'key'

current_dir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+ os.path.join(current_dir, "database.sqlite3")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

db = SQLAlchemy(app)

app.app_context().push()


#--------------------------Models and Tables--------------------------------#

class User(db.Model):
    __tablename__ = 'user'
    UserID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Email = db.Column(db.String, nullable=False)
    UserName = db.Column(db.String, unique=True, nullable=False)
    Password = db.Column(db.String, nullable=False)
    Role = db.Column(db.String, default='User')
    BookAssign = db.Column(db.Integer, nullable=False , default=0)

    TransectionR = db.relationship('Transection', backref='user', lazy=True)
    FeedbackR = db.relationship('Feedback', backref='user', lazy=True)
   


class Section(db.Model):
    __tablename__ = 'section'
    SectionID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SectionName = db.Column(db.String, nullable=False)
    CreationDate = db.Column(db.String, nullable=False)
    Description = db.Column(db.String, nullable=False)

    BookR = db.relationship('Book', backref='section', lazy=True)


class Book(db.Model):
    __tablename__ = 'book'
    BookID = db.Column(db.Integer, primary_key=True,autoincrement=True)
    BookName = db.Column(db.String, nullable=False)
    Content = db.Column(db.String, nullable=False)
    Author = db.Column(db.String, nullable=False)
    AvgRating = db.Column(db.Integer, default=0)
    SectionID = db.Column(db.Integer,db.ForeignKey('section.SectionID'), nullable=False)

   
    TransectionR = db.relationship('Transection', backref='book', lazy=True)
    FeedbackR = db.relationship('Feedback', backref='book', lazy=True)
   

class Transection(db.Model):
    __tablename__ = 'transection'
    TransID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Tenure = db.Column(db.Integer, nullable=False)
    UserID = db.Column(db.Integer, db.ForeignKey('user.UserID'), nullable=False)
    BookID = db.Column(db.Integer, db.ForeignKey('book.BookID'), nullable=False)
    Status = db.Column(db.String, nullable=False, default="Pending")
    DateIssued = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc).date())



class Feedback(db.Model):
    __tablename__ = 'feedback'
    FeedbackID = db.Column(db.Integer,primary_key = True,autoincrement=True)
    Feedback = db.Column(db.String, nullable=False)
    AvgRating = db.Column(db.Integer, default=0)
    UserID = db.Column(db.Integer, db.ForeignKey('user.UserID'),nullable=False)
    BookID = db.Column(db.Integer, db.ForeignKey('book.BookID'), nullable=False)


#--------------------------------------------Routes/Controller--------------------------------------------#

@app.route('/',methods = ['GET', 'POST'])
def hello():
    return render_template('index.html')

@app.route('/userlogin',methods = ['GET', 'POST'])
def userlogin():
    return render_template('user_login.html')

@app.route('/register',methods = ['GET', 'POST'])
def user_register():
    return render_template('user_reg.html')

 #--------------------------------------------------Admin Login--------------------------------------------------#


@app.route('/adminlogin',methods = ['GET', 'POST'])
def adminlogin():
    return render_template('librarian_login.html')

@app.route('/adminloggedin',methods = ['GET', 'POST'])
def adminloggedin():
    if request.method == 'POST':
        UserName = request.form['username']
        Password = request.form['password']

        admin = User.query.filter_by(UserName=UserName,Password=Password,Role='Admin').first()
        if  admin:
            sections = Section.query.all()
            return render_template("lbd_0.html", sections = sections)
        else:
            return render_template("loginfailed.html") 
    sections = Section.query.all()
    return render_template("lbd_0.html", sections = sections)
 
 #--------------------------------------------------User Login--------------------------------------------------#


@app.route('/userloggedin',methods = ['GET', 'POST'])
def userloggedin():
    if request.method == 'POST':
        UserName = request.form['username']
        Password = request.form['password']

        user = User.query.filter_by(UserName=UserName,Password=Password,Role='User').first()
        book = Book.query.all()
        sections = Section.query.all()
        if  user:
            session['userid'] = user.UserID
            return render_template('udb_books.html',u_name=UserName,book=book,sections=sections)
        else:
            return render_template("loginfailed.html")
    return ('Not post')



 #--------------------------------------------------User Reg--------------------------------------------------#


@app.route("/userregister", methods = ['GET', 'POST'] )      
def signup():
    if request.method=='POST':
        Email = request.form['email']
        UserName = request.form['username']
        Password = request.form['password']
        user = User(Email = Email, UserName = UserName, Password= Password)
        db.session.add(user)
        db.session.commit()
        return userloggedin()    

#--------------------------------------------------Logout--------------------------------------------------#

@app.route('/logout')
def logout():
    session.pop('userid', None)  
    return render_template("index.html")

#--------------------------------------------------Add Section--------------------------------------------------#


@app.route("/secadd",methods = ['GET', 'POST'])
def addsec():
    if request.method=='POST':
        SectionName = request.form['stitle']
        CreationDate = request.form['scdate']
        Description = request.form['sdescription']
        section = Section( SectionName =  SectionName, CreationDate = CreationDate, Description= Description)
        db.session.add(section)
        db.session.commit()
    sections = Section.query.all()    
    return render_template('lbd_0.html', sections=sections)

    
#--------------------------------------------------Add Book--------------------------------------------------#


@app.route("/addbook/<SectionID>", methods=['GET', 'POST'])
def addbook(SectionID):
    if request.method == 'POST':
        BookName = request.form['btitle']
        Author = request.form['bauthor']
        AvgRating = request.form['brating']
        if 'pdf_file' not in request.files:
            return 'No file part'
    
        file = request.files['pdf_file']
        
        if file.filename == '':
            return 'No selected file'

        if file and file.filename.endswith('.pdf'):
            upload_folder = 'static'
            filename = secure_filename(file.filename)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            book = Book(BookName=BookName, Content=filename, Author=Author, AvgRating=AvgRating, SectionID=SectionID)
            db.session.add(book)
            db.session.commit()
            
        else:
            return 'Invalid file format'
    section = Section.query.filter_by(SectionID=SectionID).first()
    books = Book.query.filter_by(SectionID=SectionID).all()
    return render_template('lbd_ab.html', section=section, books=books)    
   


@app.route('/addbook/libdashboard',methods = ['GET', 'POST'])
def libdash():
    sections = Section.query.all()
    return render_template("lbd_0.html", sections = sections)

#--------------------------------------------------Delete Book--------------------------------------------------#

@app.route("/deletebook/<BookID>", methods=['POST'])
def delete_book(BookID):
    book = Book.query.get(BookID)
    feedbacks = Feedback.query.filter_by(BookID=BookID).all()
    transactions = Transection.query.filter_by(BookID=BookID).all()
    for feedback in feedbacks:
        db.session.delete(feedback)
        db.session.commit()
    for transaction in transactions:
        db.session.delete(transaction)
        db.session.commit()
    if book:
        section_id = book.SectionID
        db.session.delete(book)
        db.session.commit() 
    return redirect(url_for('addbook', SectionID=section_id))


#--------------------------------------------------Edit Book--------------------------------------------------#

@app.route('/edit_book/<BookID>', methods=['GET','POST'])
def edit_book(BookID):    
    book = Book.query.filter_by(BookID=BookID).first()
    section = Section.query.filter_by(SectionID=book.SectionID).first()
    return render_template('edit_book.html', section=section,book=book)


@app.route('/edited_book/<BookID>', methods=['POST'])
def edited_book(BookID):  
    if request.method == 'POST':
        print(request.form)
        book = Book.query.filter_by(BookID=BookID).first()
        book.BookName = request.form['btitle']
        book.Author = request.form['bauthor']
        book.AvgRating = request.form['brating']
        file = request.files['pdf_file']

        if file and file.filename.endswith('.pdf'):
            upload_folder = 'static'
            filename = secure_filename(file.filename)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            book.Content = filename

        db.session.commit() 

    section = Section.query.filter_by(SectionID=book.SectionID).first()
    sectionid = section.SectionID
    return redirect(url_for('addbook', SectionID = sectionid))

#--------------------------------------------------Delete Section--------------------------------------------------#

@app.route("/deletesection/<int:SectionID>", methods=['POST'])
def delete_section(SectionID):
    section = Section.query.get(SectionID)
    books = Book.query.filter_by(SectionID=SectionID).all()
    for book in books:
        delete_book(book.BookID)
    if section:
        db.session.delete(section)
        db.session.commit()
    return redirect(url_for('addsec'))
    
#--------------------------------------------------Edit Section--------------------------------------------------#

@app.route('/edit_section/<SectionID>', methods=['GET','POST'])
def edit_section(SectionID):    
    section = Section.query.filter_by(SectionID=SectionID).first()
    return render_template('edit_section.html', section=section)


@app.route('/edited_section/<int:SectionID>', methods=['POST'])
def edited_section(SectionID):  
    if request.method == 'POST':
        section = Section.query.filter_by(SectionID=SectionID).first()
        if section:
            section.SectionName = request.form['stitle']
            section.CreationDate = request.form['scdate']
            section.Description = request.form['sdescription']
            db.session.commit()
    return redirect(url_for('addsec', SectionID=SectionID))

#--------------------------------------------------Search--------------------------------------------------#
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_term = request.form['search']
        books = Book.query.filter(
            (Book.BookName.like(f"%{search_term}%")) |
            (Book.Author.like(f"%{search_term}%")) |
            (Book.section.has(Section.SectionName.like(f"%{search_term}%")))
        ).all()
        sections = Section.query.all()
        return render_template('search_result.html', books=books, sections=sections)
    return render_template('search_result.html')
#--------------------------------------------------Stats--------------------------------------------------#

@app.route('/stats')
def most_lent_books():
    books_data = db.session.query(Book.BookName, func.count(Transection.BookID)).\
                 join(Transection, Book.BookID == Transection.BookID).\
                 group_by(Book.BookName).all()
    books, counts = zip(*books_data)
    plt.figure(figsize=(10, 6))
    plt.barh(books, counts, color='skyblue')
    plt.xlabel('Number of Transactions')
    plt.ylabel('Book Name')
    plt.title('Most Lent Books')
    plt.xticks(rotation=45)
    plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: int(x)))
    plt.tight_layout()
    img_path = 'static/img.png'
    plt.savefig(img_path)
    return render_template('ldb_stats.html', img_path=img_path)


#--------------------------------------------------Transactions--------------------------------------------------#

@app.route('/tenure_details/<int:BookID>')
def tenure_details(BookID):
    book = Book.query.get(BookID)
    if book:
        return render_template('lendbook.html', book_id=BookID, book_name=book.BookName)
    
#--------------------------------------------------Book Request--------------------------------------------------#

@app.route('/book_request/<int:book_id>', methods=['POST'])
def book_request(book_id):
    user_id = session.get('userid')
    current_approved_books_count = Transection.query.filter_by(UserID=user_id, Status='Approved').count()
    if current_approved_books_count >= 5:
        flash('You have 5 books in your hand. Please return one before borrowing another ;-)', 'warning')
        return redirect('/bookshop')
    tenure = request.form.get('tenure')
    prev_transection = Transection.query.filter_by(UserID=user_id, BookID=book_id, Status='Approved').first()
    if prev_transection:
        flash('You have already lent this book. Please choose another book.', 'warning')
        return redirect('/bookshop')
    if int(tenure) <= 7:
        transection = Transection(Tenure=tenure, UserID=user_id, BookID=book_id, Status='Pending')
        db.session.add(transection)
        db.session.commit()
        return redirect(url_for('lending_success', book_id=book_id))
    else:
        flash('Please select a tenure less than or equal to 7 days.', 'warning')
        return redirect('/bookshop')




@app.route('/lending_success/<int:book_id>')
def lending_success(book_id):
    book = Book.query.get(book_id)
    if book:
        return render_template('lendingsuccess.html', book=book)
    
#--------------------------------------------------Purchase Book--------------------------------------------------#

@app.route('/purchase/<int:book_id>', methods=['GET', 'POST'])
def purchase_book(book_id):
    book = Book.query.filter_by(BookID=book_id).first()
    return render_template('purchase.html',book=book)

@app.route('/view/<BookID>')
def view_book(BookID):
    book = Book.query.filter_by(BookID=BookID).first()
    if book:
        return render_template('view_book.html', book=book)

#--------------------------------------------------My books User--------------------------------------------------#

@app.route('/mybooks', methods=['GET', 'POST'])
def my_books():
    user_id = session.get('userid')
    requested_books = Transection.query.filter_by(Status='Pending', UserID=user_id).all()
    approved_books = Transection.query.filter_by(Status='Approved', UserID=user_id).all()
    declined_books = Transection.query.filter_by(Status='Declined', UserID=user_id).all()
    user = User.query.filter_by(UserID=user_id).first()
    requested_books_with_trans_id = [(transection, Book.query.get(transection.BookID), transection.TransID, transection.DateIssued.date()) for transection in requested_books]
    approved_books_with_trans_id = [(transection, Book.query.get(transection.BookID), transection.TransID, transection.DateIssued.date()) for transection in approved_books]
    declined_books_with_trans_id = [(transection, Book.query.get(transection.BookID), transection.TransID, transection.DateIssued.date()) for transection in declined_books]
    return render_template('udb_mybooks.html', user=user, requested_books=requested_books_with_trans_id, approved_books=approved_books_with_trans_id, declined_books=declined_books_with_trans_id)

#--------------------------------------------------Librarian Requests--------------------------------------------------#

@app.route('/requests')
def show_requests():
    requests = Transection.query.filter_by(Status='Pending').all()
    for request in requests:
        user = User.query.get(request.UserID)
        book = Book.query.get(request.BookID)
        request.user = user
        request.book = book
    return render_template('requests.html', requests=requests)

@app.route('/approve_request/<int:trans_id>', methods=['POST'])
def approve_request(trans_id):
    request = Transection.query.get(trans_id)
    request.Status = 'Approved'
    db.session.commit()
    return redirect(url_for('show_requests'))


@app.route('/decline_request/<int:trans_id>', methods=['POST'])
def decline_request(trans_id):
    transaction = Transection.query.get(trans_id)
    if transaction:
        transaction.Status = "Declined"
        db.session.commit()  
        return redirect(url_for('show_requests')) 
    
#--------------------------------------------------Librarian's Page Distribution--------------------------------------------------#

@app.route('/revoke_access/<int:user_id>/<int:book_id>', methods=['POST'])
def revoke_access(user_id, book_id):
    book_transection = Transection.query.filter_by(UserID=user_id, BookID=book_id, Status='Approved').first()
    if book_transection:
        book_transection.Status = 'Returned'
        db.session.commit()
    return redirect(url_for('list_books'))

#--------------------------------------------------Books Collection User--------------------------------------------------#

@app.route('/bookshop', methods=['POST','GET'])
def book_page():
    user_id = session.get('userid')
    user = User.query.filter_by(UserID=user_id).first()
    u_name = user.UserName if user else None
    lent_books = []
    if user_id:
        approved_transactions = Transection.query.filter_by(UserID=user_id, Status='Approved').all()
        lent_books = [transaction.BookID for transaction in approved_transactions]
    books = Book.query.all()
    sections = Section.query.all()
    return render_template('udb_books.html', book=books, sections=sections, u_name=u_name, lent_books=lent_books)


#-------------------------------------------------User Feedback--------------------------------------------------#

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if request.method == 'POST':
        rating = request.form['rate']
        feedback_text = request.form['feedback']
        user_id = request.form['user_id']
        book_id = request.form['book_id']
        feedback = Feedback(Feedback=feedback_text, AvgRating=rating, UserID=user_id, BookID=book_id)
        db.session.add(feedback)
        db.session.commit()
        return redirect('/mybooks')

#--------------------------------------------------Books Return User--------------------------------------------------#

@app.route('/returnbook/<int:transection_id>', methods=['POST'])
def return_book(transection_id):
    transection = Transection.query.get(transection_id)
    if transection:
        transection.Status = 'Returned'
        db.session.commit()
    return redirect(url_for('my_books'))

#--------------------------------------------------Transactions Librarian--------------------------------------------------#

@app.route('/listbook')
def list_books():
    approved_books = db.session.query(Transection, Book).join(Book).filter(Book.BookID == Transection.BookID, Transection.Status == "Approved").all()
    declined_books = db.session.query(Transection, Book).join(Book).filter(Book.BookID == Transection.BookID, Transection.Status == "Declined").all()
    return render_template('list_books.html', approved_books=approved_books, declined_books=declined_books)


#--------------------------------------------------Download pdf--------------------------------------------------#


@app.route('/download/<BookID>')
def download_file(BookID):
    book = Book.query.filter_by(BookID=BookID).first()
    return send_from_directory('static', book.Content, as_attachment=True)


@app.route('/view/<int:BookID>')
def view_file(BookID):
    book = Book.query.filter_by(BookID=int(BookID)).first()
    pdf_url = "/static/"+book.Content  
    return render_template("view_book.html", pdf_url=pdf_url)


if __name__ =="__main__":
    app.run(debug=True) 