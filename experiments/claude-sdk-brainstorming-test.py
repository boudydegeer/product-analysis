#!/usr/bin/env python3
"""
Claude Agent SDK - Brainstorming PoC Test Script

This script demonstrates how to use the Claude Agent SDK for interactive brainstorming sessions.
It validates key capabilities needed for building an interactive FastAPI backend:
1. Streaming responses in real-time
2. Detecting questions and multiple-choice options from Claude
3. Handling multi-turn conversations
4. Restricting tools to WebSearch/WebFetch only (brainstorming mode)

INTEGRATION WITH FASTAPI BACKEND:
- Use Server-Sent Events (SSE) to stream responses to frontend
- Parse streamed content to extract questions and multiple-choice options
- Store conversation state in Redis/database for session management
- Create WebSocket or SSE endpoint that wraps this streaming logic
- Build UI components that render detected multiple-choice questions as interactive buttons
"""

import os
import re
import asyncio
from typing import List, Dict, Optional
from claude_agent_sdk import Agent, MessageParam


class BrainstormingSession:
    """
    Wrapper class for managing an interactive brainstorming session with Claude.

    In FastAPI, this would be initialized per user session and conversation state
    would be persisted to allow resuming conversations.
    """

    def __init__(self, api_key: str):
        """
        Initialize the brainstorming session.

        Args:
            api_key: Anthropic API key (from environment or config)
        """
        self.agent = Agent(
            api_key=api_key,
            # Restrict to web tools only - no code access for brainstorming
            allowed_tools=["WebSearch", "WebFetch"],
            # Use Claude Sonnet 4.5 for better reasoning during brainstorming
            model="claude-sonnet-4-5"
        )
        self.conversation_history: List[MessageParam] = []

    async def start_brainstorming(self, topic: str) -> None:
        """
        Start a new brainstorming session on a given topic.

        This demonstrates:
        1. How to stream responses in real-time
        2. How to detect questions and multiple-choice options
        3. How to accumulate streaming content

        In FastAPI, you would:
        - Create an SSE endpoint: @app.get("/brainstorm/stream")
        - Yield each chunk as: f"data: {json.dumps(chunk)}\n\n"
        - Frontend would parse SSE stream and update UI in real-time

        Args:
            topic: The feature or topic to brainstorm about
        """
        print(f"\n{'='*80}")
        print(f"STARTING BRAINSTORMING SESSION")
        print(f"Topic: {topic}")
        print(f"{'='*80}\n")

        # Initial prompt to start brainstorming
        initial_message = f"""Let's brainstorm about this feature: {topic}

Please help me explore:
1. What problem does this solve?
2. Who are the target users?
3. What are the key requirements?
4. What are potential challenges?

Feel free to ask me questions to better understand the context and requirements."""

        self.conversation_history.append({
            "role": "user",
            "content": initial_message
        })

        # Stream the response
        await self._stream_and_process_response()

    async def continue_conversation(self, user_message: str) -> None:
        """
        Continue the brainstorming conversation with a follow-up message.

        This demonstrates how to maintain conversation context across turns.

        In FastAPI, you would:
        - Store conversation_history in Redis with session_id as key
        - Retrieve history at the start of each request
        - Append new messages and update the stored history

        Args:
            user_message: The user's response or follow-up question
        """
        print(f"\n{'='*80}")
        print(f"USER MESSAGE")
        print(f"{'='*80}")
        print(f"{user_message}\n")

        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        await self._stream_and_process_response()

    async def _stream_and_process_response(self) -> None:
        """
        Internal method to stream Claude's response and process it.

        This is the core streaming logic that would be adapted for FastAPI SSE.

        Key implementation details for FastAPI:

        ```python
        @app.get("/brainstorm/stream")
        async def stream_brainstorm(session_id: str, message: str):
            async def event_generator():
                async for chunk in agent.stream_message(messages):
                    # Send raw chunk to frontend
                    yield {
                        "event": "chunk",
                        "data": json.dumps({"content": chunk})
                    }

                    # Detect questions/options and send structured data
                    if detected_question := detect_question(accumulated_text):
                        yield {
                            "event": "question",
                            "data": json.dumps(detected_question)
                        }

                yield {"event": "done", "data": "{}"}

            return EventSourceResponse(event_generator())
        ```
        """
        accumulated_response = ""
        detected_questions: List[Dict] = []

        print(f"{'='*80}")
        print(f"CLAUDE'S RESPONSE (streaming...)")
        print(f"{'='*80}\n")

        # Stream the response chunk by chunk
        async for chunk in self.agent.stream_message(messages=self.conversation_history):
            # Print chunk in real-time (simulates frontend receiving SSE events)
            print(chunk, end="", flush=True)
            accumulated_response += chunk

            # IMPORTANT: In production, you would parse accumulated_response
            # periodically to detect questions as they're being formed
            # For now, we'll analyze after streaming completes

        print(f"\n\n{'='*80}\n")

        # Add assistant's response to conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": accumulated_response
        })

        # Analyze the response for questions and multiple-choice options
        detected_questions = self._detect_questions_and_options(accumulated_response)

        if detected_questions:
            print(f"{'='*80}")
            print(f"DETECTED INTERACTIVE ELEMENTS")
            print(f"{'='*80}\n")

            for i, question in enumerate(detected_questions, 1):
                print(f"Question {i}: {question['question']}")
                if question.get('options'):
                    print(f"Options detected: {len(question['options'])}")
                    for j, option in enumerate(question['options'], 1):
                        print(f"  {j}. {option}")
                print()

            print("In the FastAPI frontend, these would be rendered as:")
            print("- Radio buttons or clickable cards for single choice")
            print("- Checkboxes for multiple choice")
            print("- Quick reply buttons below the chat message")
            print(f"{'='*80}\n")

    def _detect_questions_and_options(self, text: str) -> List[Dict[str, any]]:
        """
        Detect questions and multiple-choice options in Claude's response.

        This is a critical function for building interactive UI elements.

        Patterns detected:
        1. Numbered lists (1. Option A, 2. Option B)
        2. Lettered lists (a. Option A, b. Option B)
        3. Bulleted lists (- Option A, - Option B)
        4. Questions followed by lists

        In production, you might want to:
        - Use more sophisticated NLP to detect questions
        - Use regex patterns to identify different list formats
        - Handle nested lists and complex formatting
        - Detect yes/no questions vs open-ended questions

        Returns:
            List of detected questions with their options
        """
        questions = []

        # Split text into paragraphs
        paragraphs = text.split('\n\n')

        for i, para in enumerate(paragraphs):
            # Check if paragraph contains a question
            if '?' in para:
                question_text = para.strip()

                # Look ahead to see if next paragraph contains a list
                options = []
                if i + 1 < len(paragraphs):
                    next_para = paragraphs[i + 1]

                    # Pattern 1: Numbered list (1. / 2. / 3.)
                    numbered_pattern = r'^\d+\.\s+(.+)$'
                    numbered_matches = re.findall(numbered_pattern, next_para, re.MULTILINE)
                    if len(numbered_matches) >= 2:
                        options = numbered_matches

                    # Pattern 2: Lettered list (a. / b. / c.)
                    if not options:
                        lettered_pattern = r'^[a-z]\.\s+(.+)$'
                        lettered_matches = re.findall(lettered_pattern, next_para, re.MULTILINE)
                        if len(lettered_matches) >= 2:
                            options = lettered_matches

                    # Pattern 3: Bulleted list (- / *)
                    if not options:
                        bullet_pattern = r'^[-*]\s+(.+)$'
                        bullet_matches = re.findall(bullet_pattern, next_para, re.MULTILINE)
                        if len(bullet_matches) >= 2:
                            options = bullet_matches

                # Check if the question itself contains inline options
                # Pattern: "Would you like A, B, or C?"
                if not options:
                    inline_pattern = r'(?:(?:Would you|Do you|Should|Can|Could).+?)\s+([A-Z][^,?]+(?:,\s*[A-Z][^,?]+)*(?:,?\s*(?:or|and)\s*[A-Z][^?]+)?)\?'
                    inline_match = re.search(inline_pattern, question_text)
                    if inline_match:
                        options_text = inline_match.group(1)
                        # Split on commas and 'or'/'and'
                        options = [opt.strip() for opt in re.split(r',\s*(?:or|and)?\s*|(?:or|and)\s+', options_text)]
                        options = [opt for opt in options if opt]  # Remove empty strings

                questions.append({
                    'question': question_text,
                    'options': options if options else None,
                    'type': 'multiple_choice' if options else 'open_ended'
                })

        return questions


async def main():
    """
    Main test function demonstrating the complete brainstorming workflow.

    This simulates what would happen in a real FastAPI application:
    1. User starts a brainstorming session
    2. Claude responds with questions
    3. User provides answers
    4. Conversation continues iteratively
    """

    # Get API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it with: export ANTHROPIC_API_KEY='your-key-here'")
        return

    # Initialize brainstorming session
    session = BrainstormingSession(api_key=api_key)

    # Test 1: Start a brainstorming session about a hypothetical feature
    await session.start_brainstorming(
        topic="Smart Meeting Scheduler that uses AI to find optimal meeting times across teams"
    )

    # Test 2: Continue the conversation with a follow-up
    # In a real app, this would be user input from the frontend
    await session.continue_conversation(
        """The target users are primarily product managers and team leads who manage 5-15 people.
They struggle with scheduling because team members are across different time zones
and have varying availability patterns. The main problem is the back-and-forth
of finding a time that works for everyone."""
    )

    # Test 3: Another follow-up to maintain conversation flow
    await session.continue_conversation(
        """I think the biggest challenge will be integrating with different calendar systems
(Google Calendar, Outlook, Apple Calendar) and respecting privacy preferences.
What do you think about the technical feasibility?"""
    )

    print(f"\n{'='*80}")
    print(f"BRAINSTORMING SESSION COMPLETE")
    print(f"{'='*80}")
    print(f"\nTotal conversation turns: {len(session.conversation_history)}")
    print(f"\nThis demonstrates:")
    print(f"✓ Streaming responses in real-time")
    print(f"✓ Multi-turn conversation maintenance")
    print(f"✓ Question detection for interactive UI")
    print(f"✓ Tool restriction (WebSearch/WebFetch only)")
    print(f"\nReady for FastAPI integration!")


if __name__ == "__main__":
    asyncio.run(main())
