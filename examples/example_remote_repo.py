"""
Test codekite's ability to analyze a remote GitHub repository

This script demonstrates how codekite can clone and analyze a remote GitHub repository,
and then use LLMs to generate summaries of its components.

Requirements:
- OpenAI API key set as OPENAI_API_KEY environment variable
- Internet connection to clone the repository
"""
import os
import sys
import time
from codekite import Repository
from codekite.summaries import OpenAIConfig

def format_output(title, content):
    """Helper function to format and print output"""
    print(f"\n{'=' * 80}")
    print(f"=== {title} ===")
    print(f"{'=' * 80}")
    print(content)

def test_remote_repository(repo_url):
    """Test codekite's ability to clone and analyze a remote GitHub repository"""
    start_time = time.time()

    # 1. Initialize Repository with GitHub URL (should auto-clone)
    print(f"Initializing Repository with GitHub URL: {repo_url}")
    print("This will automatically clone the repository to a local cache directory...")
    repo = Repository(repo_url)

    print(f"Repository initialized: {repo}")
    clone_time = time.time() - start_time
    print(f"Time to clone and initialize: {clone_time:.2f} seconds")

    # 2. Test File Structure Analysis
    print("\nAnalyzing repository structure...")
    file_tree = repo.get_file_tree()
    print(f"Found {len(file_tree)} files/directories")

    py_files = [f for f in file_tree if not f.get("is_dir", False) and f["path"].endswith(".py")]
    print(f"Python files: {len(py_files)}")
    if py_files:
        format_output("Sample Python Files", "\n".join([f['path'] for f in py_files[:5]]))

    # 3. Test Symbol Extraction
    if py_files:
        sample_file = py_files[0]["path"]
        print(f"\nExtracting symbols from: {sample_file}")
        symbols = repo.extract_symbols(sample_file)
        print(f"Found {len(symbols)} symbols")
        if symbols:
            format_output("Sample Symbols", "\n".join([f"{s['type']}: {s['name']}" for s in symbols[:5]]))

    # 4. Test Text Search
    print("\nPerforming text search...")
    search_term = "def"
    results = repo.search_text(search_term, file_pattern="*.py")
    print(f"Found {len(results)} matches for '{search_term}'")
    if results:
        format_output("Sample Search Results",
                     "\n".join([f"{r['file']}:{r['line_number']} - {r['line'].strip()}" for r in results[:5]]))

    # 5. Test LLM Integration (if API key is available)
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        try:
            print("\nTesting LLM integration...")
            # Try to find a working model
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

            if model_used:
                # Find a small Python file to summarize
                small_py_files = [f for f in py_files if f.get("size", 100000) < 5000]
                if small_py_files:
                    sample_small_file = small_py_files[0]["path"]
                    print(f"\nSummarizing file: {sample_small_file}")
                    file_summary = summarizer.summarize_file(sample_small_file)
                    format_output("File Summary", file_summary)

                    # If there are symbols in this file, try to summarize one
                    symbols = repo.extract_symbols(sample_small_file)
                    functions = [s for s in symbols if s.get("type").lower() in ["function", "method"]]
                    if functions:
                        func = functions[0]
                        func_name = func["name"]
                        print(f"\nSummarizing function: {func_name}")
                        func_summary = summarizer.summarize_function(sample_small_file, func_name)
                        format_output("Function Summary", func_summary)
        except Exception as e:
            print(f"Error during LLM integration: {str(e)}")
    else:
        print("\nSkipping LLM integration (no OpenAI API key found)")

    # 6. Test Dependency Analysis
    print("\nAnalyzing dependencies...")
    try:
        analyzer = repo.get_dependency_analyzer()
        dep_graph = analyzer.build_dependency_graph()

        if hasattr(dep_graph, 'nodes') and callable(getattr(dep_graph, 'nodes')):
            # NetworkX-like graph interface
            node_count = len(dep_graph.nodes())
            edge_count = len(dep_graph.edges())
            print(f"Dependency graph has {node_count} nodes and {edge_count} edges")
        else:
            # Dictionary-based graph structure
            nodes = list(dep_graph.keys())
            edges = sum(len(deps) for deps in dep_graph.values())
            print(f"Dependency graph has {len(nodes)} nodes and approximately {edges} edges")

        cycles = analyzer.find_cycles()
        if cycles:
            print(f"Found {len(cycles)} import cycles")
        else:
            print("No import cycles found")
    except Exception as e:
        print(f"Error during dependency analysis: {str(e)}")

    # Done!
    total_time = time.time() - start_time
    print(f"\nTotal analysis time: {total_time:.2f} seconds")
    print("Remote repository analysis complete!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        repo_url = sys.argv[1]
    else:
        repo_url = "https://github.com/shaneholloman/codemapper"

    test_remote_repository(repo_url)
