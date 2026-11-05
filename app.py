import os, random, sqlite3
from datetime import datetime
from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
DB_PATH = os.path.join(os.path.dirname(__file__), "together.db")
rooms = {}
sid_to_room = {}

QUIZ = [
    {"q": "What is your partner's favourite food?", "a": ["Sweet", "Biryani", "chicken", "Ice cream"]},
    {"q": "What is your partner's dream holiday?", "a": ["Beach", "Mountains", "movie", "Adventure trip"]},
    {"q": "What makes your partner happiest?", "a": ["Your messages", "Surprises", "Quality time", "Gifts"]},
    {"q": "What is your partner's favourite colour?", "a": ["Black", "Blue", "Pink", "Red"]},
    {"q": "What is your partner's favourite date?", "a": ["Movie night", "Dinner date", "Beach walk", "Long drive"]},
    {"q": "Who says 'I love you' more often?", "a": ["Me", "My partner", "Both equally", "It depends"]},
    {"q": "What does your partner prefer on weekends?", "a": ["Sleeping", "Travelling", "Watching movies", "Going out"]},
    {"q": "What is your partner's favourite drink?", "a": ["Coffee", "Tea", "Juice", "Milkshake"]},
    {"q": "What gift would your partner love most?", "a": ["Flowers", "A handwritten letter", "A surprise trip", "A personal gift"]},
    {"q": "What is your partner's dream destination?", "a": ["Maldives", "Paris", "Switzerland", "London"]},
    {"q": "What makes your partner feel loved?", "a": ["Hugs", "Sweet words", "Attention", "Small surprises"]},
    {"q": "Who is more romantic?", "a": ["Me", "My partner", "Both equally", "Neither"]},
    {"q": "What would your partner choose for a perfect evening?", "a": ["Video call", "Watching a movie", "Talking for hours", "Playing games"]},
    {"q": "What is your partner's favourite season?", "a": ["Summer", "Winter", "Rainy season", "Spring"]},
    {"q": "What does your partner miss most about you?", "a": ["Your smile", "Your voice", "Your hugs", "Your company"]},
    {"q": "What would your partner choose for a surprise?", "a": ["Flowers", "Cake", "A visit", "A love letter"]},
    {"q": "What is your partner's favourite music?", "a": ["Romantic songs", "Melody songs", "Party songs", "Old songs"]},
    {"q": "What would your partner prefer after marriage?", "a": ["A big city", "A peaceful town", "Travelling together", "A quiet home"]},
    {"q": "What is your partner most likely to do when upset?", "a": ["Stay quiet", "Talk about it", "Get angry", "Need some time"]},
    {"q": "What is your partner's favourite way to spend time together?", "a": ["Talking", "Travelling", "Cooking", "Watching movies"]},
    {"q": "Who is more likely to plan a surprise?", "a": ["Me", "My partner", "Both", "Neither"]},
    {"q": "What would your partner choose for a dream date?", "a": ["Candlelight dinner", "Beach sunset", "Long drive", "Stargazing"]},
    {"q": "What is most important to your partner in a relationship?", "a": ["Trust", "Honesty", "Communication", "Understanding"]},
    {"q": "What would your partner do first when you meet after a long time?", "a": ["Give a hug", "Hold hands", "Smile", "Start talking"]},
    {"q": "What is your partner's biggest relationship dream?", "a": ["Travelling together", "Building a home", "Growing old together", "Achieving goals together"]},
    {"q": "What is your partner's favourite animal?", "a": ["Dog", "Cat", "Rabbit", "Bird"]},
    {"q": "Which superpower would your partner choose?", "a": ["Flying", "Invisibility", "Time travel", "Reading minds"]},
    {"q": "What is your partner's ideal breakfast?", "a": ["Dosa", "Idli", "Pancakes", "Sandwich"]},
    {"q": "What would your partner choose for a holiday?", "a": ["Relaxing at home", "Beach holiday", "Mountain trip", "City tour"]},
    {"q": "What is your partner's favourite dessert?", "a": ["Chocolate cake", "Ice cream", "Gulab jamun", "Brownie"]},
    {"q": "What is your partner's favourite way to communicate?", "a": ["Text messages", "Phone calls", "Video calls", "Voice notes"]},
    {"q": "What would your partner do on a rainy day?", "a": ["Sleep", "Watch movies", "Drink hot tea", "Go outside"]},
    {"q": "Which quality does your partner value most?", "a": ["Kindness", "Loyalty", "Humour", "Patience"]},
    {"q": "What is your partner's favourite type of movie?", "a": ["Comedy", "Romance", "Action", "Thriller"]},
    {"q": "What would your partner choose as a perfect gift?", "a": ["Watch", "Jewellery", "Gadget", "Handwritten letter"]},
    {"q": "What is your partner's favourite time of day?", "a": ["Morning", "Afternoon", "Evening", "Night"]},
    {"q": "Which activity would your partner enjoy together?", "a": ["Cooking", "Dancing", "Shopping", "Gardening"]},
    {"q": "What would your partner do if you surprised them?", "a": ["Smile", "Hug you", "Become speechless", "Laugh"]},
    {"q": "What is your partner's favourite snack?", "a": ["Chips", "Chocolate", "Popcorn", "Samosa"]},
    {"q": "Which place would your partner choose for a proposal?", "a": ["Beach", "Garden", "Restaurant", "Mountains"]},
    {"q": "What is your partner's favourite celebration?", "a": ["Birthday", "Anniversary", "Festival", "New Year"]},
    {"q": "What would your partner prefer on a free day?", "a": ["Sleep longer", "Meet friends", "Travel", "Spend time with you"]},
    {"q": "What makes your partner laugh the most?", "a": ["Funny videos", "Jokes", "Your silly behaviour", "Comedy movies"]},
    {"q": "Which would your partner choose for a long journey?", "a": ["Music", "Movies", "Talking", "Sleeping"]},
    {"q": "What is your partner's favourite flower?", "a": ["Rose", "Sunflower", "Lily", "Jasmine"]},
    {"q": "What would your partner like to learn with you?", "a": ["Dancing", "Cooking", "A new language", "Photography"]},
    {"q": "What is your partner's favourite kind of surprise?", "a": ["Unexpected visit", "Small gift", "Romantic message", "Special dinner"]},
    {"q": "What would your partner choose for a cosy night?", "a": ["Hot chocolate", "A movie", "Music", "Long conversation"]},
    {"q": "Which memory would your partner like to create?", "a": ["First trip together", "First home together", "A special celebration", "A surprise adventure"]},
    {"q": "What does your partner hope for most in the future?", "a": ["Happiness", "Success", "A loving family", "Travelling together"]},
]
TRUTHS = [
    "What was the first thing you noticed about me?",
    "What is one memory with me that always makes you smile?",
    "What is something you have always wanted us to do together?",
    "When do you miss me the most?",
    "What is one little thing I do that you love?",
]
DARES = [
    "Send your partner your cutest selfie.",
    "Say three things you appreciate about your partner.",
    "Sing one line of a song for your partner.",
    "Describe your perfect virtual date in 30 seconds.",
    "Send a voice note saying something sweet.",
]
WOULD_RATHER = [
    ["A sunset beach date", "A cosy movie night"],
    ["Travel the world together", "Build a peaceful home together"],
    ["Daily long video calls", "One surprise visit every month"],
    ["Cook together on video call", "Play games together all night"],
    ["Receive handwritten letters", "Receive a surprise gift"],
]

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS room_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_code TEXT NOT NULL,
        created_at TEXT NOT NULL,
        meeting_date TEXT
    )""")
    return conn

def new_code():
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    while True:
        code = "".join(random.choice(alphabet) for _ in range(6))
        if code not in rooms:
            return code

def room_public(code):
    r = rooms[code]
    return {"code": code, "players": [{"name": p["name"]} for p in r["players"].values()],
            "game": r.get("game"), "scores": r["scores"], "meeting_date": r.get("meeting_date"),
            "started": r.get("started", False)}

def broadcast_room(code):
    if code in rooms:
        socketio.emit("room_update", room_public(code), to=code)

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("create_room")
def create_room(data):
    name = (data.get("name") or "Player 1").strip()[:24]
    code = new_code()
    rooms[code] = {"players": {}, "scores": {}, "game": None, "started": False,
        "quiz_index": 0, "quiz_answers": {}, "quiz_questions": [], "votes": {}, "rather_index": 0,
        "truth_turn": 0, "truth_prompt": None, "board": [""]*9, "turn": 0, "winner": None,
        "meeting_date": None, "chat": [],
        "fight": {"players": {}, "health": [100,100], "winner": None, "last_action": None}}
    join_room(code)
    rooms[code]["players"][request.sid] = {"name": name}
    rooms[code]["scores"][name] = 0
    sid_to_room[request.sid] = code
    conn=db(); conn.execute("INSERT INTO room_history(room_code, created_at) VALUES (?, ?)", (code, datetime.utcnow().isoformat())); conn.commit(); conn.close()
    emit("room_created", {"code": code, "name": name}); broadcast_room(code)

@socketio.on("join_room")
def handle_join(data):
    code=(data.get("code") or "").strip().upper(); name=(data.get("name") or "Player 2").strip()[:24]
    if code not in rooms:
        emit("error_message", {"message":"Room not found. Check the code and try again."}); return
    room=rooms[code]
    if len(room["players"]) >= 2 and request.sid not in room["players"]:
        emit("error_message", {"message":"This room already has two players."}); return
    join_room(code); room["players"][request.sid]={"name":name}; room["scores"].setdefault(name,0); sid_to_room[request.sid]=code
    emit("joined_room", {"code":code,"name":name}); broadcast_room(code)

@socketio.on("select_game")
def select_game(data):
    code=sid_to_room.get(request.sid); game=data.get("game")
    if not code or game not in ["quiz","truth","rather","tictactoe","countdown","fighter"]: return
    r=rooms[code]; r["game"]=game; r["started"]=True
    if game=="quiz": r["quiz_index"]=0; r["quiz_answers"]={}; r["quiz_questions"]=random.sample(QUIZ, min(10,len(QUIZ)))
    if game=="truth": r["truth_turn"]=0; r["truth_prompt"]=None
    if game=="rather": r["votes"]={}; r["rather_index"]=0
    if game=="tictactoe": r["board"]=[""]*9; r["turn"]=0; r["winner"]=None
    if game=="fighter":
        r["fight"]={"players":{},"health":[100,100],"winner":None,"last_action":None}
        for i,sid in enumerate(r["players"]): r["fight"]["players"][sid]={"x":180 if i==0 else 820,"y":0,"facing":1 if i==0 else -1,"action":"idle","block":False}
    broadcast_room(code); send_game_state(code)

def send_game_state(code):
    r=rooms[code]; game=r.get("game"); payload={"game":game}; sids=list(r["players"].keys())
    if game=="quiz":
        if not r["quiz_questions"]: r["quiz_questions"]=random.sample(QUIZ,min(10,len(QUIZ)))
        payload.update({"index":r["quiz_index"],"total":len(r["quiz_questions"]),"question":r["quiz_questions"][r["quiz_index"]],"answered":len(r["quiz_answers"])})
    elif game=="truth":
        if not r.get("truth_prompt"): r["truth_prompt"]={"truth":random.choice(TRUTHS),"dare":random.choice(DARES)}
        sid=sids[r.get("truth_turn",0)%len(sids)] if sids else None
        payload.update({"truth":r["truth_prompt"]["truth"],"dare":r["truth_prompt"]["dare"],"turn_sid":sid,"turn_name":r["players"].get(sid,{}).get("name","Waiting for a player") if sid else "Waiting for a player"})
    elif game=="rather":
        i=r.get("rather_index",0)%len(WOULD_RATHER); payload.update({"index":i,"options":WOULD_RATHER[i],"votes":len(r["votes"])})
    elif game=="tictactoe":
        sid=sids[r["turn"]%len(sids)] if sids else None
        payload.update({"board":r["board"],"turn":r["turn"],"turn_name":r["players"].get(sid,{}).get("name","Player") if sid else "Player","winner":r.get("winner")})
    elif game=="countdown": payload.update({"meeting_date":r.get("meeting_date")})
    elif game=="fighter":
        f=r["fight"]; payload.update({"players":[{"name":r["players"][sid]["name"],**f["players"].get(sid,{"x":180 if i==0 else 820,"y":0,"facing":1 if i==0 else -1,"action":"idle","block":False})} for i,sid in enumerate(sids)],"health":f["health"],"winner":f["winner"],"you":sids.index(request.sid) if request.sid in sids else 0})
    socketio.emit("game_state",payload,to=code)

@socketio.on("quiz_answer")
def quiz_answer(data):
    code=sid_to_room.get(request.sid)
    if not code or code not in rooms: return
    r=rooms[code]
    if r.get("game")!="quiz" or request.sid not in r["players"] or request.sid in r["quiz_answers"]: return
    answer=str(data.get("answer",""))
    if answer not in ("0","1","2","3"): return
    r["quiz_answers"][request.sid]=answer
    if len(r["quiz_answers"])>=2:
        sids=list(r["players"].keys()); matched=r["quiz_answers"].get(sids[0])==r["quiz_answers"].get(sids[1])
        if matched:
            for sid in sids:
                n=r["players"][sid]["name"]; r["scores"][n]=r["scores"].get(n,0)+1
        socketio.emit("quiz_round_result",{"message":"You matched! Both earn 1 point! ❤️" if matched else "Different answers! Keep discovering each other. 💕"},to=code)
        r["quiz_answers"]={}; r["quiz_index"]+=1
        if r["quiz_index"]>=len(r["quiz_questions"]): r["quiz_index"]=0; r["quiz_questions"]=random.sample(QUIZ,min(10,len(QUIZ)))
        broadcast_room(code); send_game_state(code)
    else: emit("waiting_for_partner",{"message":"Answer saved! Waiting for your partner..."})

@socketio.on("next_prompt")
def next_prompt():
    code=sid_to_room.get(request.sid)
    if not code or code not in rooms: return
    r=rooms[code]; sids=list(r["players"])
    if r.get("game")!="truth" or len(sids)<2: return
    if request.sid!=sids[r["truth_turn"]%len(sids)]: emit("error_message",{"message":"It's your partner's turn right now."}); return
    r["truth_turn"]=(r["truth_turn"]+1)%len(sids); r["truth_prompt"]={"truth":random.choice(TRUTHS),"dare":random.choice(DARES)}; send_game_state(code)

@socketio.on("rather_vote")
def rather_vote(data):
    code=sid_to_room.get(request.sid)
    if not code or code not in rooms: return
    r=rooms[code]
    if r.get("game")!="rather" or request.sid not in r["players"] or request.sid in r["votes"]: return
    try: choice=int(data.get("choice",-1))
    except (TypeError,ValueError): return
    if choice not in (0,1): return
    r["votes"][request.sid]=choice
    if len(r["votes"])>=2:
        sids=list(r["players"]); matched=r["votes"].get(sids[0])==r["votes"].get(sids[1])
        if matched:
            for sid in sids:
                n=r["players"][sid]["name"]; r["scores"][n]=r["scores"].get(n,0)+1
        socketio.emit("rather_round_result",{"message":"You both chose the same thing! Both earn 1 point! 💕" if matched else "Different choices this time! ❤️"},to=code)
        r["votes"]={}; r["rather_index"]=(r["rather_index"]+1)%len(WOULD_RATHER); broadcast_room(code); send_game_state(code)
    else: emit("waiting_for_partner",{"message":"Choice saved! Waiting for your partner."})

@socketio.on("tic_move")
def tic_move(data):
    code=sid_to_room.get(request.sid)
    if not code or code not in rooms: return
    r=rooms[code]
    if r.get("game")!="tictactoe" or r.get("winner"): return
    try: idx=int(data.get("index",-1))
    except (TypeError,ValueError): return
    sids=list(r["players"])
    if idx<0 or idx>8 or r["board"][idx] or not sids or sids[r["turn"]%len(sids)]!=request.sid: return
    mark="X" if r["turn"]%2==0 else "O"; r["board"][idx]=mark
    wins=[(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    if any(r["board"][a]==r["board"][b]==r["board"][c]==mark for a,b,c in wins):
        r["winner"]=mark; n=r["players"][request.sid]["name"]; r["scores"][n]=r["scores"].get(n,0)+2
    elif all(r["board"]): r["winner"]="draw"
    else: r["turn"]+=1
    send_game_state(code); broadcast_room(code)

@socketio.on("set_meeting_date")
def set_meeting_date(data):
    code=sid_to_room.get(request.sid)
    if not code or code not in rooms: return
    date=data.get("date")
    try: datetime.strptime(date,"%Y-%m-%d")
    except (ValueError,TypeError): emit("error_message",{"message":"Please choose a valid date."}); return
    rooms[code]["meeting_date"]=date
    conn=db(); conn.execute("UPDATE room_history SET meeting_date=? WHERE room_code=?",(date,code)); conn.commit(); conn.close(); broadcast_room(code); send_game_state(code)

@socketio.on("fighter_action")
def fighter_action(data):
    code=sid_to_room.get(request.sid)
    if not code or code not in rooms: return
    r=rooms[code]; f=r.get("fight",{}); sids=list(r["players"])
    if r.get("game")!="fighter" or request.sid not in sids or f.get("winner") or len(sids)!=2: return
    i=sids.index(request.sid); other=1-i; action=data.get("action")
    if action not in ("left","right","jump","punch","kick","block","idle"): return
    p=f["players"].setdefault(request.sid,{"x":180 if i==0 else 820,"y":0,"facing":1 if i==0 else -1,"action":"idle","block":False})
    op=f["players"].setdefault(sids[other],{"x":180 if other==0 else 820,"y":0,"facing":1 if other==0 else -1,"action":"idle","block":False})
    if action=="left": p["x"]=max(55,p["x"]-28); p["action"]="walk"
    elif action=="right": p["x"]=min(965,p["x"]+28); p["action"]="walk"
    elif action=="jump": p["y"]=90; p["action"]="jump"
    elif action=="block": p["block"]=True; p["action"]="block"
    elif action in ("punch","kick"):
        p["action"]=action; p["block"]=False
        if abs(p["x"]-op["x"])<175 and op["y"]<45:
            damage=8 if action=="punch" else 13
            if not op.get("block"): f["health"][other]=max(0,f["health"][other]-damage)
    else: p["action"]="idle"; p["block"]=False
    p["facing"]=1 if p["x"]<op["x"] else -1
    op["facing"]=-p["facing"]
    if f["health"][other]<=0:
        f["winner"]=i
        winner_name=r["players"][request.sid]["name"]; r["scores"][winner_name]=r["scores"].get(winner_name,0)+3
        socketio.emit("fighter_result",{"message":winner_name+" wins the Couple Fighters match! 💗"},to=code)
    send_game_state(code)

@socketio.on("fighter_reset")
def fighter_reset():
    code=sid_to_room.get(request.sid)
    if not code or code not in rooms: return
    r=rooms[code]
    if r.get("game")!="fighter": return
    sids=list(r["players"]); r["fight"]={"players":{},"health":[100,100],"winner":None,"last_action":None}
    for i,sid in enumerate(sids): r["fight"]["players"][sid]={"x":180 if i==0 else 820,"y":0,"facing":1 if i==0 else -1,"action":"idle","block":False}
    send_game_state(code)

@socketio.on("send_chat")
def send_chat(data):
    code=sid_to_room.get(request.sid)
    if not code or code not in rooms: return
    name=rooms[code]["players"].get(request.sid,{}).get("name","Player"); message=(data.get("message") or "").strip()[:300]
    if message: socketio.emit("chat_message",{"name":name,"message":message},to=code)

@socketio.on("disconnect")
def disconnect():
    code=sid_to_room.pop(request.sid,None)
    if code and code in rooms:
        rooms[code]["players"].pop(request.sid,None)
        rooms[code].get("fight",{}).get("players",{}).pop(request.sid,None)
        broadcast_room(code)
        if not rooms[code]["players"]: del rooms[code]

if __name__=="__main__":
    socketio.run(app,host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=True)
