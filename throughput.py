import os
import re
import datetime
from constants import *
from utilities import *
from math import ceil, floor
import statistics
SERVER_NUMS = 5

connection_pattern = re.compile("NEW USER .* CONNECTED TO THE SERVER")
log_pattern1 = re.compile("SERVER SENT A MESSAGE TO CLIENT .*")
log_pattern2 = re.compile("CLIENT .* SENT A MESSAGE TO THE SERVER")
removal_pattern = re.compile(".* REMOVED")

date_time = re.compile("\[([0-9\-]* [0-9:\.]*)\]")

def get_time(line):
    time = re.search(date_time, line).group(1)
    return(datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f"))

def get_start_end():
    connection_end_time = None
    removal_start_time = None
    for i in BASE_SERVER_PORTS:
        with open(os.path.join("logs", "servers_logs", f"server{i}.log"), 'r') as server_log:
            for line in server_log:
                if re.search(connection_pattern, line) != None:
                    time = get_time(line)
                    if connection_end_time == None:
                        connection_end_time = time
                    connection_end_time = max(time, connection_end_time)
                elif re.search(removal_pattern, line) != None:
                    time = get_time(line)
                    if removal_start_time == None:
                        removal_start_time = time
                    removal_start_time = min(removal_start_time, time) 
    return connection_end_time, removal_start_time


def calc_throughput(start_time, end_time):
    num_ints = ceil(((end_time - start_time).total_seconds()) * 2) 
    in_message_count = [0] * num_ints
    out_message_count = [0] * num_ints
    server_client_count = 0
    client_server_count = 0
    for i in BASE_SERVER_PORTS:
        with open(os.path.join("logs", "servers_logs", f"server{i}.log"), 'r') as server_log:
            for line in server_log:
                if re.search(log_pattern1, line) != None:
                    server_client_count += 1
                    out_message_count[floor(((get_time(line) - start_time).total_seconds()) * 2)] += 1
                elif re.search(log_pattern2, line) != None:
                    in_message_count[floor(((get_time(line) - start_time).total_seconds()) * 2)] += 1
                    client_server_count += 1
    return(in_message_count[2:-6], out_message_count[2:-6])
start_time, end_time = get_start_end()
in_throughput, out_throughput = calc_throughput(start_time, end_time)

print(f'''In-throughput-
Mean = {statistics.mean(in_throughput)}
Median = {statistics.median(in_throughput)}
Std Dev = {statistics.stdev(in_throughput)}
''')
print(f'''Out-throughput-
Mean = {statistics.mean(out_throughput)}
Median = {statistics.median(out_throughput)}
Std Dev = {statistics.stdev(out_throughput)}''')

plot_time_variation(in_throughput)
plot_time_variation(out_throughput)
