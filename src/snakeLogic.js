export const GRID_SIZE = 16;
export const INITIAL_DIRECTION = "RIGHT";

const DIRECTION_VECTORS = {
  UP: { x: 0, y: -1 },
  DOWN: { x: 0, y: 1 },
  LEFT: { x: -1, y: 0 },
  RIGHT: { x: 1, y: 0 },
};

const OPPOSITES = {
  UP: "DOWN",
  DOWN: "UP",
  LEFT: "RIGHT",
  RIGHT: "LEFT",
};

export function createInitialState(gridSize = GRID_SIZE) {
  const start = Math.floor(gridSize / 2);
  const snake = [
    { x: start, y: start },
    { x: start - 1, y: start },
    { x: start - 2, y: start },
  ];

  return {
    gridSize,
    snake,
    direction: INITIAL_DIRECTION,
    pendingDirection: INITIAL_DIRECTION,
    food: findFoodPosition(gridSize, snake),
    score: 0,
    status: "idle",
  };
}

export function queueDirection(state, nextDirection) {
  if (!DIRECTION_VECTORS[nextDirection]) {
    return state.pendingDirection;
  }

  if (state.snake.length > 1 && OPPOSITES[state.direction] === nextDirection) {
    return state.pendingDirection;
  }

  return nextDirection;
}

export function stepGame(state, randomIndex = 0) {
  if (state.status === "gameOver") {
    return state;
  }

  const direction = state.pendingDirection;
  const vector = DIRECTION_VECTORS[direction];
  const head = state.snake[0];
  const nextHead = { x: head.x + vector.x, y: head.y + vector.y };
  const grows = positionsEqual(nextHead, state.food);
  const nextSnake = grows ? [nextHead, ...state.snake] : [nextHead, ...state.snake.slice(0, -1)];

  if (isOutOfBounds(nextHead, state.gridSize) || hitsSelf(nextSnake)) {
    return {
      ...state,
      direction,
      pendingDirection: direction,
      status: "gameOver",
    };
  }

  const nextFood = grows
    ? findFoodPosition(state.gridSize, nextSnake, randomIndex)
    : state.food;

  return {
    ...state,
    snake: nextSnake,
    direction,
    pendingDirection: direction,
    food: nextFood,
    score: grows ? state.score + 1 : state.score,
    status: "running",
  };
}

export function findFoodPosition(gridSize, snake, randomIndex = 0) {
  const occupied = new Set(snake.map((segment) => `${segment.x},${segment.y}`));
  const openCells = [];

  for (let y = 0; y < gridSize; y += 1) {
    for (let x = 0; x < gridSize; x += 1) {
      const key = `${x},${y}`;
      if (!occupied.has(key)) {
        openCells.push({ x, y });
      }
    }
  }

  if (openCells.length === 0) {
    return null;
  }

  return openCells[randomIndex % openCells.length];
}

export function positionsEqual(a, b) {
  return Boolean(a && b) && a.x === b.x && a.y === b.y;
}

function isOutOfBounds(position, gridSize) {
  return (
    position.x < 0 ||
    position.y < 0 ||
    position.x >= gridSize ||
    position.y >= gridSize
  );
}

function hitsSelf(snake) {
  const [head, ...body] = snake;
  return body.some((segment) => positionsEqual(segment, head));
}
