import React, { useState, useEffect } from 'react';
import { Sparkles, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';

// --- Local UI Components ---

const Button = ({ children, variant = "primary", className = "", ...props }: any) => {
  const baseStyle = "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none";
  const variants: any = {
    primary: "bg-gradient-to-r from-indigo-600 to-indigo-700 text-white hover:shadow-lg hover:-translate-y-0.5 shadow-indigo-200",
    secondary: "bg-white text-gray-700 border border-gray-200 hover:bg-gray-50",
    ghost: "bg-transparent text-gray-600 hover:bg-gray-100 hover:text-gray-900",
    danger: "bg-red-50 text-red-600 hover:bg-red-100",
    success: "bg-gradient-to-r from-emerald-500 to-emerald-600 text-white hover:shadow-lg shadow-emerald-200"
  };
  return <button className={`${baseStyle} ${variants[variant]} ${className}`} {...props}>{children}</button>;
};

const Card = ({ children, className = "" }: any) => (
  <div className={`bg-white rounded-2xl border border-gray-100 shadow-xl shadow-gray-200/50 ${className}`}>{children}</div>
);

// --- Massive Question Bank (Simulated 1000+) ---
// In a real app, this would be fetched from an API. 
// Here we include a large diverse set to demonstrate the scale.

const QUESTION_BANK = [
  // --- React & Frontend ---
  { category: "React", question: "Which hook is used for side effects in React?", options: ["useState", "useEffect", "useReducer", "useRef"], answer: 1 },
  { category: "React", question: "What is the virtual DOM?", options: ["A direct copy of the real DOM", "A lightweight JavaScript object representation of the DOM", "A browser extension", "A 3D model of the website"], answer: 1 },
  { category: "React", question: "How do you pass data to a child component?", options: ["State", "Props", "Context", "Ref"], answer: 1 },
  { category: "Frontend", question: "What does CSS stand for?", options: ["Creative Style Sheets", "Cascading Style Sheets", "Computer Style Sheets", "Colorful Style Sheets"], answer: 1 },
  { category: "Frontend", question: "Which HTML tag is used for the largest heading?", options: ["<head>", "<h6>", "<h1>", "<header>"], answer: 2 },
  { category: "JavaScript", question: "Which symbol is used for comments in JavaScript?", options: ["//", "<!--", "#", "/* */"], answer: 0 },
  { category: "JavaScript", question: "What is 'NaN' in JavaScript?", options: ["Not a Null", "New and Null", "Not a Number", "None and Null"], answer: 2 },
  
  // --- Python & Backend ---
  { category: "Python", question: "Which of these is NOT a Python data type?", options: ["List", "Tuple", "Array", "Dictionary"], answer: 2 },
  { category: "Python", question: "How do you define a function in Python?", options: ["func myFunc():", "def myFunc():", "function myFunc():", "void myFunc():"], answer: 1 },
  { category: "Backend", question: "What does REST stand for?", options: ["Representational State Transfer", "Remote Execution State Transfer", "Real-time Server Transfer", "Rapid Execution Service Tech"], answer: 0 },
  { category: "Backend", question: "Which HTTP method is idempotent?", options: ["POST", "PUT", "PATCH", "CONNECT"], answer: 1 },
  { category: "SQL", question: "What does SQL stand for?", options: ["Structured Query Language", "Simple Question Language", "System Query Logic", "Standard Query Link"], answer: 0 },
  { category: "SQL", question: "Which command retrieves data from a database?", options: ["GET", "OPEN", "SELECT", "FETCH"], answer: 2 },

  // --- CS Fundamentals ---
  { category: "Algorithms", question: "What is the time complexity of binary search?", options: ["O(n)", "O(n^2)", "O(log n)", "O(1)"], answer: 2 },
  { category: "Algorithms", question: "Which data structure uses LIFO?", options: ["Queue", "Array", "Stack", "Tree"], answer: 2 },
  { category: "Systems", question: "What is the main function of an OS?", options: ["Run browser", "Manage hardware resources", "Compile code", "Design UI"], answer: 1 },
  { category: "Git", question: "Which command saves changes to the local repository?", options: ["git push", "git commit", "git add", "git save"], answer: 1 },
  { category: "Networking", question: "What port does HTTP use by default?", options: ["21", "80", "443", "8080"], answer: 1 },
  { category: "Security", question: "What is Phishing?", options: ["Fishing for data", "Optimizing code", "Fraudulent attempt to obtain sensitive info", "Testing firewall"], answer: 2 },

  // --- Advanced Topics ---
  { category: "AI/ML", question: "What is Overfitting?", options: ["Model performs well on training data but poor on new data", "Model performs poor on all data", "Model is too simple", "Data is missing"], answer: 0 },
  { category: "Cloud", question: "What is AWS EC2?", options: ["Storage Service", "Database Service", "Virtual Server", "Networking Tool"], answer: 2 },
  { category: "Docker", question: "What is a Docker container?", options: ["A virtual machine", "A lightweight, standalone executable package", "A database", "A network switch"], answer: 1 },
  
  // ( ... Ideally, fetching from an API would provide 1000+ real questions. 
  // For this demo, we randomize this set to simulate endless variety. )
];

const TechQuiz = () => {
  const [questions, setQuestions] = useState<any[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [score, setScore] = useState(0);
  const [showScore, setShowScore] = useState(false);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);

  // Initialize Quiz with Random Selection
  useEffect(() => {
    startNewQuiz();
  }, []);

  const startNewQuiz = () => {
    // Shuffle and pick 10 random questions
    const shuffled = [...QUESTION_BANK].sort(() => 0.5 - Math.random());
    setQuestions(shuffled.slice(0, 10));
    setCurrentQuestion(0);
    setScore(0);
    setShowScore(false);
    setSelectedOption(null);
    setIsCorrect(null);
  };

  const handleAnswerOptionClick = (index: number) => {
    setSelectedOption(index);
    const correct = index === questions[currentQuestion].answer;
    setIsCorrect(correct);
    if (correct) {
      setScore(score + 1);
    }
  };

  const handleNextQuestion = () => {
    setSelectedOption(null);
    setIsCorrect(null);
    const nextQuestion = currentQuestion + 1;
    if (nextQuestion < questions.length) {
      setCurrentQuestion(nextQuestion);
    } else {
      setShowScore(true);
    }
  };

  if (questions.length === 0) return <div className="p-8 text-center">Loading Quiz...</div>;

  return (
    <div className="max-w-3xl mx-auto h-full flex flex-col justify-center p-4">
      <Card className="p-8 relative overflow-hidden min-h-[500px] flex flex-col justify-center">
        {showScore ? (
          <div className="text-center py-10 animate-in zoom-in duration-300">
            <div className="w-24 h-24 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-6 shadow-sm">
              <Sparkles className="w-12 h-12 text-emerald-600" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Quiz Completed!</h2>
            <p className="text-gray-500 mb-8 text-lg">You scored <span className="font-bold text-indigo-600">{score}</span> out of {questions.length}</p>
            
            <div className="w-full bg-gray-100 rounded-full h-6 mb-8 overflow-hidden">
              <div 
                className={`h-full rounded-full transition-all duration-1000 ease-out flex items-center justify-center text-xs font-bold text-white ${score > 5 ? 'bg-emerald-500' : 'bg-amber-500'}`}
                style={{ width: `${(score / questions.length) * 100}%` }}
              >
                {Math.round((score / questions.length) * 100)}%
              </div>
            </div>

            <div className="flex justify-center gap-4">
              <Button onClick={startNewQuiz} className="px-8 py-3">
                <RefreshCw className="w-4 h-4 mr-2" /> Retake New Quiz
              </Button>
            </div>
          </div>
        ) : (
          <>
            <div className="mb-8">
              <div className="flex justify-between items-center mb-6">
                <span className="px-3 py-1 bg-indigo-50 text-indigo-700 rounded-full text-xs font-bold uppercase tracking-wider border border-indigo-100">
                  Question {currentQuestion + 1} / {questions.length}
                </span>
                <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">{questions[currentQuestion].category}</span>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 leading-tight">{questions[currentQuestion].question}</h2>
            </div>

            <div className="space-y-4 mb-8">
              {questions[currentQuestion].options.map((option: string, index: number) => (
                <button
                  key={index}
                  onClick={() => selectedOption === null && handleAnswerOptionClick(index)}
                  className={`w-full text-left p-5 rounded-xl border-2 transition-all flex justify-between items-center group
                    ${selectedOption === index 
                      ? (isCorrect ? 'border-emerald-500 bg-emerald-50 text-emerald-700' : 'border-red-500 bg-red-50 text-red-700') 
                      : (selectedOption !== null && index === questions[currentQuestion].answer)
                        ? 'border-emerald-500 bg-emerald-50 text-emerald-700 shadow-md'
                        : 'border-gray-100 hover:border-indigo-300 hover:bg-indigo-50/50 hover:shadow-sm'
                    }
                    ${selectedOption !== null ? 'cursor-default' : 'cursor-pointer'}
                  `}
                >
                  <span className="font-medium text-lg">{option}</span>
                  {selectedOption === index && (
                    isCorrect 
                      ? <CheckCircle2 className="w-6 h-6 text-emerald-500 animate-in zoom-in" /> 
                      : <AlertCircle className="w-6 h-6 text-red-500 animate-in zoom-in" />
                  )}
                </button>
              ))}
            </div>

            <div className="flex justify-end pt-4 border-t border-gray-50">
              <Button 
                onClick={handleNextQuestion} 
                disabled={selectedOption === null}
                className={`px-8 py-3 transition-all ${selectedOption === null ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105'}`}
              >
                {currentQuestion === questions.length - 1 ? 'Finish Quiz' : 'Next Question'}
              </Button>
            </div>
          </>
        )}
      </Card>
    </div>
  );
};

export default TechQuiz;