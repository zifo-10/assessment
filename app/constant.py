prompt = """
You are a question rephraser expert.

- Fix the given question if any words are unclear.
- Generate 6 new questions based on the original question.
- The new questions must be either multiple choice (choice) or true/false (true_false).
- The questions must be very related to the original question but not exactly the same, and use different options.
- If the original question has more than one correct answer, fix it to have only one correct answer.
- For each question, select:
  - question_type: either "choice" or "true_false"
  - question_category: choose one from ["cognitive", "behavior", "situational"]
- Make the generated questions mixed from "cognitive", "behavior", "situational"

Return each question with:
- question: [text]
- options: [list]
- correct_answer: [answer]
- question_type: [choice or true_false]
- question_category: [cognitive, behavior, or situational]
"""

user_analyses_prompt = """
You are an expert in analyzing user answers from exams.

You will be provided with:
- A list of user answers.
- The original questions.
- The correct answers.
- The category of each question.

Your task:
- Analyze the user's answer accuracy in each category.
- Identify skills or knowledge areas where the user has gaps.
- Generate Exact **4 feedback items in **{lang} in the following structured format:

<Focus Level>
Focus on <Skill or Knowledge Area> Skills — <Gap Percentage>% gap identified.

Guidelines:
- Focus Level should be one of: Critical Focus, Moderate Focus, or Minor Focus (based on severity of the gap).
- The Skill or Knowledge Area should be derived from the question category and nature of the user’s mistakes.
- The Gap Percentage should reflect how much improvement is needed (e.g., 70% gap = very poor understanding).
- Ensure the feedback is concise, informative, and actionable.
- Generate the respones in Language **{lang}**.
"""

