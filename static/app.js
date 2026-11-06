
const socket = io();
let currentRoom = null;
let myName = "";
let currentGame = null;
let latestGameState = null;

const $ = id => document.getElementById(id);

function toast(message) {
  const el = $("toast");
  el.textContent = message;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2600);
}

function enterRoom(code, name) {
  currentRoom = code;
  myName = name;
  $("lobby").classList.add("hidden");
  $("room").classList.remove("hidden");
  $("gameView").classList.add("hidden");
  $("roomCode").textContent = code;
  $("playerOne").textContent = name;
}

$("createBtn").onclick = () => {
  const name = $("playerName").value.trim();
  if (!name) return toast("Please enter your name first 💗");
  socket.emit("create_room", {name});
};

$("joinBtn").onclick = () => {
  const name = $("playerName").value.trim();
  const code = $("roomCodeInput").value.trim();
  if (!name || !code) return toast("Enter your name and room code.");
  socket.emit("join_room", {name, code});
};

$("roomCodeInput").addEventListener("input", e => {
  e.target.value = e.target.value.toUpperCase();
});

socket.on("room_created", d => {
  enterRoom(d.code, d.name);
  toast("Your room is ready! Share the code 💌");
});

socket.on("joined_room", d => {
  enterRoom(d.code, d.name);
  toast("You joined your little world! ♡");
});

socket.on("error_message", d => toast(d.message));

socket.on("room_update", room => {
  $("roomCode").textContent = room.code;
  const players = room.players || [];

  if (players.length) $("playerOne").textContent = players[0].name;

  $("playerTwo").textContent = players.length > 1
    ? players[1].name
    : "Waiting for your person...";

  $("partnerStatus").textContent = players.length > 1
    ? "Both of you are connected ♡"
    : "Share your code to invite your person";

  $("scores").innerHTML = Object.entries(room.scores || {})
    .map(([n,s]) =>
      `<div class="score-row"><span>${escapeHtml(n)}</span><strong>${s} pts</strong></div>`
    ).join("") || '<p class="muted">Your scores will appear here.</p>';
});

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    "&":"&amp;",
    "<":"&lt;",
    ">":"&gt;",
    '"':"&quot;",
    "'":"&#39;"
  }[c]));
}

$("copyCode").onclick = async () => {
  try {
    await navigator.clipboard.writeText(currentRoom);
    toast("Room code copied!");
  } catch {
    toast("Your room code is " + currentRoom);
  }
};

document.querySelectorAll(".game-card").forEach(btn => {
  btn.onclick = () => {
    currentGame = btn.dataset.game;
    socket.emit("select_game", {game: currentGame});
    $("room").classList.add("hidden");
    $("gameView").classList.remove("hidden");
  };
});

$("backBtn").onclick = () => {
  $("gameView").classList.add("hidden");
  $("room").classList.remove("hidden");
};

socket.on("game_state", state => {
  latestGameState = state;
  renderGame(state);
});

socket.on("waiting_for_partner", d => toast(d.message));
socket.on("quiz_round_result", d => toast(d.message));
socket.on("rather_round_result", d => toast(d.message));

socket.on("chat_message", d => {
  const box = $("chatMessages");
  const empty = box.querySelector(".empty-chat");
  if (empty) empty.remove();

  const item = document.createElement("div");
  item.className = "chat-bubble";

  const b = document.createElement("b");
  b.textContent = d.name + ": ";

  const span = document.createElement("span");
  span.textContent = d.message;

  item.append(b, span);
  box.append(item);
  box.scrollTop = box.scrollHeight;
});

$("chatForm").onsubmit = e => {
  e.preventDefault();
  const input = $("chatInput");
  const message = input.value.trim();

  if (message) {
    socket.emit("send_chat", {message});
    input.value = "";
  }
};

function stage(title, subtitle, body) {
  $("gameContent").innerHTML =
    `<h2 class="game-title">${title}</h2>
     <p class="game-subtitle">${subtitle}</p>${body}`;
}

function renderGame(s) {
  if (!s) return;
  currentGame = s.game;

  if (s.game === "quiz") {
    const q = s.question;

    stage(
      "Love Quiz ♡",
      `Question ${s.index+1} of ${s.total} · Choose what you think your partner would say`,
      `<div class="question-card">${escapeHtml(q.q)}</div>
       <div class="answer-grid">
       ${q.a.map((a,i) =>
         `<button class="answer-btn" data-answer="${i}">${escapeHtml(a)}</button>`
       ).join("")}
       </div>
       <p class="status-line">Choose an answer. Your partner answers too.</p>`
    );

    document.querySelectorAll("[data-answer]").forEach(b => {
      b.onclick = () => {
        socket.emit("quiz_answer", {answer: b.dataset.answer});
        document.querySelectorAll("[data-answer]").forEach(x => x.disabled = true);
        toast("Answer sent! Waiting for your partner.");
      };
    });

  } else if (s.game === "truth") {

    stage(
      "Truth or Dare ✨",
      "Take turns and make a sweet memory",
      `<div class="prompt-label">YOUR TRUTH</div>
       <div class="prompt-box">${escapeHtml(s.truth)}</div>
       <div class="prompt-label">YOUR DARE</div>
       <div class="prompt-box">${escapeHtml(s.dare)}</div>
       <p class="status-line">It is ${escapeHtml(s.turn_name || "a player's")} turn</p>
       <div class="action-row">
       <button id="nextPrompt" ${s.turn_sid !== socket.id ? "disabled" : ""}>
       Next prompts ↻
       </button></div>`
    );

    $("nextPrompt").onclick = () => socket.emit("next_prompt");

  } else if (s.game === "rather") {

    stage(
      "Would You Rather? 💕",
      `Round ${s.index+1} · Both choose one`,
      `<div class="choice-grid">
       <button class="choice-btn" data-choice="0">${escapeHtml(s.options[0])}</button>
       <button class="choice-btn" data-choice="1">${escapeHtml(s.options[1])}</button>
       </div>
       <p class="status-line">Pick your favourite. Your partner's choice stays secret until both vote.</p>`
    );

    document.querySelectorAll("[data-choice]").forEach(b => {
      b.onclick = () => {
        socket.emit("rather_vote", {choice: b.dataset.choice});
        document.querySelectorAll("[data-choice]").forEach(x => x.disabled = true);
        toast("Your choice is in! Waiting for your partner.");
      };
    });

  } else if (s.game === "tictactoe") {

    const status = s.winner
      ? (s.winner === "draw"
          ? "It's a draw! Play again?"
          : `Player ${s.winner} wins! ♡`)
      : `It's ${s.turn%2===0 ? "X" : "O"}'s turn`;

    stage(
      "Tic-Tac-Toe ⭕",
      "A little friendly competition",
      `<div class="board">
       ${s.board.map((v,i) =>
         `<button class="cell" data-cell="${i}" ${v || s.winner ? "disabled" : ""}>${v}</button>`
       ).join("")}
       </div>
       <p class="status-line">${status}</p>
       ${s.winner ? '<button id="restart" class="restart-btn">Play again ↻</button>' : ""}`
    );

    document.querySelectorAll("[data-cell]").forEach(b => {
      b.onclick = () => socket.emit("tic_move", {
        index: Number(b.dataset.cell)
      });
    });

    if ($("restart")) {
      $("restart").onclick = () =>
        socket.emit("select_game", {game:"tictactoe"});
    }

  } else if (s.game === "fighter") {
    fighterPlayerIndex = s.you || 0;
    const players = s.players || [];
    const boy = players[0] || {name:"Boy",x:180,y:0,action:"idle"};
    const girl = players[1] || {name:"Girl",x:820,y:0,action:"idle"};
    const health = s.health || [100,100];
    stage("Couple Fighters 💗", "Move, jump, punch and kick in your love arena", `
      <div class="fight-hud"><div><b>🥋 ${escapeHtml(boy.name || "Boy")}</b><div class="health-track"><span style="width:${health[0]}%"></span></div><small>${health[0]}%</small></div><strong>💗 VS 💗</strong><div><b>🥋 ${escapeHtml(girl.name || "Girl")}</b><div class="health-track"><span style="width:${health[1]}%"></span></div><small>${health[1]}%</small></div></div>
      <div class="fight-arena"><img class="fight-background" src="/static/images/couple_fight_arena.png" alt="Romantic fighting garden"><div class="fight-fighter boy-fighter" style="left:${Math.min(85,Math.max(5,boy.x/10))}%;bottom:${90+(boy.y||0)}px">🥋<small>${escapeHtml(boy.action||"ready")}</small></div><div class="fight-fighter girl-fighter" style="left:${Math.min(85,Math.max(5,girl.x/10))}%;bottom:${90+(girl.y||0)}px">🥋<small>${escapeHtml(girl.action||"ready")}</small></div>${s.winner !== null && s.winner !== undefined ? `<div class="fight-winner">${s.winner===0?escapeHtml(boy.name):escapeHtml(girl.name)} wins! 💕</div>`:""}</div>
      <p class="status-line">${players.length<2?"Waiting for your partner to join...":"Player 1: A/D move, W jump, F punch, G kick, S block · Player 2: ←/→ move, ↑ jump, K punch, L kick, ↓ block"}</p>
      <div class="fight-controls"><div class="fight-pad"><button data-fight="left">◀</button><button data-fight="jump">⬆</button><button data-fight="right">▶</button><button data-fight="block">🛡</button></div><div class="fight-pad attacks"><button data-fight="punch">👊 Punch</button><button data-fight="kick">🦵 Kick</button></div></div>
      ${s.winner!==null && s.winner!==undefined?'<button id="fightAgain" class="restart-btn">Fight again ↻</button>':''}`);
    bindFightControls();
    if ($("fightAgain")) $("fightAgain").onclick=()=>socket.emit("fighter_reset");
  } else if (s.game === "countdown") {

    const date = s.meeting_date;
    let days = null;

    if (date) {
      days = Math.ceil(
        (new Date(date+"T00:00:00") -
        new Date(new Date().toDateString())) / 86400000
      );
    }

    const count = date
      ? (days > 0
          ? `<div class="count-number">${days}</div><div class="count-label">DAYS UNTIL YOUR NEXT MEET-UP ♡</div>`
          : days === 0
            ? '<div class="count-number">Today!</div><div class="count-label">YOUR DAY IS HERE ♡</div>'
            : '<div class="count-number">♡</div><div class="count-label">That date has passed. Set a new one!</div>')
      : '<div class="count-number">♡</div><div class="count-label">Choose a date to start your countdown</div>';

    stage(
      "Until I see you… 🗓️",
      "A date to look forward to, together",
      `${count}
       <form id="dateForm" class="date-form">
       <input id="meetingDate" type="date" required
       min="${new Date().toISOString().slice(0,10)}"
       value="${date || ""}">
       <button>Save our date</button>
       </form>
       <p class="status-line">Your chosen date is shared with both of you.</p>`
    );

    $("dateForm").onsubmit = e => {
      e.preventDefault();
      socket.emit("set_meeting_date", {
        date: $("meetingDate").value
      });
      toast("Your special date is saved ♡");
    };
  }
}


// Couple Fighters: keyboard + touch controls, synced through Flask-SocketIO.
let fighterKeys = {};
let fighterActionTimer = null;
let fighterPlayerIndex = 0;
function sendFighterAction(action) {
  if (currentGame !== "fighter") return;
  socket.emit("fighter_action", {action});
}
function bindFightControls() {
  document.querySelectorAll("[data-fight]").forEach(btn => {
    const action = btn.dataset.fight;
    const down = e => { e.preventDefault(); sendFighterAction(action); };
    btn.addEventListener("pointerdown", down);
    btn.addEventListener("pointerup", () => { if (["left","right","block"].includes(action)) sendFighterAction("idle"); });
    btn.addEventListener("pointerleave", () => { if (["left","right","block"].includes(action)) sendFighterAction("idle"); });
  });
}
window.addEventListener("keydown", e => {
  if (currentGame !== "fighter" || e.repeat) return;
  const p1 = {a:"left",d:"right",w:"jump",s:"block",f:"punch",g:"kick"};
  const p2 = {ArrowLeft:"left",ArrowRight:"right",ArrowUp:"jump",ArrowDown:"block",k:"punch",l:"kick"};
  const map = fighterPlayerIndex === 0 ? p1 : p2;
  const action = map[e.key] || map[e.key.toLowerCase()];
  if (action) { e.preventDefault(); sendFighterAction(action); }
});
window.addEventListener("keyup", e => {
  if (currentGame !== "fighter") return;
  if (["ArrowLeft","ArrowRight","ArrowDown","a","d","s"].includes(e.key)) sendFighterAction("idle");
});
socket.on("fighter_result", d => toast(d.message));
