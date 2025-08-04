import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

with open('tests/benchmarks/list_gen_benchmark.csv', 'r') as f:
    df = pd.read_csv(f)
    print(df.head())

    mean_values = df.mean().to_dict()
    print(mean_values)
    q25_values = df.quantile(0.25).to_dict()
    q75_values = df.quantile(0.75).to_dict()




    # # Example data (replace with your actual values)
    # three groups of metrics
    group_labels = [
        "Time to First Token",
        "Time to First Meaningful Chunk",
        "Time to Final Chunk"
    ]
    means = {
        'Stream': (mean_values['ttft_stream'], mean_values['ttfmc_stream'], mean_values['ttlc_stream']),
        'Static': (mean_values['ttft_static'], mean_values['ttfmc_static'], mean_values['ttlc_static']),
    }

    quartile_errors = {
        'Stream': (
            [mean_values['ttft_stream'] - q25_values['ttft_stream'],
            mean_values['ttfmc_stream'] - q25_values['ttfmc_stream'],
            mean_values['ttlc_stream'] - q25_values['ttlc_stream']],
            [q75_values['ttft_stream'] - mean_values['ttft_stream'],
            q75_values['ttfmc_stream'] - mean_values['ttfmc_stream'],
            q75_values['ttlc_stream'] - mean_values['ttlc_stream']],
        ),
        'Static': (
            [mean_values['ttft_static'] - q25_values['ttft_static'],
            mean_values['ttfmc_static'] - q25_values['ttfmc_static'],
            mean_values['ttlc_static'] - q25_values['ttlc_static']],
            [q75_values['ttft_static'] - mean_values['ttft_static'],
            q75_values['ttfmc_static'] - mean_values['ttfmc_static'],
            q75_values['ttlc_static'] - mean_values['ttlc_static']],
        )
    }
    colors = ['#039BE5', '#2E2424']

    fig, ax = plt.subplots(figsize=(8, 6))

    width = 0.25
    multiplier = 0

    for attribute, measurement in means.items():
        x = np.arange(len(group_labels)) + (multiplier * width)
        bars = ax.bar(x, 
                      measurement, 
                      width, 
                      color = colors[multiplier % len(colors)],
                      alpha=0.7,
                      yerr=quartile_errors[attribute], 
                      label=attribute, 
                      capsize=5,
                          error_kw={
                            'ecolor': '#333333',  # Set the error bar color
                            'elinewidth': 0.8,      # Thickness of error lines
                            'alpha': 0.5          # Opacity
                        }
                )
        multiplier += 1


    ax.set_xticks(np.arange(len(group_labels)) + width / 2, group_labels)
    ax.legend(['This Library', 'Default OpenAI Response'], loc='upper right', fontsize=10)

    # # Aesthetics
    ax.set_ylabel("Time (s)", fontsize=12)
    ax.set_title("LLM Streaming Performance Metrics", fontsize=14, fontweight='bold')
    ax.spines[['top', 'right']].set_visible(False)
    ax.yaxis.grid(True, linestyle='--', alpha=0.6)
    ax.set_axisbelow(True)

    # Optional: Add subtle background color
    fig.patch.set_facecolor('#f7f7f7')
    ax.set_facecolor('#f0f0f0')

    #plt.tight_layout()
    plt.suptitle('Structured Streaming Benchmark', fontsize=14)
    plt.title("Lower is better, (n=20)", fontsize=10)
    plt.ylabel('Time (seconds)')
    plt.grid(True)
    plt.savefig('tests/benchmarks/list_gen_benchmark.png')
    plt.close()
    print("Benchmark chart created and saved as 'list_gen_benchmark.png'.")