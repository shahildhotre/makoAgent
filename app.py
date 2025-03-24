import streamlit as st
import os
import sys
import inspect
from agent import Agent
from problems.api import Problem
from main import main, benchmark
import importlib
import re

def get_source_code(obj):
    """Get source code of a function or class"""
    return inspect.getsource(obj)

def app_main():
    st.set_page_config(layout="wide")
    
    # Initialize optimized_ir at the start
    optimized_ir = ""
    
    # Initialize session state if not exists
    if 'llvm_ir' not in st.session_state:
        st.session_state.llvm_ir = ""
    if 'benchmark_metrics' not in st.session_state:
        st.session_state.benchmark_metrics = []
    if 'test_data' not in st.session_state:
        st.session_state.test_data = None
    
    # Initialize the agent
    optimizer = Agent()
    
    # Sidebar with file selection
    st.sidebar.title("File Selection")
    
    # Create a dictionary of available problems/files
    available_files = {}
    problems_dir = "problems"
    
    # Create problems directory if it doesn't exist
    if not os.path.exists(problems_dir):
        os.makedirs(problems_dir)
        st.sidebar.warning(f"Created new '{problems_dir}' directory. Please add your Python files there.")
        available_files["Example"] = {
            "path": "example",
            "code": "def example():\n    return 42",
            "description": "Example function - please add your own files to the 'problems' directory"
        }
    else:
        # Scan the problems directory for Python files
        for file in os.listdir(problems_dir):
            if file.endswith(".py") and not file.startswith("__") and not file.startswith("api.py"):
                module_name = file[:-3]  # Remove .py extension
                file_path = os.path.join(problems_dir, file)
                
                try:
                    available_files[module_name] = {
                        "path": f"{module_name}",  # Simplified path
                        "code": open(file_path).read(),
                        "description": "Python file"
                    }
                except Exception as e:
                    st.sidebar.warning(f"Error loading {file}: {str(e)}")
    
    selected_file = st.sidebar.selectbox(
        "Select a function to analyze",
        list(available_files.keys())
    )
    
    # Main content area
    st.title("LLVM IR Optimizer")
    
    # Display selected file information
    if selected_file:
        st.subheader(f"Selected File: {available_files[selected_file]['path']}")

        # Extract number from problem name (e.g., 'problem1' -> '1')
        pidx = ''.join(filter(str.isdigit, available_files[selected_file]['path']))
        if not pidx:
            st.error("File name must contain a number (e.g., problem1.py)")
            return

        # Display the Python source code
        st.subheader("Python Source Code")
        
        st.code(available_files[selected_file]['code'], language="python")
        
        
       
        if st.button("Generate LLVM IR"):
            with st.spinner("Generating LLVM IR..."):
                try:
                    sys.argv = ['dummy_program_name', '--problem', pidx]
                    main()
                except Exception as e:
                    st.error(f"Error generating LLVM IR: {str(e)}")

        llvm_ir = ""  # Initialize the variable
        if st.session_state.llvm_ir:
            llvm_ir = st.text_area(
                "Generated LLVM IR",
                value=st.session_state.llvm_ir,
                height=200,
                disabled=False
            )
        if st.session_state.benchmark_metrics:
            st.text_area(
                "Benchmark Metrics",
                value=st.session_state.benchmark_metrics,
                height=100,
                disabled=False
            )
            
        if st.session_state.test_data is not None:
            st.write("Test Data:")
            st.write(st.session_state.test_data)
       
        if st.button("Analyze and Optimize"):
            # Define the display order of sections
            section_order = ["CODE EXPLANATION", "BOTTLENECKS", "OPTIMIZATION RATIONALE", "OPTIMIZED IR"]
            sections = {name: st.empty() for name in section_order}
            section_content = {name: "" for name in section_order}
            
            with st.spinner("Analyzing code..."):
              
                current_section = None
                for section_name, chunk in optimizer.optimize_llvm_ir(llvm_ir):
                    # Display section header only when switching to a new section
                    if section_name in section_order and section_name != current_section:
                        st.subheader(section_name)
                        current_section = section_name
                    
                    # Display the section content
                    if section_name != "OPTIMIZED IR":
                        container = st.container()
                        with container:
                            st.write(chunk)
                            # Auto-scroll
                            st.markdown('<script>window.scrollTo(0,document.body.scrollHeight);</script>', unsafe_allow_html=True)
                    else:
                        # Accumulate chunks and update the same code block
                        optimized_ir += chunk
                        container = st.container()
                        with container:
                            st.code(optimized_ir, language="llvm")
                            # Auto-scroll
                            st.markdown('<script>window.scrollTo(0,document.body.scrollHeight);</script>', unsafe_allow_html=True)

                        
                        # Use the optimizer to extract valid LLVM IR
                        extracted_ir = optimizer.extract_llvm_ir(optimized_ir)

                        # st.code(extracted_ir, language="llvm")

                        # regex code to get code between <start> and <end>
                        extracted_ir = re.search(r'<start>(.*?)<end>', extracted_ir, re.DOTALL)
                        if not extracted_ir:
                            st.error("Could not find valid LLVM IR between <start> and <end> tags")
                            return
                        
                        extracted_ir = extracted_ir.group(1)
                        
                        # Clean up the IR
                        # Remove markdown code block markers
                        extracted_ir = re.sub(r'```llvm\s*', '', extracted_ir)
                        extracted_ir = re.sub(r'```\s*', '', extracted_ir)
                        
                        # Remove any empty lines at start/end and ensure proper line endings
                        extracted_ir = '\n'.join(line for line in extracted_ir.splitlines() if line.strip())

                        # Ensure the IR contains a function definition
                        if not re.search(r'define.*@\w+', extracted_ir):
                            st.error("Invalid LLVM IR: must contain a function definition")
                            return

                        # Display the cleaned IR
                        st.code(extracted_ir, language="llvm")
                        
                        try:
                            # call optimize function from problems.api
                            args = ['dummy_program_name', '--problem', pidx]
                            if extracted_ir:
                                # Ensure the IR is properly formatted
                                formatted_ir = extracted_ir.strip()
                                args.extend(['--llvm_ir', formatted_ir])
                            sys.argv = args
                            main()
                        except AssertionError as e:
                            st.error("Error: Invalid LLVM IR format. Please ensure the IR contains the correct function definition.")
                        except Exception as e:
                            st.error(f"Error during optimization: {str(e)}")

        # Add buttons for reoptimization and benchmarking

        if st.button("Reoptimize"):
            if optimized_ir:
                with st.spinner("Reoptimizing..."):
                    try:
                        for section_name, chunk in optimizer.optimize_llvm_ir(optimized_ir):
                            if section_name == "OPTIMIZED IR":
                                st.code(chunk, language="llvm")
                    except Exception as e:
                        st.error(f"Error during reoptimization: {str(e)}")
            else:
                st.warning("Please generate and optimize LLVM IR first")

        if st.button("Run Benchmark"):
            if optimized_ir:
                with st.spinner("Running benchmark..."):
                    try:
                        # Add your benchmark logic here
                        st.success("Benchmark completed!")
                    except Exception as e:
                        st.error(f"Error during benchmark: {str(e)}")
            else:
                st.warning("Please generate and optimize LLVM IR first")

if __name__ == "__main__":
    app_main() 