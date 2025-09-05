# ----------------- update_curriculum.py -----------------
from pymongo import MongoClient
from bson import ObjectId
from config.settings import MONGODB_URI, DB_NAME

# --- MongoDB connection ---



COLLECTION_NAME = "curriculum"
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# --- Example curriculum document ---
new_curriculum = {
    "programCode": "BSBA",
    "programName": "BACHELOR OF SCIENCE IN BUSINESS ADMINISTRATION Major in Marketing Management",
    "curriculumYear": "2027-2028",
    "subjects": [
    {
      "year": 1,
      "semester": "First",
      "code": "GE 200",
      "name": "Understanding the Sell",
      "lec": 3,
      "lab": 0,
      "unit": 3,
      "preRequisites": []
    },
    {
      "year": 1,
      "semester": "First",
      "code": "GE 203",
      "name": "Life and Works of Rizal",
      "lec": 3,
      "lab": 0,
      "unit": 3,
      "preRequisites": []
    },
    {
      "year": 1,
      "semester": "First",
      "code": "GE 204",
      "name": "Gender and Society",
      "lec": 3,
      "lab": 0,
      "unit": 3,
      "preRequisites": []
    },
    {
      "year": 1,
      "semester": "First",
      "code": "GE 303",
      "name": "Philippine Popular Culture",
      "lec": 3,
      "lab": 0,
      "unit": 3,
      "preRequisites": []
    },
    {
      "year": 1,
      "semester": "First",
      "code": "BACC 1",
      "name": "Basic Microeconomics",
      "lec": 3,
      "lab": 0,
      "unit": 3,
      "preRequisites": []
    },
    {
      "year": 1,
      "semester": "First",
      "code": "PE 1",
      "name": "Physical Activities Towards Health and Fitness 1 - Movement Competency Training",
      "lec": 2,
      "lab": 0,
      "unit": 2,
      "preRequisites": []
    },
    {
      "year": 1,
      "semester": "First",
      "code": "GE 201",
      "name": "Reading in Philippine History",
      "lec": 3,
      "lab": 0,
      "unit": 3,
      "preRequisites": []
    },
    {
      "year": 1,
      "semester": "Second",
      "code": "GE 402",
      "name": "Mathematics in the Modern World",
      "lec": 3,
      "lab": 0,
      "unit": 3,
      "preRequisites": []
    },
    {
      "year": 1,
      "semester": "Second",
      "code": "GE 302",
      "name": "Ethics",
      "lec": 3,
      "lab": 0,
      "unit": 3,
      "preRequisites": []
    },

    # year 2
    {
    "year": 2,
    "semester": "First",
    "code": "GE 104",
    "name": "Purposive Communication",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": []
    },
    {
    "year": 2,
    "semester": "First",
    "code": "GE 102",
    "name": "The Contemporary World",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": []
    },
    {
    "year": 2,
    "semester": "First",
    "code": "MM 1",
    "name": "Marketing Management",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": ["Mktg 1"]
    },
    {
    "year": 2,
    "semester": "First",
    "code": "MM 2",
    "name": "Product Management",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": ["Mktg 1"]
    },
    {
    "year": 2,
    "semester": "First",
    "code": "MM3",
    "name": "International Business & Trade",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": ["Mktg 1"]
    },
    {
    "year": 2,
    "semester": "First",
    "code": "ELEC 1",
    "name": "E-Commerce & Internet Marketing",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": ["Mktg 1"]
    },
    {
    "year": 2,
    "semester": "First",
    "code": "PE 2",
    "name": "Physical Activities Towards Health and Fitness 3 - Dance",
    "lec": 2,
    "lab": 0,
    "unit": 2,
    "preRequisites": ["PE 1"]
    },
    {
    "year": 2,
    "semester": "Second",
    "code": "ACCTG 1",
    "name": "Fundamentals of Accounting 1",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": []
    },
    {
    "year": 2,
    "semester": "Second",
    "code": "Math 201",
    "name": "Business Statistics",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": ["GE 402"]
    },
    {
    "year": 2,
    "semester": "Second",
    "code": "BACC 3",
    "name": "Human Resource Management",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": []
    },
    {
    "year": 2,
    "semester": "Second",
    "code": "BACC 4",
    "name": "Business Law (Obligation and Contracts)",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": []
    },
    {
    "year": 2,
    "semester": "Second",
    "code": "MM 3",
    "name": "Distribution Management",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": ["MM 1","MM 2"]
    },
    {
    "year": 2,
    "semester": "Second",
    "code": "MM 4",
    "name": "Marketing Research",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": ["MM 1","MM 2","MM 3"]
    },
    {
    "year": 2,
    "semester": "Second",
    "code": "PE 4",
    "name": "Physical Activities Towards Health and Fitness 4 - Sports",
    "lec": 2,
    "lab": 0,
    "unit": 2,
    "preRequisites": ["PE 3"]
    },

    # year 3

    {
    "year": 3,
    "semester": "First",
    "code": "Thesis 1",
    "name": "Methods of Business Research Writing",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": ["Math 201"]
    },
    {
    "year": 3,
    "semester": "First",
    "code": "BACC 5",
    "name": "Social Responsibility & Good Governance",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": []
    },
    {
    "year": 3,
    "semester": "First",
    "code": "MM 5",
    "name": "Advertising",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": ["ELEC 1"]
    },
    {
    "year": 3,
    "semester": "First",
    "code": "MM 6",
    "name": "Retail Management",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": ["MM 3"]
    },
    {
    "year": 3,
    "semester": "First",
    "code": "BACC 6",
    "name": "Income Taxation",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": ["ACCTG 11"]
    },
    {
    "year": 3,
    "semester": "Second",
    "code": "Thesis 2",
    "name": "Business Research",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": ["Thesis 1"]
    },
    {
    "year": 3,
    "semester": "Second",
    "code": "Math 202",
    "name": "Qualitative Techniques in Business",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": []
    },
    {
    "year": 3,
    "semester": "Second",
    "code": "ELEC 2",
    "name": "Franchising",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": ["ELEC 1"]
    },
    {
    "year": 3,
    "semester": "Second",
    "code": "MM 7",
    "name": "Pricing Strategy",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": ["MM 4"]
    },
    {
    "year": 3,
    "semester": "Second",
    "code": "CBMEC 1",
    "name": "Operations Management (TQM)",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": []
    },

    # year 4


  {
    "year": 4,
    "semester": "First",
    "code": "CBMEC 2",
    "name": "Strategic Management",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": ["CBMEC 1"]
  },
  {
    "year": 4,
    "semester": "First",
    "code": "BACC 7",
    "name": "Feasibility Study",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": ["ACCTG 11"]
  },
  {
    "year": 4,
    "semester": "First",
    "code": "MM 8",
    "name": "Professional Salesmanship",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": ["Mktg 1"]
  },
  {
    "year": 4,
    "semester": "First",
    "code": "ELEC 3",
    "name": "Entrepreneurial Management",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": ["CBMEC 1"]
  },
  {
    "year": 4,
    "semester": "First",
    "code": "ELEC 4",
    "name": "New Market Development",
    "lec": 3,
    "lab": 0,
    "unit": 3,
    "preRequisites": ["MM2"]
  },
  {
    "year": 4,
    "semester": "Second",
    "code": "MM 9",
    "name": "Internship / Work Integrated Learning (600 hrs)",
    "lec": 6,
    "lab": 0,
    "unit": 6,
    "preRequisites": ["Graduating"]
  }
    


  ]
}

# --- Insert new document ---
result = collection.insert_one(new_curriculum)

print(f"✅ New curriculum inserted with _id={result.inserted_id}")