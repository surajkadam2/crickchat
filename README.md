# 🏏 CrickChat

**CrickChat** is an AI-powered CLI tool that lets you **chat with cricket statistics using natural language**.

Ask questions like a cricket analyst — get **SQL-powered insights, clean tables, and human-readable explanations** instantly.

---

## 🚀 What CrickChat Does

- 💬 Converts natural language → SQL queries  
- 🗄️ Queries your **SQL Server cricket database**  
- 📊 Displays results in beautiful CLI tables  
- 🧠 Understands cricket logic (centuries, averages, strike rate, etc.)  
- 🗣️ Explains results in plain English  
- 🔁 Supports follow-up questions with memory  

---

## 🧪 Demo

### 🟢 Example 1: Sachin Tendulkar Centuries

**You:** How many centuries does Sachin Tendulkar have in ODIs?

**Output:**
                   ╷
  PlayerName       │ Centuries  
 ══════════════════╪═══════════ 
  Sachin Tendulkar │ 49
                   ╵

Rows: 1 | AI Time: 0.82s | DB Time: 0.05s

**Explanation:** Sachin Tendulkar has scored 49 centuries in ODI cricket based on available data.

---

### 🔵 Example 2: Kohli vs Rohit (T20 Comparison)

**You:**Compare Virat Kohli and Rohit Sharma in T20s

🏏 Player Comparison

Metric Virat Kohli Rohit Sharma

Runs 4008 3853
Average 52.7 31.8
Strike Rate 137.0 139.2

*(Best values highlighted in green in CLI)*

**Explanation:**
Virat Kohli has a higher batting average, while Rohit Sharma has a slightly better strike rate. Based on available data, Kohli appears more consistent while Rohit scores faster.


---

## 🧠 Tech Stack

- 🐍 Python 3.10+
- 🤖 Gemini API (LLM for SQL generation)
- 🗄️ SQL Server + SQLAlchemy
- 📊 Pandas (data loading)
- 🎨 Rich (beautiful CLI UI)
- 🔐 python-dotenv (config management)

---

## ⚙️ Installation

### ⚙️ Installation

#### 1. Clone the repo
```bash
git clone https://github.com/yourusername/crickchat.git
cd crickchat
```

#### 2. Install dependencies
```bash
pip install -r requirements.txt
```

#### 3. Setup `.env`
Create a `.env` file with:
```env
DB_SERVER=YOUR_SQL_SERVER
GEMINI_API_KEY=YOUR_API_KEY
```

#### 4. Load cricket data
```bash
python load_cricket.py
```

#### 5. Run CrickChat
```bash
python main.py
```

---

## 💡 Example Questions

### 🏏 Batting
- Who has the most centuries in Test cricket?
- Top 10 batsmen by average in ODIs
- Which player has highest strike rate in T20s?

### 🎯 Bowling
- Who took the most wickets in Test cricket?
- Best economy bowlers in T20s
- Which bowler has most 5-wicket hauls?

### 🆚 Comparisons
- Compare Virat Kohli and Rohit Sharma in ODIs
- Who is better: Babar Azam or Joe Root?
- Compare top 5 batsmen in Test cricket

### 📊 Team Insights
- Which team has highest win rate in ODIs?
- Best performing team in T20 cricket
- Show recent match results for India

### 🔀 Multi-format
- Who has most runs across all formats?
- Compare player performance in all formats
- Total centuries across ODI, Test, T20

---

## 🛡️ Safety Features
- Blocks dangerous queries (`DROP`, `DELETE`, etc.)
- Validates generated SQL
- Limits results to safe row counts
- Prevents invalid DB operations

---

## 🧠 Smart Features
- Context memory (remembers last 5 queries)
- Retry with feedback
- Edit previous question
- Explain mode (see SQL + history)
- Natural language explanations

---

## 📁 Project Structure
```
crickchat/
│
├── main.py            # CLI interface
├── prompt.py          # AI prompt + SQL generation
├── db.py              # Database connection
├── safety.py          # Input + SQL validation
├── explainer.py       # Natural language explanations
├── cards.py           # Player comparison UI
├── logger.py          # Logging system
├── config.py          # Configuration
├── load_cricket.py    # Data loader
└── tests/             # Evaluation scripts
```

---

## 🚀 Future Improvements
- 📊 Charts & visual analytics
- 🌐 Web UI (React + FastAPI)
- 🏆 Player ranking system
- 📈 Trend analysis (form, consistency)
- 🤖 Advanced cricket insights (AI analyst mode)
- 🤝 Contributing

Pull requests are welcome! Feel free to suggest features or report issues.

---

## 📜 License
MIT License

---

## 🏏 Built for Cricket Fans
CrickChat turns your database into a personal cricket analyst.

Ask. Analyze. Discover. 🚀

