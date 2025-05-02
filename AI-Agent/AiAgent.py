import ollama
from PyPDF2 import PdfReader
from typing import List, Dict
import re
import textwrap

class SHLAssessmentAnalyzer:
    def __init__(self, pdf_path: str):
        """
        Initialize with Ollama and PDF processing
        """
        self.pdf_path = pdf_path
        self.model_name = "mistral"
        self.full_text = self._extract_pdf_text()
        self.chunks = self._chunk_text()
        self.assessment_metadata = self._extract_metadata()
        
        
        print("=== DEBUG: First 300 characters ===")
        print(self.full_text[:300])
        print("\n=== DEBUG: Extracted Metadata ===")
        print(self.assessment_metadata)

    def _extract_pdf_text(self) -> str:
        """Extract all text from PDF with encoding handling"""
        text = ""
        try:
            with open(self.pdf_path, 'rb') as file:
                reader = PdfReader(file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"Error reading PDF: {e}")
        return text

    def _chunk_text(self, chunk_size: int = 2000) -> List[str]:
        """Split text into manageable chunks"""
        return textwrap.wrap(self.full_text, width=chunk_size)

    def _extract_metadata(self) -> Dict:
        """Extract key assessment metadata with robust patterns"""
        metadata = {
            'assessment_name': None,
            'job_level': None,
            'traits_measured': []
        }
        
        
        name_patterns = [
            r'#\s*(.*?)\s*[–\-]',  
            r'Assessment:\s*(.*?)\s*\n',
            r'Account Manager\s*(.*?)\s*Assessment'
        ]
        
        for pattern in name_patterns:
            if match := re.search(pattern, self.full_text, re.IGNORECASE):
                metadata['assessment_name'] = match.group(1).strip()
                break
        
    
        level_patterns = [
            r'Job Level\s*[|:]\s*(.*?)\n',
            r'Level:\s*(.*?)\s*\n'
        ]
        for pattern in level_patterns:
            if match := re.search(pattern, self.full_text, re.IGNORECASE):
                metadata['job_level'] = match.group(1).strip()
                break
        
        
        traits = []
        trait_section = re.search(r'Measured (?:Traits|Competencies):?(.*?)(?:\n\n|$)', 
                                self.full_text, re.DOTALL | re.IGNORECASE)
        if trait_section:
            traits = re.findall(r'\b([A-Z][a-z]+(?: [A-Z][a-z]+)*)\b', trait_section.group(1))
        
        if not traits:
            traits = re.findall(r'\*\*(.*?):\*\*', self.full_text)
        
        metadata['traits_measured'] = [t.strip() for t in traits if len(t.strip()) > 3]
        
        return metadata

    def ask_llm(self, prompt: str, context: str = None) -> str:
        """
        Query Mistral via Ollama with error handling
        """
        try:
            full_prompt = f"Context: {context}\n\nQuestion: {prompt}" if context else prompt
            
            response = ollama.chat(
                model=self.model_name,
                messages=[{
                    'role': 'user',
                    'content': full_prompt,
                    'temperature': 0.3
                }]
            )
            return response['message']['content']
        except Exception as e:
            return f"Error querying LLM: {e}"

    def answer_question(self, question: str) -> str:
        """
        Answer questions about the assessment with fallback logic
        """
        
        q_lower = question.lower()
        
        
        if 'name' in q_lower:
            return (f"The assessment name is: {self.assessment_metadata['assessment_name']}" 
                   if self.assessment_metadata['assessment_name'] 
                   else "Assessment name not found in document")
        
        if 'level' in q_lower and 'job' in q_lower:
            return (f"Target job level: {self.assessment_metadata['job_level']}" 
                   if self.assessment_metadata['job_level'] 
                   else "Job level not specified")
        
        if any(t in q_lower for t in ['trait', 'competenc', 'measure']):
            if self.assessment_metadata['traits_measured']:
                return f"Measured traits: {', '.join(self.assessment_metadata['traits_measured'])}"
            return "No traits/competencies found in document"
        
        
        relevant_chunk = self._find_most_relevant_chunk(question)
        return self.ask_llm(
            prompt=question,
            context=relevant_chunk[:1500]  
        )

    def _find_most_relevant_chunk(self, question: str) -> str:
        """
        Find the most relevant text chunk using keyword matching
        """
        question_words = set(re.findall(r'\w+', question.lower()))
        best_chunk = self.chunks[0]  # Default to first chunk
        best_score = 0
        
        for chunk in self.chunks:
            chunk_words = set(re.findall(r'\w+', chunk.lower()))
            score = len(question_words & chunk_words)
            if score > best_score:
                best_score = score
                best_chunk = chunk
                
        return best_chunk

    def generate_report(self) -> str:
        """
        Generate comprehensive assessment report with error handling
        """
        try:
            report = f"""
            SHL ASSESSMENT ANALYSIS REPORT
            {'='*40}
            Assessment Name: {self.assessment_metadata['assessment_name'] or 'Not found'}
            Job Level: {self.assessment_metadata['job_level'] or 'Not specified'}
            """
            
            if self.assessment_metadata['traits_measured']:
                report += f"\nMeasured Traits:\n- " + "\n- ".join(self.assessment_metadata['traits_measured'])
            
            
            summary = self.ask_llm(
                "Summarize this assessment's purpose and key features in 3 bullet points",
                context=self.chunks[0]
            )
            
            return report + "\n\nSUMMARY:\n" + summary
        except Exception as e:
            return f"Error generating report: {e}"


if __name__ == "__main__":
    print("=== SHL Assessment Analyzer ===")
    print("Make sure Ollama is running (ollama serve) and Mistral is installed (ollama pull mistral)")
    
    try:
        
        pdf_path = "Fact_Sheet_Account_Manager.pdf"
        analyzer = SHLAssessmentAnalyzer(pdf_path)
        
        print("\n=== Quick Questions ===")
        print(analyzer.answer_question("What is the assessment name?"))
        print(analyzer.answer_question("What job level is this for?"))
        print(analyzer.answer_question("What traits does it measure?"))
        
        print("\n=== Complex Question ===")
        print(analyzer.answer_question("How is sales potential measured in this assessment?"))
        
        print("\n=== Full Report ===")
        print(analyzer.generate_report())
        
    except Exception as e:
        print(f"Error: {e}")
        print("Please ensure: 1) PDF path is correct, 2) Ollama is running, 3) Mistral model is installed")
