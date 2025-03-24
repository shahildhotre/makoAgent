#LLVM IR Optimization Agentic system

To Run:

1) Install all the dependencies

   pip install -r requirements

3) Update .env file with your OPEN AI Key

4) cd aiagent_playground

    streamlit run app.py

Tech Stack:

Frontend: Streamlit

Backend: Python, LangChain, OpenAI

Demo link: https://www.loom.com/share/3df4bb0f16ba42808216f7db7cb4052b?sid=dbe27a8a-90c6-4b86-a721-e25f6030eff4

Work in progress:
 - Reoptimize Button Support
      - For now we can use Analyze and Optimize button to reoptimize IR or even if generated IR is not parsable
 - Fine Tuned LLM on LLVM IR Optimization
 - File Upload Support
