import asyncio
from backend.models import GenerateRequest, RangeConfig
from backend.ai_engine import AIEngine

async def test_precision():
    store = {"config": {"api_key_1": "dummy", "api_key": "dummy"}}
    
    total_requested = 0
    
    class MockAIEngine(AIEngine):
        def _try(self, prompt, image_data=None, prefer_key=None):
            nonlocal total_requested
            import re
            m = re.search(r"Generate between (\d+) and \d+ test cases", prompt) or \
                re.search(r"CRITICAL: You MUST generate EXACTLY (\d+) test cases", prompt)
            if m:
                count = int(m.group(1))
                total_requested += count
                print(f"Batch/Agent requested: {count}")
            else:
                print(f"NO MATCH in prompt: {prompt[:100]}...")
            return '{"suite_name": "Test", "tests": []}', "mock-model"

    async def run_test_case(tests, agents):
        nonlocal total_requested
        total_requested = 0
        engine = MockAIEngine(store)
        rc = RangeConfig(min_tests=tests, max_tests=tests)
        req = GenerateRequest(url="https://example.com", range_config=rc, is_multi_agent=True, agents=agents)
        await engine.generate_from_url(req)
        print(f"Total requested for {tests} tests / {len(agents)} agents: {total_requested}")
        assert total_requested == tests

    print("Checking 71 tests / 4 agents...")
    await run_test_case(71, ["a", "b", "c", "d"]) # 18, 18, 18, 17 = 71
    
    print("\nChecking 10 tests / 3 agents...")
    await run_test_case(10, ["a", "b", "c"]) # 4, 3, 3 = 10
    
    print("\nChecking 1 test / 5 agents...")
    await run_test_case(1, ["a", "b", "c", "d", "e"]) # 1, 0, 0, 0, 0 = 1 (well, actually 1, 0... might need a max(1) check in dist if we want at least 1 per agent)

if __name__ == "__main__":
    try:
        asyncio.run(test_precision())
    except Exception as e:
        import traceback
        traceback.print_exc()
