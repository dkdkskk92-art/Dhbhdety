const API = "";
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

let state = {
  sparks: 0,
  game: null,
  mode: null,        
  mySymbol: "X",
  pollTimer: null,
  waitTimer: null,
  chessSelectedSquare: null,
  chessAvailableMoves: []
};

function authHeaders() { return { "Authorization": "tma " + tg.initData, "Content-Type": "application/json" }; }
async function api(path, method = "GET", body = null) {
  const res = await fetch(API + path, { method, headers: authHeaders(), body: body ? JSON.stringify(body) : null });
  if (!res.ok) { const err = await res.text(); throw new Error(err); }
  return res.json();
}

const screens = ["menu","ttt-menu","level","pvp","chess-menu","wait","game-ttt","game-chess"];
function show(name) {
  screens.forEach(s => {
    const el = document.getElementById("screen-" + s);
    if (el) el.classList.toggle("active", s === name);
  });
}

async function init() {
  try {
    const me = await api("/api/auth", "POST");
    setSparks(me.sparks);
    show("menu");
  } catch(e) { tg.showAlert("Ошибка входа: " + e.message); }
}

function setSparks(n) {
  state.sparks = n;
  const el = document.getElementById("sparks");
  if (el) el.textContent = n;
}

// ==========================================
// МЕНЮ И НАВИГАЦИЯ
// ==========================================
document.getElementById("btn-menu-tictactoe").onclick = () => show("ttt-menu");
document.getElementById("btn-menu-chess").onclick = () => show("chess-menu");

document.getElementById("btn-ttt-bot").onclick = () => show("level");
document.getElementById("btn-ttt-pvp").onclick = () => show("pvp");

document.querySelectorAll("[data-back]").forEach(b => b.onclick = () => show("menu"));

// ==========================================
// КРЕСТИКИ-НОЛИКИ (Логика)
// ==========================================
document.querySelectorAll(".level").forEach(btn => {
  btn.onclick = async () => {
    try {
      const level = Number(btn.dataset.level);
      const data = await api("/api/game/bot", "POST", { level });
      state.mode = "bot"; state.mySymbol = "X";
      state.game = data;
      setSparks(data.sparks);
      show("game-ttt");
      renderBoardTTT();
      updateStatusTTT();
    } catch(e) { tg.showAlert(e.message); }
  };
});

function renderBoardTTT() {
  const boardEl = document.getElementById("board-ttt");
  boardEl.innerHTML = "";
  const g = state.game;
  const board = g ? g.board : "_________";
  
  for (let i = 0; i < 9; i++) {
    const cell = document.createElement("div");
    cell.className = "cell";
    const ch = board[i];
    if (ch === "X") { cell.classList.add("x"); cell.textContent = "✕"; }
    if (ch === "O") { cell.classList.add("o"); cell.textContent = "◯"; }
    
    const myTurn = g && g.status === "playing" && g.turn === state.mySymbol;
    if (!myTurn || ch !== "_") cell.classList.add("disabled");
    else cell.onclick = () => onCellTTT(i);
    boardEl.appendChild(cell);
  }
}

async function onCellTTT(i) {
  const g = state.game;
  if (!g || g.status !== "playing" || g.turn !== state.mySymbol) return;
  const path = state.mode === "bot" ? "/api/game/move" : "/api/game/pvp/move";
  
  const statusEl = document.getElementById("game-status-ttt");
  if (state.mode === "bot") statusEl.textContent = "Бот думает…";
  
  try {
    const data = await api(path, "POST", { game_id: g.game_id, index: i });
    state.game = data;
    setSparks(data.sparks);
    renderBoardTTT();
    updateStatusTTT();
    if (data.status === "finished") clearPoll();
  } catch (e) { 
    statusEl.textContent = "Ошибка хода"; 
  }
}

function updateStatusTTT() {
  const g = state.game;
  const el = document.getElementById("game-status-ttt");
  if (g.status === "finished") {
    el.textContent = g.winner === "draw" ? "🤝 Ничья" : (g.winner === state.mySymbol ? "🎉 Победа!" : "😔 Поражение");
  } else {
    el.textContent = g.turn === state.mySymbol ? "Ваш ход" : "Ход соперника…";
  }
}

document.getElementById("btn-create-room").onclick = async () => {
  const data = await api("/api/game/pvp/create", "POST");
  document.getElementById("room-code").textContent = data.room_code;
  state.mode = "pvp"; state.mySymbol = "X";
  state.game = { ...data, board: "_________", turn: "X", status: "waiting", winner: null };
  startWait(data.game_id, data.expires_in);
  show("wait");
};

document.getElementById("btn-join-room").onclick = async () => {
  const code = document.getElementById("room-input").value.trim().toUpperCase();
  if (code.length < 4) return tg.showAlert("Введи код комнаты");
  
  try {
    const data = await api("/api/game/pvp/join", "POST", { room_code: code });
    state.mode = "pvp"; state.mySymbol = "O";
    const fullState = await api(`/api/game/pvp/${data.game_id}`);
    state.game = fullState;
    setSparks(fullState.sparks);
    show("game-ttt");
    renderBoardTTT();
    updateStatusTTT();
    startPoll();
  } catch (e) { tg.showAlert("Ошибка: " + e.message); }
};

// ==========================================
// ШАХМАТЫ (Логика)
// ==========================================
document.getElementById("btn-chess-create").onclick = async () => {
  try {
    const data = await api("/api/game/chess/create", "POST");
    document.getElementById("room-code").textContent = data.room_code;
    state.mode = "chess"; state.mySymbol = "X";
    state.game = { ...data, status: "waiting" };
    startWait(data.game_id, data.expires_in, true);
    show("wait");
  } catch(e) { tg.showAlert(e.message); }
};

document.getElementById("btn-chess-join").onclick = async () => {
  const code = document.getElementById("chess-input").value.trim().toUpperCase();
  if (code.length < 4) return tg.showAlert("Введи код комнаты");
  
  try {
    const data = await api("/api/game/chess/join", "POST", { room_code: code });
    state.mode = "chess"; state.mySymbol = "O";
    const fullState = await api(`/api/game/pvp/${data.game_id}`);
    state.game = fullState;
    setSparks(fullState.sparks);
    show("game-chess");
    renderBoardChess();
    updateStatusChess();
    startPoll(true);
  } catch (e) { tg.showAlert("Ошибка: " + e.message); }
};

function renderBoardChess() {
  const boardEl = document.getElementById("board-chess");
  boardEl.innerHTML = "";
  const g = state.game;
  if (!g || !g.board) return;

  const fenParts = g.board.split(" ");
  const rows = fenParts[0].split("/");
  
  const unicodePieces = {
    'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟',
    'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙'
  };

  const cols = ['a','b','c','d','e','f','g','h'];

  for (let r = 0; r < 8; r++) {
    let colIndex = 0;
    const rowStr = rows[r];
    for (let c = 0; c < rowStr.length; c++) {
      const char = rowStr[c];
      if (isNaN(char)) {
        const square = cols[colIndex] + (8 - r);
        createChessCell(boardEl, square, unicodePieces[char], (r + colIndex) % 2 !== 0);
        colIndex++;
      } else {
        for (let i = 0; i < parseInt(char); i++) {
          const square = cols[colIndex] + (8 - r);
          createChessCell(boardEl, square, "", (r + colIndex) % 2 !== 0);
          colIndex++;
        }
      }
    }
  }
}

function createChessCell(container, square, pieceSymbol, isDark) {
  const cell = document.createElement("div");
  cell.className = `chess-cell ${isDark ? 'dark' : 'light'}`;
  cell.dataset.square = square;
  cell.textContent = pieceSymbol;
  
  if (state.chessSelectedSquare === square) cell.classList.add("selected");
  if (state.chessAvailableMoves.includes(square)) cell.classList.add("available");

  cell.onclick = () => onChessCellClick(square);
  container.appendChild(cell);
}

async function onChessCellClick(square) {
  const g = state.game;
  if (!g || g.status !== "playing" || g.turn !== state.mySymbol) return;

  if (state.chessAvailableMoves.includes(square)) {
    try {
      const data = await api("/api/game/chess/move", "POST", { game_id: g.game_id, from_square: state.chessSelectedSquare, to_square: square });
      state.game = data;
      setSparks(data.sparks);
      state.chessSelectedSquare = null;
      state.chessAvailableMoves = [];
      renderBoardChess();
      updateStatusChess();
      if (data.status === "finished") clearPoll();
    } catch(e) { tg.showAlert(e.message); }
    return;
  }

  try {
    const moves = await api("/api/game/chess/moves", "POST", { game_id: g.game_id, from_square: square });
    if (moves && moves.length > 0) {
      state.chessSelectedSquare = square;
      state.chessAvailableMoves = moves;
    } else {
      state.chessSelectedSquare = null;
      state.chessAvailableMoves = [];
    }
    renderBoardChess();
  } catch(e) { console.error(e); }
}

function updateStatusChess() {
  const g = state.game;
  const el = document.getElementById("game-status-chess");
  if (g.status === "finished") {
    el.textContent = g.winner === "draw" ? "🤝 Ничья" : (g.winner === state.mySymbol ? "🏆 Мат! Победа!" : "😔 Мат. Поражение");
  } else {
    el.textContent = g.turn === state.mySymbol ? "Ваш ход" : "Ход соперника…";
  }
}

// ==========================================
// ОБЩАЯ ЛОГИКА (Ожидание и Опрос)
// ==========================================
function startWait(gameId, expiresIn, isChess = false) {
  let left = expiresIn;
  const tEl = document.getElementById("wait-timer");
  
  state.waitTimer = setInterval(async () => {
    left--;
    const m = Math.floor(left / 60), s = left % 60;
    tEl.textContent = `Ожидание: ${m}:${String(s).padStart(2,"0")}`;
    
    if (left <= 0) { clearInterval(state.waitTimer); show("menu"); return; }
    
    try {
      const g = await api(`/api/game/pvp/${gameId}`);
      if (g.status === "playing") {
        clearInterval(state.waitTimer);
        state.game = g;
        setSparks(g.sparks);
        if (isChess) {
            show("game-chess"); renderBoardChess(); updateStatusChess(); startPoll(true);
        } else {
            show("game-ttt"); renderBoardTTT(); updateStatusTTT(); startPoll(false);
        }
      }
    } catch (_) {}
  }, 1000);
}

function startPoll(isChess = false) {
  clearPoll();
  state.pollTimer = setInterval(async () => {
    if (!state.game || !state.game.game_id) return;
    try {
      const g = await api(`/api/game/pvp/${state.game.game_id}`);
      const changed = JSON.stringify(g) !== JSON.stringify(state.game);
      state.game = g;
      setSparks(g.sparks);
      if (changed) {
        if (isChess) { renderBoardChess(); updateStatusChess(); }
        else { renderBoardTTT(); updateStatusTTT(); }
      }
      if (g.status === "finished") clearPoll();
    } catch (_) {}
  }, 2000);
}

function clearPoll() { clearInterval(state.pollTimer); state.pollTimer = null; }

document.getElementById("btn-cancel-wait").onclick = () => { clearInterval(state.waitTimer); show("menu"); };
document.getElementById("btn-exit-ttt").onclick = () => { clearPoll(); state.game = null; show("menu"); };
document.getElementById("btn-exit-chess").onclick = () => { clearPoll(); state.game = null; show("menu"); };

init();
