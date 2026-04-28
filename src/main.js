import {
  GRID_SIZE,
  createInitialState,
  queueDirection,
  stepGame,
} from "./snakeLogic.js";

const TICK_MS = 140;
const STORAGE_KEY = "snake-best-score";

const board = document.querySelector("#board");
const scoreValue = document.querySelector("#score");
const bestScoreValue = document.querySelector("#best-score");
const gameStateValue = document.querySelector("#game-state");
const overlay = document.querySelector("#overlay");
const overlayTitle = document.querySelector("#overlay-title");
const overlayCopy = document.querySelector("#overlay-copy");
const pauseButton = document.querySelector("#pause-button");
const restartButton = document.querySelector("#restart-button");

let state = createInitialState();
let tickHandle = null;
let bestScore = readBestScore();

buildBoard(board, GRID_SIZE);
render();
board.focus();

document.addEventListener("keydown", handleKeydown);
pauseButton.addEventListener("click", togglePause);
restartButton.addEventListener("click", restartGame);
board.addEventListener("click", () => board.focus());

function buildBoard(container, gridSize) {
  container.style.gridTemplateColumns = `repeat(${gridSize}, 1fr)`;
  const cells = [];

  for (let index = 0; index < gridSize * gridSize; index += 1) {
    const cell = document.createElement("div");
    cell.className = "cell";
    cells.push(cell);
    container.append(cell);
  }

  return cells;
}

function handleKeydown(event) {
  const keyDirection = mapKeyToDirection(event.key);

  if (event.key === " ") {
    event.preventDefault();
    togglePause();
    return;
  }

  if (event.key === "Enter" && state.status === "gameOver") {
    restartGame();
    return;
  }

  if (!keyDirection) {
    return;
  }

  event.preventDefault();

  if (state.status === "idle") {
    state = {
      ...state,
      status: "running",
      pendingDirection: queueDirection(state, keyDirection),
    };
    startLoop();
    render();
    return;
  }

  if (state.status === "paused") {
    state = {
      ...state,
      pendingDirection: queueDirection(state, keyDirection),
      status: "running",
    };
    startLoop();
    render();
    return;
  }

  if (state.status === "running") {
    state = {
      ...state,
      pendingDirection: queueDirection(state, keyDirection),
    };
  }
}

function togglePause() {
  if (state.status === "idle" || state.status === "gameOver") {
    return;
  }

  if (state.status === "paused") {
    state = { ...state, status: "running" };
    startLoop();
  } else {
    state = { ...state, status: "paused" };
    stopLoop();
  }

  render();
}

function restartGame() {
  stopLoop();
  state = createInitialState();
  render();
  board.focus();
}

function startLoop() {
  stopLoop();
  tickHandle = window.setInterval(() => {
    const randomIndex = Math.floor(Math.random() * (GRID_SIZE * GRID_SIZE));
    state = stepGame(state, randomIndex);
    updateBestScore();

    if (state.status === "gameOver") {
      stopLoop();
    }

    render();
  }, TICK_MS);
}

function stopLoop() {
  if (tickHandle !== null) {
    window.clearInterval(tickHandle);
    tickHandle = null;
  }
}

function render() {
  const cells = board.children;

  for (const cell of cells) {
    cell.className = "cell";
  }

  state.snake.forEach((segment, index) => {
    const cell = cells[toIndex(segment, state.gridSize)];
    if (!cell) {
      return;
    }
    cell.classList.add("snake");
    if (index === 0) {
      cell.classList.add("head");
    }
  });

  if (state.food) {
    const foodCell = cells[toIndex(state.food, state.gridSize)];
    foodCell?.classList.add("food");
  }

  scoreValue.textContent = String(state.score);
  bestScoreValue.textContent = String(bestScore);
  gameStateValue.textContent = formatStatus(state.status);
  pauseButton.textContent = state.status === "paused" ? "Resume" : "Pause";

  renderOverlay();
}

function renderOverlay() {
  if (state.status === "running") {
    overlay.classList.add("hidden");
    return;
  }

  overlay.classList.remove("hidden");

  if (state.status === "idle") {
    overlayTitle.textContent = "Press any arrow key to start";
    overlayCopy.textContent = "Use arrow keys or WASD. Press Space to pause.";
    return;
  }

  if (state.status === "paused") {
    overlayTitle.textContent = "Paused";
    overlayCopy.textContent = "Press Space or Resume to continue.";
    return;
  }

  overlayTitle.textContent = "Game over";
  overlayCopy.textContent = "Press Restart or Enter to try again.";
}

function updateBestScore() {
  if (state.score <= bestScore) {
    return;
  }

  bestScore = state.score;
  window.localStorage.setItem(STORAGE_KEY, String(bestScore));
}

function readBestScore() {
  const value = Number(window.localStorage.getItem(STORAGE_KEY));
  return Number.isFinite(value) ? value : 0;
}

function toIndex(position, gridSize) {
  return position.y * gridSize + position.x;
}

function formatStatus(status) {
  if (status === "gameOver") {
    return "Game Over";
  }

  return status.charAt(0).toUpperCase() + status.slice(1);
}

function mapKeyToDirection(key) {
  const normalized = key.toLowerCase();
  const keyMap = {
    arrowup: "UP",
    w: "UP",
    arrowdown: "DOWN",
    s: "DOWN",
    arrowleft: "LEFT",
    a: "LEFT",
    arrowright: "RIGHT",
    d: "RIGHT",
  };

  return keyMap[normalized] ?? null;
}
