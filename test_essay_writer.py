from test import (
    AgentState,
    plan_node,
    research_plan_node,
    generation_node,
    reflection_node,
    research_critique_node
)

def test_plan_node():
    # Create a sample state using the same AgentState from test.py
    test_state = AgentState(
        task="Write an essay about the impact of artificial intelligence on society",
        plan="",
        draft="",
        critique="",
        content=[],
        max_revisions=3,
        revision_number=0
    )
    
    # Call plan_node
    result = plan_node(test_state)
    
    # Basic assertions
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "plan" in result, "Result should contain 'plan' key"
    assert isinstance(result["plan"], str), "Plan should be a string"
    assert len(result["plan"]) > 0, "Plan should not be empty"
    
    # Print the result for manual inspection
    print("\nPlan Node Test Results:")
    print("=======================")
    print(f"Input task: {test_state['task']}")
    print("\nGenerated plan:")
    print(result["plan"])

def test_research_plan_node():
    # Create a sample state using the same AgentState from test.py
    test_state = AgentState(
        task="Write an essay about the impact of artificial intelligence on society",
        plan="",
        draft="",
        critique="",
        content=[],
        max_revisions=3,
        revision_number=0
    )
    
    # Call research_plan_node
    result = research_plan_node(test_state)
    
    # Basic assertions
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "content" in result, "Result should contain 'content' key"
    assert "queries" in result, "Result should contain 'queries' key"
    assert isinstance(result["content"], list), "Content should be a list"
    assert isinstance(result["queries"], list), "Queries should be a list"
    assert len(result["content"]) > 0, "Content should not be empty"
    assert len(result["queries"]) > 0, "Queries should not be empty"
    
    # Print the results
    print("\nResearch Plan Node Test Results:")
    print("================================")
    print(f"Input task: {test_state['task']}\n")

    # Calculate content pieces per query (2 content pieces per query as per max_results=2)
    content_index = 0
    content_per_query = 2
    
    # Display each query followed by its corresponding content
    for i, query in enumerate(result["queries"], 1):
        print(f"Query {i}:")
        print("-" * 50)
        print(query)
        print("\nResults for this query:")
        print("=" * 50)
        
        # Show the content pieces for this query
        for j in range(content_per_query):
            if content_index < len(result["content"]):
                print(f"\nContent {j+1}:")
                print(result["content"][content_index])
                content_index += 1
        
        print("\n" + "=" * 80 + "\n")

def test_generation_node():
    # Create a sample state with plan and content
    test_state = AgentState(
        task="Write an essay about the impact of artificial intelligence on society",
        plan="1. Introduction to AI\n2. Current Impact\n3. Future Implications",
        draft="",
        critique="",
        content=["AI has transformed various sectors including healthcare and education.", 
                "Recent studies show AI's impact on job market is significant."],
        max_revisions=3,
        revision_number=0
    )
    
    # Call generation_node
    result = generation_node(test_state)
    
    # Basic assertions
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "draft" in result, "Result should contain 'draft' key"
    assert "revision_number" in result, "Result should contain 'revision_number' key"
    assert isinstance(result["draft"], str), "Draft should be a string"
    assert len(result["draft"]) > 0, "Draft should not be empty"
    assert result["revision_number"] == 1, "First revision should be 1"
    
    # Print the results
    print("\nGeneration Node Test Results:")
    print("============================")
    print(f"Input task: {test_state['task']}")
    print(f"\nInput plan:\n{test_state['plan']}")
    print(f"\nInput content pieces: {len(test_state['content'])}")
    print("\nGenerated Draft:")
    print("=" * 50)
    print(result["draft"])
    print("\nRevision number:", result["revision_number"])

def test_reflection_node():
    # Create a sample state with a draft
    test_state = AgentState(
        task="Write an essay about the impact of artificial intelligence on society",
        plan="",
        draft="AI has revolutionized many sectors of society. From healthcare to education, \
              its impact is profound. In healthcare, AI helps in diagnosis and treatment. \
              In education, it provides personalized learning experiences.",
        critique="",
        content=[],
        max_revisions=3,
        revision_number=1
    )
    
    # Call reflection_node
    result = reflection_node(test_state)
    
    # Basic assertions
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "critique" in result, "Result should contain 'critique' key"
    assert isinstance(result["critique"], str), "Critique should be a string"
    assert len(result["critique"]) > 0, "Critique should not be empty"
    
    # Print the results
    print("\nReflection Node Test Results:")
    print("=============================")
    print("Input draft:")
    print("-" * 50)
    print(test_state["draft"])
    print("\nGenerated Critique:")
    print("-" * 50)
    print(result["critique"])

def test_research_critique_node():
    # Create a sample state with a critique
    test_state = AgentState(
        task="Write an essay about the impact of artificial intelligence on society",
        plan="",
        draft="",
        critique="The essay needs more specific examples of AI applications in healthcare. \
                 Include statistics about AI adoption in hospitals. \
                 Add recent breakthroughs in AI-driven medical diagnosis.",
        content=[],
        max_revisions=3,
        revision_number=1
    )
    
    # Call research_critique_node
    result = research_critique_node(test_state)
    
    # Basic assertions
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "content" in result, "Result should contain 'content' key"
    assert "queries" in result, "Result should contain 'queries' key"
    assert isinstance(result["content"], list), "Content should be a list"
    assert isinstance(result["queries"], list), "Queries should be a list"
    assert len(result["content"]) > 0, "Content should not be empty"
    assert len(result["queries"]) > 0, "Queries should not be empty"
    
    # Print the results
    print("\nResearch Critique Node Test Results:")
    print("===================================")
    print("Input critique:")
    print("-" * 50)
    print(test_state["critique"])

    # Display queries and their corresponding content
    content_per_query = 2
    content_index = 0
    
    for i, query in enumerate(result["queries"], 1):
        print(f"\nQuery {i}:")
        print("-" * 50)
        print(query)
        print("\nResults for this query:")
        print("=" * 50)
        
        # Show the content pieces for this query
        for j in range(content_per_query):
            if content_index < len(result["content"]):
                print(f"\nContent {j+1}:")
                print(result["content"][content_index])
                content_index += 1
        
        print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    test_research_critique_node()
