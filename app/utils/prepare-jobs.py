import pandas as pd

from app.client.mongo_client import MongoDBClient
from app.model.job_dto import JobDTO
import os

mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
db_name = os.getenv('DB_NAME', 'assessment')
collection_name = os.getenv('COLLECTION_NAME', 'job')
mongo_client = MongoDBClient(mongo_uri, db_name, collection_name)


def process_training_data(file_path):
    df = pd.read_excel(file_path)

    df.columns = [str(col).strip() for col in df.columns]

    job_detail_cols = ['#', 'رمز المهنة', 'مسمى المهنة', 'تصنيف المهنة', 'الترخيص']

    # Step 1: Identify training columns and their levels
    training_cols = {}
    skip = set(job_detail_cols)

    i = 0
    while i < len(df.columns):
        col = df.columns[i]
        if col in skip or "Unnamed" in col:
            i += 1
            continue

        # Ensure that "مهن مقيدة" is not processed as a training column
        if "مهن مقيدة" in col:
            i += 1
            continue

        training_name = col
        training_cols[training_name] = []

        # add this named col and all following unnamed cols as its levels
        training_cols[training_name].append(col)
        j = i + 1
        while j < len(df.columns) and "Unnamed" in df.columns[j]:
            training_cols[training_name].append(df.columns[j])
            j += 1

        i = j  # skip ahead to next named training

    results = []

    # Step 2: Process the rows and create dictionaries for MongoDB insertion
    for _, row in df.iterrows():
        job = {
            "job_name": row["مسمى المهنة"],
            "job_code": row["رمز المهنة"],
            "classification": row["تصنيف المهنة"],
            "trainings": []
        }

        for training_name, cols in training_cols.items():
            levels = []
            for i, col in enumerate(cols):
                val = row.get(col)
                difficulty = 0  # default difficulty to 0

                if pd.notna(val) and str(val).strip() != "":
                    try:
                        difficulty = int(float(val))
                    except ValueError:
                        pass  # keep it as 0 if invalid

                # Add each level
                levels.append({
                    "level": i + 1,
                    "difficulty": difficulty
                })

            if levels:
                job["trainings"].append({
                    "training_name": training_name,
                    "levels": levels
                })

        results.append(job)

    # Return the list of dictionaries to be inserted into MongoDB
    return results


# Example usage:
file_path = "training-jobs.xlsx"  # change this to your file path
training_data = process_training_data(file_path)
i = 0
for job in training_data:
    i += 1
    try:
        # Insert each job into MongoDB
        insert = mongo_client.insert_one(JobDTO(**job).model_dump())
        print('inserted', insert)
    except Exception as e:
        print(e)
