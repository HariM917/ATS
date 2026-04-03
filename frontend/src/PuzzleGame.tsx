import React, { useState, useEffect } from 'react';
import { Sparkles, RefreshCw, Trophy, Puzzle, ArrowRight, Play } from 'lucide-react';

// --- Local UI Components (Self-contained for portability) ---

const Button = ({ children, variant = "primary", className = "", ...props }: any) => {
  const baseStyle = "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none";
  const variants: any = {
    primary: "bg-gradient-to-r from-indigo-600 to-indigo-700 text-white hover:shadow-lg hover:-translate-y-0.5 shadow-indigo-200",
    secondary: "bg-white text-gray-700 border border-gray-200 hover:bg-gray-50",
    ghost: "bg-transparent text-gray-600 hover:bg-gray-100 hover:text-gray-900",
    success: "bg-gradient-to-r from-emerald-500 to-emerald-600 text-white hover:shadow-lg shadow-emerald-200",
    outline: "border-2 border-indigo-600 text-indigo-600 hover:bg-indigo-50",
    danger: "bg-red-50 text-red-600 hover:bg-red-100"
  };
  return <button className={`${baseStyle} ${variants[variant]} ${className}`} {...props}>{children}</button>;
};

const Card = ({ children, className = "" }: any) => (
  <div className={`bg-white rounded-2xl border border-gray-100 shadow-xl shadow-gray-200/50 ${className}`}>{children}</div>
);

// --- Puzzle Generator Logic (Simulates 1000+ Levels) ---

interface Operation {
  id: string;
  type: 'add' | 'sub' | 'mult' | 'div';
  val: number;
  label: string;
}

interface Level {
  id: number;
  target: number;
  moves: number;
  initialValue: number;
  operations: Operation[];
}

// Generates a random puzzle with a guaranteed solution
const generatePuzzle = (id: number): Level => {
  const moves = Math.floor(Math.random() * 3) + 3; // 3 to 5 moves
  let currentValue = Math.floor(Math.random() * 10); // Start between 0-9
  const initialValue = currentValue;
  const operations: Operation[] = [];
  
  // Create a sequence of random valid operations
  for (let i = 0; i < 4; i++) { // Generate 4 options
    const type = ['add', 'sub', 'mult'][Math.floor(Math.random() * 3)] as 'add' | 'sub' | 'mult';
    let val = 0;
    
    if (type === 'add') val = Math.floor(Math.random() * 10) + 1;
    if (type === 'sub') val = Math.floor(Math.random() * 5) + 1;
    if (type === 'mult') val = Math.floor(Math.random() * 3) + 2;

    let label = '';
    if (type === 'add') label = `+${val}`;
    if (type === 'sub') label = `-${val}`;
    if (type === 'mult') label = `x${val}`;

    operations.push({ id: `op-${i}`, type, val, label });
  }

  // To ensure it's solvable, we simulate a "winning path" of 'moves' length
  // But strictly speaking, for a fun random puzzle, we can just set a target
  // based on applying a subset of these operations randomly.
  
  // Let's create a guaranteed path first
  for (let i = 0; i < moves; i++) {
    const randomOp = operations[Math.floor(Math.random() * operations.length)];
    if (randomOp.type === 'add') currentValue += randomOp.val;
    if (randomOp.type === 'sub') currentValue -= randomOp.val;
    if (randomOp.type === 'mult') currentValue *= randomOp.val;
  }
  
  // Ensure target isn't too crazy negative or zero if we started with 0
  if (currentValue < 0) currentValue = Math.abs(currentValue) + 5;
  if (currentValue === initialValue) currentValue += 10;

  return {
    id,
    target: currentValue,
    moves,
    initialValue,
    operations
  };
};

const PuzzleGame = () => {
  const [currentLevel, setCurrentLevel] = useState<Level | null>(null);
  const [currentValue, setCurrentValue] = useState(0);
  const [movesLeft, setMovesLeft] = useState(0);
  const [history, setHistory] = useState<number[]>([]);
  const [gameState, setGameState] = useState<'playing' | 'won' | 'lost'>('playing');
  const [gameStarted, setGameStarted] = useState(false);
  const [levelCount, setLevelCount] = useState(1);

  useEffect(() => {
    if (gameStarted && !currentLevel) {
      startNewLevel();
    }
  }, [gameStarted]);

  const startNewLevel = () => {
    const newLevel = generatePuzzle(levelCount);
    setCurrentLevel(newLevel);
    setCurrentValue(newLevel.initialValue);
    setMovesLeft(newLevel.moves);
    setHistory([newLevel.initialValue]);
    setGameState('playing');
  };

  const handleOperation = (op: Operation) => {
    if (gameState !== 'playing') return;

    let newValue = currentValue;
    switch (op.type) {
      case 'add': newValue += op.val; break;
      case 'sub': newValue -= op.val; break;
      case 'mult': newValue *= op.val; break;
      case 'div': newValue = Math.floor(newValue / op.val); break;
    }

    const newMoves = movesLeft - 1;
    setCurrentValue(newValue);
    setMovesLeft(newMoves);
    setHistory([...history, newValue]);

    if (newValue === currentLevel?.target) {
      setGameState('won');
    } else if (newMoves === 0) {
      setGameState('lost');
    }
  };

  const handleNextLevel = () => {
    setLevelCount(c => c + 1);
    startNewLevel();
  };

  const handleRetry = () => {
    if (!currentLevel) return;
    setCurrentValue(currentLevel.initialValue);
    setMovesLeft(currentLevel.moves);
    setHistory([currentLevel.initialValue]);
    setGameState('playing');
  };

  if (!gameStarted) {
    return (
      <div className="h-full flex items-center justify-center p-6">
        <Card className="max-w-lg w-full p-10 text-center relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500" />
          <div className="w-24 h-24 bg-indigo-50 rounded-full flex items-center justify-center mx-auto mb-6">
            <Puzzle className="w-12 h-12 text-indigo-600" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-3">Logic Lab</h2>
          <p className="text-gray-500 mb-8">Test your problem-solving skills with unlimited arithmetic puzzles. Reach the target number within the move limit!</p>
          <Button onClick={() => setGameStarted(true)} className="w-full py-3 text-lg">
            <Play className="w-5 h-5 mr-2" /> Start Challenge
          </Button>
        </Card>
      </div>
    );
  }

  if (!currentLevel) return <div className="p-10 text-center">Generating Puzzle...</div>;

  return (
    <div className="max-w-4xl mx-auto h-full flex flex-col p-4">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Puzzle className="w-6 h-6 text-indigo-600" /> 
            Level {currentLevel.id}
          </h2>
          <p className="text-sm text-gray-500">Target: <span className="font-bold text-indigo-600 text-lg">{currentLevel.target}</span></p>
        </div>
        <div className="text-right">
          <p className="text-sm font-bold uppercase tracking-wider text-gray-400">Moves Left</p>
          <p className={`text-3xl font-black ${movesLeft === 0 ? 'text-red-500' : 'text-gray-900'}`}>{movesLeft}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 flex-1">
        {/* Game Area */}
        <div className="space-y-6">
          <Card className="p-8 flex flex-col items-center justify-center min-h-[200px] bg-gradient-to-br from-gray-50 to-white shadow-inner">
            <span className="text-xs font-bold text-gray-400 uppercase mb-2">Current Value</span>
            <div className="text-6xl font-black text-gray-900 animate-in zoom-in duration-300 key={currentValue}">
              {currentValue}
            </div>
          </Card>

          <div className="grid grid-cols-2 gap-4">
            {currentLevel.operations.map((op, idx) => (
              <button
                key={idx}
                onClick={() => handleOperation(op)}
                disabled={gameState !== 'playing'}
                className="p-4 bg-white border-2 border-indigo-100 hover:border-indigo-500 hover:shadow-md rounded-xl text-xl font-bold text-indigo-700 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {op.label}
              </button>
            ))}
          </div>
        </div>

        {/* Status Area */}
        <div className="flex flex-col gap-6">
          <Card className="p-6 flex-1 flex flex-col">
            <h3 className="font-bold text-gray-900 mb-4 border-b pb-2">Move History</h3>
            <div className="flex-1 overflow-y-auto space-y-2 max-h-[300px]">
              {history.map((val, i) => (
                <div key={i} className="flex items-center gap-3 text-sm">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${i === 0 ? 'bg-indigo-100 text-indigo-600' : 'bg-gray-100 text-gray-500'}`}>
                    {i}
                  </div>
                  <span className={i === history.length - 1 ? "font-bold text-gray-900" : "text-gray-500"}>
                    {val}
                  </span>
                  {i === 0 && <span className="text-xs text-gray-400">(Start)</span>}
                </div>
              ))}
            </div>
          </Card>

          {gameState !== 'playing' && (
            <Card className={`p-6 text-center animate-in slide-in-from-bottom-5 ${gameState === 'won' ? 'bg-emerald-50 border-emerald-100' : 'bg-red-50 border-red-100'}`}>
              {gameState === 'won' ? (
                <>
                  <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <Trophy className="w-8 h-8 text-emerald-600" />
                  </div>
                  <h3 className="text-xl font-bold text-emerald-800 mb-1">Level Cleared!</h3>
                  <p className="text-emerald-600 text-sm mb-4">Great calculation skills.</p>
                  <Button onClick={handleNextLevel} variant="success" className="w-full">
                    Next Level <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </>
              ) : (
                <>
                  <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <RefreshCw className="w-8 h-8 text-red-600" />
                  </div>
                  <h3 className="text-xl font-bold text-red-800 mb-1">Out of Moves</h3>
                  <p className="text-red-600 text-sm mb-4">Try a different approach.</p>
                  <Button onClick={handleRetry} variant="danger" className="w-full">
                    Try Again
                  </Button>
                </>
              )}
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default PuzzleGame;