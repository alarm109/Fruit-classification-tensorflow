import csv
import datetime
from pathlib import Path


header = ['Timestamp', 'Loss', 'Accuracy', 'Recall', 'Precision', 'F1_metric', 'AUC', 'Epochs', 'Batch_size']
result_path = './results.csv'


def write_results_to_csv(results, epochs, batch_size):
    results.append(epochs)
    results.append(batch_size)

    timestamp = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
    results.insert(0, timestamp)

    if Path(result_path).exists():
        with open(result_path, 'a') as f:
            writer = csv.writer(f)
            writer.writerow(results)
    else:
        with open(result_path, 'w') as f:
            writer = csv.writer(f)

            writer.writerow(header)
            writer.writerow(results)
