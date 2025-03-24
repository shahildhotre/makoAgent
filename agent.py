from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
import os
from typing import Generator

from dotenv import load_dotenv

load_dotenv()

class Agent:
    def __init__(self, api_key=None):
        # Initialize OpenAI API key
        if api_key:
            os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
        
        # Initialize the LLM
        self.llm = ChatOpenAI(
            temperature=0.2,  # Slight randomness to explore different optimizations
            model_name="gpt-4",
            max_tokens=None,
            timeout=None,
            max_retries=2,
            # api_key="...",  # if you prefer to pass api key in directly instead of using env vars
            # base_url="...",
            # organization="...",
            # other params...
        )
        
        # Updated prompt to focus on pure analysis without formatting requirements
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are an expert in LLVM IR optimization. Analyze the provided LLVM IR code and provide a detailed technical analysis."""
            ),
            ("human", "{llvm_ir}")
        ])
        
        # Create the optimization chain using composition
        self.optimization_chain = self.prompt | self.llm

    def analyze_code(self, llvm_ir: str) -> Generator[str, None, None]:
        """Analyzes the LLVM IR code and provides an explanation of its functionality."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Explain what this LLVM IR code does in detail, focusing on its functionality and purpose."),
            ("human", "{llvm_ir}")
        ])
        chain = prompt | self.llm
        buffer = ""
        for chunk in chain.stream({"llvm_ir": llvm_ir}):
            buffer += chunk.content
            if any(buffer.endswith(x) for x in ['. ', '! ', '? ', '\n']):
                yield buffer
                buffer = ""
        if buffer:  # Yield any remaining content
            yield buffer

    def identify_bottlenecks(self, llvm_ir: str) -> Generator[str, None, None]:
        """Identifies performance bottlenecks in the LLVM IR code."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Identify and explain performance bottlenecks in this LLVM IR code."),
            ("human", "{llvm_ir}")
        ])
        chain = prompt | self.llm
        buffer = ""
        for chunk in chain.stream({"llvm_ir": llvm_ir}):
            buffer += chunk.content
            if any(buffer.endswith(x) for x in ['. ', '! ', '? ', '\n']):
                yield buffer
                buffer = ""
        if buffer:  # Yield any remaining content
            yield buffer

    def suggest_optimizations(self, llvm_ir: str) -> Generator[str, None, None]:
        """Suggests optimization changes and explains their benefits."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Suggest specific optimization changes for this LLVM IR code and explain why they would help improve performance."),
            ("human", "{llvm_ir}")
        ])
        chain = prompt | self.llm
        buffer = ""
        for chunk in chain.stream({"llvm_ir": llvm_ir}):
            buffer += chunk.content
            if any(buffer.endswith(x) for x in ['. ', '! ', '? ', '\n']):
                yield buffer
                buffer = ""
        if buffer:  # Yield any remaining content
            yield buffer

    def  generate_optimized_ir(self, llvm_ir: str, optimization_suggestions: str) -> str:
        """Generates the optimized version of the LLVM IR code."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Generate an optimized version of this LLVM IR code, applying appropriate optimization techniques mentioned in the optimization suggestions. Always give the optimized LLVM IR code in the format of a code block. start code block with 'define' and end code block with 'attributes'"),
            ("human", '''Original LLVM IR: "{llvm_ir}"

            Suggested optimizations to apply:"{optimization_suggestions}"''')
            ])
        chain = prompt | self.llm
        # Return complete response instead of streaming
        return chain.invoke({"llvm_ir": llvm_ir, "optimization_suggestions": optimization_suggestions}).content

    def optimize_llvm_ir(self, llvm_ir: str):
        """
        Takes LLVM IR code as input and yields analysis and optimized code chunks.
        
        Args:
            llvm_ir (str): The LLVM IR code to optimize
            
        Yields:
            tuple: (section_name, content_chunk)
        """
        try:
            # Stream each section
            for chunk in self.analyze_code(llvm_ir):
                yield ("CODE EXPLANATION", chunk)
            
            for chunk in self.identify_bottlenecks(llvm_ir):
                yield ("BOTTLENECKS", chunk)
            
            optimization_suggestions = ""
            for chunk in self.suggest_optimizations(llvm_ir):
                optimization_suggestions += chunk
                yield ("OPTIMIZATION RATIONALE", chunk)
            
            # Get full optimized IR output instead of chunks
            optimized_ir = self.generate_optimized_ir(llvm_ir, optimization_suggestions)
            yield ("OPTIMIZED IR", optimized_ir)
                
        except Exception as e:
            raise RuntimeError(f"Optimization failed: {str(e)}")
        
    def extract_llvm_ir(self, extracted_optimized_ir: str) -> str:
        """Extracts valid LLVM IR from the optimized code."""
        # Extract the content between 'define' and 'attributes'
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Extract valid LLVM IR from the optimized code. start code block with <start> and end code block with <end>"),
            ("human", "{extracted_optimized_ir}")
        ])
        chain = prompt | self.llm
        return chain.invoke({"extracted_optimized_ir": extracted_optimized_ir}).content

def main():
    # Example usage
    sample_llvm_ir = """
    define i32 @example_function(i32 %a, i32 %b) {
        %1 = add i32 %a, %b
        %2 = mul i32 %1, %1
        ret i32 %2
    }
    """
    
    # Initialize the optimization agent
    optimizer = Agent()
    
    # Get optimization suggestions
    result = optimizer.optimize_llvm_ir(sample_llvm_ir)

    
    
    # Print results
    print("Optimized LLVM IR:")
    for section, content in result:
        print(f"{section}:")
        print(content)

if __name__ == "__main__":
    main()
