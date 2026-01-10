"""Service for parsing Feature Brief markdown into structured data"""
import re
from typing import List
from dataclasses import dataclass, asdict


@dataclass
class ParsedBrief:
    """Structured data extracted from Feature Brief"""
    name: str
    description: str
    problem_statement: str
    target_users: List[str]
    core_functionality: List[str]
    success_metrics: List[str]
    technical_considerations: List[str]

    def to_dict(self) -> dict:
        """Convert to dict for Feature model creation"""
        return asdict(self)


class BriefParser:
    """Parser for Feature Brief markdown documents"""

    def parse(self, brief_text: str) -> ParsedBrief:
        """
        Parse Feature Brief markdown into structured data

        Args:
            brief_text: Markdown text of the Feature Brief

        Returns:
            ParsedBrief with extracted information

        Raises:
            ValueError: If brief is invalid or missing required sections
        """
        # Extract feature name from H1
        name = self._extract_name(brief_text)
        if not name:
            raise ValueError("No feature name found in H1 heading")

        # Extract sections
        problem_statement = self._extract_section_text(brief_text, "Problem Statement")
        target_users = self._extract_section_list(brief_text, "Target Users")
        core_functionality = self._extract_section_list(brief_text, "Core Functionality")
        success_metrics = self._extract_section_list(brief_text, "Success Metrics")
        technical_considerations = self._extract_section_list(brief_text, "Technical Considerations")

        # Create description from problem statement
        description = self._create_description(problem_statement, core_functionality)

        return ParsedBrief(
            name=name,
            description=description,
            problem_statement=problem_statement,
            target_users=target_users,
            core_functionality=core_functionality,
            success_metrics=success_metrics,
            technical_considerations=technical_considerations
        )

    def _extract_name(self, text: str) -> str:
        """Extract feature name from H1 heading"""
        match = re.search(r'^#\s+Feature Brief:\s*(.+?)$', text, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Fallback: try any H1
        match = re.search(r'^#\s+(.+?)$', text, re.MULTILINE)
        if match:
            name = match.group(1).strip()
            # Remove "Feature Brief:" prefix if present
            name = re.sub(r'^Feature Brief:\s*', '', name, flags=re.IGNORECASE)
            return name

        return ""

    def _extract_section_text(self, text: str, section_name: str) -> str:
        """Extract text content from a section"""
        # Find section heading (H2 or H3)
        pattern = rf'^##\s+{re.escape(section_name)}\s*$\n(.*?)(?=^##|\Z)'
        match = re.search(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)

        if not match:
            return ""

        content = match.group(1).strip()

        # Remove markdown formatting (bold, italic)
        content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)  # Bold
        content = re.sub(r'\*(.+?)\*', r'\1', content)      # Italic
        content = re.sub(r'__(.+?)__', r'\1', content)      # Bold alt
        content = re.sub(r'_(.+?)_', r'\1', content)        # Italic alt

        return content

    def _extract_section_list(self, text: str, section_name: str) -> List[str]:
        """Extract list items from a section"""
        # Find section heading
        pattern = rf'^##\s+{re.escape(section_name)}\s*$\n(.*?)(?=^##|\Z)'
        match = re.search(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)

        if not match:
            return []

        content = match.group(1).strip()

        # Extract list items (both - and *)
        items = []
        for line in content.split('\n'):
            # Match list items (handle indentation for nested lists)
            match = re.match(r'^\s*[-*]\s+(.+)$', line)
            if match:
                item = match.group(1).strip()
                # Remove markdown formatting
                item = re.sub(r'\*\*(.+?)\*\*', r'\1', item)  # Bold
                item = re.sub(r'\*(.+?)\*', r'\1', item)      # Italic
                item = re.sub(r'__(.+?)__', r'\1', item)      # Bold alt
                item = re.sub(r'_(.+?)_', r'\1', item)        # Italic alt
                items.append(item)

        return items

    def _create_description(self, problem_statement: str, core_functionality: List[str]) -> str:
        """Create a concise description from problem statement and functionality"""
        if not problem_statement:
            return ""

        # Use first sentence of problem statement
        first_sentence = problem_statement.split('.')[0] + '.'

        # If very short, add first functionality point
        if len(first_sentence) < 50 and core_functionality:
            first_sentence += f" {core_functionality[0]}"

        return first_sentence
