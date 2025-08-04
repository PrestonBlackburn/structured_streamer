import pandas as pd
import matplotlib.pyplot as plt

with open('tests/benchmarks/list_gen_benchmark.csv', 'r') as f:
    df = pd.read_csv(f)
    print(df.head())

    df.plot(kind='line', figsize=(10, 6))
    plt.title('List Generation Benchmark')
    plt.xlabel('Iteration')
    plt.ylabel('Time (seconds)')
    plt.grid(True)
    plt.legend(loc='upper left')
    plt.savefig('tests/benchmarks/list_gen_benchmark.png')
    plt.show()
    plt.close()
    print("Benchmark chart created and saved as 'list_gen_benchmark.png'.")