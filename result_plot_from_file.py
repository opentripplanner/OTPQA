import json, violin

def plot_results(dataset, label):

    data = []
    total_times = []

    if "responses" in dataset:
        for resp in dataset['responses']:
            if "total_time" in resp:
                total_times.append( float(resp["total_time"][:-5]) / 1000.00) #to seconds

        data.append(total_times)
        violin.violin_plot(data, bp=True, scale=True, labels=[label])


if __name__=='__main__':
    import sys

    if len(sys.argv)<3:
        print "usage: cmd json_summary_file_name plot_label"
        exit()

    dataset = json.load(open(sys.argv[1]))
    plot_results(dataset, sys.argv[2])
