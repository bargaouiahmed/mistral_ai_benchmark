from dotenv import load_dotenv
import os
import json
import re
from mistralai import Mistral

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise ValueError("API_KEY not found in environment variables. Please check your .env file.")

model = "mistral-large-latest"
client = Mistral(api_key=API_KEY)

# Improved prompt with clear formatting instructions and code example requirements
prompt = """
Generate a 10-question coding quiz with the following specifications:

1. Each question should be challenging but not obscure
2. Cover various programming concepts including JavaScript, Python, and general CS knowledge
3. IMPORTANT: For questions involving code evaluation, include the complete code snippet in the question
4. Format each question exactly as follows:
   - Numbered question (1-10) followed by the question text
   - Include any code blocks directly in the question text
   - Four answer options labeled a, b, c, d
   - Mark the correct answer with ***correct*** (e.g., ***a***)
5. No explanations, commentary, or extra text

Example format for a code evaluation question:
1. What is the output of the following JavaScript code?
```javascript
let x = 10;
let y = 20;
console.log(y, x);
```
   a) 10, 20
   b) 20, 10
   c) 20, 20
   d) 10, 10
   ***b***

Provide only the formatted questions and answers, ensuring code snippets are complete.
"""

try:
    # Make API call
    chat_response = client.chat.complete(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # Get raw response
    raw_content = chat_response.choices[0].message.content

    # Parse the quiz questions
    quiz_data = []

    # Split the content into individual questions
    # This pattern looks for numbered items (1., 2., etc.) at the beginning of a line
    question_pattern = r'(?:^|\n)(\d+\.\s+.*?)(?=\n\d+\.\s+|\Z)'
    questions = re.findall(question_pattern, raw_content, re.DOTALL)

    for i, question_text in enumerate(questions):
        # Extract the question and options
        # First, find the options section
        options_match = re.search(r'\n\s*a\)\s+(.*?)\n\s*b\)\s+(.*?)\n\s*c\)\s+(.*?)\n\s*d\)\s+(.*?)(?:\n|$)',
                                  question_text, re.DOTALL)

        if not options_match:
            continue

        option_a, option_b, option_c, option_d = [opt.strip() for opt in options_match.groups()]

        # Extract the question part (everything before the options)
        question_part = question_text[:options_match.start()].strip()

        # Clean up numbering from the question
        if question_part.startswith(f"{i + 1}."):
            question_part = question_part[len(f"{i + 1}."):]
        question_part = question_part.strip()

        # Find the correct answer
        correct_answer = None
        correct_pattern = r'\*\*\*([a-d])\*\*\*'
        correct_match = re.search(correct_pattern, question_text)
        if correct_match:
            correct_answer = correct_match.group(1)

            # Clean the options of the correct answer markers
            option_a = re.sub(correct_pattern, '', option_a).strip()
            option_b = re.sub(correct_pattern, '', option_b).strip()
            option_c = re.sub(correct_pattern, '', option_c).strip()
            option_d = re.sub(correct_pattern, '', option_d).strip()

        # Create question object
        quiz_data.append({
            "id": i + 1,
            "question": question_part,
            "options": {
                "a": option_a,
                "b": option_b,
                "c": option_c,
                "d": option_d
            },
            "correctAnswer": correct_answer
        })

    # Convert to JSON for frontend use
    quiz_json = json.dumps(quiz_data, indent=2)

    print("Quiz generated successfully!")
    print(f"Total questions parsed: {len(quiz_data)}")
    print("\nJSON output for frontend:")
    print(quiz_json)

    # Optionally save to file
    with open("coding_quiz.json", "w") as f:
        f.write(quiz_json)
    print("\nQuiz saved to coding_quiz.json")

except Exception as e:
    print(f"Error: {str(e)}")