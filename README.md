# 📘 Class Project - Knowledge-graph

## **Course Knowledge Graph Generator (PNG → JSON → MongoDB → Neo4j)**

This repository contains two core automation scripts used to build a complete **course knowledge graph** for the CSC3331 Big Data Environment course.  
The workflow converts **course images → structured JSON → MongoDB documents → Neo4j graph nodes** with prerequisite relationships.

---

# 🚀 Project Overview

This project automates the entire pipeline required in **Part 2 & Part 3** of the assignment:

1. **Extract course information from PNG images**
2. **Generate strict structured JSON files automatically**
3. **Store JSON into MongoDB**
4. **Migrate MongoDB data into Neo4j**
5. **Build a complete knowledge graph**

---

# 🗂️ Repository Structure

├── PNJtoJSON.py # OCR + Gemini script (PNG → JSON)

├── MongoDBToNeo4j.py # Migration script (MongoDB → Neo4j)

├── data_set/ # Folder containing PNG course images

├── json_output/ # Folder where JSON files are generated

└── README.md

---

# 🧠 1. PNG → JSON Generator (`PNJtoJSON.py`)

### 📌 Purpose

Automatically converts every course PNG screenshot into a **clean, validated JSON file** using:

- OCR  
- Gemini Vision model  
- Structured JSON formatting  

---

## 🔧 How It Works

1. Loads PNG images from the dataset  
2. Uses OCR + Gemini vision to extract:
   - Course Code  
   - Course Title  
   - Credits  
   - Description  
   - Discipline  
   - Pre/Corequisites  
3. Validates generated JSON  
4. Saves a JSON file next to each PNG  
5. Tracks:
   - corrupted images  
   - empty JSON responses  
   - processing errors  

---

## 📁 Output Example

```json
{
  "course_code": "CSC3321",
  "title": "Database Systems",
  "credits": 3,
  "discipline": "Computer Science",
  "description": "Introduction to relational models...",
  "prerequisites": ["CSC2301"]
}
```

## 📝 Validation Included

At the end of execution, the script prints:

Total PNGs processed

A list of PNGs that generated empty or invalid JSON

A list of files that failed or need manual fixing

This ensures correctness before loading data into MongoDB.


# 🗄️ 2. MongoDB → Neo4j Migration (MongoDBToNeo4j.py)
📌 Purpose

Reads all validated course documents from MongoDB and builds a fully structured Neo4j knowledge graph.

## 🔧 How It Works
MongoDB Phase

Connects to MongoDB Atlas or local instance

Reads all stored course documents

Normalizes prerequisite lists

Ensures required fields exist on each course

Neo4j Phase

For each course:

### Creates a node  

```cypher
(:Course {
  code: "CSC3321",
  title: "Database Systems",
  credits: 3,
  discipline: "Computer Science",
  description: "..."
})
```

### Creates prerequisite relationships

```cypher
(:Course {code:"CSC2301"})-[:PREREQUISITE]->(:Course {code:"CSC3321"})
```

## 📊 Output in Neo4j

The resulting graph allows exploration of:

All course nodes

Discipline groups

Full prerequisite paths

Minor and specialization structures

Example questions you can answer:

Which math courses are required for CS?

What is the prerequisite chain for AI courses?

Which courses depend on MTH1303?

What are all art- or humanities-related electives?

# ▶️ How to Run the Scripts

1️⃣ Generate JSON Files

python PNJtoJSON.py

2️⃣ Insert JSON into MongoDB

(Use your insertion script or MongoDB import command)

3️⃣ Migrate MongoDB → Neo4j

python MongoDBToNeo4j.py

## 🔧 Installation

Install Required Python Packages

pip install pillow pymongo neo4j google-generativeai

## 📌 Requirements

Python 3.10+

OpenAI Gemini API key

MongoDB Atlas or local MongoDB

# ⭐ Contributors

Haytam Yazid
