from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import sqlite3
import json
import pickle
from datetime import datetime
import praw

@csrf_exempt
def sync(request):
	conn = sqlite3.connect('/home/ankileaderboard/anki_leaderboard_pythonanywhere/Leaderboard.db')
	c = conn.cursor()

	User = request.POST.get("Username", "")
	Streak = request.POST.get("Streak", "")
	Cards = request.POST.get("Cards", "")
	Time = request.POST.get("Time", "")
	Sync_Date = request.POST.get("Sync_Date", "")
	Month = request.POST.get("Month","")
	Country = request.POST.get("Country","")
	Retention = request.POST.get("Retention","")

	league_reviews = request.POST.get("league_reviews", 0)
	league_time = request.POST.get("league_time", 0)
	league_retention = request.POST.get("league_retention", 0)
	league_days_learned = request.POST.get("league_days_percent", 0)
	Update_League = request.POST.get("Update_League", True)

	Token = request.POST.get("Token_v3", None)
	Version = request.POST.get("Version", None)

	try:
		sus = c.execute("SELECT suspended FROM Leaderboard WHERE Username = (?)", (User,)).fetchone()[0]
		if sus:
			return HttpResponse(f"<h3>Account suspended</h3>This account was suspended due to the following reason:<br><br>{sus}<br><br>Please write an e-mail to leaderboard_support@protonmail.com or a message me on <a href='https://www.reddit.com/user/Ttime5'>Reddit</a>, if you think that this was a mistake.")
	except:
		pass

	if Retention == "":
		Retention = 0
	if Month == "":
		Month = 0

	### Filter ###

	if User == "" or len(User) > 15:
		return HttpResponse("Error - invalid username")

	if "🥇" in User or "🥈" in User or "🥉" in User or "|" in User:
		return HttpResponse("""<h3>Error - invalid username</h3>
			🥇, 🥈, 🥉 and | aren't allowed in usernames anymore.<br><br>
			If you already have an account that is affected by this, please write an e-mail
			to leaderboard_support@protonmail.com or dm me on <a href="https://www.reddit.com/user/Ttime5">Reddit</a> so we can sort this out.
			Alternatively, you can also create a new account, but keep in mind that this would reset your league progress.""")

	if not Streak.isdigit():
		return HttpResponse("Error - invalid streak value")

	if not Cards.isdigit():
		return HttpResponse("Error - invalid cards value")

	try:
		float(Time)
	except:
		return HttpResponse("Error - invalid time value")

	try:
		check_sync_date = datetime.strptime(Sync_Date, '%Y-%m-%d %H:%M:%S.%f')
	except:
		return HttpResponse("Error invalid timestamp")

	try:
		int(Month)
	except:
		return HttpResponse("Error - invalid month value")

	try:
		float(Retention)
	except:
		return HttpResponse("Error - invalid retention value")

	try:
		int(league_reviews)
	except:
		return HttpResponse("Error - invalid league_reviews value")

	try:
		float(league_time)
	except:
		return HttpResponse("Error - invalid league_time value")

	try:
		float(league_retention)
	except:
		return HttpResponse("Error - invalid league_retention value")

	try:
		float(league_days_learned)
	except:
		return HttpResponse("Error - invalid league_days_learned value")

	### XP ###

	if float(league_retention) >= 85:
		retention_bonus = 1
	if float(league_retention) < 85 and float(league_retention) >= 70:
		retention_bonus = 0.85
	if float(league_retention) < 70 and float(league_retention) >= 55:
		retention_bonus = 0.70
	if float(league_retention) < 55 and float(league_retention) >= 40:
		retention_bonus = 0.55
	if float(league_retention) < 40 and float(league_retention) >= 25:
		retention_bonus = 0.40
	if float(league_retention) < 25 and float(league_retention) >= 10:
		retention_bonus = 0.25
	if float(league_retention) < 10:
		retention_bonus = 0

	xp = int(float(league_days_learned) * ((6 * float(league_time) * 1) + (2 * int(league_reviews) * float(retention_bonus))))

	### Commit to database ###

	if c.execute("SELECT Username FROM Leaderboard WHERE Username = (?)", (User,)).fetchone():
		t = c.execute("SELECT Username, Token FROM Leaderboard WHERE Username = (?)", (User,)).fetchone()
		if t[1] == Token or t[1] is None:
			c.execute("UPDATE Leaderboard SET Streak = (?), Cards = (?), Time_Spend = (?), Sync_Date = (?), Month = (?), Country = (?), Retention = (?), Token = (?), version = (?) WHERE Username = (?) ", (Streak, Cards, Time, Sync_Date, Month, Country, Retention, Token, Version, User))
			conn.commit()

			if Update_League == True:
				if c.execute("SELECT username FROM League WHERE username = (?)", (User,)).fetchone():
					c.execute("UPDATE League SET xp = (?), time_spend = (?), reviews = (?), retention = (?), days_learned = (?) WHERE username = (?) ", (xp, league_time, league_reviews, league_retention, league_days_learned, User))
					conn.commit()
				else:
					c.execute('INSERT INTO League (username, xp, time_spend, reviews, retention, league, days_learned) VALUES(?, ?, ?, ?, ?, ?, ?)', (User, xp, league_time, league_reviews, league_retention, "Delta", league_days_learned))
					conn.commit()

			print("Updated entry: " + str(User) + " (" + str(Version) + ")")
			return HttpResponse("Done!")
		else:
			#with open('/home/ankileaderboard/anki_leaderboard_pythonanywhere/main/config.txt') as json_file:
			#	data = json.load(json_file)
			#r = praw.Reddit(username = data["un"], password = data["pw"], client_id = data["cid"], client_secret = data["cs"], user_agent = data["ua"])
			#r.redditor('Ttime5').message('Verification Error', "Username: " + str(User) + "\n" + "Token: " + str(Token) + "\n" + str(t[1]) + "\n" + "Version: " + str(Version))
			print("Verification error: " + str(User))
			return HttpResponse("""<h3>Error - invalid token</h3>
			The verification token you sent doesn't match the one in the database.
			Make sure that you're using the newest version.<br><br>
			If you recently changed devices, you need to copy your old meta.json file into the leaderboard add-on folder of your new device.<br><br>
			If you need help, please contact me via <a href='https://www.reddit.com/user/Ttime5'>Reddit</a> or send an email to leaderboard_support@protonmail.com.""")
	else:
		c.execute('INSERT INTO Leaderboard (Username, Streak, Cards , Time_Spend, Sync_Date, Month, Country, Retention, Token, version) VALUES(?, ?, ?, ?, ?, ?, ?, ?,?,?)', (User, Streak, Cards, Time, Sync_Date, Month, Country, Retention, Token, Version))
		conn.commit()
		if Update_League == True:
			c.execute('INSERT INTO League (username, xp, time_spend, reviews, retention, league, days_learned) VALUES(?, ?, ?, ?, ?, ?, ?)', (User, xp, league_time, league_reviews, league_retention, "Delta", league_days_learned))
			conn.commit()
		print("Created new entry: " + str(User))
		return HttpResponse("Done!")


@csrf_exempt
def all_users(request):
	conn = sqlite3.connect('/home/ankileaderboard/anki_leaderboard_pythonanywhere/Leaderboard.db')
	c = conn.cursor()
	Username_List = []
	c.execute("SELECT Username FROM Leaderboard")
	for i in c.fetchall():
		username = i[0]
		Username_List.append(username)
	return HttpResponse(json.dumps(Username_List))

@csrf_exempt
def get_data(request):
	sortby = request.POST.get("sortby", "Cards")
	conn = sqlite3.connect('/home/ankileaderboard/anki_leaderboard_pythonanywhere/Leaderboard.db')
	c = conn.cursor()
	c.execute("SELECT Username, Streak, Cards, Time_Spend, Sync_Date, Month, Subject, Country, Retention, groups FROM Leaderboard WHERE suspended IS NULL ORDER BY {} DESC".format(sortby))
	data = []
	for row in c.fetchall():
		if row[9]:
			data.append([row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], pickle.loads(row[9])])
		else:
			data.append([row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], []])
	return HttpResponse(json.dumps(data))

@csrf_exempt
def league_data(request):
	conn = sqlite3.connect('/home/ankileaderboard/anki_leaderboard_pythonanywhere/Leaderboard.db')
	c = conn.cursor()
	c.execute("SELECT username, xp, time_spend, reviews, retention, league, history, days_learned FROM League WHERE suspended IS NULL ORDER BY xp DESC")
	return HttpResponse(json.dumps(c.fetchall()))

@csrf_exempt
def delete(request):
	conn = sqlite3.connect('/home/ankileaderboard/anki_leaderboard_pythonanywhere/Leaderboard.db')
	c = conn.cursor()
	User = request.POST.get("Username", None)
	Token = request.POST.get("Token_v3", None)

	if c.execute("SELECT Username FROM Leaderboard WHERE Username = (?)", (User,)).fetchone():
		t = c.execute("SELECT Username, Token FROM Leaderboard WHERE Username = (?)", (User,)).fetchone()
		if t[1] == Token or t[1] is None:
			c.execute("DELETE FROM Leaderboard WHERE Username = (?)", (User,))
			conn.commit()
			c.execute("DELETE FROM League WHERE username = (?)", (User,))
			conn.commit()
			print("Deleted account: " + str(User))
			return HttpResponse("Deleted")
		return HttpResponse("Failed")
	else:
	    return HttpResponse("<h3>Error</h3>Couldn't find user")
@csrf_exempt
def create_group(request):
	conn = sqlite3.connect('/home/ankileaderboard/anki_leaderboard_pythonanywhere/Leaderboard.db')
	c = conn.cursor()
	Group_Name = request.POST.get("Group_Name", None).strip()
	User = request.POST.get("User", None)
	Pwd = request.POST.get("Pwd", None)
	Mail = request.POST.get("Mail", None)

	if c.execute("SELECT Group_Name FROM Groups WHERE Group_Name = (?)", (Group_Name,)).fetchone():
		return HttpResponse("This group already exists.")
	else:
		if Group_Name:
			c.execute('INSERT INTO Groups (Group_Name, pwd, admins) VALUES(?, ?, ?)', (Group_Name, Pwd, f"{User},"))
			conn.commit()
			with open('/home/ankileaderboard/anki_leaderboard_pythonanywhere/main/config.txt') as json_file:
				data = json.load(json_file)
			r = praw.Reddit(username = data["un"], password = data["pw"], client_id = data["cid"], client_secret = data["cs"], user_agent = data["ua"])
			r.redditor('Ttime5').message('Group Request', f"{User} requested a new group: {Group_Name}\nE-Mail: {Mail}")
			print(f"{User} requested a new group: {Group_Name}")
			return HttpResponse("Done!")

@csrf_exempt
def joinGroup(request):
	conn = sqlite3.connect('/home/ankileaderboard/anki_leaderboard_pythonanywhere/Leaderboard.db')
	c = conn.cursor()
	username = request.POST.get("username", None)
	group = request.POST.get("group", None)
	pwd = request.POST.get("pwd", None)
	token = request.POST.get("token", None)
	check_pwd = c.execute("SELECT pwd FROM Groups WHERE Group_Name = (?)", (group,)).fetchone()
	check_token = c.execute("SELECT Token FROM Leaderboard WHERE Username = (?)", (username,)).fetchone()
	check_banned = c.execute("SELECT banned FROM Groups WHERE Group_Name = (?)", (group,)).fetchone()
	group_list = c.execute("SELECT groups FROM Leaderboard WHERE Username = (?)", (username,)).fetchone()[0]
	if not group_list:
		group_list = []
	else:
		group_list = pickle.loads(group_list)

	try:
		if username in check_banned[0]:
			return HttpResponse("You're banned from this group.")
	except:
		pass

	if check_pwd[0]:
		if check_pwd[0] == pwd and check_token[0] == token:
			if group not in group_list:
				group_list.append(group)
			c.execute("UPDATE Leaderboard SET groups = (?) WHERE Username = (?)", (pickle.dumps(group_list), username))
			conn.commit()
			c.execute("UPDATE Leaderboard SET Subject = (?) WHERE Username = (?)", (group.replace(" ", ""), username))
			conn.commit()
			return HttpResponse("Done!")
		else:
			return HttpResponse("<h3>Something went wrong</h3>Wrong password or verification token.")
	else:
		if check_token[0] == token:
			if group not in group_list:
				group_list.append(group)
			c.execute("UPDATE Leaderboard SET groups = (?) WHERE Username = (?)", (pickle.dumps(group_list), username))
			conn.commit()
			c.execute("UPDATE Leaderboard SET Subject = (?) WHERE Username = (?)", (group.replace(" ", ""), username))
			conn.commit()
			return HttpResponse("Done!")
		else:
			return HttpResponse("<h3>Something went wrong</h3>Wrong verification token.")

@csrf_exempt
def manageGroup(request):
	conn = sqlite3.connect('/home/ankileaderboard/anki_leaderboard_pythonanywhere/Leaderboard.db')
	c = conn.cursor()
	username = request.POST.get("user", None)
	group = request.POST.get("group", None)
	oldPwd = request.POST.get("oldPwd", None)
	newPwd = request.POST.get("newPwd", None)
	token = request.POST.get("token", None)
	addAdmin = request.POST.get("addAdmin", "")
	check_pwd_admins = c.execute("SELECT pwd, admins FROM Groups WHERE Group_Name = (?)", (group,)).fetchone()
	check_token = c.execute("SELECT Token FROM Leaderboard WHERE Username = (?)", (username,)).fetchone()
	if addAdmin:
		newAdmin = f"{check_pwd_admins[1]} {addAdmin},"
	else:
		newAdmin = check_pwd_admins[1]


	if check_pwd_admins[0]:
		if check_pwd_admins[0] == oldPwd and check_token[0] == token and username in check_pwd_admins[1]:
			c.execute("UPDATE Groups SET pwd = (?), admins = (?) WHERE Group_Name = (?) ", (newPwd, newAdmin, group))
			conn.commit()
			return HttpResponse("Done!")
		else:
			return HttpResponse("<h3>Something went wrong</h3>You're either not an admin of this group, or the password is wrong.")
	else:
		if check_token[0] == token and username in check_pwd_admins[1]:
			c.execute("UPDATE Groups SET pwd = (?), admins = (?) WHERE Group_Name = (?) ", (newPwd, newAdmin, group))
			conn.commit()
			return HttpResponse("Done!")
		else:
			return HttpResponse("<h3>Something went wrong</h3>You're not an admin of this group.")

@csrf_exempt
def banUser(request):
	conn = sqlite3.connect('/home/ankileaderboard/anki_leaderboard_pythonanywhere/Leaderboard.db')
	c = conn.cursor()
	toBan = request.POST.get("toBan", None)
	group = request.POST.get("group", None)
	pwd = request.POST.get("pwd", None)
	token = request.POST.get("token", None)
	user = request.POST.get("user", None)
	check_group = c.execute("SELECT pwd, admins, banned FROM Groups WHERE Group_Name = (?)", (group,)).fetchone()
	check_token = c.execute("SELECT Token FROM Leaderboard WHERE Username = (?)", (user,)).fetchone()
	toBan_groups = c.execute("SELECT groups FROM Leaderboard WHERE Username = (?)", (user,)).fetchone()[0]
	if not toBan_groups:
		toBan_groups = []
	else:
		toBan_groups = pickle.loads(toBan_groups)

	if check_group[0]:
		if check_group[0] == pwd and user in check_group[1] and check_token[0] == token:
			if toBan_groups:
				toBan_groups.remove(group)
				c.execute("UPDATE Leaderboard SET groups = (?) WHERE Username = (?) ", (pickle.dumps(toBan_groups), toBan))
				conn.commit()
				c.execute("UPDATE Groups SET banned = (?) WHERE Group_Name = (?) ", (f"{check_group[2]}, {toBan}", group))
				conn.commit()
				c.execute("UPDATE Leaderboard SET Subject = (?) WHERE Username = (?) ", (None, toBan))
				conn.commit()
			else:
				c.execute("UPDATE Groups SET banned = (?) WHERE Group_Name = (?) ", (f"{check_group[2]}, {toBan}", group))
				conn.commit()
				c.execute("UPDATE Leaderboard SET Subject = (?) WHERE Username = (?) ", (None, toBan))
				conn.commit()
			return HttpResponse("Done!")
		else:
			return HttpResponse("<h3>Something went wrong</h3>You're either not an admin of this group, or the password is wrong.")
	else:
		if user in check_group[1] and check_token[0] == token:
			if toBan_groups:
				toBan_groups.remove(group)
				c.execute("UPDATE Leaderboard SET groups = (?) WHERE Username = (?) ", (pickle.dumps(toBan_groups), toBan))
				conn.commit()
				c.execute("UPDATE Groups SET banned = (?) WHERE Group_Name = (?) ", (f"{check_group[2]}, {toBan}", group))
				conn.commit()
			else:
				c.execute("UPDATE Groups SET banned = (?) WHERE Group_Name = (?) ", (f"{check_group[2]}, {toBan}", group))
				conn.commit()
				c.execute("UPDATE Leaderboard SET Subject = (?) WHERE Username = (?) ", (None, toBan))
				conn.commit()
			return HttpResponse("Done!")
		else:
			return HttpResponse("<h3>Something went wrong</h3>You're not an admin of this group.")

@csrf_exempt
def leaveGroup(request):
	conn = sqlite3.connect('/home/ankileaderboard/anki_leaderboard_pythonanywhere/Leaderboard.db')
	c = conn.cursor()
	group = request.POST.get("group", None)
	token = request.POST.get("token", None)
	user = request.POST.get("user", None)
	check_token = c.execute("SELECT Token FROM Leaderboard WHERE Username = (?)", (user,)).fetchone()[0]
	group_list = c.execute("SELECT groups FROM Leaderboard WHERE Username = (?)", (user,)).fetchone()[0]
	group_list = pickle.loads(group_list)
	if check_token == token:
		group_list.remove(group.replace(" ", ""))
		c.execute("UPDATE Leaderboard SET groups = (?) WHERE Username = (?) ", (pickle.dumps(group_list), user))
		conn.commit()
		return HttpResponse("Done!")
	else:
		return HttpResponse("<h3>Something went wrong</h3>Wrong verification token.")


@csrf_exempt
def groups(request):
	conn = sqlite3.connect('/home/ankileaderboard/anki_leaderboard_pythonanywhere/Leaderboard.db')
	c = conn.cursor()
	Group_List = []
	c.execute("SELECT Group_Name FROM Groups WHERE verified = 1")
	for i in c.fetchall():
		Group_Name = i[0]
		Group_List.append(Group_Name)
	return HttpResponse(json.dumps((sorted(Group_List, key=str.lower))))

@csrf_exempt
def setStatus(request):
	conn = sqlite3.connect('/home/ankileaderboard/anki_leaderboard_pythonanywhere/Leaderboard.db')
	c = conn.cursor()
	statusMsg = request.POST.get("status", None)
	if len(statusMsg) > 280:
		statusMsg = None
	username = request.POST.get("username", None)
	Token = request.POST.get("Token_v3", None)
	t = c.execute("SELECT Username, Token FROM Leaderboard WHERE Username = (?)", (username,)).fetchone()
	if t[1] == Token or t[1] is None:
		c.execute("UPDATE Leaderboard SET Status = (?) WHERE username = (?) ", (statusMsg, username))
		conn.commit()
		return HttpResponse("Done!")

@csrf_exempt
def getStatus(request):
	conn = sqlite3.connect('/home/ankileaderboard/anki_leaderboard_pythonanywhere/Leaderboard.db')
	c = conn.cursor()
	username = request.POST.get("username", None)
	return HttpResponse(json.dumps(c.execute("SELECT Status FROM Leaderboard WHERE Username = (?)", (username,)).fetchone()))

@csrf_exempt
def getUserinfo(request):
	conn = sqlite3.connect('/home/ankileaderboard/anki_leaderboard_pythonanywhere/Leaderboard.db')
	c = conn.cursor()
	user = request.POST.get("user", None)
	a = request.POST.get("a", False)
	if a:
		country = c.execute("SELECT Country FROM Leaderboard WHERE Username = (?)", (user,)).fetchone()[0]
		group = c.execute("SELECT Subject, groups FROM Leaderboard WHERE Username = (?)", (user,)).fetchone()
		g_old = group[0]
		if not group[1]:
			g_new = []
		else:
			g_new = pickle.loads(group[1])
		if g_old not in g_new:
		    g_new.append(g_old)
		league = c.execute("SELECT league, history FROM League WHERE username = (?)", (user,)).fetchone()
		status = c.execute("SELECT Status FROM Leaderboard WHERE Username = (?)", (user,)).fetchone()[0]
		return HttpResponse(json.dumps([country, g_new, league[0], league[1], status]))
	else:
		u1 = c.execute("SELECT Country, Subject FROM Leaderboard WHERE Username = (?)", (user,)).fetchone()
		u2 = c.execute("SELECT league, history FROM League WHERE username = (?)", (user,)).fetchone()
		return HttpResponse(json.dumps(u1 + u2))

@csrf_exempt
def reportUser(request):
	user = request.POST.get("user", "")
	report_user = request.POST.get("reportUser", "")
	message = request.POST.get("message", "")

	with open('/home/ankileaderboard/anki_leaderboard_pythonanywhere/main/config.txt') as json_file:
		data = json.load(json_file)
	r = praw.Reddit(username = data["un"], password = data["pw"], client_id = data["cid"], client_secret = data["cs"], user_agent = data["ua"])
	r.redditor('Ttime5').message('Report', f"{user} reported {report_user}. \n Message: {message}")
	return HttpResponse("Done!")

def season(request):
	return HttpResponse(json.dumps([[2021,3,19,0,0,0],[2021,4,2,0,0,0], "Season 13"]))