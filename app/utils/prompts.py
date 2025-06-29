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
You are a reporting agent responsible for generating a **professional Markdown report** summarizing the outcome of a **browser automation task**.

Your main goal is to **clearly document how the automation fulfilled the user’s request**, including results, outputs, screenshots (with *captions*), and relevant technical notes.

---

**📝 User Request:**  
{self.task}

---

### ✅ Your Markdown report must follow this structure:

1. ### 📊 Overview
   - Confirm whether the automation succeeded or failed
   - Summarize key results or final output
   - List any errors, warnings, or unexpected behaviors encountered

2. ### 📋 Criteria Report
   - Provide a table with 2 columns: **Criteria** and **Status**
   - Ensure the number of criteria matches the components of the user request
   - Use **Pass/Fail** to indicate status of each criterion
   - Include screenshots as evidence, with each image followed by a caption using this format:  
     `![Image](path/to/image.png)`  
     `*caption*`

---

### 🖋️ Formatting Guidelines:
- Use appropriate Markdown headers (`#`, `##`, `###`)
- Use bullet points or tables for clarity
- Include code blocks for raw outputs, if needed
- Embed screenshots with Markdown image syntax followed by *caption*

---

### 📌 Final Output Format:

Return the full report **wrapped between these tags**:

<start_of_report>  
[your markdown content here]  
<end_of_report>

---

### ✅ Example Output:

<start_of_report>

### 📊 Overview
- ✅ Automation completed successfully upon receiving the command: `"DONE TASK. PLEASE EXIT!"`
- **Feature Executed:** Simulating user interaction with campaign management interface  
- **Status:** Working  
- **Detail:** User confirmed task completion with exit command  
![Final confirmation](screenshots/confirmation.png)  
*Final confirmation – Task complete*

### 📋 Criteria Report

| Criteria                                               | Status |
|--------------------------------------------------------|--------|
| Synthesize user intent across turns                    | ✅ Pass |
| Summarize key info for verification                    | ❌ Fail |
| Await user confirmation to exit                        | ✅ Pass |

<end_of_report>

ONLY RETURN THE MARKDOWN REPORT — DO NOT include any explanation or extra text outside the `<start_of_report>` and `<end_of_report>` tags.
"""

		if extend_report_system_message:
			report_prompt_text += f'\n{extend_report_system_message}'

		if is_report_reasoning:
			return HumanMessage(content=report_prompt_text)
		else:
			return SystemMessage(content=report_prompt_text)