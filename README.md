# FlowControl – Surgical Planning Application

## Project Title and Description

**Title:**  
FlowControl – Surgical Planning Application

**Brief Description:**  
FlowControl is an application designed for surgical planning workflows for scoliosis procedures. The application provides structured data entry for radiographic parameters, automated curve classification, and decision-support tools for instrumentation planning.

It integrates radiographic analysis, implant inventory tracking, and multi-step surgical planning in a single workflow-driven interface.

---

# Key Features

- Guided **multi-step surgical planning workflow**
- **Radiographic adaptive analysis**
- Automated **Lenke classification**
- **Selective Thoracic Fusion (STF)** and **Selective Lumbar Fusion (SLF)** evaluation
- **UIV and LIV decision support**
- **Anchor selection and rod planning**
- **Correction strategy planning**
- **Inventory tracking integration**
- **Export and communication tools for surgical plans**
- Conditional UI logic based on clinical parameters

---

# Installation

## Prerequisites

- Python **3.x**
- pip (Python package manager)

Recommended Python version:

Python 3.10 or 3.11

---

## Dependencies

Key Python libraries used:

- tkinter
- Pillow (PIL)
- tkcalendar
- openpyxl
- pandas
- pyodbc

Install dependencies:

```bash
pip install pillow tkcalendar openpyxl pandas pyodbc
```

---

## Installation Steps

### 1. Clone the repository

### 2. Install dependencies

### 3. Run the application

```bash
python flowbi_wan.py
```
---

# Usage

## Starting the Application

Run from the project root directory:

```bash
python flowbi_wan.py
```
---

## Workflow Overview

Typical workflow:

1. Create or load a surgical plan
2. Enter radiographic parameters
3. Perform radiographic adaptive analysis
4. Review Lenke classification
5. Evaluate STF / SLF eligibility
6. Select UIV and LIV
7. Choose anchors and rods
8. Define correction strategies
9. Review post-operative planning
10. Export or communicate the surgical plan

---

# Project Structure

```
flowcontrol/
│
├── flowbi_wan.py
│   Main application entry point
│
├── pages/
│   User interface pages and workflow logic
│
├── inventory/
│   Inventory tracking and database modules
│
├── assets/
│   Images, icons, and UI resources
│
└── README.md
```

---

# Inventory Tracking

The application supports implant inventory integration via database connections.

Features include:

- Implant availability lookup
- Inventory tracking
- Integration with surgical planning modules

# Additional Notes

## Data Requirements

The application relies on:

- JSON configuration files
- Database connections for inventory
- Asset files for UI rendering

Ensure required resources are present before running the application.

---