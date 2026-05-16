from flask import Flask, render_template, request, redirect, session
import psycopg2
import random

app = Flask(__name__)
app.secret_key = "secret"

conn = psycopg2.connect(
    host="localhost",
    database="online_voting",
    user="pateladil",
    password="adil7841"
)

cur = conn.cursor()

PARTIES = ["BJP", "Congress", "AIMIM", "AAP"]


def generate_voter_id():
    return "VOT" + str(random.randint(1000, 9999))


@app.route('/')
def home():
    return redirect('/admin_login')


@app.route('/admin_signup', methods=['GET','POST'])
def admin_signup():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        cur.execute("INSERT INTO admin (username,password) VALUES (%s,%s)", (u,p))
        conn.commit()
        return redirect('/admin_login')
    return render_template('admin_signup.html')


@app.route('/admin_login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        cur.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (u,p))
        admin = cur.fetchone()
        if admin:
            session['admin'] = u
            return redirect('/dashboard')
    return render_template('admin_login.html')


@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect('/admin_login')

    cur.execute("SELECT COUNT(*) FROM voters")
    total_voters = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM voters WHERE voted=TRUE")
    total_votes = cur.fetchone()[0]

    results = {}
    for party in PARTIES:
        cur.execute("SELECT COUNT(*) FROM voters WHERE vote_party=%s", (party,))
        results[party] = cur.fetchone()[0]

    cur.execute("SELECT * FROM voters ORDER BY id DESC LIMIT 5")
    recent = cur.fetchall()

    return render_template(
        "dashboard.html",
        admin=session['admin'],
        total_voters=total_voters,
        total_votes=total_votes,
        results=results,
        recent=recent
    )


@app.route('/create_voter', methods=['GET','POST'])
def create_voter():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        password = request.form['password']
        voter_id = generate_voter_id()

        cur.execute("""
        INSERT INTO voters
        (voter_id,name,phone,email,address,password)
        VALUES(%s,%s,%s,%s,%s,%s)
        """,(voter_id, name, phone, email, address, password))

        conn.commit()
        return redirect('/dashboard')

    return render_template('create_voter.html', admin=session['admin'])


@app.route('/search_voter', methods=['GET','POST'])
def search_voter():
    voter = None
    if request.method == 'POST':
        vid = request.form['voter_id']
        cur.execute("SELECT * FROM voters WHERE voter_id=%s", (vid,))
        voter = cur.fetchone()

    return render_template('search_voter.html', admin=session['admin'], voter=voter)


@app.route('/edit_voter/<vid>', methods=['GET','POST'])
def edit_voter(vid):
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        password = request.form['password']

        cur.execute("""
        UPDATE voters
        SET name=%s, phone=%s, email=%s, address=%s, password=%s
        WHERE voter_id=%s
        """,(name, phone, email, address, password, vid))

        conn.commit()
        return redirect('/search_voter')

    cur.execute("SELECT * FROM voters WHERE voter_id=%s", (vid,))
    voter = cur.fetchone()

    return render_template("edit_voter.html", admin=session['admin'], v=voter)


@app.route('/delete_voter/<vid>')
def delete_voter():
    cur.execute("DELETE FROM voters WHERE voter_id=%s", (vid,))
    conn.commit()
    return redirect('/search_voter')


@app.route('/verify_voter', methods=['GET','POST'])
def verify_voter():
    status = None
    if request.method == 'POST':
        vid = request.form['voter_id']
        cur.execute("SELECT * FROM voters WHERE voter_id=%s", (vid,))
        voter = cur.fetchone()
        status = "Valid Voter ID" if voter else "Invalid Voter ID"

    return render_template("verify_voter.html", admin=session['admin'], status=status)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/admin_login')


@app.route('/voter_login', methods=['GET','POST'])
def voter_login():
    if request.method == 'POST':
        vid = request.form['voter_id']
        p = request.form['password']

        cur.execute("SELECT * FROM voters WHERE voter_id=%s AND password=%s", (vid,p))
        voter = cur.fetchone()

        if voter:
            if voter[7]:
                return render_template("already_voted.html")

            session['voter'] = vid
            return redirect('/vote')

    return render_template('voter_login.html')


@app.route('/vote', methods=['GET','POST'])
def vote():
    if request.method == 'POST':
        party = request.form['party']
        vid = session['voter']

        cur.execute("UPDATE voters SET voted=TRUE, vote_party=%s WHERE voter_id=%s",(party,vid))
        conn.commit()

        return render_template('vote_success.html', party=party)

    return render_template('vote.html', parties=PARTIES)


if __name__ == "__main__":
    app.run(debug=True)