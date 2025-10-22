from pymongo import MongoClient

# --- 1️⃣ Connect to MongoDB ---
client = MongoClient("mongodb://admin:admin@162.250.127.92:27017")  # existing URI
db = client["assessment"]

# --- 2️⃣ Define target collection ---
target_collection = db["training_details"]

# --- 3️⃣ Define filter and updates ---
filter_query = {"training_name": "معدات الحماية الفردية"}

new_values = {
    "$set": {
        "description_ar": (
            "تُعد معدات الحماية الشخصية (PPE) الخط الدفاعي الأخير ضد مخاطر مكان العمل. "
            "وتشمل الممارسات الأساسية اختيار معدات الحماية الشخصية المناسبة — مثل الخوذ، والقفازات، "
            "والنظارات الواقية، وأجهزة التنفس — بناءً على تقييم المخاطر، وضمان ملاءمتها بشكل صحيح، "
            "وتدريب العاملين على استخدامها بشكل صحيح. يجب أن تلبي معدات الحماية الشخصية معايير السلامة، "
            "وأن تُفحص بانتظام، وتُخزن بشكل مناسب، وتُستبدل عندما تصبح بالية. ورغم أن معدات الحماية الشخصية "
            "لا تقضي على المخاطر تمامًا، إلا أنها تقلل بشكل كبير من مخاطر الإصابة عند استخدامها بشكل منتظم."
        ),
        "description_en": (
            "Personal Protective Equipment (PPE) is the last defense against workplace hazards. "
            "Key practices include selecting the right PPE—such as helmets, gloves, goggles, and respirators—"
            "based on hazard assessments, ensuring proper fit, and training workers on correct use. "
            "PPE must meet safety standards, be inspected regularly, stored properly, and replaced when worn. "
            "While PPE doesn't remove hazards, it greatly reduces injury risk when used consistently."
        ),
    }
}

# --- 4️⃣ Perform update ---
result = target_collection.update_one(filter_query, new_values)

# --- 5️⃣ Print result ---
if result.matched_count > 0:
    if result.modified_count > 0:
        print("✅ Training description updated successfully.")
    else:
        print("ℹ️ Training found, but no changes were necessary (already up to date).")
else:
    print("❌ No training found with name 'معدات الحماية الفردية'.")
