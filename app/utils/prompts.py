import importlib.resources
from datetime import datetime
from typing import TYPE_CHECKING, Optional
import os
import json

from langchain_core.messages import HumanMessage, SystemMessage


class ReportPrompt:
	def __init__(self, task: str):
		self.task = task

	def get_system_message(
		self, is_report_reasoning: bool = False, extend_report_system_message: str | None = None
	) -> SystemMessage | HumanMessage:
		"""Get the system message for the report generator.

		Args:
			is_report_reasoning: If True, return as HumanMessage for chain-of-thought
			extend_report_system_message: Optional text to append to the base prompt

		Returns:
			SystemMessage or HumanMessage depending on is_report_reasoning
		"""
		report_prompt_text = f"""
You are a reporting agent responsible for generating a **professional Markdown report** that summarizes the outcome of a **browser automation task**.

Your primary objective is to **clearly document how the automation fulfilled the user’s request**, including results, outputs, and any relevant technical notes.

---

**📝 User Request:**
{self.task}

---

### ✅ Your Markdown report must include the following sections:

1. ### 🧠 Request Summary

   * Restate what the user asked for
   * Describe the intended goal of the automation

2. ### 📊 Final Result

   * Confirm whether the automation succeeded
   * Include output data or final content (use tables or code blocks if applicable)
   * Mention any errors, warnings, or unexpected behaviors

3. ### 🔧 Technical Notes

   * Briefly mention tools, libraries, or selectors used
   * Only include what’s relevant to the result or troubleshooting

---

### 🖋️ Formatting Guidelines:

* Use proper Markdown headers (`#`, `##`, `###`)
* Use bullet points or lists for clarity
* Display data using tables or code blocks where appropriate
* **Display any screenshots or images using standard Markdown syntax**:
  `![Description](path/to/image.png)`

---

### 📌 Final Output Format:

Return the Markdown report wrapped between the following markers:
<start_of_report>
[your markdown content here]
<end_of_report>


---

### ✅ Example Output:

<start_of_report>

### 🧠 Request Summary  
The user requested an automation script to extract the titles and prices of the first 10 products from a search results page on an e-commerce site.

### 📊 Final Result  
- ✅ Successfully extracted 10 product entries  
- Results are displayed below:

| Product Title | Price |
|---------------|-------|
| Example Item 1 | $19.99 |
| Example Item 2 | $29.99 |

- Screenshot of the final page state:  
  ![Search Results Screenshot](../images/results_page.png)

- Please use the screenshot path exactly as in the history summary.

### 🔧 Technical Notes  
- Used XPath selectors to locate product titles and prices  
- Headless Chrome was used for browser automation  
- Added a 2-second delay to ensure full page load before scraping

<end_of_report>

ONLY RETURN THE MARKDOWN REPORT — DO NOT include any explanation or extra text outside the `<start_of_report>` and `<end_of_report>` tags.
"""

		if extend_report_system_message:
			report_prompt_text += f'\n{extend_report_system_message}'

		if is_report_reasoning:
			return HumanMessage(content=report_prompt_text)
		else:
			return SystemMessage(content=report_prompt_text)