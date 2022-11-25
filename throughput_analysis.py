import os
import re
import datetime
from constants import *
from utilities import *
from math import ceil, floor
import statistics


def get_time(line):
    """Takes a line from logfile and returns the time of logging

    :param line: The line from logfile
    :type line: str
    :return: The datetime object corresponding to the time of logging
    :rtype: datetime.datetime
    """
    
    time = re.search(date_time, line).group(1)
    return datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f")

def get_start_end():
    """Finds the time of the last user authentication and the time of last user removal

    :return: The time of last user authentication, time of last user removal
    :rtype: datetime.datetime, datetime.datetime
    """
    connection_end_time = None
    removal_start_time = None
    for i in BASE_SERVER_PORTS:
        with open(os.path.join("logs", "servers_logs", f"server{i}.log"), 'r') as server_log:
            for line in server_log:
                if re.search(connection_pattern, line) != None or re.search(authentication_pattern, line) != None:
                    time = get_time(line)
                    if connection_end_time == None:
                        connection_end_time = time
                    connection_end_time = max(time, connection_end_time)
                elif re.search(removal_pattern, line) != None:
                    time = get_time(line)
                    if removal_start_time == None:
                        removal_start_time = time
                    removal_start_time = max(removal_start_time, time) 
    return connection_end_time, removal_start_time

def get_cuts(arr):
    """Finds the indices for steady state throughput interval

    :param arr: List of messages per interval
    :type arr: list
    :return: The indices of the steady state part
    :rtype: int, int
    """
    i = -1
    j = 0
    while arr[i] == 0:
        i -= 1
    while arr[j] == 0:
        j += 1
    return j + 2, i - 4

    
def calc_throughput(start_time, end_time):
    """Calculates the throughput

    :param start_time: The time of last user authentication
    :type start_time: datetime.datetime
    :param end_time: The time of last user removal
    :type end_time: datetime.datetime
    :return: Lists of messages per interval (in-throughput, out-throughput)
    :rtype: list, list
    """
    num_ints = ceil(((end_time - start_time).total_seconds()) * 5) 
    in_message_count = [0] * num_ints
    out_message_count = [0] * num_ints
    server_client_count = 0
    client_server_count = 0
    for i in BASE_SERVER_PORTS:
        with open(os.path.join("logs", "servers_logs", f"server{i}.log"), 'r') as server_log:
            for line in server_log:
                if re.search(log_pattern1, line) != None:
                    server_client_count += 1
                    out_message_count[floor(((get_time(line) - start_time).total_seconds()) * 5)] += 1
                elif re.search(log_pattern2, line) != None:
                    in_message_count[floor(((get_time(line) - start_time).total_seconds()) * 5)] += 1
                    client_server_count += 1
    x, y = get_cuts(in_message_count)
    a, b = get_cuts(out_message_count)
    return in_message_count[x:y], out_message_count[a:b]


if __name__ == "__main__":
    connection_pattern = re.compile("NEW USER .* CONNECTED TO THE SERVER")
    authentication_pattern = re.compile("Authenticating .*")
    log_pattern1 = re.compile("SERVER SENT A MESSAGE TO CLIENT .*")
    log_pattern2 = re.compile("CLIENT .* SENT A MESSAGE TO THE SERVER")
    removal_pattern = re.compile(".* REMOVED")

    date_time = re.compile("\[([0-9\-]* [0-9:\.]*)\]")

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
