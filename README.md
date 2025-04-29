# dopros


# STEPS TO RUN THE PROJECT:

## Prerequisites:
#### 1. A NEMO-based ASR model
#### 2. A .gguf-based language model
#### 3. Python 3.10

## Installation:
#### 1. Inside of the project folder, run:
```bash
pip install -r requirements.txt
```

#### 2. Create a database: inside of src/case, create a transcriptions.db

#### 3. Create a folder in which all transcriptions will be stored

#### 4. Run these commands to initialize the db and the tables inside: 
```bash
python -m src.case.db
python -m src.case.repository.py
```
#### 5. create a .env file and fill in your data. An example can be found in .env.example

```bash
python ui_tk.py
```

## For testing of different modules:
#### This project is modular. Which means you can change code in llm, transcription and then add code in their main method to test
#### To run each module as a single entity, simply run command: 
```bash
python -m *path to main module*
```

### Example:

```bash
python -m src.llm.llm
```
#
P.S. This project runs on python 3.10 for now due to compatibility issues between nemo_toolkit[asr], our linux distro and python versioning mismatches.
