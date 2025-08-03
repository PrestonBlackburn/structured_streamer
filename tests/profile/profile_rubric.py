import asyncio
from struct_strm.structs.rubric_structs import (
    simulate_stream_rubric_outline_struct,
    simulate_stream_rubric_final_struct
)
from struct_strm.ui_components import RubricComponent
from pyinstrument import Profiler

async def test_rubric_ui():

    profiler = Profiler(interval=0.00001, async_mode="enabled")
    profiler.start()

    stream = simulate_stream_rubric_outline_struct()
    stream_2 = simulate_stream_rubric_final_struct()

    component = RubricComponent()
    html_component_stream = component.render(stream, stream_2)

    async for item in html_component_stream:
        # helps capture async stack
        await asyncio.sleep(0.0001) 
    
    profiler.stop()
    results_file = "tests/profile/pyinst_profile.html"
    profiler.write_html(results_file)
    
if __name__ == "__main__":
    asyncio.run(test_rubric_ui())