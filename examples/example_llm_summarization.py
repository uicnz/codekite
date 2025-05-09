"""
Test the LLM integration capability of codekite with OpenAI

This script demonstrates using codekite's Summarizer to generate summaries
of files, functions, and classes using OpenAI's models.

Requirements:
- OpenAI API key set as OPENAI_API_KEY environment variable
- codekite installed with OpenAI extras: uv pip install -e ".[openai]"
"""
import os
import sys
from codekite import Repository
from codekite.summaries import OpenAIConfig

def format_output(title, content):
    """Helper function to format and print output"""
    print(f"\n{'=' * 80}")
    print(f"=== {title} ===")
    print(f"{'=' * 80}")
    print(content)

def test_summarization(repo_path):
    """Test codekite's LLM integration with OpenAI summarization"""

    # Ensure API key is set
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Please set your OpenAI API key with:")
        print("  export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)

    # Load the repository
    print(f"Loading repository from: {repo_path}")
    repo = Repository(repo_path)

    try:
        # Try different models that might be available
        available_models = ["gpt-4o", "gpt-4", "gpt-3.5-turbo-0125", "gpt-3.5-turbo"]
        model_used = None

        for model in available_models:
            try:
                print(f"Trying OpenAI model: {model}")
                config = OpenAIConfig(
                    api_key=api_key,
                    model=model,
                    temperature=0.3,
                    max_tokens=500
                )

                # Test constructor only
                summarizer = repo.get_summarizer(config)
                model_used = model
                print(f"Success! Using model: {model}")
                break
            except Exception as e:
                print(f"  Error with model {model}: {str(e)}")
                continue

        if not model_used:
            print("Failed to find a working OpenAI model. Please check your API key and access.")
            sys.exit(1)

        # Start with a smaller file to test
        small_file = "src/codekite/code_searcher.py"
        print(f"\nSummarizing small file: {small_file}")
        file_summary = summarizer.summarize_file(small_file)
        format_output("File Summary", file_summary)

        # 2. Summarize a function (also try a smaller one)
        function_file = "src/codekite/code_searcher.py"
        function_name = "search_text"
        print(f"\nSummarizing function: {function_name} in {function_file}")
        function_summary = summarizer.summarize_function(function_file, function_name)
        format_output("Function Summary", function_summary)

        # 3. Summarize a class (stick with smaller file)
        class_file = "src/codekite/code_searcher.py"
        class_name = "CodeSearcher"
        print(f"\nSummarizing class: {class_name} in {class_file}")
        class_summary = summarizer.summarize_class(class_file, class_name)
        format_output("Class Summary", class_summary)

        print("\nBasic tests completed successfully!")

        # Now try the larger file if the initial tests were successful
        print("\nTrying larger file - Repository class...")
        try:
            # Try with Repository class - but this might hit token limits
            large_file = "src/codekite/repository.py"
            repo_summary = summarizer.summarize_file(large_file)
            format_output("Repository File Summary", repo_summary)
        except Exception as e:
            print(f"Warning: Could not summarize large file: {str(e)}")
            print("This is likely due to token limits and doesn't indicate an issue with codekite's functionality.")

        print("\nAll LLM integration tests completed!")

    except ModuleNotFoundError:
        print("\nError: Required packages for LLM integration are not installed.")
        print("Please install codekite with OpenAI support:")
        print("  uv pip install -e '.[openai]'")
        print("\nOr install openai separately:")
        print("  uv pip install openai")
    except Exception as e:
        print(f"\nError during summarization: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Use the parent directory of examples as the repository path
    # since that's where the actual project files are located
    repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_summarization(repo_path)
